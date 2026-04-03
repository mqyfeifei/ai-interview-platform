# backend/app/services/interview_service.py
import os
import re
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
from app.services.tts_service import TTSService, bytes_to_b64
from app.services.resume_service import ResumeService
from app.models.interview import Interview, InterviewChat
from app.models.prompt import AiPrompt
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.models.example import Example
from app.models.question import Question
from app.models.interview import InterviewScore, Dimension, TTSAudio
from app.utils.llm_client import DeepSeekClient

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
    # === 新增：全局线程池，用于异步 TTS 合成 ===
    # max_workers=5 表示最多同时处理 5 个 TTS 请求
    tts_executor = ThreadPoolExecutor(max_workers=5)
    
    @staticmethod
    def _synthesize_audio_async(text, voice, fmt='mp3'):
        """
        异步 TTS 合成包装器
        在线程池中执行同步的 synthesize_bytes，避免阻塞主线程
        """
        try:
            # 使用火山引擎或本地 pyttsx3 合成音频
            audio_bytes = TTSService.synthesize_bytes(text, voice=voice, fmt=fmt)
            return audio_bytes
        except Exception as e:
            print(f'异步 TTS 合成失败：{e}')
            return None
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
    def _extract_resume_context(user_id: int, max_chars: int = 800) -> str:
        """
        拉取并解析用户主简历，进行去敏与核心要点抽取，防止 Token 溢出。
        """
        try:
            # 获取主简历及其 JSON content
            resume_data = ResumeService.get_main_resume(user_id)
            content = resume_data.get('content', {})
            if not content:
                return ""

            # 1. 基础信息去敏 (绝对禁止加入手机号和邮箱)
            personal = content.get('personal', {})
            name = personal.get('name', '候选人')

            # 2. 技能抽取 (Top-10)
            skills_list = content.get('skills', [])
            skills_names = [s.get('name', '') for s in skills_list if s.get('name')]
            skills_str = "、".join(skills_names[:10])

            # 3. 工作经历抽取 (最近 2 条)
            # 3. 【修复点】：合并工作、实习、校园经历
            works = content.get('workExperiences', [])
            interns = content.get('internshipExperiences', [])
            campus = content.get('campusExperiences', [])
            all_exps = []
            for w in works:
                all_exps.append({'org': w.get('company', '某公司'), 'role': w.get('role', '某职位'), 'period': f"{w.get('startDate', '')} 至 {w.get('endDate', '')}", 'desc': w.get('description', '')})
            for i in interns:
                all_exps.append({'org': i.get('company', '某公司'), 'role': i.get('role', '实习生'), 'period': f"{i.get('startDate', '')} 至 {i.get('endDate', '')}", 'desc': i.get('description', '')})
            for c in campus:
                org_name = c.get('school') or c.get('organization') or '某学校/组织'
                all_exps.append({'org': org_name, 'role': c.get('role', '成员'), 'period': f"{c.get('startDate', '')} 至 {c.get('endDate', '')}", 'desc': c.get('description', '')})

            work_context = ""

            # 取最前面的 3 条经历（前端传入通常已经按时间排好序）
            for exp in all_exps[:3]:
                desc = exp['desc'].replace('\n', ' ')[:100] if exp['desc'] else ''
                work_context += f"- {exp['org']} | {exp['role']} ({exp['period']})\n  核心职责/成就: {desc}...\n"

            # 4. 组装简历摘要模板
            resume_text = f"""
            【候选人简历摘要】
            - 姓名: {name}
            - 核心技能: {skills_str if skills_str else '未填写'}
            - 近期经历:
            {work_context if work_context else '未填写'}
            """

            # 5. 安全硬截断，作为兜底防止恶意的超长输入
            return resume_text.strip()[:max_chars]

        except Exception as e:
            print(f"简历摘要提取失败: {str(e)}")
            return ""

    @staticmethod
    def start_interview(user_id, job_id):
        # 0. 【修复点】：提前拉取简历，判断是否为空
        resume_data = ResumeService.get_main_resume(user_id)
        content = resume_data.get('content', {})
        has_experience = bool(content.get('workExperiences') or content.get('internshipExperiences') or content.get('campusExperiences'))
        has_skills = bool(content.get('skills'))
        # 如果既没有经历也没有技能，判定为空简历
        is_resume_empty = not (has_experience or has_skills)

        # 1. 创建面试记录
        interview = Interview(
            user_id=user_id,
            job_id=job_id,
            status='in_progress',
            question_count=1,
            start_time=datetime.now()
        )
        db.session.add(interview)
        db.session.flush() # 使用 flush 获取 interview.id 供后续绑定
        # db.session.commit()

        # 2. 动态获取角色设定与提示词
        prompt_config = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
        base_greeting = prompt_config.greeting_message if prompt_config else "你好，我们开始面试吧。"
        greeting = base_greeting

        # 3. 【修复点】：结合简历生成个性化开场白
        if not is_resume_empty:
            try:
                resume_context = InterviewService._extract_resume_context(user_id)
                llm = DeepSeekClient()
                # 要求 LLM 融合基础配置和简历信息，生成一句话开场
                sys_msg = f"你是一个专业的面试官。请根据候选人简历摘要，结合默认开场白：【{base_greeting}】，生成一句自然、友好的个性化开场欢迎语（要求：绝对不要提问，只打招呼并简短提及对方的背景，字数控制在80字左右）。\n\n{resume_context}"

                greeting_reply = llm.generate_reply([{"role": "system", "content": sys_msg}])
                if greeting_reply:
                    greeting = greeting_reply.strip()
            except Exception as e:
                print(f"个性化开场白生成失败，降级使用默认配置: {str(e)}")

        # 4. 记录开场白至 InterviewChat
        chat = InterviewChat(interview_id=interview.id, role='ai', content=greeting)
        db.session.add(chat)
        db.session.commit()

        # 5. 【修复点】：下发 warning 字段，供前端弹窗/Toast提示
        return {
            "interview_id": interview.id,
            "question": greeting,
            "warning": "系统检测到您的简历未完善，本次面试将进入「标准盲面」模式，无法为您进行个性化项目追问。" if is_resume_empty else None
        }

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
        base_prompt = prompt_config.system_prompt if prompt_config else "你是面试官，【核心指令】：当你觉得已经问了足够多的问题（例如超过 5 题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。"
    
        # ================= 优化点：动态注入"面试大纲" =================
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
    
        resume_context = InterviewService._extract_resume_context(interview.user_id)
    
        enhanced_system_prompt = f"""
                {base_prompt}
                {emotion_instruction}
                {resume_context}
                【提问策略调整指令】：
                如果你在上述“候选人简历摘要”中看到了相关的项目和技能，请尽量结合 TA 的实际过往经历进行提问（例如：“你在 X 公司的 Y 项目中用到了 Z 技术，能具体说说...”）。如果简历为空，则直接进入常规提问。
                    
                【面试提问大纲约束】：
                为了保证面试的标准化，请你**严格**围绕以下“面试大纲”中的知识点向候选人提问。
                - 每次提问请挑选 1 个具体的知识点进行深入考察。
                - 请不要提出大纲范围之外（天马行空）的技术问题。
                - 如果候选人回答不会，请宽慰他，并从大纲中换一个全新的知识点继续提问。
                    
                面试大纲（标准知识点库）：
                [{valid_tags_str}]
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
        audio_chunks = []
        # === 新增：标点符号缓冲机制 ===
        sentence_buffer = ""
        # 匹配中文和英文的句末停顿符号
        punctuation_pattern = re.compile(r'[。！？；\n\!\?\;]')
            
        # === 新增：音频队列，用于缓存异步 TTS 的结果 ===
        import queue
        audio_queue = queue.Queue()
            
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                full_reply += content
                sentence_buffer += content
    
                # 初始化准备传给前端的 payload，无论有没有音频，文字都要立刻传过去保证打字机效果
                payload = {'chunk': content}
    
                # === 使用异步 TTS 合成，不阻塞流式响应 ===
                # 检查缓冲字符串是否以标点符号结尾（或者是包含换行符）
                if punctuation_pattern.search(content):
                    try:
                        voice = getattr(prompt_config, 'preferred_voice', 'BV001_streaming') if prompt_config else 'BV001_streaming'
                            
                        # 在线程池中异步执行 TTS 合成，立即返回不阻塞
                        future = InterviewService.tts_executor.submit(
                            InterviewService._synthesize_audio_async,
                            sentence_buffer,
                            voice,
                            'mp3'
                        )
                            
                        # 添加回调函数，当 TTS 完成后将音频数据放入队列
                        def tts_callback(fut):
                            try:
                                audio_bytes = fut.result()
                                if audio_bytes:
                                    audio_b64 = bytes_to_b64(audio_bytes)
                                    audio_chunks.append(audio_bytes)
                                    # 将音频数据放入队列，供后续发送
                                    audio_queue.put(audio_b64)
                            except Exception as e:
                                print(f'TTS 回调失败：{e}')
                            
                        future.add_done_callback(tts_callback)
    
                        # 清空缓冲区，迎接下一句话
                        sentence_buffer = ""
                    except Exception as e:
                        print('TTS 异步合成失败:', e)
    
                # === 检查是否有已完成的 TTS 音频需要发送 ===
                try:
                    # 非阻塞获取队列中的音频数据
                    audio_b64_from_queue = audio_queue.get_nowait()
                    payload['audio_b64'] = audio_b64_from_queue
                except queue.Empty:
                    pass
    
                # 立即发送文本 chunk（如果有音频，会一起发送）
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # === 使用异步 TTS 处理最后不带标点的 buffer ===
        if sentence_buffer.strip() and sentence_buffer != "[INTERVIEW_OVER]":
            try:
                voice = getattr(prompt_config, 'preferred_voice', 'BV001_streaming') if prompt_config else 'BV001_streaming'
                
                # 同步合成最后的音频（因为流已经结束，可以等待）
                audio_bytes = TTSService.synthesize_bytes(sentence_buffer, voice=voice, fmt='mp3')
                if audio_bytes:
                    audio_b64 = bytes_to_b64(audio_bytes)
                    audio_chunks.append(audio_bytes)
                    # 发送最后一个音频包
                    yield f"data: {json.dumps({'chunk': '', 'audio_b64': audio_b64}, ensure_ascii=False)}\n\n"
            except Exception as e:
                print('Final TTS failed:', e)
        
        # === 发送队列中剩余的音频数据 ===
        while not audio_queue.empty():
            try:
                remaining_audio = audio_queue.get_nowait()
                yield f"data: {json.dumps({'chunk': '', 'audio_b64': remaining_audio}, ensure_ascii=False)}\n\n"
            except queue.Empty:
                break

        # 5. 清理标识符并存入数据库
        clean_reply = full_reply.replace("[INTERVIEW_OVER]", "").strip()
        ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=clean_reply)
        db.session.add(ai_chat)

        # === 恢复音频文件保存逻辑 ===
        try:
            if audio_chunks:
                uploads_root = os.path.join(current_app.root_path, 'uploads')
                tts_dir = os.path.join(uploads_root, 'tts', str(interview.id))
                os.makedirs(tts_dir, exist_ok=True)
                file_name = f"interview_{interview.id}_chat_{ai_chat.id}_{int(datetime.now().timestamp())}.mp3"
                file_path = os.path.join(tts_dir, file_name)

                # 对于纯二进制的 MP3，可以直接拼接 byte 文件存储用于回放
                with open(file_path, 'wb') as f:
                    for chunk_bytes in audio_chunks:
                        f.write(chunk_bytes)

                tts_record = TTSAudio(
                    prompt_id=prompt_config.id if prompt_config else None,
                    file_path=os.path.relpath(file_path, current_app.root_path),  # 存储相对路径
                    format='mp3',
                    voice=getattr(prompt_config, 'preferred_voice', 'BV001_streaming') if prompt_config else 'BV001_streaming',
                    duration=None  # 可选：后续可以用 pydub 或 mutagen 获取时长
                )
                db.session.add(tts_record)
                db.session.flush() # 生成 id

                # 关联到聊天记录（我们上面新增了外键）
                ai_chat.tts_audio_id = tts_record.id
        except Exception as e:
            print('Error while handling audio chunks persistence:', e)

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
                            "这里填标准知识点名称，如'HTML5语义化'等": 20
                        }}
                    }}

                【绝对指令】：对于 knowledge_tags_eval 字段，你**只能**从下面的“标准知识点库”中挑选你在对话中考察到的知识点进行 0-100 的打分。
                如果候选人回答完全错误或不会，给20分以下。
                **禁止直接照抄模板里的文字，必须填写真实的标签名称。**
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
        valid_tags_found = 0
        for tag_name, score in tags_eval.items():
            # 跳过大模型照抄的模板废话
            if "真实的" in tag_name or "这里填" in tag_name:
                continue
            # 严格去数据库匹配已有的标签，找不到就直接丢弃（防大模型幻觉）
            tag = KnowledgeTag.query.filter_by(name=tag_name).first()
            if tag:
                valid_tags_found += 1
                mastery = UserKnowledgeMastery.query.filter_by(user_id=interview.user_id, tag_id=tag.id).first()
                if not mastery:
                    # 用户第一次接触这个标签，直接存入分数
                    mastery = UserKnowledgeMastery(user_id=interview.user_id, tag_id=tag.id,
                                                   mastery_level=score)
                    db.session.add(mastery)
                else:
                    # 已有记录，将历史分数与本次分数取平均（模拟平滑的成长或遗忘）
                    mastery.mastery_level = int((mastery.mastery_level + score) / 2)
                    
        # === 兜底机制：如果大模型没有正确输出任何有效标签，或者该岗位由于数据库空导致大纲为空 ===
        if valid_tags_found == 0 and len(questions) > 0:
            # 随便找1-2个岗位标签，赋一个及格分兜底，保证流程非空
            fallback_tags = set()
            for q in questions:
                for t in q.knowledge_tags:
                    if t.name not in fallback_tags:
                        fallback_tags.add(t)
                        if len(fallback_tags) >= 2:
                            break
                if len(fallback_tags) >= 2:
                    break
            
            for t in fallback_tags:
                mastery = UserKnowledgeMastery.query.filter_by(user_id=interview.user_id, tag_id=t.id).first()
                score = 50 # 默认及格偏下分数
                if not mastery:
                    mastery = UserKnowledgeMastery(user_id=interview.user_id, tag_id=t.id, mastery_level=score)
                    db.session.add(mastery)
                else:
                    mastery.mastery_level = int((mastery.mastery_level + score) / 2)
        # ========================================================================

        db.session.commit()
        result = {
            "reportId": interview.id,
            "jobName": interview.job.name if hasattr(interview, 'job') and interview.job else None
        }
        result.update(report_data)
        return result