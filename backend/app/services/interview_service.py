# backend/app/services/interview_service.py
from app.extensions import db
from app.models.interview import Interview, InterviewChat
from app.models.prompt import AiPrompt
from app.models.knowledge import KnowledgeItem
from app.utils.llm_client import DeepSeekClient
from openai import OpenAI
from flask import current_app
import json
from app.models.interview import InterviewScore, Dimension
import json
from sentence_transformers import SentenceTransformer

# 推荐在类外部进行全局加载，避免每次调用时重复加载模型进内存
# 'BAAI/bge-small-zh-v1.5' 首次运行会自动下载
local_embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
class InterviewService:
    # @staticmethod
    # def get_embedding(text):
    #     """调用嵌入模型获取文本的 1536 维向量"""
    #     client = OpenAI(
    #         api_key=current_app.config['EMBEDDING_API_KEY'],
    #         base_url=current_app.config.get('EMBEDDING_BASE_URL')  # 若使用第三方兼容API则配置
    #     )
    #     response = client.embeddings.create(
    #         input=text,
    #         model="text-embedding-3-small"  # 或你的具体模型名称
    #     )
    #     return response.data[0].embedding

    @staticmethod
    def get_embedding(text):
        """调用本地开源模型获取文本向量"""
        # bge-small-zh 输出为 512 维向量
        embeddings = local_embedding_model.encode(text)
        return embeddings.tolist()

    @staticmethod
    def start_interview(user_id, job_id):
        # 1. 创建面试记录
        interview = Interview(user_id=user_id, job_id=job_id, status='in_progress', question_count=1)
        db.session.add(interview)
        db.session.commit()

        # 2. 动态获取角色设定与提示词
        prompt_config = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
        system_msg = prompt_config.system_prompt if prompt_config else "你是一个专业的面试官。"
        greeting = prompt_config.greeting_message if prompt_config else "你好，我们开始面试吧。"

        # 3. 记录开场白至 InterviewChat
        chat = InterviewChat(interview_id=interview.id, role='ai', content=greeting)
        db.session.add(chat)
        db.session.commit()

        return {"interview_id": interview.id, "question": greeting}

    @staticmethod
    def process_chat_round_stream(interview_id, user_answer):
        """处理对话并返回流式生成器"""
        interview = Interview.query.get(interview_id)

        # 1. 记录用户回答
        user_chat = InterviewChat(interview_id=interview.id, role='user', content=user_answer)
        db.session.add(user_chat)
        interview.question_count += 1

        # 2. 向量检索：匹配相关的考察知识点或参考答案
        user_vector = InterviewService.get_embedding(user_answer)
        # 依据 L2 距离查询最相关的知识库条目
        related_knowledge = KnowledgeItem.query.filter_by(job_id=interview.job_id) \
            .order_by(KnowledgeItem.embedding.l2_distance(user_vector)).limit(1).first()

        # 3. 组装上下文与 RAG 提示词
        prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id).first()
        messages = [{"role": "system", "content": prompt_config.system_prompt if prompt_config else "你是面试官。"}]

        if related_knowledge:
            messages.append({"role": "system",
                             "content": f"参考知识点：{related_knowledge.content}。请依据此知识点对用户的回答进行追问或评价。"})

        # 加载历史对话
        history = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
        for msg in history:
            messages.append({"role": "user" if msg.role == 'user' else "assistant", "content": msg.content})

        # 4. 调用大模型流式输出
        llm = DeepSeekClient()
        response_stream = llm.generate_reply(messages, stream=True)

        full_reply = ""
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                full_reply += content
                # 按照 Server-Sent Events (SSE) 格式 yielded
                yield f"data: {json.dumps({'chunk': content})}\n\n"

        # 5. 流式输出结束后，异步或在此处将 AI 回复存入数据库
        ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=full_reply)
        db.session.add(ai_chat)
        db.session.commit()

        @staticmethod
        def finish_interview(interview_id):
            """结束面试并生成评价写入数据库"""
            interview = Interview.query.get(interview_id)
            if interview.status == 'completed':
                return

            # 1. 提取所有对话记录
            chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
            chat_history = "\n".join([f"{c.role}: {c.content}" for c in chats])

            # 2. 调用大模型生成 JSON 格式的评价
            system_prompt = """
                请作为资深面试官对以下面试记录进行评分。
                必须严格返回 JSON 格式，包含：total_score(总分0-100), dimensions(包含: 技术正确性, 逻辑严谨性, 岗位匹配度, 表达沟通, 应变能力。每个维度提供 score 0-100 和 comment 评语)。
                """
            llm = DeepSeekClient()
            response_text = llm.generate_reply([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_history}
            ])

            # 解析 JSON（实际应用需增加 JSON 提取正则表达式及异常重试机制）
            report_data = json.loads(response_text)

            # 3. 更新面试总表
            interview.total_score = report_data.get("total_score", 0)
            interview.status = 'completed'

            # 4. 写入维度评分表
            for dim_name, dim_data in report_data.get("dimensions", {}).items():
                dimension = Dimension.query.filter_by(name=dim_name).first()
                if dimension:
                    score_record = InterviewScore(
                        interview_id=interview.id,
                        dimension_id=dimension.id,
                        score=dim_data.get("score"),
                        comment=dim_data.get("comment")
                    )
                    db.session.add(score_record)

            db.session.commit()
            return report_data