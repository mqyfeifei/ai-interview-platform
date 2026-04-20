# backend/app/services/interview_qa_handler.py
"""
面试服务 - 问答处理模块
核心职责：状态调度、Prompt组装、响应解析与流式输出编排。
"""

import json
import queue
import re
import threading
import time
from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.interview import Interview, InterviewChat
from app.models.job import Job
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.models.prompt import AiPrompt
from app.services import coem
from app.services.interview_prompt_builder import InterviewPromptBuilder
from app.services.interview_response_parser import InterviewResponseParser
from app.services.interview_state_manager import InterviewStateManager
from app.services.interview_tts_helper import InterviewTTSHelper
from app.services.tts_service import TTSService, bytes_to_b64
from app.utils.llm_client import DeepSeekClient
from app.services.interview_graph_helper import InterviewGraphHelper
from app.services.interview_session_manager import InterviewSessionManager, ROUND_ALIASES


class InterviewQAHandler:
    """面试问答处理器"""

    _speed_cache_lock = threading.Lock()
    _MEANINGLESS_ANSWER_PATTERN = __import__('re').compile(
        r'^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|1|2|3|4|5|6|7|8|9|0|[，。！？、\s]+)$',
        __import__('re').IGNORECASE
    )
    _TEACHING_UNKNOWN_PATTERN = re.compile(
        r'(不会|不太会|不清楚|不知道|没做过|没了解过|不会答|答不上来|忘了|记不清|没思路)',
        re.IGNORECASE,
    )
    _TEACHING_UNSURE_PATTERN = re.compile(
        r'(我猜|可能是|大概|应该是|不确定|也许)',
        re.IGNORECASE,
    )
    _TEACHING_EFFORT_MARKERS = ('首先', '然后', '最后', '因为', '所以', '例如', '比如', '项目', '指标', '优化', '权衡', '落地')

    @staticmethod
    def normalize_answer_text(text):
        return (text or '').strip()

    @classmethod
    def is_meaningless_answer(cls, text):
        t = cls.normalize_answer_text(text)
        if not t:
            return True
        if len(t) <= 2:
            return True
        return bool(cls._MEANINGLESS_ANSWER_PATTERN.match(t))

    @staticmethod
    def _safe_dump_reference_answer(value):
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)
        return str(value or '')

    @staticmethod
    def _build_mastery_profile(interview, job_tag_map):
        if not job_tag_map:
            return "暂无相关掌握度记录"
        rows = db.session.query(
            UserKnowledgeMastery.mastery_level,
            KnowledgeTag.name
        ).join(
            KnowledgeTag, KnowledgeTag.id == UserKnowledgeMastery.tag_id
        ).filter(
            UserKnowledgeMastery.user_id == interview.user_id,
            UserKnowledgeMastery.tag_id.in_(list(job_tag_map.keys()))
        ).all()
        if not rows:
            return "暂无相关掌握度记录"
        return "，".join([f"{row.name}({row.mastery_level}分)" for row in rows])

    @staticmethod
    def _build_emotion_instruction(voice_mode, normalized_answer, actual_speed, interview):
        emotion_instruction = ""
        try:
            from app.services.multimodal_emotion_service import get_multimodal_emotion_prompt
            audio_tags = normalized_answer if '[' in normalized_answer else ""
            if voice_mode and (audio_tags or actual_speed is not None):
                emotion_prompt = get_multimodal_emotion_prompt(
                    audio_tags=audio_tags,
                    asr_text=normalized_answer,
                    job_id=interview.job_id,
                    user_id=interview.user_id,
                    use_coem=True,
                )
                if emotion_prompt:
                    emotion_instruction = f"""
【候选人情绪状态分析】：
{emotion_prompt}
请在 spoken_text 的开头用一句自然口语做情绪承接，不要模板化。
"""
        except Exception as e:
            print(f"[多模态情感分析] 异常: {e}")
        return emotion_instruction

    @staticmethod
    def _build_coem_hint(related_question, resume_context, normalized_answer, interview):
        if not current_app.config.get('USE_COEM_FOR_TEXT', False):
            return ""
        try:
            from app.services.interview_service import InterviewService
            docs = []
            if related_question and related_question.reference_answer:
                docs.append(InterviewQAHandler._safe_dump_reference_answer(related_question.reference_answer))
            if resume_context:
                docs.append(resume_context)
            seed_text = "\n\n".join(docs) if docs else normalized_answer
            chunks = coem.chunk_text(
                seed_text,
                max_chars=current_app.config.get('COEM_CHUNK_MAX_CHARS', 800),
                overlap=current_app.config.get('COEM_CHUNK_OVERLAP', 100),
            )
            ranked = coem.initial_rank(
                chunks,
                normalized_answer,
                InterviewService,
                top_k=min(3, current_app.config.get('COEM_MAX_CHUNKS', 4)),
                job_id=interview.job_id,
            )
            hints = []
            for item in ranked:
                text = str(item.get('chunk', {}).get('text', '') or '').strip()
                if text:
                    hints.append(text[:180])
            if not hints:
                return ""
            return "COEM检索上下文（供内部参考）：\n" + "\n".join([f"- {h}" for h in hints])
        except Exception:
            return ""

    @staticmethod
    def _resolve_teaching_feedback_mode(session_style, normalized_answer):
        if session_style != 'teaching':
            return {'mode': 'none', 'instruction': ''}

        answer = str(normalized_answer or '').strip()
        if not answer:
            return {
                'mode': 'unknown',
                'instruction': '教学面触发：候选人未有效作答。先用1-2句讲清核心概念，再给一个最小可用示例，最后只追问1个基础确认问题。',
            }

        if InterviewQAHandler._TEACHING_UNKNOWN_PATTERN.search(answer):
            return {
                'mode': 'unknown',
                'instruction': '教学面触发：候选人明确表示不会/不清楚。先解释正确思路与关键概念，再给可复述的答题模板，最后追问1个由浅入深的问题。',
            }

        if InterviewQAHandler._TEACHING_UNSURE_PATTERN.search(answer):
            return {
                'mode': 'unsure',
                'instruction': '教学面触发：候选人表达不确定。优先纠偏，指出可能误区，补充正确结论与判断依据，然后再提1个验证理解的问题。',
            }

        effort_hit = sum(1 for marker in InterviewQAHandler._TEACHING_EFFORT_MARKERS if marker in answer)
        if len(answer) >= 80 or effort_hit >= 2:
            return {
                'mode': 'effortful',
                'instruction': '教学面触发：候选人回答认真。先肯定一个具体亮点，再指出一个可提升方向（结构、边界或指标），给出可执行改进建议后再继续追问。',
            }

        return {
            'mode': 'normal',
            'instruction': '教学面常规：保持引导式追问；若发现明显事实错误，先纠错并解释原因，再继续提问。',
        }

    @staticmethod
    def _stream_spoken_text(spoken_text, voice_mode, tts_voice):
        full_reply = ""
        sentence_buffer = ""
        audio_queue = queue.Queue()
        pending_tts_futures = []

        def submit_tts_segment(segment_text):
            clean_segment = InterviewTTSHelper.strip_stream_control_tokens(segment_text)
            if not clean_segment or not voice_mode:
                return
            speakable_chars = InterviewTTSHelper.count_tts_speakable_chars(clean_segment)
            if speakable_chars < InterviewTTSHelper._MIN_TTS_SPEAKABLE_CHARS:
                return
            future = InterviewTTSHelper.tts_executor.submit(
                InterviewTTSHelper.synthesize_audio_async,
                clean_segment,
                tts_voice,
                'mp3'
            )
            pending_tts_futures.append({'future': future, 'text': clean_segment, 'submitted_at': time.monotonic()})

        def flush_ready_tts_futures():
            while pending_tts_futures:
                head = pending_tts_futures[0]
                if not head['future'].done():
                    break
                pending_tts_futures.pop(0)
                try:
                    audio_bytes = head['future'].result()
                    if audio_bytes:
                        audio_queue.put(bytes_to_b64(audio_bytes))
                except Exception as e:
                    print(f"[TTS] 异步合成失败: {e}")

        for content in InterviewTTSHelper.split_stream_display_chunks(spoken_text):
            if not content or not content.strip():
                continue
            full_reply += content
            sentence_buffer += content
            payload = {'chunk': content}

            if voice_mode:
                ready_segments, sentence_buffer = InterviewTTSHelper.extract_ready_tts_segments(sentence_buffer)
                for segment in ready_segments:
                    submit_tts_segment(segment)

            flush_ready_tts_futures()
            try:
                payload['audio_b64'] = audio_queue.get_nowait()
            except queue.Empty:
                pass
            yield payload

        if voice_mode and sentence_buffer:
            tail_segment = InterviewTTSHelper.extract_tail_tts_segment(sentence_buffer)
            if tail_segment:
                submit_tts_segment(tail_segment)

        for head in pending_tts_futures:
            try:
                audio_bytes = head['future'].result(timeout=InterviewTTSHelper._TTS_HEAD_BLOCK_TIMEOUT_SECONDS)
                if audio_bytes:
                    yield {'chunk': '', 'audio_b64': bytes_to_b64(audio_bytes)}
            except Exception:
                pass

        while True:
            try:
                yield {'chunk': '', 'audio_b64': audio_queue.get_nowait()}
            except queue.Empty:
                break

    @staticmethod
    def process_chat_round_stream(interview_id, user_answer, voice_mode=False, voice=None, interview_round=None):
        from app.services.asr_service import global_speed_cache

        interview = Interview.query.get(interview_id)
        if not interview:
            yield f"data: {json.dumps({'chunk': '会话不存在或已结束', 'done': True}, ensure_ascii=False)}\n\n"
            return

        session_config = getattr(interview, 'session_config', None)
        session_style = str(getattr(session_config, 'interview_style', 'confident') or 'confident').strip().lower()
        if session_style not in ('pressure', 'confident', 'teaching'):
            session_style = 'confident'

        normalized_answer = InterviewQAHandler.normalize_answer_text(user_answer)
        try:
            from app.services.emotion_tag_parser import EmotionTagParser
            normalized_answer = EmotionTagParser.clean_emotion_tags(normalized_answer)
        except Exception:
            pass

        with InterviewQAHandler._speed_cache_lock:
            actual_speed = global_speed_cache.pop(normalized_answer, None)

        turn_state_before = InterviewStateManager.build_turn_state(
            interview=interview,
            session_config=session_config,
            asked_count=int(getattr(interview, 'question_count', 0) or 0),
        )

        if InterviewQAHandler.is_meaningless_answer(normalized_answer):
            last_ai_chat = InterviewChat.query.filter_by(interview_id=interview.id, role='ai').order_by(InterviewChat.timestamp.desc()).first()
            reminder = InterviewResponseParser.build_ack_followup(
                last_ai_content=last_ai_chat.content if last_ai_chat else '',
                session_style=session_style,
                max_questions_per_turn=turn_state_before.max_questions_per_turn,
            )
            ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=reminder, timestamp=datetime.utcnow())
            db.session.add(ai_chat)
            db.session.commit()

            if voice_mode:
                try:
                    prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id, is_active=True).first()
                    tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, voice)
                    audio_bytes = TTSService.synthesize_bytes(reminder, voice=tts_voice, fmt='mp3')
                    if audio_bytes:
                        yield f"data: {json.dumps({'chunk': reminder, 'audio_b64': bytes_to_b64(audio_bytes)}, ensure_ascii=False)}\n\n"
                        return
                except Exception as e:
                    print(f"短确认词TTS失败: {e}")
            yield f"data: {json.dumps({'chunk': reminder}, ensure_ascii=False)}\n\n"
            return

        # 有效回答才计入轮次与状态推进
        user_chat = InterviewChat(interview_id=interview.id, role='user', content=normalized_answer, timestamp=datetime.utcnow())
        db.session.add(user_chat)
        interview.question_count = int(getattr(interview, 'question_count', 0) or 0) + 1

        prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id, is_active=True).first()
        base_prompt = (
            prompt_config.system_prompt if prompt_config else
            "你是企业一线面试官。请基于候选人回答持续追问并评估能力，当达到合理题量且评估充分后再结束面试。"
        )

        questions, job_tag_map = InterviewGraphHelper.get_job_graph_snapshot(interview.job_id)
        valid_tags_str = "、".join([tag.name for tag in job_tag_map.values()]) if job_tag_map else '暂无'
        mastery_profile_str = InterviewQAHandler._build_mastery_profile(interview, job_tag_map)

        round_raw = interview_round if interview_round is not None else getattr(session_config, 'interview_round', None)
        session_round = ROUND_ALIASES.get(
            str(round_raw).strip().lower() if round_raw is not None else '',
            'first_round',
        )
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
        assigned_questions = assigned_result.get('selected_questions', []) if isinstance(assigned_result, dict) else (assigned_result or [])
        round_focus_prompt = (assigned_result.get('round_focus', '') if isinstance(assigned_result, dict) else '') or '综合考察基础能力、项目真实性和问题拆解能力'

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
                f"- 候选题：{item['question'].content[:90]}（标签：{'、'.join(item['tag_names'])}；来源：{getattr(item['question'], 'source', '') or '通用'}）"
            )
        assigned_question_prompt = '\n'.join(assigned_question_lines) if assigned_question_lines else '暂无候选题'
        graph_edge_context = InterviewGraphHelper.build_adjacent_tag_context(assigned_tag_ids, session_style)

        resume_context = InterviewGraphHelper.extract_resume_context(interview.user_id)
        emotion_instruction = InterviewQAHandler._build_emotion_instruction(
            voice_mode=voice_mode,
            normalized_answer=normalized_answer,
            actual_speed=actual_speed,
            interview=interview,
        )

        source_options = InterviewSessionManager.get_job_source_options(interview.job_id)
        company_name = InterviewSessionManager.normalize_target_source(getattr(session_config, 'target_source', '通用'))
        if company_name not in source_options:
            company_name = '通用'
        job = Job.query.get(interview.job_id) if interview.job_id else None
        job_name = (job.name if job else '目标岗位')
        company_role_desc = f"{company_name} {job_name}" if company_name != '通用' else f"{job_name}（通用题库）"

        route_prompt_map = {
            'first_round': '图谱路线：优先根节点与基础概念，问法简洁，逐步深入。',
            'second_round': '图谱路线：优先相邻节点与知识关联，重点考察迁移与串联能力。',
            'third_round': '图谱路线：优先跨节点综合题与边界权衡，关注工程决策质量。',
        }
        route_prompt = route_prompt_map.get(session_round, route_prompt_map['first_round'])
        round_label_map = {'first_round': '一面', 'second_round': '二面', 'third_round': '三面'}
        style_label_map = {'pressure': '压力面', 'teaching': '教学面', 'confident': '自信面'}

        turn_state = InterviewStateManager.build_turn_state(
            interview=interview,
            session_config=session_config,
            asked_count=int(getattr(interview, 'question_count', 0) or 0),
            target_mix_override=(assigned_result.get('question_mix', {}) or {}).get('target') if isinstance(assigned_result, dict) else None,
        )
        teaching_feedback = InterviewQAHandler._resolve_teaching_feedback_mode(session_style, normalized_answer)
        related_question = diverse_refs[0]['question'] if diverse_refs else None
        follow_up_chain_context = InterviewGraphHelper.build_follow_up_chain_context(
            related_question,
            interview_round=session_round,
            interview_style=session_style,
            max_items=3,
        ) if related_question else ''

        system_prompt = InterviewPromptBuilder.build_turn_system_prompt(
            base_prompt=base_prompt,
            emotion_instruction=emotion_instruction,
            resume_context=resume_context,
            company_role_desc=company_role_desc,
            active_round_label=round_label_map.get(turn_state.session_round, '一面'),
            active_style_label=style_label_map.get(turn_state.session_style, '自信面'),
            source_options=source_options,
            company_name=company_name,
            mastery_profile_str=mastery_profile_str,
            route_prompt=route_prompt,
            assigned_question_prompt=assigned_question_prompt,
            graph_edge_context=graph_edge_context,
            follow_up_chain_context=follow_up_chain_context,
            round_focus_prompt=round_focus_prompt,
            valid_tags_str=valid_tags_str,
            user_answer_evidence=normalized_answer or '',
            turn_state=turn_state,
            teaching_feedback_mode=teaching_feedback.get('mode', 'none'),
            teaching_feedback_instruction=teaching_feedback.get('instruction', ''),
        )

        messages = [{"role": "system", "content": system_prompt}]
        if related_question:
            messages.append({
                "role": "system",
                "content": (
                    f"参考题目：{related_question.content}\n"
                    f"参考答案要点：{InterviewQAHandler._safe_dump_reference_answer(related_question.reference_answer)}"
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
                    "content": f"最近几轮已覆盖：{'、'.join(recent_tag_names[:6])}。优先切换到新知识点。"
                })

        history = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
        for msg in history:
            messages.append({"role": "user" if msg.role == 'user' else "assistant", "content": msg.content})

        coem_hint = InterviewQAHandler._build_coem_hint(related_question, resume_context, normalized_answer, interview)
        if coem_hint:
            messages.append({"role": "system", "content": coem_hint})

        llm = DeepSeekClient()
        temp = InterviewSessionManager.resolve_generation_temperature(
            prompt_config=prompt_config,
            default_temp=0.82,
            seed=(interview.id * 1000 + interview.question_count),
        )
        raw_reply = llm.generate_reply(messages, stream=False, temperature=temp)
        parsed = InterviewResponseParser.parse_structured_reply(raw_reply)
        spoken_text = InterviewResponseParser.sanitize_spoken_text(
            parsed.get('spoken_text') or '',
            max_questions_per_turn=turn_state.max_questions_per_turn,
        )

        model_should_end = bool(parsed.get('should_end_interview', False))
        can_finish_now = int(getattr(interview, 'question_count', 0) or 0) >= int(turn_state.min_questions)
        must_finish_now = int(getattr(interview, 'question_count', 0) or 0) >= int(turn_state.max_questions)
        should_end = must_finish_now or (model_should_end and can_finish_now)
        if should_end:
            if not any(token in spoken_text[-60:] for token in ('感谢', '谢谢', '辛苦了')):
                spoken_text = (spoken_text.rstrip() + "\n感谢你参加今天的面试，辛苦了。").strip()
            spoken_text = spoken_text + "[INTERVIEW_OVER]"

        internal_thought = str(parsed.get('internal_thought', '') or '').strip()
        if internal_thought:
            current_app.logger.info(
                '[InterviewThought] interview_id=%s phase=%s thought=%s',
                interview.id,
                turn_state.phase.value,
                internal_thought[:500],
            )

        selected_voice = voice
        if voice_mode and not selected_voice:
            selected_voice = getattr(getattr(interview, 'session_config', None), 'voice_id', None)
        tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, selected_voice) if voice_mode else None
        stream_text = spoken_text.replace('[INTERVIEW_OVER]', '')
        for payload in InterviewQAHandler._stream_spoken_text(stream_text, voice_mode=voice_mode, tts_voice=tts_voice):
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        if '[INTERVIEW_OVER]' in spoken_text:
            yield f"data: {json.dumps({'chunk': '[INTERVIEW_OVER]', 'interview_over': True}, ensure_ascii=False)}\n\n"

        ai_chat = InterviewChat(
            interview_id=interview.id,
            role='ai',
            content=stream_text,
            timestamp=datetime.utcnow(),
            question_id=related_question.id if related_question else None,
        )
        db.session.add(ai_chat)

        meta = interview.graph_coverage_meta if isinstance(interview.graph_coverage_meta, dict) else {}
        meta['dialog_state'] = turn_state.phase.value
        meta['phase_targets'] = turn_state.phase_targets
        meta['phase_progress'] = turn_state.phase_progress
        if internal_thought:
            meta['latest_internal_thought'] = internal_thought[:1000]
        interview.graph_coverage_meta = meta
        db.session.commit()

        yield f"data: {json.dumps({'chunk': '', 'done': True}, ensure_ascii=False)}\n\n"
