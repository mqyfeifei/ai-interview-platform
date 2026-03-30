from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, or_
import yaml

from app.services.auth_service import AuthService
from app.services.learning_service import LearningService
from app.api.v1.auth_utils import admin_required
from app.extensions import db
from app.models.user import User
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension
from app.models.job import Job
from app.models.question import Question
from app.models.knowledge import KnowledgeItem
from app.models.prompt import AiPrompt
from app.models.learning import UserLearning


admin_bp = Blueprint('admin', __name__)

_JOB_MAPPING_CACHE = None


def _serialize_question(question):
    return {
        'id': question.id,
        'job_id': question.job_id,
        'content': question.content,
        'type': question.type,
        'difficulty': question.difficulty,
        'keywords': question.keywords,
        'reference_answer': question.reference_answer,
        'knowledge_points': question.knowledge_points
    }


def _serialize_knowledge(item):
    return {
        'id': item.id,
        'title': item.title,
        'content': item.content,
        'type': item.type,
        'job_id': item.job_id,
        'tags': item.tags
    }


def _resolve_entity():
    entity = (request.args.get('entity') or '').strip().lower()
    if not entity:
        body = request.get_json(silent=True) or {}
        entity = str(body.get('entity', 'question')).strip().lower()
    return entity or 'question'


def _load_job_mapping_from_config():
    global _JOB_MAPPING_CACHE
    if _JOB_MAPPING_CACHE is not None:
        return _JOB_MAPPING_CACHE

    backend_root = Path(__file__).resolve().parents[3]
    kb_config_path = backend_root / 'FuChuangTiKu' / 'kb.config.yaml'
    mapping = {}

    if kb_config_path.exists():
        with open(kb_config_path, 'r', encoding='utf-8') as fp:
            cfg = yaml.safe_load(fp) or {}
        raw_mapping = cfg.get('job_mapping', {})
        if isinstance(raw_mapping, dict):
            for key, val in raw_mapping.items():
                if not key:
                    continue
                if isinstance(val, dict):
                    mapping[str(key).strip().lower()] = {
                        'name': str(val.get('name') or '').strip(),
                        'desc': str(val.get('desc') or '').strip()
                    }
                elif isinstance(val, str):
                    mapping[str(key).strip().lower()] = {'name': val.strip(), 'desc': ''}

    _JOB_MAPPING_CACHE = mapping
    return _JOB_MAPPING_CACHE


def _build_job_profile(domain_key):
    domain = (domain_key or '').strip().lower()
    mapping = _load_job_mapping_from_config()
    profile = mapping.get(domain)

    if profile and profile.get('name'):
        return {'name': profile['name'], 'desc': profile.get('desc') or ''}

    # 配置缺失时采用动态兜底，避免岗位名称硬编码在代码里
    display_name = domain.replace('_', ' ').strip().title() if domain else 'General'
    return {
        'name': f'{display_name}工程师',
        'desc': f'自动生成岗位（domain={domain or "general"}）'
    }


def _get_or_create_job_by_domain(domain_key):
    domain_key = (domain_key or '').strip().lower()
    job_info = _build_job_profile(domain_key)

    job = Job.query.filter_by(name=job_info['name']).first()
    if not job:
        job = Job(name=job_info['name'], description=job_info['desc'])
        db.session.add(job)
        db.session.flush()
    return job


def _normalize_question_type(raw_type):
    value = (raw_type or 'technical').strip()
    return value[:20] if len(value) > 20 else value


def _extract_domain_from_dataset(dataset_type, file_path):
    if dataset_type and '_' in dataset_type:
        return dataset_type.split('_')[-1]
    stem = Path(file_path).stem
    return stem.split('_')[0] if '_' in stem else stem


def _create_default_prompt_for_job(job):
    prompt_name = f'{job.name}默认面试官'
    default_system_prompt = (
        f'你是一位专业的{job.name}面试官。请围绕该岗位核心能力进行提问与追问，'
        '关注候选人的基础能力、项目实践和问题解决能力。'
        '【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。'
        '结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。'
    )
    default_greeting = f'你好，欢迎参加{job.name}岗位面试。我们先从你的相关项目经验开始。'

    return AiPrompt(
        name=prompt_name,
        job_id=job.id,
        role_description=f'{job.name}岗位默认提示词配置',
        system_prompt=default_system_prompt,
        greeting_message=default_greeting,
        questioning_style='专业、结构化追问',
        temperature=0.7,
        max_tokens=500,
        is_active=True
    )


