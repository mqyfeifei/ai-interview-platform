# backend/app/services/interview_service.py
import os
import re
import json
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

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
from app.models.interview import InterviewScore, Dimension, TTSAudio, InterviewSessionConfig
from app.utils.llm_client import DeepSeekClient

from openai import OpenAI
from flask import current_app
from sentence_transformers import SentenceTransformer
from datetime import datetime


_EMBEDDING_MODEL_NAME = 'BAAI/bge-small-zh-v1.5'
_local_embedding_model = None
_embedding_model_lock = threading.Lock()

try:
    # 将线程池最大并发限制到 2，避免火山引擎 QPS 并发率限制。
    _TTS_MAX_WORKERS = 1
except Exception:
    _TTS_MAX_WORKERS = 1

class InterviewService:
    # === 新增：全局线程池，用于异步 TTS 合成 ===
    tts_executor = ThreadPoolExecutor(max_workers=_TTS_MAX_WORKERS)
    _speed_cache_lock = threading.Lock()

    _MEANINGLESS_ANSWER_PATTERN = re.compile(
        r'^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|1|2|3|4|5|6|7|8|9|0|[，。！？、\s]+)$',
        re.IGNORECASE
    )
    _TTS_SENTENCE_BOUNDARY_PATTERN = re.compile(r'[。！？；!?;!？\n]')
    _TTS_SOFT_BOUNDARY_PATTERN = re.compile(r'[，,:：]')
    _TTS_SPEAKABLE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')
    _MIN_TTS_SPEAKABLE_CHARS = 2
    _TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS = 8  # ✅ 降低从 12 到 8，提高分割频率，不遗漏短句
    _TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS = 70
    _TTS_HEAD_BLOCK_TIMEOUT_SECONDS = 30
    _STREAM_DISPLAY_CHUNK_CHARS = 10

    @staticmethod
    def _get_tts_voice(prompt_config=None, selected_voice=None):
        explicit_voice = (selected_voice or '').strip()
        if explicit_voice:
            return explicit_voice
        voice = getattr(prompt_config, 'preferred_voice', None) if prompt_config else None
        return voice or TTSService.get_default_speaker()

    @staticmethod
    def _synthesize_audio_async(text, voice, fmt='mp3'):
        """
        异步 TTS 合成包装。
        在线程池中执行同步的 synthesize_bytes，避免阻塞主线程
        """
        try:
            # 使用火山引擎或本地 pyttsx3 合成音频
            audio_bytes = TTSService.synthesize_bytes(text, voice=voice, fmt=fmt)
            return audio_bytes
        except Exception as e:
            print(f'异步 TTS 合成失败：{e}')
            return None

    @staticmethod
    def _normalize_answer_text(text):
        return (text or '').strip()

    @classmethod
    def _is_meaningless_answer(cls, text):
        t = cls._normalize_answer_text(text)
        if not t:
            return True
        if len(t) <= 2:
            return True
        return bool(cls._MEANINGLESS_ANSWER_PATTERN.match(t))

    @staticmethod
    def _strip_stream_control_tokens(text):
        t = (text or '').replace('[INTERVIEW_OVER]', '').strip()
        # 移除 markdown 中的 *, # 等符号
        t = re.sub(r'[*_~>#`]+', '', t)

        # 移除不可发音且非标点的特殊字符，如 emoji 等，防止 TTS 引擎报错或降级。
        # 允许中英文字符、数字，以及常见标点符号、空格
        allowed_pattern = re.compile(r'[^\u4e00-\u9fffa-zA-Z0-9，。！？；、：“”《》（）\.,!?;\'"()\[\]\-\+\s\n·—－￥]')
        t = allowed_pattern.sub('', t)

        # 将多个空格替换为一个空格
        t = re.sub(r'\s+', ' ', t)
        return t.strip()

    @classmethod
    def _count_tts_speakable_chars(cls, text):
        return len(cls._TTS_SPEAKABLE_CHAR_PATTERN.findall(text or ''))

    @classmethod
    def _is_valid_tts_segment(cls, text, force=False):
        clean_text = cls._strip_stream_control_tokens(text)
        if not clean_text:
            return False

        min_chars = 1 if force else cls._MIN_TTS_SPEAKABLE_CHARS
        return cls._count_tts_speakable_chars(clean_text) >= min_chars

    @classmethod
    def _extract_ready_tts_segments(cls, buffer_text):
        """
        从累计缓冲中提取已闭合的可播报句子，返回(segments, remaining_text)。
        优先在句末停顿切分；若句子过长则在逗号等软停顿处切分，降低单段过长带来的延迟。
        """
        text = buffer_text or ''
        segments = []
        segment_start = 0
        speakable_count = 0
        last_soft_boundary = -1

        def append_segment_if_valid(split_pos, force_valid=False):
            nonlocal segment_start, speakable_count, last_soft_boundary
            if split_pos <= segment_start:
                return False

            candidate = text[segment_start:split_pos]
            if not cls._is_valid_tts_segment(candidate, force=force_valid):
                return False

            segments.append(cls._strip_stream_control_tokens(candidate))
            segment_start = split_pos
            speakable_count = 0
            last_soft_boundary = -1
            return True

        for index, ch in enumerate(text):
            char_pos = index + 1
            if cls._TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
                # 英文和常见符号在发音时较快，中文更慢更长，简单按字符数容易把很长的英文算成太短。
                # 此处将所有能发音的字符等价看待，不区分中英，因为上面已经降低了阈值。
                speakable_count += 1

            if cls._TTS_SOFT_BOUNDARY_PATTERN.match(ch):
                last_soft_boundary = char_pos
                if speakable_count >= cls._TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS:
                    append_segment_if_valid(char_pos, force_valid=False)
                    continue

            if cls._TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
                # 强行断句，不再判断是不是太短。即便是1个字的“好。”也直接送去播报。
                append_segment_if_valid(char_pos, force_valid=True)
                continue

            if speakable_count >= cls._TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS:
                split_pos = last_soft_boundary if last_soft_boundary > segment_start else char_pos
                did_split = append_segment_if_valid(split_pos, force_valid=False)
                if did_split and split_pos < char_pos:
                    # 若在当前字符之前切分，重新统计当前段剩余可发音字符。
                    speakable_count = cls._count_tts_speakable_chars(text[segment_start:char_pos])


        return segments, text[segment_start:]

    @classmethod
    def _extract_tail_tts_segment(cls, buffer_text):
        """
        流式结束时提取剩余尾句（允许更短，但仍需可发音）。
        ✅ 改进点：更严格的有效性检查，确保不会发送空白或纯标点
        ✅ 优化：降低阈值从 1 个可发音字符到任何非空字符，最大化覆盖率
        """
        if not buffer_text:
            return None
        
        candidate = cls._strip_stream_control_tokens(buffer_text)
        
        # 如果整个候选文本为空（纯标点/空格），则返回 None
        if not candidate or not candidate.strip():
            return None
        
        # 尾句只要包含至少 1 个可发音字符，就应该被合成
        # 这包括中英文、数字等，但排除纯标点符号
        speakable_count = cls._count_tts_speakable_chars(candidate)
        if speakable_count >= 1:
            return candidate
        
        # 如果没有可发音字符但有其他字符（如标点），检查是否值得单独发音
        # 通常纯标点不需要额外合成，但如果整个 buffer 中有意义，保留之
        if candidate and speakable_count == 0 and len(candidate.strip()) > 0:
            # 这里是纯标点或其他符号，例如"…"、"！"等
            # 为避免冗余，直接返回 None
            # 如果需要保留这些符号的语音，可改为返回 candidate
            return None
        
        return None

    @classmethod
    def _split_stream_display_chunks(cls, content):
        """将单次模型大块输出拆成更细粒度文本事件，改善前端逐字体验。""" # type: ignore
        text = content or ''
        if not text:
            return []

        pieces = []
        current = []
        speakable_count = 0

        for ch in text:
            current.append(ch)
            if cls._TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
                speakable_count += 1

            if cls._TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
                pieces.append(''.join(current))
                current = []
                speakable_count = 0
                continue

            if cls._TTS_SOFT_BOUNDARY_PATTERN.match(ch) and speakable_count >= 4:
                pieces.append(''.join(current))
                current = []
                speakable_count = 0
                continue

            if speakable_count >= cls._STREAM_DISPLAY_CHUNK_CHARS:
                pieces.append(''.join(current))
                current = []
                speakable_count = 0

        if current:
            pieces.append(''.join(current))

        return pieces

    @staticmethod
    def _get_local_embedding_model():
        global _local_embedding_model
        if _local_embedding_model is not None:
            return _local_embedding_model

        with _embedding_model_lock:
            if _local_embedding_model is not None:
                return _local_embedding_model
            try:
                model = SentenceTransformer(_EMBEDDING_MODEL_NAME, local_files_only=False)
            except ValueError as e:
                raise RuntimeError(
                    "本地向量模型加载失败：当前 sentence-transformers/transformers 与 "
                    f"{_EMBEDDING_MODEL_NAME} 不兼容。请升级/降级依赖后重试。原始错误: {e}"
                ) from e
            model.max_seq_length = 512
            _local_embedding_model = model
            return _local_embedding_model

    @staticmethod
    def get_embedding(text):
        """调用本地开源模型获取文本向量。"""
        # bge-small-zh 输出 512 维向量
        embeddings = InterviewService._get_local_embedding_model().encode(text)
        return embeddings.tolist()

    @staticmethod
    def _extract_resume_context(user_id: int, max_chars: int = 800) -> str:
        """
        拉取并解析用户主简历，进行去敏与核心要点抽取，防止 Token 溢出。 # pyright: ignore[reportUndefinedVariable]
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

            # 3. 工作经历抽取 (最多 2 条)
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

            # 4. 组装简历摘要模块
            resume_text = f"""
            【候选人简历摘要】
            - 姓名: {name}
            - 核心技能: {skills_str if skills_str else '未填写'}
            - 近期经历:
            {work_context if work_context else '未填写'}
            """

            # 5. 安全硬截断，作为兜底防止恶意的超长输入。
            return resume_text.strip()[:max_chars]

        except Exception as e:
            print(f"简历摘要提取失败 {str(e)}")
            return ""

    @staticmethod

    def _initialize_user_graph_from_resume(user_id, resume_skills_list, base_score=60):
        """
        根据简历技能对用户知识图谱进行冷启动：
        - 先进行实体对齐，再为命中的标签写入 user_knowledge_mastery 初始分
        """
        if not resume_skills_list:
            return

        aligned_entities = InterviewService._align_resume_entities(resume_skills_list)
        if not aligned_entities:
            return

        for entity in aligned_entities:
            tag = entity['tag']
            score = max(base_score, entity['mastery_level'])
            mastery = UserKnowledgeMastery.query.filter_by(user_id=user_id, tag_id=tag.id).first()
            if not mastery:
                db.session.add(
                    UserKnowledgeMastery(
                        user_id=user_id,
                        tag_id=tag.id,
                        mastery_level=score,
                        last_updated=datetime.utcnow()
                    )
                )
                continue
            mastery.mastery_level = max(mastery.mastery_level or 0, score)
            mastery.last_updated = datetime.utcnow()

    @staticmethod
    def _normalize_tag_name(name):
        text = (name or '').strip().lower()
        text = re.sub(r'[\s\-_()（）\[\]【】,.，。/\\]+', '', text)
        return text

    @staticmethod
    def _skill_level_to_score(skill_item):
        if isinstance(skill_item, dict):
            for key in ('mastery', 'mastery_level', 'score', 'level', 'proficiency'):
                if skill_item.get(key) is not None:
                    raw_value = skill_item.get(key)
                    break
            else:
                raw_value = None

            if isinstance(raw_value, (int, float)):
                return int(raw_value)

            text = str(raw_value or '').strip().lower()
        else:
            text = str(skill_item or '').strip().lower()

        mapping = {
            '精通': 80,
            '熟悉': 60,
            '了解': 45,
            '入门': 30,
            'beginner': 30,
            'familiar': 60,
            'intermediate': 60,
            'proficient': 80,
            'expert': 90,
        }
        return mapping.get(text, 60)

    @staticmethod
    def _align_resume_entities(resume_skills_list):
        if not resume_skills_list:
            return []

        all_tags = KnowledgeTag.query.all()
        if not all_tags:
            return []

        alias_map = {
            'vue3': 'vue',
            'vuejs': 'vue',
            'reactjs': 'react',
            'nodejs': 'node.js',
            'springboot': 'springboot',
            'typescript': 'ts',
        }

        aligned = []
        for skill in resume_skills_list:
            if isinstance(skill, dict):
                raw_name = (skill.get('name') or skill.get('skill') or skill.get('tag') or '').strip()
            else:
                raw_name = str(skill).strip()

            if not raw_name:
                continue

            normalized = InterviewService._normalize_tag_name(raw_name)
            alias = alias_map.get(normalized, normalized)

            matched_tag = None
            best_score = 0.0

            for tag in all_tags:
                candidate = InterviewService._normalize_tag_name(tag.name)
                score = 0.0
                if candidate == alias or candidate == normalized:
                    score = 1.0
                elif alias and (alias in candidate or candidate in alias):
                    score = 0.9
                else:
                    score = SequenceMatcher(None, alias, candidate).ratio()

                if score > best_score:
                    best_score = score
                    matched_tag = tag

            if not matched_tag or best_score < 0.35:
                try:
                    vec = InterviewService.get_embedding(raw_name)
                    matched_tag = KnowledgeTag.query.order_by(KnowledgeTag.embedding.l2_distance(vec)).first()
                    best_score = max(best_score, 0.5 if matched_tag else 0.0)
                except Exception:
                    matched_tag = None

            if not matched_tag:
                continue

            aligned.append({
                'raw_name': raw_name,
                'tag': matched_tag,
                'matched_by': 'alias_or_fuzzy' if best_score < 1.0 else 'exact',
                'mastery_level': InterviewService._skill_level_to_score(skill),
            })

        return aligned

    @staticmethod
    def _get_job_graph_snapshot(job_id):
        questions = Question.query.filter_by(job_id=job_id).all()
        tag_map = {}
        for question in questions:
            for tag in question.knowledge_tags:
                tag_map[tag.id] = tag
        return questions, tag_map

    @staticmethod
    def _estimate_target_depth(mastery_level):
        if mastery_level >= 75:
            return 3
        if mastery_level >= 45:
            return 2
        return 1

    @staticmethod
    def _assign_questions(job_id, user_id, limit=5):
        questions = Question.query.filter_by(job_id=job_id, status='published').all()
        if not questions:
            questions = Question.query.filter_by(job_id=job_id).all()

        if not questions:
            return []

        _, tag_map = InterviewService._get_job_graph_snapshot(job_id)
        mastery_rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.tag_id.in_(list(tag_map.keys()) or [0])
        ).all() if tag_map else []
        mastery_map = {row.tag_id: row.mastery_level or 0 for row in mastery_rows}

        ranked = []
        for question in questions:
            question_tags = list(question.knowledge_tags or [])
            tag_ids = [tag.id for tag in question_tags]
            mastery_values = [mastery_map.get(tag_id, 0) for tag_id in tag_ids]
            avg_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0
            target_depth = InterviewService._estimate_target_depth(avg_mastery)
            depth = question.reference_answer_depth or 1
            depth_gap = abs(depth - target_depth)
            score = (100 - depth_gap * 25) + avg_mastery * 0.35
            if depth == target_depth:
                score += 20
            ranked.append({
                'question': question,
                'tag_ids': tag_ids,
                'tag_names': [tag.name for tag in question_tags],
                'avg_mastery': avg_mastery,
                'target_depth': target_depth,
                'score': score,
            })

        ranked.sort(key=lambda item: (-item['score'], -item['avg_mastery'], item['question'].id))
        return ranked[:limit]

    @staticmethod
    def _build_adjacent_tag_context(tag_ids, interview_style='confident'):
        if not tag_ids:
            return ''

        tags = KnowledgeTag.query.filter(KnowledgeTag.id.in_(list(set(tag_ids)))).all()
        if not tags:
            return ''

        related_names = []
        seen = set()

        def push(tag_name):
            if tag_name and tag_name not in seen:
                seen.add(tag_name)
                related_names.append(tag_name)

        for tag in tags:
            if interview_style == 'pressure':
                for child in tag.children or []:
                    push(child.name)
            elif interview_style == 'teaching':
                if tag.parent:
                    push(tag.parent.name)
                    for sibling in tag.parent.children or []:
                        if sibling.id != tag.id:
                            push(sibling.name)
            else:
                if tag.parent:
                    push(tag.parent.name)
                for child in tag.children or []:
                    push(child.name)

        if not related_names:
            return ''

        return '、'.join(related_names[:12])

    @staticmethod
    def _compute_graph_coverage(interview):
        questions, tag_map = InterviewService._get_job_graph_snapshot(interview.job_id)
        core_tag_ids = list(tag_map.keys())
        if not core_tag_ids:
            return {
                'coverage_rate': 0.0,
                'depth_rate': 0.0,
                'meta': {
                    'core_nodes': [],
                    'touched_nodes': [],
                    'max_depth': 0,
                    'core_count': 0,
                    'touched_count': 0,
                }
            }

        mastery_rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == interview.user_id,
            UserKnowledgeMastery.tag_id.in_(core_tag_ids)
        ).all()

        touched_tag_ids = [row.tag_id for row in mastery_rows if (row.mastery_level or 0) > 0]
        touched_set = set(touched_tag_ids)

        def get_depth(tag):
            depth = 1
            visited = set()
            current = tag
            while current and current.parent_id and current.parent_id not in visited:
                visited.add(current.id)
                current = KnowledgeTag.query.get(current.parent_id)
                if current:
                    depth += 1
            return depth

        max_depth = 0
        for tag_id in touched_set:
            tag = tag_map.get(tag_id) or KnowledgeTag.query.get(tag_id)
            if tag:
                max_depth = max(max_depth, get_depth(tag))

        core_count = len(core_tag_ids)
        touched_count = len(touched_set)
        coverage_rate = round((touched_count / core_count) * 100, 2) if core_count else 0.0
        depth_rate = round((min(max_depth, 3) / 3) * 100, 2) if max_depth else 0.0

        return {
            'coverage_rate': coverage_rate,
            'depth_rate': depth_rate,
            'meta': {
                'core_nodes': [tag_map[tag_id].name for tag_id in core_tag_ids if tag_id in tag_map],
                'touched_nodes': [tag_map[tag_id].name for tag_id in touched_set if tag_id in tag_map],
                'max_depth': max_depth,
                'core_count': core_count,
                'touched_count': touched_count,
            }
        }

    @staticmethod
    def _normalize_interview_style(voice_mode=False, interview_style=None, voice_role=None):
        # 仅根据“显式样式”决定，不再依赖文字/语音模式
        style_aliases = {
            '压力面': 'pressure',
            'pressure': 'pressure',
            'strict': 'pressure',
            '自信面': 'confident',
            'confident': 'confident',
            'balanced': 'confident',
            '教学面': 'teaching',
            'teaching': 'teaching',
            'technical': 'teaching',  # 兼容旧值
            'coach': 'teaching',
        }

        raw_style = (interview_style or '').strip()
        if raw_style:
            normalized = style_aliases.get(raw_style.lower()) or style_aliases.get(raw_style)
            if normalized:
                return normalized

        # 兼容旧前端：未传 style 时，仍可从 voice_role 兜底推断
        normalized_role = (voice_role or '').strip().lower()
        role_style_map = {
            'role_strict': 'pressure',
            'role_warm': 'confident',
            'role_calm': 'teaching',
        }
        if normalized_role in role_style_map:
            return role_style_map[normalized_role]

        return 'confident'

    @staticmethod
    def _build_session_config_payload(voice_mode=False, interview_style=None, voice_role=None):
        style = InterviewService._normalize_interview_style(
            voice_mode=voice_mode,
            interview_style=interview_style,
            voice_role=voice_role,
        )

        profile_map = {
            'confident': {
                'tech_ratio': 60.0,
                'scenario_ratio': 40.0,
                'difficulty_level': 2,
                'tone_descriptor': 'balanced_confident'
            },
            'teaching': {
                'tech_ratio': 80.0,
                'scenario_ratio': 20.0,
                'difficulty_level': 2,
                'tone_descriptor': 'teaching_guided'
            },
            'pressure': {
                'tech_ratio': 70.0,
                'scenario_ratio': 30.0,
                'difficulty_level': 3,
                'tone_descriptor': 'pressure_challenge'
            }
        }
        profile = profile_map.get(style, profile_map['confident'])

        return {
            'interview_style': style,
            'tech_ratio': profile['tech_ratio'],
            'scenario_ratio': profile['scenario_ratio'],
            'is_dynamic_adjust': True,
            'voice_id': voice_role or None,
            'speech_speed': 1.0,
            'tone_descriptor': profile['tone_descriptor'],
            'enabled_dimensions': ['knowledge', 'logic', 'communication'],
            'difficulty_level': profile['difficulty_level'],
        }

    @staticmethod
    def start_interview(user_id, job_id, voice_mode=False, interview_style=None, voice_role=None):

        # 0. 【修复点】：提前拉取简历，判断是否为空
        resume_data = ResumeService.get_main_resume(user_id)
        content = resume_data.get('content', {})
        has_experience = bool(content.get('workExperiences') or content.get('internshipExperiences') or content.get('campusExperiences'))
        has_skills = bool(content.get('skills'))
        # 如果既没有经历也没有技能，判定为空简历
        is_resume_empty = not (has_experience or has_skills)

        # 简历技能冷启动：在面试开始前初始化用户图谱掌握度锚点
        if has_skills:
            InterviewService._initialize_user_graph_from_resume(
                user_id=user_id,
                resume_skills_list=content.get('skills', [])
            )

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

        # 创建并绑定会话配置，避免所有记录都走数据库默认 confident
        session_payload = InterviewService._build_session_config_payload(
            voice_mode=voice_mode,
            interview_style=interview_style,
            voice_role=voice_role,
        )
        db.session.add(InterviewSessionConfig(interview_id=interview.id, **session_payload))

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

        # 4. 记录开场白到 InterviewChat
        chat = InterviewChat(interview_id=interview.id, role='ai', content=greeting)
        db.session.add(chat)
        db.session.commit()

        # ✅ 改进：开场白 TTS 异步化，设置 3 秒超时，不阻塞响应
        greeting_audio_b64 = None
        if voice_mode:
            # 异步提交 TTS 任务（不等待完成，立即返回响应）
            tts_voice = InterviewService._get_tts_voice(prompt_config, voice)
            speak_text = InterviewService._strip_stream_control_tokens(greeting)
            
            # 使用线程池异步执行，不阻塞主流程
            future = InterviewService.tts_executor.submit(
                InterviewService._synthesize_audio_async,
                speak_text,
                tts_voice,
                'mp3'
            )
            
            # 设置 3 秒超时尝试获取结果，超时则返回 None（用户体验不受影响）
            try:
                audio_bytes = future.result(timeout=3.0)
                if audio_bytes:
                    greeting_audio_b64 = bytes_to_b64(audio_bytes)
                    print(f"[开场白 TTS] 3秒内合成成功，音频大小={len(audio_bytes)} bytes")
                else:
                    print(f"[开场白 TTS] 合成返回空数据")
            except TimeoutError:
                print(f"[开场白 TTS] 3秒超时，返回 None，继续主流程（后续可在客户端重试）")
            except Exception as e:
                print(f"[开场白 TTS] 异步合成异常: {str(e)}")

        # 5. 【修复点】：下发 warning 字段，供前端弹窗/Toast提示
        return {
            "interview_id": interview.id,
            "question": greeting,
            "audio_b64": greeting_audio_b64,
            "session_config": {
                "interview_style": session_payload['interview_style'],
                "tech_ratio": session_payload['tech_ratio'],
                "scenario_ratio": session_payload['scenario_ratio'],
                "difficulty_level": session_payload['difficulty_level'],
                "voice_id": session_payload['voice_id'],
            },
            "warning": "系统检测到您的简历未完善，本次面试将进入「标准盲面」模式，无法为您进行个性化项目追问。" if is_resume_empty else None
        }

    @staticmethod
    def process_chat_round_stream(interview_id, user_answer, voice_mode=False, voice=None):
        """处理对话并返回流式生成器"""
        interview = Interview.query.get(interview_id)
        normalized_answer = InterviewService._normalize_answer_text(user_answer)

        # ================= 直接从全局缓存中获取语速 =================
        # 如果当前回答的文本刚好在缓存里，说明是刚才语音识别来的，拿到语速并删掉缓存
        with InterviewService._speed_cache_lock:
            actual_speed = global_speed_cache.pop(normalized_answer, None)
        # ============================================================

        # 1. 记录用户回答
        user_chat = InterviewChat(interview_id=interview.id, role='user', content=normalized_answer)
        db.session.add(user_chat)
        interview.question_count += 1

        if InterviewService._is_meaningless_answer(normalized_answer):
            reminder = "我只收到了较短的确认词（如“好/嗯嗯”）。请你围绕上一题给出更具体的回答，至少包含观点、做法或一个真实例子。"
            ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=reminder)
            db.session.add(ai_chat)
            db.session.commit()

            if voice_mode:
                try:
                    prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id, is_active=True).first()
                    tts_voice = InterviewService._get_tts_voice(prompt_config, voice)
                    audio_bytes = TTSService.synthesize_bytes(reminder, voice=tts_voice, fmt='mp3')
                    if audio_bytes:
                        yield f"data: {json.dumps({'chunk': reminder, 'audio_b64': bytes_to_b64(audio_bytes)}, ensure_ascii=False)}\n\n"
                        return
                except Exception as e:
                    print(f'短回答提示 TTS 失败: {e}')

            yield f"data: {json.dumps({'chunk': reminder}, ensure_ascii=False)}\n\n"
            return

    
        # 2. 组装上下文与 RAG 提示词


        prompt_config = AiPrompt.query.filter_by(job_id=interview.job_id, is_active=True).first()
        base_prompt = prompt_config.system_prompt if prompt_config else "你是面试官，【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。"

        # ================= 优化点：动态注入面试大纲 =================
        # 从数据库拉取真实的知识点，约束 AI 只能在这个范围内提问

        questions, job_tag_map = InterviewService._get_job_graph_snapshot(interview.job_id)
        valid_tags_str = "、".join([tag.name for tag in job_tag_map.values()])

        session_style = getattr(getattr(interview, 'session_config', None), 'interview_style', 'confident')
        assigned_questions = InterviewService._assign_questions(interview.job_id, interview.user_id, limit=3)
        assigned_question_lines = []
        assigned_tag_ids = []
        for item in assigned_questions:
            assigned_tag_ids.extend(item['tag_ids'])
            assigned_question_lines.append(
                f"- 深度{item['target_depth']}候选题：{item['question'].content[:80]}（标签：{'、'.join(item['tag_names'])}）"
            )
        graph_edge_context = InterviewService._build_adjacent_tag_context(assigned_tag_ids, session_style)

        # ================= GraphRAG 注入：岗位子图内的用户掌握度画像 =================
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
        # ========================================================================
    

        # ================= 动态拼装情感安抚指令 =================
        emotion_instruction = ""
        if actual_speed is not None:
            emotion_instruction = f"""
                【语音情感与状态隐式分析】：
                用户本次回答使用的是语音输入。系统检测到其语速为 {actual_speed} 字/秒。
                （参考：正常中等语速约 3-5 字/秒。大于 5 字/秒可能偏向紧张/激动，小于 3 字/秒可能偏向犹豫/边想边答）。
                请你结合语速和文本内容，简单分析候选人当前的情绪状态，并*在本次回复的最开头，用一两句话自然地给予情绪反馈或安抚*（例如：“听得出你有些紧张，没关系..”）。
                    """
        # ========================================================

        resume_context = InterviewService._extract_resume_context(interview.user_id)


        style_prompt_map = {
            'pressure': '压力面：如果候选人回答正确且完整，请立即向下追问其子概念、实现细节和边界条件。',
            'teaching': '教学面：如果候选人卡壳或回答偏浅，请优先回到父节点概念，并用同级兄弟概念做横向启发。',
            'confident': '自信面：保持鼓励式追问，兼顾基础与应用，适度深挖但避免持续施压。',
        }
        style_prompt = style_prompt_map.get(session_style, style_prompt_map['confident'])
        assigned_question_prompt = '\n'.join(assigned_question_lines) if assigned_question_lines else '暂无候选题'
    

        enhanced_system_prompt = f"""
                {base_prompt}
                {emotion_instruction}
                {resume_context}
                【提问策略调整指令】：

                如果你在上述“候选人简历摘要”中看到了相关的项目和技能，请尽量结合 TA 的实际过往经历进行提问（例如：“你在 X 公司的 Y 项目中用到了 Z 技术，能具体说说...”）。如果简历为空，则直接进入常规提问。

            【GraphRAG 图谱追问策略】：
            以下是候选人的知识点掌握度画像：{mastery_profile_str}。
            当前面试类型：{session_style}。
            {style_prompt}
            本轮优先候选题如下：
            {assigned_question_prompt}
            与候选题相关的相邻图谱节点：{graph_edge_context or '暂无'}。
            所有追问必须严格限定在下方“面试大纲（标准知识点库）”的范围内。

                    
                【面试提问大纲约束】：
                为了保证面试的标准化，请 **严格** 围绕以下“面试大纲”中的知识点向候选人提问。
                - 每次提问请挑选 1 个具体的知识点进行深入考察。
                - 请不要提出大纲范围之外（天马行空）的技术问题。
                - 如果候选人回答不会，请宽慰他，并从大纲中换一个全新的知识点继续提问。
                    
                面试大纲（标准知识点库）：
                [{valid_tags_str}]
                """
        # ===============================================================

        messages = [{"role": "system", "content": enhanced_system_prompt}]

    
        related_question = assigned_questions[0]['question'] if assigned_questions else None

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

        tts_voice = InterviewService._get_tts_voice(prompt_config, voice) if voice_mode else None

        full_reply = ""
        audio_chunks = []
        sentence_buffer = ""
        sent_audio_packets = 0
        tts_submitted_segments = 0
        tts_submitted_chars = 0

        # === 新增：音频队列，用于缓存异步 TTS 的结果 ===
        import queue
        audio_queue = queue.Queue()
        pending_tts_futures = []
        llm_raw_chunk_count = 0
        llm_raw_char_count = 0

        def submit_tts_segment(segment_text):
            nonlocal tts_submitted_segments, tts_submitted_chars
            clean_segment = InterviewService._strip_stream_control_tokens(segment_text)
            if not clean_segment or not voice_mode:
                return

            # ✅ 改进：更严格的校验，防止发送过短或不可发音的片段
            speakable_chars = InterviewService._count_tts_speakable_chars(clean_segment)
            if speakable_chars < InterviewService._MIN_TTS_SPEAKABLE_CHARS:
                print(f"[TTS] 跳过过短片段（可发音字符={speakable_chars}）：{repr(clean_segment[:30])}")
                return

            tts_submitted_segments += 1
            tts_submitted_chars += len(clean_segment)

            future = InterviewService.tts_executor.submit(
                InterviewService._synthesize_audio_async,
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
            """
            仅按提交顺序提取已完成的异步 TTS，避免语音片段乱序。
            ✅ 改进：增加详细的日志记录，便于调试和监测吞字问题
            """
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

        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                llm_raw_chunk_count += 1
                llm_raw_char_count += len(content)

                for display_chunk in InterviewService._split_stream_display_chunks(content):
                    full_reply += display_chunk
                    sentence_buffer += display_chunk

                    # 初始化准备传给前端的 payload，无论有没有音频，文字都要立刻传过去保证打字机效果
                    payload = {'chunk': display_chunk}

                    # 提取完整句并异步合成，避免把纯标点超短碎片送入 TTS。
                    if voice_mode:
                        ready_segments, sentence_buffer = InterviewService._extract_ready_tts_segments(sentence_buffer)
                        for segment in ready_segments:
                            submit_tts_segment(segment)

                    # 将已经完成的异步 TTS 结果转入发送队列
                    flush_ready_tts_futures()

                    # === 检查是否有已完成的 TTS 音频需要发送 ===
                    try:
                        # 非阻塞获取队列中的音频数据
                        audio_b64_from_queue = audio_queue.get_nowait()
                        payload['audio_b64'] = audio_b64_from_queue
                        sent_audio_packets += 1
                    except queue.Empty:
                        pass

                    # 立即发送文字 chunk（如果有音频，会一起发送）
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                    # 若当前时刻还有已完成音频，立即补发，降低“音频追不上文字”的体感。
                    while voice_mode and (not audio_queue.empty()):
                        try:
                            remaining_audio = audio_queue.get_nowait()
                            sent_audio_packets += 1
                            yield f"data: {json.dumps({'chunk': '', 'audio_b64': remaining_audio}, ensure_ascii=False)}\n\n"
                        except queue.Empty:
                            break

        if voice_mode:
            tail_segment = InterviewService._extract_tail_tts_segment(sentence_buffer)
            if tail_segment:
                print(f"[TTS] 处理尾句：{repr(tail_segment[:50])}")
                submit_tts_segment(tail_segment)
            elif sentence_buffer.strip():
                # 记录被过滤的尾句，便于调试
                print(f"[TTS] 尾句被过滤（可能为纯标点或空白）：{repr(sentence_buffer[:30])}")

        # 逐步等待剩余异步 TTS，并边完成边下发，避免“最后一口气才出音频”。
        settle_deadline = time.monotonic() + 180
        while pending_tts_futures:
            flush_ready_tts_futures()

            while voice_mode and (not audio_queue.empty()):
                try:
                    remaining_audio = audio_queue.get_nowait()
                    sent_audio_packets += 1
                    yield f"data: {json.dumps({'chunk': '', 'audio_b64': remaining_audio}, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    break

            if not pending_tts_futures:
                break

            # === 修复点：释放 GIL，防止长循环抢占 TTS 线程资源 ===
            time.sleep(0.05)

            if time.monotonic() >= settle_deadline:
                stale = pending_tts_futures[0]['text'] if pending_tts_futures else ''
                print(f"TTS 异步收尾超时（总等待180s），剩余片段将跳过，示例={stale[:30]}")
                break

            time.sleep(0.03)

        pending_tts_futures.clear()

        # === 发送队列中剩余的音频数据 ===
        while voice_mode and (not audio_queue.empty()):
            try:
                remaining_audio = audio_queue.get_nowait()
                sent_audio_packets += 1
                yield f"data: {json.dumps({'chunk': '', 'audio_b64': remaining_audio}, ensure_ascii=False)}\n\n"
            except queue.Empty:
                break

        # 5. 清理标识符并存入数据库
        clean_reply = full_reply.replace("[INTERVIEW_OVER]", "").strip()

        if voice_mode:
            # ✅ 改进的日志记录，便于监测和调试吞字问题
            coverage = 0.0 if len(clean_reply) == 0 else (tts_submitted_chars / len(clean_reply))
            total_audio_bytes = sum(len(chunk) for chunk in audio_chunks) if audio_chunks else 0
            
            print(
                f"[TTS Summary] 本轮 TTS 处理完毕：\n"
                f"  - 提交片段数：{tts_submitted_segments}\n"
                f"  - 提交字符数：{tts_submitted_chars} / 清洗后回复字符数 {len(clean_reply)}\n"
                f"  - 字符覆盖率：{coverage:.2%}\n"
                f"  - 下发音频片段数：{sent_audio_packets}\n"
                f"  - 音频文件总大小：{total_audio_bytes} bytes\n"
                f"  - LLM 流块数：{llm_raw_chunk_count}，原始字符数 {llm_raw_char_count}"
            )
            
            # 覆盖率低于 80% 时发出警告
            if coverage < 0.8 and len(clean_reply) > 0:
                missing_chars = len(clean_reply) - tts_submitted_chars
                print(f"⚠️  [TTS] 警告：合成覆盖率低于 80%，未合成 {missing_chars} 个字符")


        ai_chat = InterviewChat(interview_id=interview.id, role='ai', content=clean_reply)
        db.session.add(ai_chat)

        # === 恢复音频文件保存逻辑 ===
        try:
            if voice_mode and audio_chunks:
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
                    voice=InterviewService._get_tts_voice(prompt_config, voice),
                    duration=None  # 可选：后续可以借 pydub 或 mutagen 获取时长
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

        # ================= 优化点1: 扁平化组装真实标准知识点 =================
        # 获取当前岗位下所有题目的关联标签
        questions = Question.query.filter_by(job_id=interview.job_id).all()
        tag_set = set()
        for q in questions:
            for tag in q.knowledge_tags:
                tag_set.add(tag.name)
        valid_tags_str = "、".join(list(tag_set))
        # ======================================================================
        # ======================================================================

        # ================= 优化点2: 引入优秀回答范例，提升 AI 建议的具体性 =================
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
                    请作为资深面试官对以下面试记录进行综合评估：
                    必须严格返回 JSON 格式，不要输出任何额外的 markdown 标记或解释说明。结构如下：
                    {{
                        "total_score": 85,
                        "dimensions": {{
                            "技术正确性": {{"score": 80, "comment": "评价..."}},
                            "逻辑严谨性": {{"score": 90, "comment": "评价..."}},
                            "岗位匹配度": {{"score": 85, "comment": "评价..."}},
                            "表达沟通力": {{"score": 80, "comment": "评价..."}},
                            "应变能力": {{"score": 75, "comment": "评价..."}}
                        }},
                        "highlights": "列出面试中表现突出的至少2个亮点",
                        "improvements": "指出回答中的主要不足与知识盲区",
                        "suggestions": "针对不足给出3条具体、可操作的学习改进建议",
                        "knowledge_tags_eval": {{
                            "这里填标准知识点名称，如'HTML5语义化'": 20
                        }}
                    }}

                【绝对指令】：对于 knowledge_tags_eval 字段，你**只能**从下面的“标准知识点库”中挑选你在对话中考察到的知识点进行 0-100 的打分。
                如果候选人回答完全错误或不会，打 0分以下。
                **禁止直接照抄模板里的文字，必须填写真实的标签名称！**
                **禁止自己捏造、改写或发明新的知识点名称！如果对话涉及的知识不在下表中，请忽略它！**

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

            # # 返回明确的错误结构给前端，前端可据此提示用户“报告生成异常，请重试”。
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

        graph_coverage = InterviewService._compute_graph_coverage(interview)
        interview.graph_coverage_rate = graph_coverage['coverage_rate']
        interview.graph_depth_rate = graph_coverage['depth_rate']
        interview.graph_coverage_meta = graph_coverage['meta']

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


        def _normalize_score(raw_score):
            try:
                score_value = int(float(raw_score))
            except (TypeError, ValueError):
                return None
            return max(0, min(100, score_value))

        def update_node_score(target_tag, score, weight):
            """
            图谱级联更新：
            1) 先更新当前节点
            2) 再按衰减权重向父节点递归传播
            """
            if not target_tag or weight <= 0:
                return

            weighted_score = int(max(0, min(100, round(score * weight))))
            mastery = UserKnowledgeMastery.query.filter_by(
                user_id=interview.user_id,
                tag_id=target_tag.id
            ).first()

            if not mastery:
                mastery = UserKnowledgeMastery(
                    user_id=interview.user_id,
                    tag_id=target_tag.id,
                    mastery_level=weighted_score,
                    last_updated=datetime.utcnow()
                )
                db.session.add(mastery)
            else:
                # 指数平滑：新分数 = int((老分数 * 0.6) + (本次得分 * 0.4))
                mastery.mastery_level = int((mastery.mastery_level * 0.6) + (weighted_score * 0.4))
                mastery.last_updated = datetime.utcnow()

            if target_tag.parent_id:
                parent_tag = KnowledgeTag.query.get(target_tag.parent_id)
                if parent_tag:
                    update_node_score(parent_tag, score, weight * 0.3)

        # ================= 优化点 3: 严格校验，切断自动生成逻辑 =================

        tags_eval = report_data.get("knowledge_tags_eval", {})
        valid_tags_found = 0
        for tag_name, score in tags_eval.items():
            # 跳过大模型照抄的模板废话

            if not isinstance(tag_name, str):
                continue
            if "真实的" in tag_name or "这里填" in tag_name:

                continue
            normalized_score = _normalize_score(score)
            if normalized_score is None:
                continue
            # 严格去数据库匹配已有的标签，找不到就直接丢弃（防大模型幻觉）
            tag = KnowledgeTag.query.filter_by(name=tag_name).first()
            if tag:
                valid_tags_found += 1

                update_node_score(tag, normalized_score, 1.0)
                    
        # === 兜底机制：如果大模型没有正确输出任何有效标签，或者该岗位由于数据库空导致大纲为空 ===
        if valid_tags_found == 0 and len(questions) > 0:
            # 随便找1-2个岗位标签，赋一个及格分兜底，保证流程非空
            fallback_tags = []
            fallback_tag_ids = set()

            for q in questions:
                for t in q.knowledge_tags:
                    if t.id not in fallback_tag_ids:
                        fallback_tags.append(t)
                        fallback_tag_ids.add(t.id)
                        if len(fallback_tags) >= 2:
                            break
                if len(fallback_tags) >= 2:
                    break

            for t in fallback_tags:
                update_node_score(t, 50, 1.0)  # 默认及格偏下分数
        # ========================================================================

        db.session.commit()
        result = {
            "reportId": interview.id,
            "jobName": interview.job.name if hasattr(interview, 'job') and interview.job else None
        }
        result.update(report_data)
        return result
