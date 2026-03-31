# backend/app/services/interview_service.py
import os
import re
import json

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
from app.services.asr_service import global_speed_cache
from app.models.interview import Interview, InterviewChat
from app.models.prompt import AiPrompt
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.models.example import Example
from app.models.question import Question
from app.utils.llm_client import DeepSeekClient
from app.models.interview import InterviewScore, Dimension
from openai import OpenAI
from flask import current_app
from sentence_transformers import SentenceTransformer
from datetime import datetime




# 推荐在类外部进行全局加载，避免每次调用时重复加载模型进内存
# 'BAAI/bge-small-zh-v1.5' 首次运行会自动下载
local_embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5', local_files_only=False)
# ================= 新增：配置 Tokenizer 安全截断 =================
# 显式限制模型的最大序列长度为 512（bge-small 默认上限）。
# 这样即使输入的字符串 token 数量超过上限，底层的 tokenizer 也会自动进行安全截断，
# 而不会报 token index out of range 错误或 warning。
local_embedding_model.max_seq_length = 512
# =============================================================

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

        # ================= 直接从全局缓存中获取语速 =================
        # 如果当前回答的文本刚好在缓存里，说明是刚才语音识别来的，拿到语速并删掉缓存
        actual_speed = global_speed_cache.pop(user_answer, None)
        # ============================================================

        # 1. 记录用户回答
        user_chat = InterviewChat(interview_id=interview.id, role='user', content=user_answer)
        db.session.add(user_chat)
        interview.question_count += 1

        # 2. 向量检索：匹配相关的考察知识点或参考答案
        user_vector = InterviewService.get_embedding(user_answer)
        # 依据 L2 距离查询最相关的知识库条目
        related_question = Question.query.filter_by(job_id=interview.job_id, status='published') \
            .order_by(Question.embedding.l2_distance(user_vector)).limit(1).first()

        # 3. 组装上下文与 RAG 提示词
        prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id, is_active=True).first()
        base_prompt = prompt_config.system_prompt if prompt_config else "你是面试官，【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。"

        # ================= 优化点：动态注入“面试大纲” =================
        # 从数据库拉取真实的知识点，约束 AI 只能在这个范围内提问
        # 获取当前岗位下所有题目的关联标签
        questions = Question.query.filter_by(job_id=interview.job_id).all()
        tag_set = set()
        for q in questions:
            for tag in q.knowledge_tags:
                tag_set.add(tag.name)
        valid_tags_str = "、".join(list(tag_set))

        # ================= 动态拼装情感安抚指令 =================
        emotion_instruction = ""
        if actual_speed is not None:
            emotion_instruction = f"""
                【语音情感与状态隐式分析】：
                用户本次回答使用的是语音输入。系统检测到其语速为 {actual_speed} 字/秒。
                （参考：正常中等语速约 3-5 字/秒。大于 5 字/秒可能偏快/紧张/激动，小于 3 字/秒可能偏慢/犹豫/边想边答）。
                请你结合语速和文本内容，简单分析候选人当前的情绪状态，并**在本次回复的最开头，用一两句话自然地给予情绪反馈或安抚**（例如：“听得出你有些紧张，没关系...”）。
                    """
        # ========================================================

        enhanced_system_prompt = f"""
                {base_prompt}
                {emotion_instruction}
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

        if related_question:
            messages.append({"role": "system",
                     "content": f"参考题目：{related_question.content}。参考答案要点：{related_question.reference_answer}。请围绕此知识点对候选人进行专业追问。"})

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

# 写报告逻辑
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
        # 获取当前岗位下所有题目的关联标签
        questions = Question.query.filter_by(job_id=interview.job_id).all()
        tag_set = set()
        for q in questions:
            for tag in q.knowledge_tags:
                tag_set.add(tag.name)
        valid_tags_str = "、".join(list(tag_set))
        # ======================================================================
        # ======================================================================

        # ================= 优化点 2: 引入优秀回答范例，提升 AI 建议的具体性 =================
        # 用面试核心对话内容做向量检索
        combined_text = " ".join([c.content for c in chats if c.role == 'user'])
        example_context = ""

        # 防空判断，避免没有 user 回复时获取 embedding 报错
        if combined_text.strip():
            # 【修改点】：将截取长度缩减到 400 字符，避免汉字密集导致 Token 溢出 512 上限
            chat_vector = InterviewService.get_embedding(combined_text[-400:])

            if chat_vector:
                # 向量检索相关的优秀范例
                related_examples = Example.query.filter_by(job_id=interview.job_id) \
                    .order_by(Example.embedding.l2_distance(chat_vector)).limit(2).all()

                if related_examples:
                    example_context = "\n\n【优秀回答参考范例】：\n请对比候选人回答与以下范例，并在给出建议时适当参考：\n"
                    for ex in related_examples:
                        example_context += f"问题：{ex.question}\n回答框架：{ex.framework}\n范例回答：{ex.answer}\n---\n"
        # ====================================================================================


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
                {example_context}
                """
        llm = DeepSeekClient()
        response_text = llm.generate_reply([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"面试记录如下：\n{chat_history}"}
        ])

        # ================= 优化点：增强 JSON 正则提取与异常阻断 =================
        try:
            # 1. 粗略清理 markdown 标记
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

            # 2. 引入正则，提取首尾大括号之间的核心 JSON 块（防止 AI 在前后加废话）
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(0)
            else:
                raise ValueError("未在模型响应中匹配到有效的 JSON 结构")

            report_data = json.loads(cleaned_text)

        except (json.JSONDecodeError, ValueError) as e:
            # 记录真实报错（如果你配置了日志，建议加上 current_app.logger.error）
            print(f"解析报告 JSON 失败: {str(e)}。原始响应: {response_text}")

            # 核心防线：终止向下执行，防止将 0 分存入数据库
            db.session.rollback() # 回滚可能存在的意外事务

            # 直接抛出异常，触发 v1/interview.py 的 except 捕获机制
            raise ValueError("AI 报告生成异常，请稍后再试（大模型返回格式不合规）")
            
            # # 返回明确的错误结构给前端，前端可据此提示用户“报告生成异常，请重试”
            # # 注意：此时 interview.status 依然是 'evaluating'，为重试留下了余地
            # return {
            #     "error": "AI 报告生成异常，请稍后再试",
            #     "detail": "大模型返回格式不合规"
            # }, 500
        # ========================================================================

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
        # ================= 优化点 3: 严格校验，切断自动生成逻辑 =================
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