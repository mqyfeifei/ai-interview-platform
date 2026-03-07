# backend/app/services/interview_service.py
import os

# 启用 Hugging Face 在线模式并配置中国镜像站
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["HF_DATASETS_OFFLINE"] = "0"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

try:
    import huggingface_hub.constants as hf_constants
    hf_constants.HF_HUB_OFFLINE = False
except Exception:
    pass

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
from datetime import datetime
from app.models.learning import KnowledgeTag, UserKnowledgeMastery

# 推荐在类外部进行全局加载，避免每次调用时重复加载模型进内存
# 'BAAI/bge-small-zh-v1.5' 首次运行会自动下载
local_embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5', local_files_only=False)
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
        interview = Interview(
            user_id=user_id,
            job_id=job_id,
            status='in_progress',
            question_count=1,
            start_time=datetime.now()
        )
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
        base_prompt = prompt_config.system_prompt if prompt_config else "你是面试官，【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。"

        # ================= 优化点：动态注入“面试大纲” =================
        # 从数据库拉取真实的知识点，约束 AI 只能在这个范围内提问
        existing_tags = KnowledgeTag.query.all()
        tag_list = [t.name for t in existing_tags]
        tags_str = "、".join(tag_list)

        enhanced_system_prompt = f"""
                {base_prompt}

                【面试提问大纲约束】：
                为了保证面试的标准化，请你**严格**围绕以下“面试大纲”中的知识点向候选人提问。
                - 每次提问请挑选 1 个具体的知识点进行深入考察。
                - 请不要提出大纲范围之外（天马行空）的技术问题。
                - 如果候选人回答不会，请宽慰他，并从大纲中换一个全新的知识点继续提问。

                面试大纲（标准知识点库）：
                [{tags_str}]
                """
        # ===============================================================

        messages = [{"role": "system", "content": enhanced_system_prompt}]

        if related_knowledge:
            messages.append({"role": "system",
                             "content": f"参考知识点：{related_knowledge.content}。请依据此知识点对用户的回答进行专业追问或评价。"})
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
                # 直接将内容流式发给前端，前端需通过正则检测到 [INTERVIEW_OVER] 后自动调用 /finish 接口
                yield f"data: {json.dumps({'chunk': content})}\n\n"

        # 5. 清理标识符并存入数据库
        # 将特殊标记从存入数据库的真实对话中剔除，保持聊天记录干净
        clean_reply = full_reply.replace("[INTERVIEW_OVER]", "").strip()
        ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=clean_reply)
        db.session.add(ai_chat)

        # 可选：如果后端检测到结束，可将状态更为待评价
        if "[INTERVIEW_OVER]" in full_reply:
            interview.status = 'evaluating'
        db.session.commit()

    @staticmethod
    def finish_interview(interview_id):
        """结束面试并生成详尽评价写入数据库"""
        interview = Interview.query.get(interview_id)
        if interview.status == 'completed':
            return {"msg": "面试已出具报告", "reportId": interview.id}


        # 1. 提取所有对话记录
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
        chat_history = "\n".join([f"{c.role}: {c.content}" for c in chats])

        # ================= 优化点 1: 扁平化组装真实标准知识点 =================
        existing_tags = KnowledgeTag.query.all()
        tag_list = [t.name for t in existing_tags]
        valid_tags_str = "、".join(tag_list)
        # ======================================================================
        # ======================================================================

        # 2. 强化系统提示词，强制输出详尽的 JSON 结构
        system_prompt = f"""
                    请作为资深面试官对以下面试记录进行综合评估。
                    必须严格返回 JSON 格式，不要输出任何额外的 markdown 标记或解释说明。结构如下：
                    {{
                        "total_score": 85,
                        "dimensions": {{
                            "技术正确性": {{"score": 80, "comment": "评价..."}},
                            "逻辑严谨性": {{"score": 90, "comment": "评价..."}},
                            "岗位匹配度": {{"score": 85, "comment": "评价..."}},
                            "表达沟通": {{"score": 80, "comment": "评价..."}},
                            "应变能力": {{"score": 75, "comment": "评价..."}}
                        }},
                        "highlights": "列出面试中表现突出的至少2个亮点",
                        "improvements": "指出回答中的主要不足与知识盲区",
                        "suggestions": "针对不足给出3条具体、可操作的学习改进建议",
                        "knowledge_tags_eval": {{
                            "真实的知识点名称": 20
                        }}
                    }}

                【绝对指令】：对于 knowledge_tags_eval 字段，你**只能**从下面的“标准知识点库”中挑选你在对话中考察到的知识点进行 0-100 的打分。
                如果候选人回答完全错误或不会，给20分以下。
                **禁止自己捏造、改写或发明新的知识点名称！如果对话涉及的知识不在下表中，请忽略它。**

                标准知识点库：
                [{valid_tags_str}]
                """
        llm = DeepSeekClient()
        response_text = llm.generate_reply([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"面试记录如下：\n{chat_history}"}
        ])

        # 清理可能附带的 markdown 格式以确保 JSON 解析成功
        cleaned_json_text = response_text.replace("```json", "").replace("```", "").strip()
        report_data = json.loads(cleaned_json_text)

        # 3. 写入总表详细评价字段
        interview.total_score = report_data.get("total_score", 0)
        interview.evaluation_highlights = report_data.get("highlights", "")
        interview.evaluation_improvements = report_data.get("improvements", "")
        interview.evaluation_suggestions = report_data.get("suggestions", "")
        interview.status = 'completed'
        # ================= 新增：记录结束时间和计算用时 =================
        interview.end_time = datetime.now()  # 记录当前结束时间
        if interview.start_time:
            # 计算时间差，并将总秒数存入 used_time 字段
            time_diff = interview.end_time - interview.start_time
            interview.used_time = int(time_diff.total_seconds())
        # ================================================================

        # 4. 写入维度评分表
        for dim_name, dim_data in report_data.get("dimensions", {}).items():
            dimension = Dimension.query.filter_by(name=dim_name).first()
            if dimension:
                score_record = InterviewScore(
                    interview_id=interview.id,
                    dimension_id=dimension.id,
                    score=dim_data.get("score", 0),
                    comment=dim_data.get("comment", "")
                )
                db.session.add(score_record)
        # ================= 优化点 2: 严格校验，切断自动生成逻辑 =================
        tags_eval = report_data.get("knowledge_tags_eval", {})
        for tag_name, score in tags_eval.items():
            # 严格去数据库匹配已有的标签，找不到就直接丢弃（防大模型幻觉）
            tag = KnowledgeTag.query.filter_by(name=tag_name).first()
            if tag:
                mastery = UserKnowledgeMastery.query.filter_by(user_id=interview.user_id, tag_id=tag.id).first()
                if not mastery:
                    # 用户第一次接触这个标签，直接存入分数
                    mastery = UserKnowledgeMastery(user_id=interview.user_id, tag_id=tag.id,
                                                   mastery_level=score)
                    db.session.add(mastery)
                else:
                    # 已有记录，将历史分数与本次分数取平均（模拟平滑的成长或遗忘）
                    mastery.mastery_level = int((mastery.mastery_level + score) / 2)
        # ========================================================================

        db.session.commit()
        result = {
            "reportId": interview.id,
            "jobName": interview.job.name if hasattr(interview, 'job') and interview.job else None
        }
        result.update(report_data)
        return result