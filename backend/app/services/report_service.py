import concurrent.futures
from sqlalchemy import func
import re
import json
from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension
from app.models.job import Job, DEFAULT_JOBS, get_job_front_key
from app.models.question import Question
from app.models.example import Example
from app.models.learning import Resource, KnowledgeTag, UserKnowledgeMastery  # 图谱推荐依赖模型
from app.services.interview_service import InterviewService
from app.utils.llm_client import DeepSeekClient


class ReportService:
    DIMENSION_NAME_TO_KEY = {
        '技术正确性': 'technical',
        '逻辑严谨性': 'logic',
        '岗位匹配度': 'matching',
        '表达沟通': 'expression',
        '应变能力': 'adaptability'
    }

    _MEANINGLESS_ANSWER_PATTERN = re.compile(
        r'^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|1|2|3|4|5|6|7|8|9|0|[，。！？、\s]+)$',
        re.IGNORECASE
    )

    @staticmethod
    def _split_text_to_list(raw_text):
        if not raw_text:
            return []
        text = str(raw_text).replace('\r', '\n')
        lines = [line.strip(' -•\t') for line in text.split('\n') if line.strip()]
        if lines:
            return lines
        return [text.strip()]

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

            if not matched_tag:
                return None

            visited_ids = set()
            current_tag = matched_tag
            used_fallback = False

            while current_tag and current_tag.id not in visited_ids:
                visited_ids.add(current_tag.id)

                query = Resource.query.join(Resource.knowledge_tags).filter(KnowledgeTag.id == current_tag.id)

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

        visited_ids = set()
        current_tag = tag
        used_fallback = False

        while current_tag and current_tag.id not in visited_ids:
            visited_ids.add(current_tag.id)

            query = Resource.query.filter(Resource.tag_id == current_tag.id)

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
        questions = Question.query.filter_by(job_id=interview.job_id).all()
        core_tags = {}
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
        for score_obj, dim in scores:
            key = cls.DIMENSION_NAME_TO_KEY.get(dim.name)
            if key:
                dimensions[key] = score_obj.score or 0
        return dimensions

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
            key = cls.DIMENSION_NAME_TO_KEY.get(dim_name)
            if key and avg_score is not None:
                avg_dimensions[key] = int(round(float(avg_score)))
        return avg_dimensions

    @classmethod
    def _build_questions(cls, interview_id, fallback_score):
        interview = db.session.get(Interview, int(interview_id))
        job_id = interview.job_id if interview else None

        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp.asc()).all()
        questions = []
        question_index = 1

        for idx, chat in enumerate(chats):
            if chat.role != 'ai':
                continue

            answer = ''
            for j in range(idx + 1, len(chats)):
                if chats[j].role == 'user':
                    maybe_answer = chats[j].content or ''
                    if not cls._is_meaningless_answer(maybe_answer):
                        answer = maybe_answer
                    break
                if chats[j].role == 'ai':
                    break

            q_text = chat.content or ''
            is_follow_up = ('追问' in q_text) or ('继续' in q_text and '请' in q_text)

            reference = None
            if job_id:
                try:
                    q_vec = InterviewService.get_embedding(q_text[:200])
                    # 【核心逻辑】依赖 question.py：查询题库匹配原题的标准知识点/参考答案
                    matched_q = Question.query.filter_by(job_id=job_id) \
                        .order_by(Question.embedding.l2_distance(q_vec)).first()
                    if matched_q:
                        reference = matched_q.reference_answer
                except Exception:
                    reference = None

            questions.append({
                'id': chat.id,
                'question': q_text,
                'answer': answer,
                'score': fallback_score,
                'comment': '',
                'isFollowUp': is_follow_up,
                'index': question_index,
                'reference': reference
            })
            question_index += 1
        return questions

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

        highlights = cls._split_text_to_list(interview.evaluation_highlights)

        # 【修改】使用推荐资源方法将待提升点与 learning.py 的资源关联起来
        raw_improvements = cls._split_text_to_list(interview.evaluation_improvements)
        improvements = []
        for item in raw_improvements:
            improvements.append({
                'point': item,
                'resource': cls._get_recommended_resource(item, interview.user_id) # 图谱匹配+降级推荐
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
            'dimensions': cls._build_dimensions(interview.id),
            'avgDimensions': cls._build_avg_dimensions(interview.job_id),
            'highlights': highlights,
            'improvements': improvements,
            'suggestions': suggestions,
            'graphCoverageRate': interview.graph_coverage_rate or 0,
            'graphDepthRate': interview.graph_depth_rate or 0,
            'graphCoverageMeta': interview.graph_coverage_meta or {},
            'graphResources': cls._build_gap_resources(interview),
            'questions': questions,
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
            items.append({
                'id': interview.id,
                'jobId': get_job_front_key(job),
                'jobName': job.name if job else '',
                'totalScore': interview.total_score or 0,
                'duration': interview.used_time or 0,
                'questionCount': interview.question_count or 0,
                'startTime': interview.start_time.isoformat() if interview.start_time else None,
                'endTime': interview.end_time.isoformat() if interview.end_time else None,
                'createdAt': (interview.end_time or interview.start_time).isoformat() if (interview.end_time or interview.start_time) else None
            })

        return {'list': items, 'total': total}

    @classmethod
    def analyze_reply_details(cls, report_id, user_id):
        interview = db.session.get(Interview, int(report_id))
        if not interview:
            raise ValueError('报告不存在')
        if user_id and interview.user_id != user_id:
            raise ValueError('无权限访问该报告')

        chats = InterviewChat.query.filter_by(interview_id=interview.id).order_by(InterviewChat.timestamp.asc()).all()
        analyses = []
        analysis_index = 1

        for idx, chat in enumerate(chats):
            if chat.role != 'ai':
                continue

            user_reply = None
            for j in range(idx + 1, len(chats)):
                if chats[j].role == 'user':
                    if not cls._is_meaningless_answer(chats[j].content or ''):
                        user_reply = chats[j]
                    break
                if chats[j].role == 'ai':
                    break

            analyses.append({
                'index': analysis_index,
                'questionChatId': chat.id,
                'answerChatId': user_reply.id if user_reply else None,
                'question': chat.content or '',
                'answer': (user_reply.content if user_reply else '') or '',
                'answerAt': user_reply.timestamp.isoformat() if (user_reply and user_reply.timestamp) else None
            })
            analysis_index += 1

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
                'questionCount': interview.question_count or 0
            })

        return {'list': records, 'total': total}
