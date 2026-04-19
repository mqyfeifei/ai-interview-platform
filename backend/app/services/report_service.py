import concurrent.futures
from sqlalchemy import func
import re
import json
from collections import Counter
from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension
from app.models.job import Job, DEFAULT_JOBS, get_job_front_key
from app.models.question import Question
from app.models.example import Example
from app.models.learning import Resource, KnowledgeTag, UserKnowledgeMastery, UserLearning  # 图谱推荐依赖模型
from app.services.interview_service import InterviewService
from app.utils.llm_client import DeepSeekClient


class ReportService:
    _MAX_IMPROVEMENT_POINT_LENGTH = 140
    DIMENSION_ALIASES = {
        '表达沟通力': '表达沟通',
        '表达能力': '表达沟通',
        '沟通表达': '表达沟通',
    }

    DIMENSION_NAME_TO_KEY = {
        '技术正确性': 'technical',
        '逻辑严谨性': 'logic',
        '岗位匹配度': 'matching',
        '表达沟通': 'expression',
        '应变能力': 'adaptability'
    }

    @classmethod
    def _normalize_dimension_name(cls, dim_name):
        name = str(dim_name or '').strip()
        return cls.DIMENSION_ALIASES.get(name, name)

    _MEANINGLESS_ANSWER_PATTERN = re.compile(
        r'^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|1|2|3|4|5|6|7|8|9|0|[，。！？、\s]+)$',
        re.IGNORECASE
    )

    @staticmethod
    def _split_text_to_list(raw_text):
        if not raw_text:
            return []
        text = str(raw_text).replace('\r', '\n')
        lines = [ReportService._sanitize_summary_line(line) for line in text.split('\n')]
        lines = [line for line in lines if line]
        if lines:
            return lines
        cleaned = ReportService._sanitize_summary_line(text)
        return [cleaned] if cleaned else []

    @staticmethod
    def _sanitize_summary_line(text):
        cleaned = str(text or '').strip(' -•\t')
        if not cleaned:
            return ''
        cleaned = re.sub(r'^\{+\s*', '', cleaned)
        cleaned = re.sub(r'\s*\}+$', '', cleaned)
        cleaned = re.sub(r'^[\'"]+|[\'"]+$', '', cleaned).strip()
        if cleaned in ('...', '…', '{}', '[]'):
            return ''
        return cleaned

    @staticmethod
    def _clean_json_block(raw_text):
        if not raw_text:
            return ''
        cleaned = str(raw_text).strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return cleaned.strip()

    @classmethod
    def _is_meaningless_answer(cls, text):
        t = (text or '').strip()
        if not t:
            return True
        if len(t) <= 2:
            return True
        return bool(cls._MEANINGLESS_ANSWER_PATTERN.match(t))

    @staticmethod
    def _is_enterprise_source(source):
        normalized = (source or '').strip()
        return bool(normalized) and normalized != '通用'

    @staticmethod
    def _normalize_reference_answer(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _fetch_job_questions(job):
        if not job:
            return []
        if hasattr(job.questions, 'all'):
            return job.questions.filter_by(status='published').all() or job.questions.all()
        return list(job.questions or [])

    @staticmethod
    def _normalize_source_name(source):
        raw = str(source or '').strip()
        if not raw:
            return '通用'
        normalized = re.sub(r'[\s·•·\-_（）()]+', '', raw)
        return normalized or '通用'

    @classmethod
    def _filter_questions_by_source(cls, questions, target_source):
        q_list = list(questions or [])
        normalized_target = cls._normalize_source_name(target_source)
        if normalized_target == '通用':
            return [q for q in q_list if cls._normalize_source_name(getattr(q, 'source', '通用')) == '通用'] or q_list

        enterprise = [q for q in q_list if cls._normalize_source_name(getattr(q, 'source', '通用')) == normalized_target]
        generic = [q for q in q_list if cls._normalize_source_name(getattr(q, 'source', '通用')) == '通用']
        merged = enterprise + generic
        return merged or q_list

    @classmethod
    def _match_question_by_text(cls, text, job_question_ids):
        if not text or not job_question_ids:
            return None
        try:
            q_vec = InterviewService.get_embedding(str(text)[:200])
            return (
                Question.query
                .filter(Question.id.in_(job_question_ids))
                .order_by(Question.embedding.l2_distance(q_vec))
                .first()
            )
        except Exception:
            return None

    @classmethod
    def _collect_reply_items(cls, interview):
        if not interview:
            return []

        job = db.session.get(Job, interview.job_id)
        target_source = getattr(getattr(interview, 'session_config', None), 'target_source', '通用')
        job_questions = cls._filter_questions_by_source(cls._fetch_job_questions(job), target_source)
        job_question_ids = [q.id for q in job_questions]

        chats = (
            InterviewChat.query
            .filter_by(interview_id=interview.id)
            .order_by(InterviewChat.timestamp.asc())
            .all()
        )

        items = []
        analysis_index = 1
        for idx, chat in enumerate(chats):
            if chat.role != 'ai':
                continue
            question_text = (chat.content or '').replace('[INTERVIEW_OVER]', '').strip()
            if not question_text:
                continue

            user_reply = None
            for j in range(idx + 1, len(chats)):
                if chats[j].role == 'user':
                    if not cls._is_meaningless_answer(chats[j].content or ''):
                        user_reply = chats[j]
                    break
                if chats[j].role == 'ai':
                    break

            matched_q = None
            if chat.question_id:
                matched_q = db.session.get(Question, int(chat.question_id))
                if matched_q and job_question_ids and matched_q.id not in job_question_ids:
                    matched_q = None
            if matched_q is None:
                matched_q = cls._match_question_by_text(question_text, job_question_ids)

            source = (matched_q.source or '').strip() if matched_q else ''
            is_enterprise = cls._is_enterprise_source(source)

            items.append({
                'index': analysis_index,
                'questionChatId': chat.id,
                'answerChatId': user_reply.id if user_reply else None,
                'question': question_text,
                'answer': (user_reply.content if user_reply else '') or '',
                'answerAt': user_reply.timestamp.isoformat() if (user_reply and user_reply.timestamp) else None,
                'questionId': matched_q.id if matched_q else None,
                'questionSource': source,
                'isEnterpriseQuestion': is_enterprise,
                'reference': cls._normalize_reference_answer(matched_q.reference_answer if matched_q else None),
            })
            analysis_index += 1

        return items

    @classmethod
    def _build_report_weaknesses(cls, interview, limit=6):
        items = cls._collect_reply_items(interview)
        q_ids = [it.get('questionId') for it in items if it.get('questionId')]
        if not q_ids:
            return []

        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        tag_counter = Counter()
        tag_map = {}
        question_map = {q.id: q for q in questions}
        tag_bad_examples = {}
        for item in items:
            q_id = item.get('questionId')
            if not q_id or q_id not in question_map:
                continue
            gap_detail = cls._build_question_gap_detail(item)
            if not gap_detail:
                continue
            q_obj = question_map[q_id]
            for tag in list(getattr(q_obj, 'knowledge_tags', []) or []):
                if not cls._is_tag_related_to_gap(tag.name, item, gap_detail):
                    continue
                bucket = tag_bad_examples.setdefault(tag.id, [])
                bucket.append(gap_detail)
                tag_counter[tag.id] += 1
                tag_map[tag.id] = tag

        if not tag_counter:
            return []

        rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == interview.user_id,
            UserKnowledgeMastery.tag_id.in_(list(tag_counter.keys()))
        ).all()

        mastery_map = {r.tag_id: int(r.mastery_level or 0) for r in rows}
        weakness_rows = []
        for tag_id, freq in tag_counter.items():
            mastery_level = mastery_map.get(tag_id, 45)
            if mastery_level >= 75:
                continue
            tag = tag_map.get(tag_id)
            if not tag:
                continue
            weakness_rows.append({
                'tag_id': tag.id,
                'name': tag.name,
                'mastery_level': mastery_level,
                'estimated_hours': int(tag.estimated_hours or 0) if getattr(tag, 'estimated_hours', None) is not None else None,
                'frequency': int(freq or 0),
                'examples': (tag_bad_examples.get(tag.id) or [])[:2]
            })

        weakness_rows.sort(key=lambda x: (x['mastery_level'], -x['frequency']))
        return weakness_rows[:limit]

    @classmethod
    def _build_dimension_feedback(cls, dimensions):
        labels = {
            'technical': '技术正确性',
            'logic': '逻辑严谨性',
            'matching': '岗位匹配度',
            'expression': '表达沟通',
            'adaptability': '应变能力'
        }
        highlights = []
        improvements = []
        for key, label in labels.items():
            score = int((dimensions or {}).get(key, 0) or 0)
            if score >= 75:
                highlights.append(f'【{label}】该维度表现较好，能较稳定地支撑面试目标。')
            else:
                detail = f'【{label}】该维度仍有提升空间，建议结合本场题目补齐关键细节。'
                if key == 'technical':
                    detail = f'【{label}】建议针对本次涉及知识点补齐原理推导、边界条件和工程落地细节。'
                improvements.append(detail)
        return highlights, improvements

    @staticmethod
    def _truncate_text(text, limit=80):
        t = str(text or '').strip()
        if len(t) <= limit:
            return t
        return f"{t[:limit]}..."

    @staticmethod
    def _extract_reference_keywords(reference_points):
        keywords = []
        for ref in reference_points or []:
            for token in re.split(r'[，。；、,：:（）()\s]+', str(ref or '')):
                token = token.strip()
                if len(token) >= 2:
                    keywords.append(token)
        return list(dict.fromkeys(keywords))[:6]

    @staticmethod
    def _normalize_text_for_match(text):
        return re.sub(r'[\s·•\-_（）()、,，。；:：]+', '', str(text or '').lower())

    @classmethod
    def _extract_match_tokens(cls, text):
        normalized = cls._normalize_text_for_match(text)
        if not normalized:
            return []
        parts = re.findall(r'[a-z0-9\+\#\.\/]+|[\u4e00-\u9fff]{2,}', normalized)
        if parts:
            return list(dict.fromkeys(parts))
        return [normalized] if len(normalized) >= 2 else []

    @classmethod
    def _is_tag_related_to_gap(cls, tag_name, item, gap_detail):
        tag_text = str(tag_name or '').strip()
        if not tag_text:
            return False

        question_text = str(item.get('question') or '')
        answer_text = str(item.get('answer') or '')
        refs = item.get('reference') or []
        missing_keywords = (gap_detail or {}).get('missing_keywords') or []

        corpus = " ".join(
            [question_text, answer_text] +
            [str(x) for x in refs] +
            [str(x) for x in missing_keywords]
        )
        normalized_corpus = cls._normalize_text_for_match(corpus)
        normalized_tag = cls._normalize_text_for_match(tag_text)
        if normalized_tag and normalized_tag in normalized_corpus:
            return True

        tag_tokens = cls._extract_match_tokens(tag_text)
        corpus_tokens = set(cls._extract_match_tokens(corpus))
        if not tag_tokens or not corpus_tokens:
            return False

        overlap = [tok for tok in tag_tokens if tok in corpus_tokens]
        if overlap:
            return True

        # 复合标签（A/B、A与B）的弱匹配兜底
        sub_tokens = []
        for seg in re.split(r'[\/与和及、]+', tag_text):
            sub_tokens.extend(cls._extract_match_tokens(seg))
        sub_tokens = list(dict.fromkeys(sub_tokens))
        return bool(sub_tokens and any(tok in corpus_tokens for tok in sub_tokens))

    @classmethod
    def _build_question_gap_detail(cls, item):
        answer = (item.get('answer') or '').strip()
        question = cls._truncate_text(item.get('question') or '', 36)
        if cls._is_meaningless_answer(answer):
            return {
                'question': question,
                'answer': cls._truncate_text(answer or '（未作答）', 50),
                'gap_type': 'no_answer',
                'missing_keywords': [],
                'issue': '回答信息不足，缺少可验证的知识点与实现过程。'
            }

        refs = item.get('reference') or []
        keywords = cls._extract_reference_keywords(refs)
        missing = [kw for kw in keywords if kw not in answer][:2]
        if missing:
            return {
                'question': question,
                'answer': cls._truncate_text(answer, 50),
                'gap_type': 'keyword_gap',
                'missing_keywords': missing,
                'issue': f'未覆盖关键点：{ "、".join(missing) }。'
            }

        if len(answer) < 30:
            return {
                'question': question,
                'answer': cls._truncate_text(answer, 50),
                'gap_type': 'too_short',
                'missing_keywords': [],
                'issue': '回答偏简略，缺少步骤拆解或场景化说明。'
            }
        return None

    @classmethod
    def _filter_missing_keywords_by_tag(cls, tag_name, missing_keywords):
        keywords = [str(x).strip() for x in (missing_keywords or []) if str(x).strip()]
        if not keywords:
            return []

        tag_tokens = set(cls._extract_match_tokens(tag_name))
        if not tag_tokens:
            return []

        matched = []
        normalized_tag = cls._normalize_text_for_match(tag_name)
        for kw in keywords:
            kw_tokens = set(cls._extract_match_tokens(kw))
            normalized_kw = cls._normalize_text_for_match(kw)
            if kw_tokens and kw_tokens.intersection(tag_tokens):
                matched.append(kw)
            elif normalized_kw and normalized_kw in normalized_tag:
                matched.append(kw)
        return matched[:2]

    @classmethod
    def _build_weakness_point(cls, weakness):
        tag_name = str(weakness.get('name') or '该知识点').strip() or '该知识点'
        examples = weakness.get('examples') or []
        if not examples:
            text = f'你在{tag_name}相关题目上的回答稳定性不足，建议补齐“概念-原理-场景”三层表达。'
            return cls._truncate_text(text, cls._MAX_IMPROVEMENT_POINT_LENGTH)

        ex = examples[0] if isinstance(examples[0], dict) else {}
        question = cls._truncate_text(ex.get('question') or '本场相关题目', 30)
        gap_type = ex.get('gap_type') or ''
        missing_keywords = [str(x).strip() for x in (ex.get('missing_keywords') or []) if str(x).strip()]
        related_missing_keywords = cls._filter_missing_keywords_by_tag(tag_name, missing_keywords)

        if gap_type == 'keyword_gap' and related_missing_keywords:
            reason = f'在“{question}”这题中，你对{tag_name}的关键点（{"、".join(related_missing_keywords)}）覆盖不足，因此该知识点被识别为待提升项。'
        elif gap_type == 'keyword_gap':
            reason = f'在“{question}”这题中，你对{tag_name}的核心概念与实现细节覆盖不足，因此该知识点被识别为待提升项。'
        elif gap_type == 'no_answer':
            reason = f'在“{question}”这题中，你的回答信息不足，未体现{tag_name}的核心思路与实现过程，因此被识别为待提升项。'
        elif gap_type == 'too_short':
            reason = f'在“{question}”这题中，你的回答偏简略，缺少{tag_name}的步骤与边界说明，因此该知识点需要继续补强。'
        else:
            issue = str(ex.get('issue') or '回答不够完整').strip('。')
            reason = f'在“{question}”这题中，你在{tag_name}上的表现存在短板（{issue}），因此被识别为待提升项。'

        return cls._truncate_text(reason, cls._MAX_IMPROVEMENT_POINT_LENGTH)

    @staticmethod
    def _format_session_config(interview):
        cfg = getattr(interview, 'session_config', None)
        round_text_map = {
            'first_round': '一面',
            'second_round': '二面',
            'third_round': '三面',
            'hr_round': 'HR面',
            '1': '一面',
            '2': '二面',
            '3': '三面'
        }
        style_text_map = {
            'confident': '自信面',
            'teaching': '教学面',
            'pressure': '压力面',
            'gentle': '教学面',
            'strict': '压力面'
        }
        round_raw = getattr(cfg, 'interview_round', None) if cfg else None
        style_raw = getattr(cfg, 'interview_style', None) if cfg else None
        round_key = str(round_raw).strip().lower() if round_raw is not None else ''
        style_key = str(style_raw).strip().lower() if style_raw is not None else ''
        source_raw = (getattr(cfg, 'target_source', '') or '').strip() if cfg else ''
        source_text = source_raw if source_raw and source_raw != '通用' else ''
        return {
            'interviewRound': round_raw or '',
            'interviewRoundText': round_text_map.get(round_key, round_raw or ''),
            'interviewStyle': style_raw or '',
            'interviewStyleText': style_text_map.get(style_key, style_raw or ''),
            'targetSource': source_raw or '通用',
            'targetSourceText': source_text,
            'startTime': interview.start_time.isoformat() if interview.start_time else None
        }

    @classmethod
    def _build_summary_tags(cls, interview):
        labels = {
            'technical': '技术正确性',
            'logic': '逻辑严谨性',
            'matching': '岗位匹配度',
            'expression': '表达沟通',
            'adaptability': '应变能力'
        }
        dimensions, _ = cls._build_dimensions(interview.id)
        sorted_dims = sorted(dimensions.items(), key=lambda x: int(x[1] or 0), reverse=True)
        highlight_tags = [f"{labels.get(k, k)}优势" for k, score in sorted_dims if int(score or 0) >= 80][:2]
        weak_dim_tags = [f"{labels.get(k, k)}待提升" for k, score in sorted_dims[::-1] if int(score or 0) < 75][:1]

        weakness_rows = cls._build_report_weaknesses(interview, limit=2)
        weakness_tags = [row.get('name') for row in weakness_rows if row.get('name')]
        weakness_tags.extend(weak_dim_tags)
        return {
            'highlightTags': list(dict.fromkeys(highlight_tags))[:3],
            'weaknessTags': list(dict.fromkeys(weakness_tags))[:3]
        }

    @staticmethod
    def _tag_depth(tag):
        depth = 1
        visited = set()
        current = tag
        while current and current.parent_id and current.id not in visited:
            visited.add(current.id)
            current = KnowledgeTag.query.get(current.parent_id)
            if current:
                depth += 1
        return depth

    @staticmethod
    def _get_completed_resource_ids(user_id):
        rows = UserLearning.query.filter_by(user_id=user_id, status='completed').all()
        return {row.resource_id for row in rows}

    @classmethod
    def _get_recommended_resource(cls, point_text, user_id):
        """
        基于图谱断层进行资源推荐：
        1) 将改进点文本匹配到 KnowledgeTag 节点
        2) 优先推荐该节点下资源
        3) 若无资源，沿 parent_id 向上降级推荐
        """
        if not point_text:
            return None

        completed_resource_ids = cls._get_completed_resource_ids(user_id)

        try:
            matched_tag = KnowledgeTag.query.filter(KnowledgeTag.name.ilike(f"%{point_text}%")).first()

            if not matched_tag:
                token_candidates = [
                    token.strip() for token in re.split(r'[，。；、,\s]+', str(point_text))
                    if token and token.strip()
                ]
                token_candidates.sort(key=len, reverse=True)
                for token in token_candidates[:5]:
                    tag = KnowledgeTag.query.filter(KnowledgeTag.name.ilike(f"%{token}%")).first()
                    if tag:
                        matched_tag = tag
                        break

            # 文本匹配失败时，使用向量检索知识点进行兜底
            if not matched_tag:
                try:
                    vec = InterviewService.get_embedding(point_text)
                    matched_tag = KnowledgeTag.query.order_by(KnowledgeTag.embedding.l2_distance(vec)).first()
                except Exception:
                    matched_tag = None

            if not matched_tag:
                return None

            visited_ids = set()
            current_tag = matched_tag
            used_fallback = False

            while current_tag and current_tag.id not in visited_ids:
                visited_ids.add(current_tag.id)

                query = Resource.query.join(Resource.knowledge_tags).filter(KnowledgeTag.id == current_tag.id)
                if completed_resource_ids:
                    query = query.filter(~Resource.id.in_(list(completed_resource_ids)))

                mastery = UserKnowledgeMastery.query.filter_by(
                    user_id=user_id,
                    tag_id=current_tag.id
                ).first()

                if mastery:
                    target_level = mastery.mastery_level or 0
                    if target_level < 40:
                        query = query.order_by(Resource.difficulty.asc(), Resource.id.asc())
                    elif target_level > 70:
                        query = query.order_by(Resource.difficulty.desc(), Resource.id.asc())
                    else:
                        query = query.order_by(Resource.id.asc())
                else:
                    query = query.order_by(Resource.id.asc())

                res = query.first()
                if res:
                    reason = f"系统检测到您的{matched_tag.name}知识薄弱，推荐该资源帮助补齐短板。"
                    if used_fallback:
                        reason = f"系统检测到您的{matched_tag.name}知识薄弱，当前子节点资源不足，已为您降级推荐上层知识点【{current_tag.name}】资源。"

                    return {
                        'id': res.id,
                        'title': res.title,
                        'type': res.type,
                        'url': res.url,
                        'source': res.source,
                        'matchedTag': matched_tag.name,
                        'resourceTag': current_tag.name,
                        'resourceTagId': current_tag.id,
                        'resourceTagDepth': cls._tag_depth(current_tag),
                        'reason': reason
                    }

                if current_tag.parent_id:
                    current_tag = KnowledgeTag.query.get(current_tag.parent_id)
                    used_fallback = True
                else:
                    current_tag = None

        except Exception as e:
            print(f"[Error] Failed to fetch recommended resource: {e}")

        return None

    @classmethod
    def _get_recommended_resource_by_tag(cls, tag, user_id):
        if not tag:
            return None

        completed_resource_ids = cls._get_completed_resource_ids(user_id)

        visited_ids = set()
        current_tag = tag
        used_fallback = False

        while current_tag and current_tag.id not in visited_ids:
            visited_ids.add(current_tag.id)

            query = Resource.query.filter(Resource.tag_id == current_tag.id)
            if completed_resource_ids:
                query = query.filter(~Resource.id.in_(list(completed_resource_ids)))

            mastery = UserKnowledgeMastery.query.filter_by(
                user_id=user_id,
                tag_id=current_tag.id
            ).first()
            if mastery and (mastery.mastery_level or 0) < 40:
                query = query.order_by(Resource.difficulty.asc().nullslast(), Resource.id.asc())
            else:
                query = query.order_by(Resource.id.asc())

            res = query.first()
            if res:
                reason = f"系统检测到您在【{tag.name}】上的掌握度较低，推荐该资源进行补强。"
                if used_fallback:
                    reason = f"系统检测到您在【{tag.name}】上的掌握度较低，当前节点资源不足，已为您降级推荐上层知识点【{current_tag.name}】资源。"

                return {
                    'id': res.id,
                    'title': res.title,
                    'type': res.type,
                    'url': res.url,
                    'source': res.source,
                    'matchedTag': tag.name,
                    'resourceTag': current_tag.name,
                    'resourceTagId': current_tag.id,
                    'resourceTagDepth': cls._tag_depth(current_tag),
                    'reason': reason
                }

            if current_tag.parent_id:
                current_tag = KnowledgeTag.query.get(current_tag.parent_id)
                used_fallback = True
            else:
                current_tag = None

        return None

    @classmethod
    def _build_gap_resources(cls, interview):
        job = db.session.get(Job, interview.job_id)
        if not job:
            return []

        core_tags = {}
        tags_rel = job.knowledge_tags
        if hasattr(tags_rel, 'all'):
            job_tags = tags_rel.all()
        else:
            job_tags = list(tags_rel or [])

        for tag in job_tags:
            core_tags[tag.id] = tag

        # 兜底：若岗位大纲为空，则从岗位题目反推一次
        if not core_tags:
            questions_rel = job.questions
            questions = questions_rel.all() if hasattr(questions_rel, 'all') else list(questions_rel or [])
            for q in questions:
                for tag in q.knowledge_tags:
                    core_tags[tag.id] = tag

        if not core_tags:
            return []

        weak_rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == interview.user_id,
            UserKnowledgeMastery.tag_id.in_(list(core_tags.keys())),
            UserKnowledgeMastery.mastery_level < 60
        ).order_by(UserKnowledgeMastery.mastery_level.asc()).all()

        results = []
        seen_resource_ids = set()
        for row in weak_rows:
            tag = core_tags.get(row.tag_id)
            if not tag:
                continue
            resource = cls._get_recommended_resource_by_tag(tag, interview.user_id)
            if not resource or resource['id'] in seen_resource_ids:
                continue
            seen_resource_ids.add(resource['id'])
            results.append(resource)
            if len(results) >= 5:
                break

        # 按图谱深度排序形成学习路径：基础概念在前，进阶原理在后
        results.sort(key=lambda item: (item.get('resourceTagDepth', 999), item.get('id', 0)))

        return results

    @classmethod
    def _build_reply_text_evaluations(cls, pairs):
        """
        批量评估用户的面试回答，利用向量检索获取标准参考点 (Example 模型)，交由 LLM 进行评价。
        """
        if not pairs:
            return {}

        llm = DeepSeekClient()

        def fetch_reference(item):
            reference_hint = ""
            try:
                # 获取当前问题的向量
                vec = InterviewService.get_embedding(item['question'])

                # 【核心逻辑】依赖 example.py：查询最近似的参考范例
                ex = Example.query.order_by(Example.embedding.l2_distance(vec)).first()
                if ex:
                    reference_hint = f"参考框架：{ex.framework}；范例要点：{ex.answer[:200]}"
            except Exception as e:
                print(f"[Error] Failed to fetch example for question index {item.get('index', 'unknown')}: {e}")

            return {
                'index': item['index'],
                'question': item['question'],
                'answer': item['answer'],
                'reference': reference_hint
            }

        payload = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            payload = list(executor.map(fetch_reference, pairs))

        system_prompt = (
            '你是一名专业技术面试评估助手。请仅评价用户回答质量，不要打分。\n'
            '【评估要求】\n'
            '1. 请严格参考提供的 "reference"（参考框架和要点）作为你的评价基准。如果 reference 为空，请依据你的专业技术知识进行客观评价。\n'
            '2. 如果用户的 answer 覆盖了 reference 中的要点，请予以肯定；如果有遗漏或偏差，请结合参考框架给出具体的改进建议。\n'
            '3. 必须严格返回 JSON 数组，不要包含 markdown 格式。\n'
            '4. 数组每项结构为：{"index": 1, "evaluationText": "..."}。\n'
            '5. evaluationText 要求：2-3 句中文，先肯定，再指出问题，最后给改进建议。'
        )

        user_prompt = f'请对以下问答中的“用户回答”逐条评价：\n{json.dumps(payload, ensure_ascii=False)}'

        try:
            response_text = llm.generate_reply([
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ])
        except Exception as e:
            print(f"[Error] LLM generate_reply failed: {e}")
            raise ValueError("大模型服务响应异常，请稍后重试")

        cleaned = cls._clean_json_block(response_text)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[Error] Failed to parse LLM response to JSON. Raw text: {cleaned}")
            raise ValueError('AI 返回格式无效或非标准 JSON')

        if not isinstance(parsed, list):
            raise ValueError('AI 返回格式无效：期望一个 JSON 数组')

        result = {}
        for item in parsed:
            try:
                idx = int(item.get('index'))
            except (TypeError, ValueError):
                continue

            text = (item.get('evaluationText') or '').strip()
            if text:
                result[idx] = text

        return result

    @classmethod
    def _build_dimensions(cls, interview_id):
        scores = db.session.query(InterviewScore, Dimension).join(
            Dimension, InterviewScore.dimension_id == Dimension.id
        ).filter(InterviewScore.interview_id == interview_id).all()

        dimensions = {v: 0 for v in cls.DIMENSION_NAME_TO_KEY.values()}
        comments = {v: '' for v in cls.DIMENSION_NAME_TO_KEY.values()}
        for score_obj, dim in scores:
            key = cls.DIMENSION_NAME_TO_KEY.get(cls._normalize_dimension_name(dim.name))
            if key:
                dimensions[key] = score_obj.score or 0
                comments[key] = (score_obj.comment or '').strip()
        return dimensions, comments

    @classmethod
    def _build_avg_dimensions(cls, job_id):
        rows = db.session.query(
            Dimension.name,
            func.avg(InterviewScore.score)
        ).join(
            InterviewScore, InterviewScore.dimension_id == Dimension.id
        ).join(
            Interview, Interview.id == InterviewScore.interview_id
        ).filter(
            Interview.status == 'completed',
            Interview.job_id == job_id
        ).group_by(Dimension.name).all()

        avg_dimensions = {v: 65 for v in cls.DIMENSION_NAME_TO_KEY.values()}
        for dim_name, avg_score in rows:
            key = cls.DIMENSION_NAME_TO_KEY.get(cls._normalize_dimension_name(dim_name))
            if key and avg_score is not None:
                avg_dimensions[key] = int(round(float(avg_score)))
        return avg_dimensions

    @classmethod
    def _build_questions(cls, interview_id, fallback_score):
        interview = db.session.get(Interview, int(interview_id))
        questions = []
        for item in cls._collect_reply_items(interview):
            q_text = item.get('question') or ''
            is_follow_up = ('追问' in q_text) or ('继续' in q_text and '请' in q_text)
            questions.append({
                'id': item.get('questionChatId'),
                'question': q_text,
                'answer': item.get('answer') or '',
                'score': fallback_score,
                'comment': '',
                'isFollowUp': is_follow_up,
                'index': item.get('index'),
                'reference': item.get('reference') or [],
                'questionId': item.get('questionId'),
                'questionSource': item.get('questionSource') or '',
                'isEnterpriseQuestion': bool(item.get('isEnterpriseQuestion')),
            })
        return questions

    @classmethod
    def _effective_question_count(cls, interview):
        try:
            return len(cls._collect_reply_items(interview))
        except Exception:
            return int(getattr(interview, 'question_count', 0) or 0)

    @staticmethod
    def _build_chat_details(interview_id):
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp.asc()).all()
        result = []
        for chat in chats:
            result.append({
                'id': chat.id,
                'role': chat.role,
                'content': chat.content or '',
                'timestamp': chat.timestamp.isoformat() if chat.timestamp else None,
                'duration': chat.duration or 0,
                'questionId': chat.question_id
            })
        return result

    @classmethod
    def get_report_detail(cls, report_id, user_id=None):
        interview = db.session.get(Interview, int(report_id))
        if not interview:
            raise ValueError('报告不存在')
        if user_id and interview.user_id != user_id:
            raise ValueError('无权限访问该报告')

        job = db.session.get(Job, interview.job_id)
        total_score = interview.total_score or 0

        dimensions, dimension_comments = cls._build_dimensions(interview.id)
        dim_highlights, dim_improvements = cls._build_dimension_feedback(dimensions)
        highlights = []
        for dim_key, dim_score in dimensions.items():
            label_map = {
                'technical': '技术正确性',
                'logic': '逻辑严谨性',
                'matching': '岗位匹配度',
                'expression': '表达沟通',
                'adaptability': '应变能力'
            }
            label = label_map.get(dim_key, dim_key)
            comment = (dimension_comments.get(dim_key) or '').strip()
            if comment:
                summary = '可继续保持这一优势' if int(dim_score or 0) >= 80 else '建议继续通过专项练习强化'
                highlights.append(f'【{label}】{comment}。{summary}。')
        highlights.extend(cls._split_text_to_list(interview.evaluation_highlights))
        highlights.extend(dim_highlights)
        highlights = list(dict.fromkeys([h for h in highlights if h]))

        raw_improvements = cls._split_text_to_list(interview.evaluation_improvements) + dim_improvements
        report_weaknesses = cls._build_report_weaknesses(interview, limit=8)
        improvements = []
        for weakness in report_weaknesses:
            tag = KnowledgeTag.query.get(weakness['tag_id'])
            resource = cls._get_recommended_resource_by_tag(tag, interview.user_id) if tag else None
            examples = weakness.get('examples') or []
            point = cls._build_weakness_point(weakness)
            improvements.append({
                'point': point,
                'resource': resource,
                'weaknessTag': weakness['name'],
                'masteryLevel': weakness['mastery_level'],
                'estimatedHours': weakness.get('estimated_hours'),
                'examples': examples,
            })
        if not improvements:
            for item in raw_improvements:
                point = cls._truncate_text(item, cls._MAX_IMPROVEMENT_POINT_LENGTH)
                improvements.append({
                    'point': point,
                    'resource': cls._get_recommended_resource(item, interview.user_id)
                })

        suggestions = cls._split_text_to_list(interview.evaluation_suggestions)

        if not highlights:
            highlights = ['暂无亮点总结']
        if not improvements:
            improvements = [{'point': '暂无待提升项', 'resource': None}]
        if not suggestions:
            suggestions = ['暂无改进建议']

        questions = cls._build_questions(interview.id, total_score)

        created_time = interview.end_time or interview.start_time
        start_time = interview.start_time
        end_time = interview.end_time
        duration = interview.used_time
        if duration is None and interview.start_time and interview.end_time:
            duration = int((interview.end_time - interview.start_time).total_seconds())

        summary_tags = cls._build_summary_tags(interview)
        graph_resources = cls._build_gap_resources(interview)
        recommended_resources = []
        seen_resource_ids = set()
        for imp in improvements:
            res = imp.get('resource') if isinstance(imp, dict) else None
            if res and res.get('id') not in seen_resource_ids:
                learning_row = UserLearning.query.filter_by(user_id=interview.user_id, resource_id=res.get('id')).first()
                seen_resource_ids.add(res.get('id'))
                recommended_resources.append({
                    **res,
                    'weaknessTag': imp.get('weaknessTag'),
                    'masteryLevel': imp.get('masteryLevel'),
                    'bookmarked': bool(learning_row and learning_row.bookmarked)
                })
        for res in graph_resources:
            if res.get('id') not in seen_resource_ids:
                learning_row = UserLearning.query.filter_by(user_id=interview.user_id, resource_id=res.get('id')).first()
                seen_resource_ids.add(res.get('id'))
                recommended_resources.append({**res, 'bookmarked': bool(learning_row and learning_row.bookmarked)})
            if len(recommended_resources) >= 8:
                break

        return {
            'id': interview.id,
            'sessionId': str(interview.id),
            'jobId': get_job_front_key(job),
            'jobName': job.name if job else '',
            'totalScore': total_score,
            'duration': duration or 0,
            'startTime': start_time.isoformat() if start_time else None,
            'endTime': end_time.isoformat() if end_time else None,
            'createdAt': created_time.isoformat() if created_time else None,
            'dimensions': dimensions,
            'avgDimensions': cls._build_avg_dimensions(interview.job_id),
            'highlights': highlights,
            'improvements': improvements,
            'weaknesses': report_weaknesses,
            'suggestions': suggestions,
            'sessionConfig': cls._format_session_config(interview),
            'highlightTags': summary_tags.get('highlightTags') or [],
            'weaknessTags': summary_tags.get('weaknessTags') or [],
            'graphCoverageRate': interview.graph_coverage_rate or 0,
            'graphDepthRate': interview.graph_depth_rate or 0,
            'graphCoverageMeta': interview.graph_coverage_meta or {},
            'graphResources': graph_resources,
            'recommendedResources': recommended_resources,
            'questions': questions,
            'questionCount': len(questions),
            'chatDetails': cls._build_chat_details(interview.id)
        }

    @classmethod
    def list_reports(cls, user_id=None, page=1, page_size=10, job_id=None):
        query = Interview.query.filter(Interview.status == 'completed')
        if user_id:
            query = query.filter(Interview.user_id == user_id)
        if job_id:
            query = query.filter(Interview.job_id == int(job_id))

        total = query.count()
        rows = query.order_by(Interview.end_time.desc().nullslast(), Interview.start_time.desc()) \
            .offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for interview in rows:
            job = db.session.get(Job, interview.job_id)
            summary_tags = cls._build_summary_tags(interview)
            items.append({
                'id': interview.id,
                'jobId': get_job_front_key(job),
                'jobName': job.name if job else '',
                'totalScore': interview.total_score or 0,
                'duration': interview.used_time or 0,
                'questionCount': cls._effective_question_count(interview),
                'startTime': interview.start_time.isoformat() if interview.start_time else None,
                'endTime': interview.end_time.isoformat() if interview.end_time else None,
                'createdAt': (interview.end_time or interview.start_time).isoformat() if (interview.end_time or interview.start_time) else None,
                'sessionConfig': cls._format_session_config(interview),
                'highlightTags': summary_tags.get('highlightTags') or [],
                'weaknessTags': summary_tags.get('weaknessTags') or [],
            })

        return {'list': items, 'total': total}

    @classmethod
    def analyze_reply_details(cls, report_id, user_id):
        interview = db.session.get(Interview, int(report_id))
        if not interview:
            raise ValueError('报告不存在')
        if user_id and interview.user_id != user_id:
            raise ValueError('无权限访问该报告')

        analyses = cls._collect_reply_items(interview)

        try:
            ai_eval_map = cls._build_reply_text_evaluations(analyses)
        except Exception as e:
            print(f"[Error] Failed to execute _build_reply_text_evaluations: {e}")
            ai_eval_map = {}

        for item in analyses:
            item['evaluationText'] = ai_eval_map.get(
                item['index'],
                '本次回答暂无法完成AI评价，建议围绕问题关键词补充结构化回答，并结合具体案例展开。'
            )

        return {
            'reportId': interview.id,
            'userId': interview.user_id,
            'totalRounds': len(analyses),
            'items': analyses
        }

    @classmethod
    def generate_reference_answer(cls, report_id, item_index, user_id):
        interview = db.session.get(Interview, int(report_id))
        if not interview:
            raise ValueError('报告不存在')
        if user_id and interview.user_id != user_id:
            raise ValueError('无权限访问该报告')

        try:
            target_index = int(item_index)
        except Exception:
            raise ValueError('题目序号无效')
        if target_index <= 0:
            raise ValueError('题目序号无效')

        items = cls._collect_reply_items(interview)
        target = next((it for it in items if it.get('index') == target_index), None)
        if not target:
            raise ValueError('未找到对应题目')

        question_text = (target.get('question') or '').strip()
        if not question_text:
            raise ValueError('题目内容为空，无法生成参考答案')

        answer_text = (target.get('answer') or '').strip()
        example_payload = None
        try:
            vec = InterviewService.get_embedding(question_text[:200])
            example = (
                Example.query
                .filter_by(job_id=interview.job_id)
                .order_by(Example.embedding.l2_distance(vec))
                .first()
            )
            if example:
                example_payload = {
                    'question': example.question or '',
                    'framework': example.framework or '',
                    'answer': example.answer or '',
                }
        except Exception:
            example_payload = None

        reference_points = target.get('reference') or []
        source = target.get('questionSource') or '通用'
        special_tag = f'企业真题（{source}）' if cls._is_enterprise_source(source) else '通用题'
        prompt_lines = [
            '你是资深面试官，请针对这道题生成一份“参考优秀回答”。',
            '要求：',
            '1. 结构清晰，先结论后展开，控制在 220-380 字。',
            '2. 用中文输出，风格贴近真实候选人的高质量面试回答，不要出现“作为AI”。',
            '3. 如有给定要点和优秀范例，请融合其优点但不要原文照抄。',
            f'4. 题目类型标签：{special_tag}。',
            '',
            f'面试题：{question_text}',
            f'用户原回答（用于改进对比）：{answer_text or "（用户未作答）"}',
            f'题库参考要点：{json.dumps(reference_points, ensure_ascii=False)}',
            f'历史优秀范例：{json.dumps(example_payload, ensure_ascii=False)}',
            '',
            '请直接输出“参考优秀回答”正文，不要输出标题和额外说明。'
        ]
        llm = DeepSeekClient()
        generated = llm.generate_reply(
            messages=[{'role': 'system', 'content': '\n'.join(prompt_lines)}],
            temperature=0.6
        )
        result_text = (generated or '').strip()
        if not result_text:
            raise ValueError('生成参考优秀回答失败，请稍后重试')

        return {
            'reportId': interview.id,
            'index': target_index,
            'question': question_text,
            'questionSource': source,
            'isEnterpriseQuestion': cls._is_enterprise_source(source),
            'referenceAnswer': result_text,
        }

    @classmethod
    def list_history_records(cls, user_id, page=1, page_size=10):
        if not user_id:
            raise ValueError('缺少登录凭证')

        query = Interview.query.filter(
            Interview.user_id == user_id,
            Interview.status == 'completed'
        )

        total = query.count()
        rows = query.order_by(
            Interview.end_time.desc().nullslast(),
            Interview.start_time.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        records = []
        for interview in rows:
            job = db.session.get(Job, interview.job_id)
            interview_time = interview.end_time or interview.start_time
            summary_tags = cls._build_summary_tags(interview)
            records.append({
                'id': interview.id,
                'reportId': interview.id,
                'interviewDate': interview_time.isoformat() if interview_time else None,
                'startTime': interview.start_time.isoformat() if interview.start_time else None,
                'endTime': interview.end_time.isoformat() if interview.end_time else None,
                'createdAt': interview_time.isoformat() if interview_time else None,
                'jobId': get_job_front_key(job),
                'jobName': job.name if job else '',
                'totalScore': interview.total_score or 0,
                'duration': interview.used_time or 0,
                'questionCount': cls._effective_question_count(interview),
                'sessionConfig': cls._format_session_config(interview),
                'highlightTags': summary_tags.get('highlightTags') or [],
                'weaknessTags': summary_tags.get('weaknessTags') or [],
            })

        return {'list': records, 'total': total}
