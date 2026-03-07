from sqlalchemy import func
import re
import json
from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension
from app.models.job import Job
from app.utils.llm_client import DeepSeekClient


class ReportService:
    DIMENSION_NAME_TO_KEY = {
        '技术正确性': 'technical',
        '逻辑严谨性': 'logic',
        '岗位匹配度': 'matching',
        '表达沟通': 'expression',
        '应变能力': 'adaptability'
    }

    FRONT_JOB_KEY_TO_NAME = {
        'java-backend': 'Java后端开发',
        'web-frontend': '前端开发',
        'python-algorithm': 'Python算法工程师',
        'fullstack': '全栈开发工程师',
        'android': 'Android开发',
        'devops': 'DevOps工程师'
    }

    @classmethod
    def _job_to_front_key(cls, job):
        if not job:
            return None
        for key, value in cls.FRONT_JOB_KEY_TO_NAME.items():
            if value == job.name:
                return key

        name = (job.name or '').lower()
        if 'java' in name:
            return 'java-backend'
        if '前端' in job.name or 'frontend' in name or 'web' in name:
            return 'web-frontend'
        if 'python' in name or '算法' in job.name:
            return 'python-algorithm'
        if '全栈' in job.name:
            return 'fullstack'
        if 'android' in name:
            return 'android'
        if 'devops' in name:
            return 'devops'
        return None

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
    def _build_reply_text_evaluations(cls, pairs):
        if not pairs:
            return {}

        llm = DeepSeekClient()
        payload = [
            {
                'index': item['index'],
                'question': item['question'],
                'answer': item['answer']
            }
            for item in pairs
        ]

        system_prompt = (
            '你是一名专业技术面试评估助手。请仅评价用户回答质量，不要打分。'
            '必须严格返回 JSON 数组，不要包含 markdown。'
            '数组每项结构为：{"index": 1, "evaluationText": "..."}。'
            'evaluationText 要求：2-3 句中文，先肯定，再指出问题，最后给改进建议。'
        )

        user_prompt = f'请对以下问答中的“用户回答”逐条评价：\n{json.dumps(payload, ensure_ascii=False)}'
        response_text = llm.generate_reply([
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ])

        cleaned = cls._clean_json_block(response_text)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            raise ValueError('AI 返回格式无效')

        result = {}
        for item in parsed:
            try:
                idx = int(item.get('index'))
            except Exception:
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
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp.asc()).all()
        questions = []
        question_index = 1

        for idx, chat in enumerate(chats):
            if chat.role != 'ai':
                continue

            answer = ''
            for j in range(idx + 1, len(chats)):
                if chats[j].role == 'user':
                    answer = chats[j].content
                    break
                if chats[j].role == 'ai':
                    break

            q_text = chat.content or ''
            is_follow_up = ('追问' in q_text) or ('继续' in q_text and '请' in q_text)
            questions.append({
                'id': chat.id,
                'question': q_text,
                'answer': answer,
                'score': fallback_score,
                'comment': '',
                'isFollowUp': is_follow_up,
                'index': question_index
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
        improvements = [
            {'point': item, 'resource': None} for item in cls._split_text_to_list(interview.evaluation_improvements)
        ]
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
            'jobId': cls._job_to_front_key(job),
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
                'jobId': cls._job_to_front_key(job),
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
        except Exception:
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
                'jobId': cls._job_to_front_key(job),
                'jobName': job.name if job else '',
                'totalScore': interview.total_score or 0,
                'duration': interview.used_time or 0,
                'questionCount': interview.question_count or 0
            })

        return {'list': records, 'total': total}