def _serialize_prompt(prompt):
    return {
        'id': prompt.id,
        'name': prompt.name,
        'job_id': prompt.job_id,
        'job_name': prompt.job.name if getattr(prompt, 'job', None) else None,
        'role_description': prompt.role_description,
        'system_prompt': prompt.system_prompt,
        'greeting_message': prompt.greeting_message,
        'questioning_style': prompt.questioning_style,
        'temperature': float(prompt.temperature) if prompt.temperature is not None else None,
        'max_tokens': prompt.max_tokens,
        'is_active': prompt.is_active,
        'created_at': prompt.created_at.isoformat() if prompt.created_at else None
    }


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


def error_response(msg, status_code=400):
    return jsonify({"code": status_code, "msg": msg, "message": msg}), status_code


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    login_id = data.get('login_id') or data.get('loginId') or data.get('target') or data.get('email') or data.get('phone')
    password = data.get('password')

    try:
        result = AuthService.admin_login_with_password(login_id, password)
        return success_response(result, '管理员登录成功')
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/ping', methods=['GET'])
@admin_required
def admin_ping():
    return success_response({"ok": True}, '管理员鉴权通过')


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    try:
        total_users = db.session.query(func.count(User.id)).scalar() or 0
        today_new_users = (
            db.session.query(func.count(User.id))
            .filter(func.date(User.created_at) == date.today())
            .scalar() or 0
        )
        total_interviews = db.session.query(func.count(Interview.id)).scalar() or 0
        today_new_interviews = (
            db.session.query(func.count(Interview.id))
            .filter(func.date(Interview.start_time) == date.today())
            .scalar() or 0
        )
        total_jobs = db.session.query(func.count(Job.id)).scalar() or 0
        total_questions = db.session.query(func.count(Question.id)).scalar() or 0

        top_jobs_rows = (
            db.session.query(
                Job.id,
                Job.name,
                func.count(Interview.id).label('interview_count')
            )
            .join(Interview, Interview.job_id == Job.id)
            .group_by(Job.id, Job.name)
            .order_by(func.count(Interview.id).desc(), Job.id.asc())
            .limit(5)
            .all()
        )

        top_jobs = [
            {
                'job_id': row.id,
                'job_name': row.name,
                'interview_count': int(row.interview_count or 0)
            }
            for row in top_jobs_rows
        ]

        # 用户排行榜：面试次数/均分/连续学习天数综合评分
        user_perf_rows = (
            db.session.query(
                User.id.label('user_id'),
                User.username.label('username'),
                func.count(Interview.id).label('interview_count'),
                func.avg(Interview.total_score).label('avg_score')
            )
            .outerjoin(Interview, Interview.user_id == User.id)
            .group_by(User.id, User.username)
            .all()
        )

        # 获取用户学习完成日期集合（按天聚合）
        learn_dates = {}
        learn_query = (
            db.session.query(
                UserLearning.user_id,
                func.date(UserLearning.finish_time).label('day')
            )
            .filter(UserLearning.finish_time != None)
            .group_by(UserLearning.user_id, func.date(UserLearning.finish_time))
            .all()
        )
        for u_id, day in learn_query:
            learn_dates.setdefault(u_id, set()).add(day)

        user_rankings = []
        for row in user_perf_rows:
            streak = 0
            day_check = date.today()
            user_days = sorted(learn_dates.get(row.user_id, []), reverse=True)
            # 计算连续学习天数(当天及往前)
            while day_check in user_days:
                streak += 1
                day_check -= timedelta(days=1)

            interview_count = int(row.interview_count or 0)
            avg_score = float(row.avg_score or 0)
            score = interview_count * 0.5 + avg_score * 0.3 + streak * 0.2
            user_rankings.append({
                'user_id': row.user_id,
                'username': row.username,
                'interview_count': interview_count,
                'avg_score': round(avg_score, 2),
                'streak_days': streak,
                'score': round(score, 2)
            })

        user_rankings = sorted(user_rankings, key=lambda x: x['score'], reverse=True)[:10]

        # 最新动态：用户注册 + 面试完成 + 题库新增
        recent_events = []

        for u in db.session.query(User.username, User.created_at).order_by(User.created_at.desc()).limit(10):
            recent_events.append({
                'text': f"{u.username} 注册为新用户",
                'time': u.created_at.isoformat(),
                'type': 'user_register'
            })

        for row in (
                db.session.query(Interview, User.username.label('username'), Job.name.label('job_name'))
                .join(User, Interview.user_id == User.id)
                .join(Job, Interview.job_id == Job.id)
                .filter(Interview.status == 'completed', Interview.end_time != None)
                .order_by(Interview.end_time.desc())
                .limit(10)
        ):
            interview, username, job_name = row
            recent_events.append({
                'text': f"{username} 完成了 {job_name} 面试",
                'time': interview.end_time.isoformat(),
                'type': 'interview_completed'
            })

        for q in db.session.query(Question.id, Question.content).order_by(Question.id.desc()).limit(10):
            content = q.content or '题目'
            short = content[:12] + '...' if len(content) > 12 else content
            recent_events.append({
                'text': f"系统新增「{short}」题库",
                'time': None,
                'type': 'question_added'
            })

        # 按时间排序，None 放后面
        recent_events = sorted(recent_events, key=lambda x: x['time'] or '', reverse=True)[:10]

        # 时间序列：最近7天每日累积用户总数和面试总数
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        user_by_date = {
            row.day: int(row.user_count)
            for row in db.session.query(func.date(User.created_at).label('day'), func.count(User.id).label('user_count'))
            .filter(func.date(User.created_at) >= start_date)
            .group_by(func.date(User.created_at)).all()
        }

        interview_by_date = {
            row.day: int(row.interview_count)
            for row in db.session.query(func.date(Interview.start_time).label('day'), func.count(Interview.id).label('interview_count'))
            .filter(func.date(Interview.start_time) >= start_date)
            .group_by(func.date(Interview.start_time)).all()
        }

        current_users = 0
        current_interviews = 0
        usage_trend = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            current_users += user_by_date.get(day, 0)
            current_interviews += interview_by_date.get(day, 0)
            usage_trend.append({
                'date': day.isoformat(),
                'total_users': current_users,
                'total_interviews': current_interviews
            })

        return success_response(
            {
                'total_users': int(total_users),
                'today_new_users': int(today_new_users),
                'total_interviews': int(total_interviews),
                'today_new_interviews': int(today_new_interviews),
                'total_jobs': int(total_jobs),
                'total_questions': int(total_questions),
                'top_jobs': top_jobs,
                'top_users': user_rankings,
                'recent_events': recent_events,
                'usage_trend': usage_trend
            },
            '获取管理大盘数据成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)
        keyword = (request.args.get('keyword', default='', type=str) or '').strip()
        role = (request.args.get('role', default=None, type=str) or '').strip().lower()

        if page < 1:
            return error_response('page 必须大于等于 1', 400)
        if size < 1:
            return error_response('size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        query = User.query

        status = request.args.get('is_active', default=None)
        if status is not None and status != '':
            if status in ['true', '1', 'True', 'TRUE', 't']:
                query = query.filter(User.is_active == True)
            elif status in ['false', '0', 'False', 'FALSE', 'f']:
                query = query.filter(User.is_active == False)

        user_id = request.args.get('user_id', default=None, type=int)
        if user_id:
            query = query.filter(User.id == user_id)

        grade = (request.args.get('grade', default=None, type=str) or '').strip()
        if grade:
            query = query.filter(User.grade == grade)

        major = (request.args.get('major', default=None, type=str) or '').strip()
        if major:
            query = query.filter(User.major.ilike(f'%{major}%'))

        school = (request.args.get('school', default=None, type=str) or '').strip()
        if school:
            query = query.filter(User.school.ilike(f'%{school}%'))

        username = (request.args.get('username', default=None, type=str) or '').strip()
        if username:
            query = query.filter(User.username.ilike(f'%{username}%'))

        email = (request.args.get('email', default=None, type=str) or '').strip()
        if email:
            query = query.filter(User.email.ilike(f'%{email}%'))

        created_range = request.args.get('created_range', default=None, type=int)
        if created_range is not None and created_range > 0:
            from_date = datetime.utcnow() - timedelta(days=created_range)
            query = query.filter(User.created_at >= from_date)

        if role:
            query = query.filter(User.role == role)

        if keyword:
            like_pattern = f'%{keyword}%'
            query = query.filter(
                or_(
                    User.username.ilike(like_pattern),
                    User.email.ilike(like_pattern)
                )
            )

        total = query.count()
        items = (
            query
            .order_by(User.created_at.desc(), User.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return success_response(
            {
                'list': [user.to_dict() for user in items],
                'page': page,
                'size': size,
                'total': total
            },
            '获取用户列表成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    try:
        data = request.get_json(silent=True) or {}
        if 'is_active' not in data:
            return error_response('缺少 is_active 字段', 400)
        if not isinstance(data.get('is_active'), bool):
            return error_response('is_active 必须是布尔值', 400)

        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)

        user.is_active = data.get('is_active')
        db.session.commit()

        return success_response(user.to_dict(), '用户状态更新成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)

        db.session.delete(user)
        db.session.commit()

        return success_response(None, '用户删除成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/jobs', methods=['GET'])
@admin_required
def list_jobs():
    try:
        jobs = Job.query.order_by(Job.id.asc()).all()
        return success_response({'list': [job.to_dict() for job in jobs], 'total': len(jobs)}, '获取岗位列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/jobs', methods=['POST'])
@admin_required
def create_job():
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return error_response('岗位名称不能为空', 400)

        if Job.query.filter_by(name=name).first():
            return error_response('岗位名称已存在', 400)

        job = Job(
            name=name,
            description=data.get('description'),
            tech_stack=data.get('tech_stack') if isinstance(data.get('tech_stack'), list) else None,
            icon_url=data.get('icon_url')
        )
        db.session.add(job)
        db.session.flush()

        default_prompt = _create_default_prompt_for_job(job)
        db.session.add(default_prompt)
        db.session.commit()
        return success_response(
            {
                **job.to_dict(),
                'default_prompt_id': default_prompt.id,
                'default_prompt_name': default_prompt.name
            },
            '岗位创建成功'
        )
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@admin_required
def update_job(job_id):
    try:
        job = Job.query.get(job_id)
        if not job:
            return error_response('岗位不存在', 404)

        data = request.get_json(silent=True) or {}
        if 'name' in data:
            name = (data.get('name') or '').strip()
            if not name:
                return error_response('岗位名称不能为空', 400)
            duplicate = Job.query.filter(Job.name == name, Job.id != job_id).first()
            if duplicate:
                return error_response('岗位名称已存在', 400)
            job.name = name

        if 'description' in data:
            job.description = data.get('description')
        if 'icon_url' in data:
            job.icon_url = data.get('icon_url')
        if 'tech_stack' in data:
            if data.get('tech_stack') is not None and not isinstance(data.get('tech_stack'), list):
                return error_response('tech_stack 必须为数组或 null', 400)
            job.tech_stack = data.get('tech_stack')

        db.session.commit()
        return success_response(job.to_dict(), '岗位更新成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@admin_required
def delete_job(job_id):
    try:
        job = Job.query.get(job_id)
        if not job:
            return error_response('岗位不存在', 404)

        db.session.delete(job)
        db.session.commit()
        return success_response({'deleted_id': job_id}, '岗位删除成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions', methods=['GET'])
@admin_required
def list_question_entities():
    try:
        entity = _resolve_entity()
        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)
        job_id = request.args.get('job_id', type=int)

        if page < 1 or size < 1:
            return error_response('page 和 size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        if entity == 'question':
            query = Question.query
            if job_id:
                query = query.filter(Question.job_id == job_id)
            total = query.count()
            records = (
                query.order_by(Question.id.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            payload = [_serialize_question(item) for item in records]
        elif entity == 'knowledge':
            query = KnowledgeItem.query
            if job_id:
                query = query.filter(KnowledgeItem.job_id == job_id)
            total = query.count()
            records = (
                query.order_by(KnowledgeItem.id.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            payload = [_serialize_knowledge(item) for item in records]
        else:
            return error_response('entity 仅支持 question 或 knowledge', 400)

        return success_response(
            {'entity': entity, 'list': payload, 'page': page, 'size': size, 'total': total},
            '获取题库列表成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/questions', methods=['POST'])
@admin_required
def create_question_entity():
    try:
        data = request.get_json(silent=True) or {}
        entity = _resolve_entity()

        if entity == 'question':
            content = (data.get('content') or '').strip()
            if not content:
                return error_response('content 不能为空', 400)
            if not data.get('job_id'):
                return error_response('job_id 不能为空', 400)

            item = Question(
                job_id=data.get('job_id'),
                content=content,
                type=_normalize_question_type(data.get('type')),
                difficulty=data.get('difficulty'),
                keywords=data.get('keywords') if isinstance(data.get('keywords'), list) else None,
                reference_answer=data.get('reference_answer'),
                knowledge_points=data.get('knowledge_points') if isinstance(data.get('knowledge_points'), list) else None
            )
            db.session.add(item)
            db.session.commit()
            return success_response(_serialize_question(item), '题目创建成功')

        if entity == 'knowledge':
            content = (data.get('content') or '').strip()
            if not content:
                return error_response('content 不能为空', 400)
            if not data.get('type'):
                return error_response('type 不能为空', 400)

            item = KnowledgeItem(
                title=data.get('title'),
                content=content,
                type=data.get('type'),
                job_id=data.get('job_id'),
                tags=data.get('tags') if isinstance(data.get('tags'), list) else None
            )
            db.session.add(item)
            db.session.commit()
            return success_response(_serialize_knowledge(item), '知识项创建成功')

        return error_response('entity 仅支持 question 或 knowledge', 400)
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/<int:item_id>', methods=['PUT'])
@admin_required
def update_question_entity(item_id):
    try:
        data = request.get_json(silent=True) or {}
        entity = _resolve_entity()

        if entity == 'question':
            item = Question.query.get(item_id)
            if not item:
                return error_response('题目不存在', 404)

            if 'job_id' in data:
                item.job_id = data.get('job_id')
            if 'content' in data:
                content = (data.get('content') or '').strip()
                if not content:
                    return error_response('content 不能为空', 400)
                item.content = content
            if 'type' in data:
                item.type = _normalize_question_type(data.get('type'))
            if 'difficulty' in data:
                item.difficulty = data.get('difficulty')
            if 'keywords' in data:
                if data.get('keywords') is not None and not isinstance(data.get('keywords'), list):
                    return error_response('keywords 必须是数组或 null', 400)
                item.keywords = data.get('keywords')
            if 'reference_answer' in data:
                item.reference_answer = data.get('reference_answer')
            if 'knowledge_points' in data:
                if data.get('knowledge_points') is not None and not isinstance(data.get('knowledge_points'), list):
                    return error_response('knowledge_points 必须是数组或 null', 400)
                item.knowledge_points = data.get('knowledge_points')

            db.session.commit()
            return success_response(_serialize_question(item), '题目更新成功')

        if entity == 'knowledge':
            item = KnowledgeItem.query.get(item_id)
            if not item:
                return error_response('知识项不存在', 404)

            if 'title' in data:
                item.title = data.get('title')
            if 'content' in data:
                content = (data.get('content') or '').strip()
                if not content:
                    return error_response('content 不能为空', 400)
                item.content = content
            if 'type' in data:
                item.type = data.get('type')
            if 'job_id' in data:
                item.job_id = data.get('job_id')
            if 'tags' in data:
                if data.get('tags') is not None and not isinstance(data.get('tags'), list):
                    return error_response('tags 必须是数组或 null', 400)
                item.tags = data.get('tags')

            db.session.commit()
            return success_response(_serialize_knowledge(item), '知识项更新成功')

        return error_response('entity 仅支持 question 或 knowledge', 400)
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_question_entity(item_id):
    try:
        entity = _resolve_entity()

        if entity == 'question':
            item = Question.query.get(item_id)
            if not item:
                return error_response('题目不存在', 404)
            db.session.delete(item)
            db.session.commit()
            return success_response({'deleted_id': item_id, 'entity': entity}, '题目删除成功')

        if entity == 'knowledge':
            item = KnowledgeItem.query.get(item_id)
            if not item:
                return error_response('知识项不存在', 404)
            db.session.delete(item)
            db.session.commit()
            return success_response({'deleted_id': item_id, 'entity': entity}, '知识项删除成功')

        return error_response('entity 仅支持 question 或 knowledge', 400)
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/import', methods=['POST'])
@admin_required
def import_questions():
    try:
        data = request.get_json(silent=True) or {}
        clear_existing = bool(data.get('clear_existing', False))
        dry_run = bool(data.get('dry_run', False))
        base_dir = (data.get('base_dir') or 'FuChuangTiKu').strip()

        backend_root = Path(__file__).resolve().parents[3]
        kb_root = (backend_root / base_dir).resolve()
        if not kb_root.exists() or not kb_root.is_dir():
            return error_response(f'题库目录不存在: {kb_root}', 400)

        index_path = kb_root / 'index.yaml'
        datasets = []
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as fp:
                index_data = yaml.safe_load(fp) or {}
            datasets = index_data.get('datasets', []) or []
            datasets = [item for item in datasets if 'questions' in str(item.get('type', ''))]
        else:
            for qf in sorted((kb_root / 'data' / 'questions').glob('*.yaml')):
                datasets.append({'type': qf.stem, 'path': str(qf.relative_to(kb_root)).replace('\\\\', '/')})

        if not datasets:
            return error_response('未发现可导入的 questions YAML 文件', 400)

        all_objects = []
        file_stats = []
        skipped = 0

        for ds in datasets:
            ds_type = ds.get('type')
            ds_path = ds.get('path')
            if not ds_path:
                continue

            yaml_path = (kb_root / ds_path).resolve()
            if not yaml_path.exists():
                continue

            with open(yaml_path, 'r', encoding='utf-8') as fp:
                payload = yaml.safe_load(fp) or {}

            items = payload.get('items', []) or []
            domain = _extract_domain_from_dataset(ds_type, str(yaml_path))
            job = _get_or_create_job_by_domain(domain)

            imported_count = 0
            for item in items:
                content = (item.get('question') or '').strip()
                if not content:
                    skipped += 1
                    continue

                key_points = item.get('key_points') if isinstance(item.get('key_points'), list) else None
                tags = item.get('tags') if isinstance(item.get('tags'), list) else None
                reference_answer = item.get('answer')
                if not reference_answer and key_points:
                    reference_answer = '\\n'.join([f'- {kp}' for kp in key_points])

                all_objects.append(
                    Question(
                        job_id=job.id,
                        content=content,
                        type=_normalize_question_type(item.get('type')),
                        difficulty=item.get('difficulty'),
                        keywords=tags,
                        reference_answer=reference_answer,
                        knowledge_points=key_points
                    )
                )
                imported_count += 1

            file_stats.append(
                {
                    'type': ds_type,
                    'file': str(yaml_path),
                    'job_id': job.id,
                    'job_name': job.name,
                    'count': imported_count
                }
            )

        if not dry_run:
            if clear_existing:
                db.session.query(Question).delete()
                db.session.flush()

            if all_objects:
                db.session.bulk_save_objects(all_objects)
            db.session.commit()
        else:
            db.session.rollback()

        return success_response(
            {
                'dry_run': dry_run,
                'clear_existing': clear_existing,
                'base_dir': str(kb_root),
                'imported_total': len(all_objects),
                'skipped': skipped,
                'files': file_stats
            },
            '题库批量导入完成'
        )
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/prompts', methods=['GET'])
@admin_required
def list_prompts():
    try:
        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)
        keyword = (request.args.get('keyword', default='', type=str) or '').strip()

        if page < 1:
            return error_response('page 必须大于等于 1', 400)
        if size < 1:
            return error_response('size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        query = AiPrompt.query
        if keyword:
            pattern = f'%{keyword}%'
            query = query.filter(
                or_(
                    AiPrompt.name.ilike(pattern),
                    AiPrompt.questioning_style.ilike(pattern),
                    AiPrompt.role_description.ilike(pattern)
                )
            )

        total = query.count()
        prompts = (
            query
            .order_by(AiPrompt.id.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        data = [_serialize_prompt(prompt) for prompt in prompts]
        return success_response({'list': data, 'page': page, 'size': size, 'total': total}, '获取提示词列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/prompts', methods=['POST'])
@admin_required
def create_prompt():
    try:
        data = request.get_json(silent=True) or {}

        name = (data.get('name') or '').strip()
        if not name:
            return error_response('name 不能为空', 400)

        incoming_text = data.get('system_prompt')
        if incoming_text is None:
            incoming_text = data.get('content')
        if incoming_text is None:
            incoming_text = data.get('text')
        incoming_text = str(incoming_text or '').strip()
        if not incoming_text:
            return error_response('提示词内容不能为空', 400)

        is_active = data.get('is_active', True)
        if not isinstance(is_active, bool):
            return error_response('is_active 必须是布尔值', 400)

        prompt = AiPrompt(
            name=name,
            job_id=data.get('job_id'),
            role_description=data.get('role_description') or data.get('description'),
            system_prompt=incoming_text,
            greeting_message=data.get('greeting_message'),
            questioning_style=data.get('questioning_style') or data.get('scene_key'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 500),
            is_active=is_active
        )

        db.session.add(prompt)
        db.session.commit()
        return success_response(_serialize_prompt(prompt), '提示词创建成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['GET'])
@admin_required
def get_prompt_detail(prompt_id):
    try:
        prompt = AiPrompt.query.get(prompt_id)
        if not prompt:
            return error_response('Prompt 不存在', 404)
        return success_response(_serialize_prompt(prompt), '获取提示词详情成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
@admin_required
def update_prompt(prompt_id):
    try:
        prompt = AiPrompt.query.get(prompt_id)
        if not prompt:
            return error_response('Prompt 不存在', 404)

        data = request.get_json(silent=True) or {}

        # 兼容多种前端字段命名，核心更新系统提示词文本
        incoming_text = data.get('system_prompt')
        if incoming_text is None:
            incoming_text = data.get('content')
        if incoming_text is None:
            incoming_text = data.get('text')

        if incoming_text is not None:
            incoming_text = str(incoming_text).strip()
            if not incoming_text:
                return error_response('提示词内容不能为空', 400)
            prompt.system_prompt = incoming_text

        if 'name' in data:
            name = (data.get('name') or '').strip()
            if not name:
                return error_response('name 不能为空', 400)
            prompt.name = name
        if 'role_description' in data:
            prompt.role_description = data.get('role_description')
        if 'greeting_message' in data:
            prompt.greeting_message = data.get('greeting_message')
        if 'questioning_style' in data:
            prompt.questioning_style = data.get('questioning_style')
        if 'temperature' in data:
            prompt.temperature = data.get('temperature')
        if 'max_tokens' in data:
            prompt.max_tokens = data.get('max_tokens')
        if 'is_active' in data:
            if not isinstance(data.get('is_active'), bool):
                return error_response('is_active 必须是布尔值', 400)
            prompt.is_active = data.get('is_active')
        if 'job_id' in data:
            prompt.job_id = data.get('job_id')

        db.session.commit()
        return success_response(_serialize_prompt(prompt), '提示词更新成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@admin_required
def delete_prompt(prompt_id):
    try:
        prompt = AiPrompt.query.get(prompt_id)
        if not prompt:
            return error_response('Prompt 不存在', 404)

        db.session.delete(prompt)
        db.session.commit()
        return success_response({'deleted_id': prompt_id}, '提示词删除成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/interviews', methods=['GET'])
@admin_required
def list_interviews():
    try:
        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)

        if page < 1:
            return error_response('page 必须大于等于 1', 400)
        if size < 1:
            return error_response('size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        base_query = (
            db.session.query(Interview, User, Job)
            .join(User, User.id == Interview.user_id)
            .join(Job, Job.id == Interview.job_id)
        )

        total = base_query.count()
        rows = (
            base_query
            .order_by(Interview.start_time.desc().nullslast(), Interview.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        data = []
        for interview, user, job in rows:
            data.append(
                {
                    'interview_id': interview.id,
                    'user_id': user.id,
                    'username': user.username,
                    'real_name': user.real_name,
                    'job_id': job.id,
                    'job_name': job.name,
                    'status': interview.status,
                    'total_score': interview.total_score,
                    'question_count': interview.question_count,
                    'used_time': interview.used_time,
                    'start_time': interview.start_time.isoformat() if interview.start_time else None,
                    'end_time': interview.end_time.isoformat() if interview.end_time else None
                }
            )

        return success_response(
            {'list': data, 'page': page, 'size': size, 'total': total},
            '获取面试记录列表成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/users/<int:user_id>/performance', methods=['GET'])
@admin_required
def get_user_performance(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)

        rows = (
            db.session.query(Interview, Job)
            .outerjoin(Job, Job.id == Interview.job_id)
            .filter(Interview.user_id == user_id)
            .order_by(Interview.start_time.desc().nullslast(), Interview.id.desc())
            .all()
        )

        interview_list = [
            {
                'interview_id': interview.id,
                'job_id': interview.job_id,
                'job_name': job.name if job else None,
                'status': interview.status,
                'score': interview.total_score,
                'start_time': interview.start_time.isoformat() if interview.start_time else None,
                'end_time': interview.end_time.isoformat() if interview.end_time else None,
                'question_count': interview.question_count,
                'used_time': interview.used_time
            }
            for interview, job in rows
        ]

        growth_curve = LearningService.get_growth_curve(user_id)

        ability_rows = (
            db.session.query(Dimension.name, func.avg(InterviewScore.score).label('avg_score'))
            .join(InterviewScore, InterviewScore.dimension_id == Dimension.id)
            .join(Interview, InterviewScore.interview_id == Interview.id)
            .filter(Interview.user_id == user_id, Interview.status == 'completed')
            .group_by(Dimension.name)
            .all()
        )

        abilities = {}
        name_map = {
            '专业知识': 'knowledge',
            '逻辑思维': 'logic',
            '表达能力': 'expression',
            '问题解决': 'problemSolving',
            '代码能力': 'coding',
            '学习能力': 'learning'
        }
        for name, avg_score in ability_rows:
            key = name_map.get(name, name)
            abilities[key] = int(round(avg_score or 0))

        # 保证全部 6 个维度存在
        default_abilities = {
            'knowledge': 0,
            'logic': 0,
            'expression': 0,
            'problemSolving': 0,
            'coding': 0,
            'learning': 0
        }
        abilities = {**default_abilities, **abilities}

        learning_completed = UserLearning.query.filter_by(user_id=user_id, status='completed').count()
        learning_active = UserLearning.query.filter_by(user_id=user_id, status='in_progress').count()

        return success_response(
            {
                'interviews': interview_list,
                'growth_curve': growth_curve,
                'abilities': abilities,
                'learning': {
                    'completed': learning_completed,
                    'in_progress': learning_active
                }
            },
            '获取用户绩效数据成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/interviews/<int:interview_id>/details', methods=['GET'])
@admin_required
def get_interview_details(interview_id):
    try:
        row = (
            db.session.query(Interview, User, Job)
            .join(User, User.id == Interview.user_id)
            .join(Job, Job.id == Interview.job_id)
            .filter(Interview.id == interview_id)
            .first()
        )
        if not row:
            return error_response('面试记录不存在', 404)

        interview, user, job = row

        chats = (
            InterviewChat.query
            .filter(InterviewChat.interview_id == interview_id)
            .order_by(InterviewChat.timestamp.asc(), InterviewChat.id.asc())
            .all()
        )
        chat_history = [
            {
                'id': chat.id,
                'role': chat.role,
                'content': chat.content,
                'timestamp': chat.timestamp.isoformat() if chat.timestamp else None,
                'duration': chat.duration,
                'question_id': chat.question_id
            }
            for chat in chats
        ]

        score_rows = (
            db.session.query(InterviewScore, Dimension)
            .join(Dimension, Dimension.id == InterviewScore.dimension_id)
            .filter(InterviewScore.interview_id == interview_id)
            .all()
        )
        dimension_scores = [
            {
                'dimension_id': dim.id,
                'dimension_name': dim.name,
                'score': score.score,
                'comment': score.comment
            }
            for score, dim in score_rows
        ]

        report = {
            'total_score': interview.total_score,
            'highlights': interview.evaluation_highlights,
            'improvements': interview.evaluation_improvements,
            'suggestions': interview.evaluation_suggestions,
            'dimension_scores': dimension_scores
        }

        return success_response(
            {
                'interview': {
                    'interview_id': interview.id,
                    'status': interview.status,
                    'user_id': user.id,
                    'username': user.username,
                    'real_name': user.real_name,
                    'job_id': job.id,
                    'job_name': job.name,
                    'question_count': interview.question_count,
                    'used_time': interview.used_time,
                    'start_time': interview.start_time.isoformat() if interview.start_time else None,
                    'end_time': interview.end_time.isoformat() if interview.end_time else None
                },
                'chat_history': chat_history,
                'report': report
            },
            '获取面试详情成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)
