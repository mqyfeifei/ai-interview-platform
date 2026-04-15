# backend/app/services/interview_qa_handler.py
"""
面试服务 - 问答处理模块
负责处理用户回答、调用大模型生成追问、流式输出等核心逻辑
"""

import json
import time
import queue
import threading
from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.interview import Interview, InterviewChat
from app.models.prompt import AiPrompt
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.services.tts_service import TTSService, bytes_to_b64
from app.utils.llm_client import DeepSeekClient
from app.services import coem


class InterviewQAHandler:
    """面试问答处理器"""
    
    # 语速缓存锁(避免循环导入，在此定义)
    _speed_cache_lock = threading.Lock()
    
    # === 无意义回答检测正则 ===
    _MEANINGLESS_ANSWER_PATTERN = __import__('re').compile(
        r'^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|1|2|3|4|5|6|7|8|9|0|[，。！？、\s]+)$',
        __import__('re').IGNORECASE
    )
    
    @staticmethod
    def normalize_answer_text(text):
        """标准化回答文本"""
        return (text or '').strip()
    
    @classmethod
    def is_meaningless_answer(cls, text):
        """
        检测是否为无意义回答
        
        Args:
            text: 用户回答文本
            
        Returns:
            bool: 是否为无意义回答
        """
        t = cls.normalize_answer_text(text)
        if not t:
            return True
        if len(t) <= 2:
            return True
        return bool(cls._MEANINGLESS_ANSWER_PATTERN.match(t))
    
    @staticmethod
    def process_chat_round_stream(interview_id, user_answer, voice_mode=False, voice=None, interview_round=None):
        """
        处理对话轮次并返回流式生成器
        
        流程:
        1. 记录用户回答
        2. 检测无意义回答
        3. 组装上下文与RAG提示词
        4. 调用大模型流式输出
        5. 实时TTS合成音频
        6. 流式推送给前端
        
        Args:
            interview_id: 面试ID
            user_answer: 用户回答文本
            voice_mode: 是否语音模式
            voice: 音色名称
            
        Yields:
            str: SSE格式的数据流
        """
        from app.services.interview_graph_helper import InterviewGraphHelper
        from app.services.interview_tts_helper import InterviewTTSHelper
        from app.services.asr_service import global_speed_cache
        
        interview = Interview.query.get(interview_id)
        normalized_answer = InterviewQAHandler.normalize_answer_text(user_answer)
        
        # ================= 清理腾讯云ASR情感标签 =================
        try:
            from app.services.emotion_tag_parser import EmotionTagParser
            clean_answer = EmotionTagParser.clean_emotion_tags(normalized_answer)
            if clean_answer != normalized_answer:
                print(f"[情感标签] 原始文本: {normalized_answer[:50]}...")
                print(f"[情感标签] 清理后: {clean_answer[:50]}...")
                normalized_answer = clean_answer
        except Exception as e:
            print(f"[情感标签] 清理失败: {str(e)}")
        # ========================================================
        
        # ================= 从全局缓存中获取语速 =================
        with InterviewQAHandler._speed_cache_lock:
            actual_speed = global_speed_cache.pop(normalized_answer, None)
        # ========================================================
        
        # 1. 记录用户回答
        user_chat = InterviewChat(
            interview_id=interview.id,
            role='user',
            content=normalized_answer
        )
        db.session.add(user_chat)
        interview.question_count += 1
        
        # 2. 检测无意义回答
        if InterviewQAHandler.is_meaningless_answer(normalized_answer):
            reminder = "我只收到了较短的确认词（如'好/嗯嗯/'）。请你围绕上一题给出更具体的回答，至少包含观点、做法或一个真实例子。"
            ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=reminder)
            db.session.add(ai_chat)
            db.session.commit()
            
            if voice_mode:
                try:
                    prompt_config = AiPrompt.query.filter_by(
                        job_id=interview.job_id, is_active=True
                    ).first()
                    tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, voice)
                    audio_bytes = TTSService.synthesize_bytes(reminder, voice=tts_voice, fmt='mp3')
                    if audio_bytes:
                        yield f"data: {json.dumps({'chunk': reminder, 'audio_b64': bytes_to_b64(audio_bytes)}, ensure_ascii=False)}\n\n"
                        return
                except Exception as e:
                    print(f'短回答提示 TTS 失败: {e}')
            
            yield f"data: {json.dumps({'chunk': reminder}, ensure_ascii=False)}\n\n"
            return
        
        # 3. 组装上下文与RAG提示词
        prompt_config = AiPrompt.query.filter_by(
            job_id=interview.job_id, is_active=True
        ).first()
        base_prompt = (
            prompt_config.system_prompt if prompt_config else
            "你是面试官，【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），"
            "或者你认为已经充分评估了该候选人的能力时，请主动结束面试。"
            "结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。"
        )
        
        # 动态注入面试大纲
        questions, job_tag_map = InterviewGraphHelper.get_job_graph_snapshot(interview.job_id)
        valid_tags_str = "、".join([tag.name for tag in job_tag_map.values()])
        
        session_config = getattr(interview, 'session_config', None)
        session_style = getattr(session_config, 'interview_style', 'confident')
        from app.services.interview_session_manager import InterviewSessionManager, ROUND_ALIASES

        raw_round = interview_round if interview_round is not None else getattr(session_config, 'interview_round', None)
        session_round = ROUND_ALIASES.get(
            str(raw_round).strip().lower() if raw_round is not None else '',
            'first_round',
        )
        # 轮次优先级: API传参 > 会话配置 > 当前已记录的 question_count
        round_index = None
        if interview_round is not None:
            try:
                round_index = int(interview_round)
            except Exception:
                round_index = {
                    'first_round': 1,
                    'second_round': 2,
                    'third_round': 3,
                }.get(session_round)
        if round_index is None:
            try:
                round_index = int(getattr(getattr(interview, 'session_config', None), 'interview_round', None) or 0)
            except Exception:
                round_index = {
                    'first_round': 1,
                    'second_round': 2,
                    'third_round': 3,
                }.get(session_round, 0)
        if not round_index:
            round_index = max(1, int(getattr(interview, 'question_count', 0) or 0) + 1)
        recent_tag_ids = InterviewGraphHelper.get_recent_asked_tag_ids(interview.id, limit=3)
        assigned_result = InterviewGraphHelper.assign_questions(
            interview.job_id,
            interview.user_id,
            limit=6,
            recent_tag_ids=recent_tag_ids,
            interview_round=session_round,
            interview_style=session_style,
            target_source=getattr(session_config, 'target_source', '通用'),
            is_dynamic_adjust=bool(getattr(session_config, 'is_dynamic_adjust', True)),
        )

        # 兼容旧格式(list)和阶段二新格式(dict)
        fallback_applied = False
        fallback_detail = []
        round_focus = ''
        if isinstance(assigned_result, dict):
            assigned_questions = assigned_result.get('selected_questions', [])
            fallback_applied = bool(assigned_result.get('fallback_applied', False))
            fallback_detail = assigned_result.get('fallback_detail', []) or []
            round_focus = assigned_result.get('round_focus', '') or ''
        else:
            assigned_questions = assigned_result or []

        if fallback_applied:
            current_app.logger.info(
                '[InterviewFallback] interview_id=%s round=%s job_id=%s detail=%s',
                interview.id,
                session_round,
                interview.job_id,
                json.dumps(fallback_detail, ensure_ascii=False),
            )
        question_mix = assigned_result.get('question_mix', {}) if isinstance(assigned_result, dict) else {}
        difficulty_mix = assigned_result.get('difficulty_mix', {}) if isinstance(assigned_result, dict) else {}
        strategy_adjustments = assigned_result.get('strategy_adjustments', []) if isinstance(assigned_result, dict) else []
        if question_mix or difficulty_mix:
            current_app.logger.info(
                '[InterviewStrategy] interview_id=%s round=%s style=%s mix=%s difficulty=%s adjustments=%s',
                interview.id,
                session_round,
                session_style,
                json.dumps(question_mix, ensure_ascii=False),
                json.dumps(difficulty_mix, ensure_ascii=False),
                json.dumps(strategy_adjustments, ensure_ascii=False),
            )
        
        # 选择多样化候选题
        diverse_refs = InterviewSessionManager.pick_diverse_questions(
            assigned_questions,
            interview_id=interview.id,
            round_index=interview.question_count,
            pick_count=2,
        )
        
        assigned_question_lines = []
        assigned_tag_ids = []
        for item in diverse_refs:
            assigned_tag_ids.extend(item['tag_ids'])
            assigned_question_lines.append(
                f"- 深度{item.get('reference_answer_depth', item['target_depth'])}候选题：{item['question'].content[:80]}"
                f"（标签：{'、'.join(item['tag_names'])}；必需技能：{'、'.join(item.get('required_skill_names', [])[:4]) or '暂无'}）"
            )
        
        graph_edge_context = InterviewGraphHelper.build_adjacent_tag_context(
            assigned_tag_ids, session_style
        )
        
        # GraphRAG: 岗位子图内的用户掌握度画像
        mastery_profile_str = "暂无相关掌握度记录"
        if job_tag_map:
            mastery_rows = db.session.query(
                UserKnowledgeMastery.mastery_level,
                KnowledgeTag.name
            ).join(
                KnowledgeTag,
                KnowledgeTag.id == UserKnowledgeMastery.tag_id
            ).filter(
                UserKnowledgeMastery.user_id == interview.user_id,
                UserKnowledgeMastery.tag_id.in_(list(job_tag_map.keys()))
            ).all()
            
            if mastery_rows:
                mastery_profile_str = "，".join(
                    [f"{row.name}({row.mastery_level}分)" for row in mastery_rows]
                )
        
        # 动态拼装情感安抚指令（结合语速 + 多模态情感分析）
        emotion_instruction = ""
        
        # 使用新的多模态情感分析服务
        try:
            from app.services.multimodal_emotion_service import get_multimodal_emotion_prompt
            
            # 提取音频标签（如果有）
            audio_tags = normalized_answer if '[' in normalized_answer else ""
            
            # 执行多模态情感分析（语音模式才用）
            if voice_mode and (audio_tags or actual_speed is not None):
                emotion_prompt = get_multimodal_emotion_prompt(
                    audio_tags=audio_tags,
                    asr_text=normalized_answer,
                    job_id=interview.job_id,
                    user_id=interview.user_id,
                    use_coem=False  # 简化，不使用COEM
                )
                
                if emotion_prompt:
                    emotion_instruction = f"""

【候选人情绪状态分析】：
{emotion_prompt}

请根据上述情绪分析结果，在回复的最开头用一两句话自然地给予情绪反馈或安抚：
- 如果检测到紧张/焦虑：例如“听得出你有些紧张，没关系，我们慢慢来...”
- 如果检测到自信/轻松：例如“感受到你的自信，很好！让我们继续深入...”
- 如果检测到犹豫/思考：例如“这个问题确实需要思考，不用着急...”
- 保持自然、温和的语气，让候选人感到被理解和支持
"""
                    print(f"[多模态情感分析] {emotion_prompt}")
            
        except Exception as e:
            print(f"[多模态情感分析] 异常: {e}")
            # 降级到原有逻辑
            emotion_instruction = ""
        
        resume_context = InterviewGraphHelper.extract_resume_context(interview.user_id)
        
        style_prompt_map = {
            'pressure': '压力面：说话短一点、直接一点，追问要紧凑，尽量像真实面试官那样连着追。',
            'teaching': '教学面：语气温和一点，先点出问题，再一步一步带着候选人往下想。',
            'confident': '自信面：语气自然一点，像真实面试官一样聊天，先问结论，再顺着理由追问。',
        }
        style_prompt = style_prompt_map.get(session_style, style_prompt_map['confident'])
        route_prompt_map = {
            'first_round': (
                '【图谱推进路线 - 一面】：优先围绕根节点、基础概念、核心定义提问。'
                '问题要短，先确认候选人是否掌握最基础的主干知识，再逐步展开。'
            ),
            'second_round': (
                '【图谱推进路线 - 二面】：优先围绕邻接节点、父子关系、相邻知识点对比提问。'
                '问题要比一面更深入，重点看候选人能不能把关联概念串起来。'
            ),
            'third_round': (
                '【图谱推进路线 - 三面】：优先围绕跨节点组合题、桥接节点、边界条件和综合判断提问。'
                '问题可以更开放一些，但必须能体现多节点关联与真实业务权衡。'
            ),
        }
        route_prompt = route_prompt_map.get(session_round, route_prompt_map['first_round'])
        spoken_style_instruction = (
            '【口语化表达要求】：'
            '请把回答说得像真实面试官，不要写成说明书。'
            '句子尽量自然、简短、顺口，少用长串书面语。'
            '不要重复同一个词，也不要一口气堆很多定语。'
            '如果是语音面试，优先使用更像“当面聊天”的说法，避免过于正式。'
            '提问时可以先一句自然铺垫，再直接问核心点。'
        )
        if voice_mode:
            if session_style == 'pressure':
                spoken_style_instruction += ' 语音模式下尽量 1-2 句，少铺垫，直接追问。'
            elif session_style == 'teaching':
                spoken_style_instruction += ' 语音模式下可以 2-4 句，先解释半句，再引导半句。'
            else:
                spoken_style_instruction += ' 语音模式下每次输出尽量控制在 1-3 句，保持自然。'
        assigned_question_prompt = '\n'.join(assigned_question_lines) if assigned_question_lines else '暂无候选题'
        round_focus_prompt = round_focus or '本轮重点：综合考察候选人的基础能力、问题拆解与表达清晰度。'
        user_answer_evidence = normalized_answer or ''
        # 风格 + 轮次的复合行为约束
        deep_dive_instruction = ''
        if session_style == 'pressure':
            deep_dive_instruction = (
                '\n压力模式强制化追问：从候选人回答中识别1-2个关键技术点或逻辑薄弱点，' \
                '对每个点至少执行连续3层追问（示例路径：为什么→底层实现→边界/高并发场景），' \
                '不要在第一层进行解释或安抚，优先曝光漏洞并持续深挖直至候选人给出明确细节或无法回答。'
            )
        elif session_style == 'confident':
            deep_dive_instruction = (
                '\n自信面追问策略：以鼓励为主，优先让候选人陈述自己的思路并给予积极反馈。' \
                '当回答较好时，可提出1-2个延展问题让候选人展示应用与权衡；' \
                '如果候选人卡壳，可提示可能的卡壳点或给出轻度引导（例如提示查看的方向或需要补充的层面），' \
                '但不要在本轮全面解释正确答案或替代候选人完成作答。'
            )
        elif session_style == 'teaching':
            deep_dive_instruction = (
                '\n教学面追问策略：以引导与教学为主，遇到错误或回答偏浅时先给出简短解释，' \
                '然后通过分步问题、类比或示例帮助候选人理解，并提供改进建议。' \
                '在必要时可分解问题并逐步示范核心概念，但仍应鼓励候选人尝试补充答案以巩固学习。'
            )
        assigned_question_prompt = '\n'.join(assigned_question_lines) if assigned_question_lines else '暂无候选题'
        
        enhanced_system_prompt = f"""
            {base_prompt}
            {emotion_instruction}
            {resume_context}
            
            【提问策略调整指令】：
            如果你在上述"候选人简历摘要"中看到了相关的项目和技能，请尽量结合 TA 的实际过往经历进行提问
            （例如："你在 X 公司的 Y 项目中用到了 Z 技术，能具体说说..."）。
            如果简历为空，则直接进入常规提问。

                        【事实一致性约束（必须遵守）】：
                        - 不允许凭空说“你提到了XXX”或“你刚刚说了XXX”。
                        - 只有当下方“用户本轮原话”中明确出现某术语，才可使用“你提到/你刚才说”的表达。
                        - 若术语未在原话中出现，请改成中性表达：
                            例如“你有 React 项目经验，我们聊聊调度机制/Fiber”。
                        用户本轮原话："{user_answer_evidence}"
            
            【GraphRAG 图谱追问策略】：
            以下是候选人的知识点掌握度画像：{mastery_profile_str}。
            当前面试类型：{session_style}。
            {style_prompt}
            {route_prompt}
            {spoken_style_instruction}
            {deep_dive_instruction}
            本轮优先候选题如下：
            {assigned_question_prompt}
            与候选题相关的相邻图谱节点：{graph_edge_context or '暂无'}。
            所有追问必须严格限定在下方"面试大纲（标准知识点库）"的范围内。
            避免连续两轮围绕完全相同的知识点提问，优先切换到同层相邻节点或同岗位另一核心能力点。
            
            【面试提问大纲约束】：
            本轮考察重点：{round_focus_prompt}
            为了保证面试的标准化，请 **严格** 围绕以下"面试大纲"中的知识点向候选人提问。
            - 每次提问请挑选 1 个具体的知识点进行深入考察。
            - 请不要提出大纲范围之外（天马行空）的技术问题。
            - 如果候选人回答不会，请宽慰他，并从大纲中换一个全新的知识点继续提问。
            
            面试大纲（标准知识点库）：
            [{valid_tags_str}]
        """
        
        # 4. 构建消息历史
        messages = [{"role": "system", "content": enhanced_system_prompt}]
        
        related_question = diverse_refs[0]['question'] if diverse_refs else None
        related_question_meta = InterviewGraphHelper.build_question_graph_meta(related_question) if related_question else {}
        follow_up_chain_text = ''
        if related_question and session_round in ('second_round', 'third_round'):
            follow_up_chain_text = InterviewGraphHelper.build_follow_up_chain_context(
                related_question,
                interview_round=session_round,
                interview_style=session_style,
                max_items=3,
            )
        if related_question:
            messages.append({
                "role": "system",
                "content": (
                    f"参考题目：{related_question.content}。"
                    f"参考答案要点：{related_question.reference_answer}。"
                    f"参考答案深度：{related_question_meta.get('reference_answer_depth', 1)}。"
                    f"必需技能：{ '、'.join(related_question_meta.get('skill_names', [])[:6]) or '暂无' }。"
                    f"请围绕此知识点对候选人进行专业追问。"
                    f"不要声称候选人已经提到该知识点，除非其原话中明确出现该术语。"
                )
            })
        if follow_up_chain_text:
            messages.append({
                "role": "system",
                "content": (
                    f"结构化追问链模板：\n{follow_up_chain_text}\n"
                    f"请优先沿着这些链路继续追问，并根据候选人回答自然改写，不要生硬照搬。"
                )
            })
        
        if recent_tag_ids:
            recent_tag_names = []
            for tag_id in recent_tag_ids:
                tag = job_tag_map.get(tag_id) or KnowledgeTag.query.get(tag_id)
                if tag and tag.name not in recent_tag_names:
                    recent_tag_names.append(tag.name)
            if recent_tag_names:
                messages.append({
                    "role": "system",
                    "content": (
                        f"最近几轮已经覆盖过的知识点：{'、'.join(recent_tag_names[:6])}。"
                        f"请优先切换到其他知识点，不要连续重复提问同一主题。"
                    )
                })
        
        # 加载历史对话
        history = InterviewChat.query.filter_by(
            interview_id=interview_id
        ).order_by(InterviewChat.timestamp).all()
        for msg in history:
            messages.append({
                "role": "user" if msg.role == 'user' else "assistant",
                "content": msg.content
            })
        
        # If CoEM is enabled for text-only mode, attempt CoEM pipeline (opt-in)
        try:
            if (not voice_mode) and current_app.config.get('USE_COEM_FOR_TEXT', False):
                try:
                    # Prepare conversation history and query
                    conversation_messages = []
                    for msg in history:
                        conversation_messages.append({'role': 'user' if msg.role == 'user' else 'assistant', 'content': msg.content})

                    query = normalized_answer

                    # Candidate source: use recent assigned question's reference answer + resume context as a simple document
                    candidate_docs = []
                    if related_question and related_question.reference_answer:
                        candidate_docs.append(related_question.reference_answer)
                    if resume_context:
                        candidate_docs.append(resume_context)

                    # Merge candidate docs into a single text and chunk
                    merged_text = '\n\n'.join(candidate_docs) if candidate_docs else normalized_answer
                    chunks = coem.chunk_text(merged_text, max_chars=current_app.config.get('COEM_CHUNK_MAX_CHARS', 800), overlap=current_app.config.get('COEM_CHUNK_OVERLAP', 100))

                    # Initial rank
                    from app.services.interview_service import InterviewService
                    scored = coem.initial_rank(chunks, query, InterviewService, top_k=current_app.config.get('COEM_MAX_CHUNKS', 4), job_id=interview.job_id)

                    # Sage enrich
                    sage_client = DeepSeekClient()
                    enhanced = coem.coem_sage_enrich(scored, query, sage_client, timeout=current_app.config.get('COEM_SAGE_TIMEOUT', 5.0))

                    # Rerank
                    reranked = coem.rerank_enhanced_chunks(enhanced, query, InterviewService, top_k=current_app.config.get('COEM_MAX_CHUNKS', 4))

                    # Generate final answer via CoEM-Core will be done in streaming mode later.
                    top_enhanced = reranked
                    # mark that we have CoEM candidates ready for streaming
                    _coem_ready = True
                except Exception as ce:
                    current_app.logger.exception('CoEM pipeline failed, falling back to default LLM flow: %s', ce)
                    _coem_ready = False
                    # fall through to default behavior
        except Exception:
            # If current_app is not available or config access fails, ignore and use default path
            _coem_ready = False

        # 5. 调用大模型流式输出
        llm = DeepSeekClient()
        stream_temp = InterviewSessionManager.resolve_generation_temperature(
            prompt_config=prompt_config,
            default_temp=0.88,
            seed=(interview.id * 1000 + interview.question_count),
        )
        # NOTE: do not call llm.generate_reply() yet — decide later whether to use CoEM streaming or LLM streaming

        tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, voice) if voice_mode else None
        
        full_reply = ""
        audio_chunks = []
        sentence_buffer = ""
        sent_audio_packets = 0
        tts_submitted_segments = 0
        tts_submitted_chars = 0
        
        # 音频队列，用于缓存异步TTS的结果
        audio_queue = queue.Queue()
        pending_tts_futures = []
        
        def submit_tts_segment(segment_text):
            nonlocal tts_submitted_segments, tts_submitted_chars
            clean_segment = InterviewTTSHelper.strip_stream_control_tokens(segment_text)
            if not clean_segment or not voice_mode:
                return
            
            # 更严格的校验，防止发送过短或不可发音的片段
            speakable_chars = InterviewTTSHelper.count_tts_speakable_chars(clean_segment)
            if speakable_chars < InterviewTTSHelper._MIN_TTS_SPEAKABLE_CHARS:
                print(f"[TTS] 跳过过短片段（可发音字符={speakable_chars}）：{repr(clean_segment[:30])}")
                return
            
            tts_submitted_segments += 1
            tts_submitted_chars += len(clean_segment)
            
            future = InterviewTTSHelper.tts_executor.submit(
                InterviewTTSHelper.synthesize_audio_async,
                clean_segment,
                tts_voice,
                'mp3'
            )
            pending_tts_futures.append({
                'future': future,
                'text': clean_segment,
                'submitted_at': time.monotonic(),
            })
            print(f"[TTS] 提交合成片段 #{tts_submitted_segments}（可发音字符={speakable_chars}）：{repr(clean_segment[:50])}")
        
        def flush_ready_tts_futures():
            """仅按提交顺序提取已完成的异步TTS，避免语音片段乱序"""
            flushed_count = 0
            while pending_tts_futures:
                head = pending_tts_futures[0]
                done_future = head['future']
                
                if not done_future.done():
                    break
                
                pending_tts_futures.pop(0)
                try:
                    audio_bytes = done_future.result()
                    if audio_bytes:
                        audio_chunks.append(audio_bytes)
                        audio_queue.put(bytes_to_b64(audio_bytes))
                        flushed_count += 1
                        print(f"[TTS] 完成合成：{repr(head['text'][:50])} ({len(audio_bytes)} bytes)")
                    else:
                        print(f"[TTS] 合成返回空音频：{repr(head['text'][:50])}")
                except Exception as e:
                    print(f'[TTS] 异步合成失败（文本：{repr(head["text"][:30])}）：{e}')

        def extract_stream_content(chunk):
            """兼容不同流式返回格式，统一提取文本内容。"""
            if isinstance(chunk, str):
                return chunk

            if isinstance(chunk, dict):
                try:
                    return (chunk.get('choices') or [{}])[0].get('delta', {}).get('content')
                except Exception:
                    return None

            try:
                choices = getattr(chunk, 'choices', None)
                if choices:
                    return choices[0].delta.content
            except Exception:
                return None

            return None

        # Decide response_stream: use CoEM streaming if available and enabled, otherwise use LLM streaming
        if (not voice_mode) and current_app.config.get('USE_COEM_FOR_TEXT', False) and _coem_ready:
            try:
                core_client = DeepSeekClient()
                # coem.coem_core_generate returns a generator when streaming=True
                response_stream = coem.coem_core_generate(top_enhanced, query, conversation_messages, core_client, streaming=True)
            except Exception as e:
                current_app.logger.exception('CoEM core streaming failed, falling back to LLM stream: %s', e)
                response_stream = llm.generate_reply(messages, stream=True, temperature=stream_temp)
        else:
            response_stream = llm.generate_reply(messages, stream=True, temperature=stream_temp)

        # 6. 流式处理模型输出
        for chunk in response_stream:
            content = extract_stream_content(chunk)
            if not content:
                continue

            for display_chunk in InterviewTTSHelper.split_stream_display_chunks(content):
                full_reply += display_chunk
                sentence_buffer += display_chunk

                # 初始化准备传给前端的payload
                payload = {'chunk': display_chunk}

                # 提取完整句并异步合成
                if voice_mode:
                    ready_segments, sentence_buffer = InterviewTTSHelper.extract_ready_tts_segments(sentence_buffer)
                    for segment in ready_segments:
                        submit_tts_segment(segment)

                # 将已经完成的异步TTS结果转入发送队列
                flush_ready_tts_futures()

                # 检查是否有已完成的TTS音频需要发送
                try:
                    audio_b64_from_queue = audio_queue.get_nowait()
                    payload['audio_b64'] = audio_b64_from_queue
                    sent_audio_packets += 1
                except queue.Empty:
                    pass

                # 立即发送文字chunk（如果有音频，会一起发送）
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # 7. 处理剩余的尾句
        if voice_mode and sentence_buffer:
            tail_segment = InterviewTTSHelper.extract_tail_tts_segment(sentence_buffer)
            if tail_segment:
                submit_tts_segment(tail_segment)
        
        # 等待所有TTS任务完成
        for head in pending_tts_futures:
            try:
                audio_bytes = head['future'].result(timeout=InterviewTTSHelper._TTS_HEAD_BLOCK_TIMEOUT_SECONDS)
                if audio_bytes:
                    audio_chunks.append(audio_bytes)
                    yield f"data: {json.dumps({'chunk': '', 'audio_b64': bytes_to_b64(audio_bytes)}, ensure_ascii=False)}\n\n"
                    sent_audio_packets += 1
                    print(f"[TTS] 最终完成合成：{repr(head['text'][:50])} ({len(audio_bytes)} bytes)")
            except Exception as e:
                print(f'[TTS] 最终等待超时或失败：{e}')
        
        # 清空队列中剩余的音频
        while True:
            try:
                audio_b64 = audio_queue.get_nowait()
                yield f"data: {json.dumps({'chunk': '', 'audio_b64': audio_b64}, ensure_ascii=False)}\n\n"
                sent_audio_packets += 1
            except queue.Empty:
                break
        
        # 8. 保存AI回复到数据库
        ai_chat = InterviewChat(
            interview_id=interview.id,
            role='ai',
            content=full_reply,
            timestamp=datetime.utcnow(),
            question_id=related_question.id if related_question else None,
        )
        db.session.add(ai_chat)
        db.session.commit()
        
        # 9. 发送结束标记
        yield f"data: {json.dumps({'chunk': '', 'done': True}, ensure_ascii=False)}\n\n"


# 导入依赖
from app.services.interview_session_manager import InterviewSessionManager
from app.services.interview_graph_helper import InterviewGraphHelper
from app.services.interview_tts_helper import InterviewTTSHelper
from app.models.learning import UserKnowledgeMastery
