from flask import Blueprint, jsonify, request, current_app
from datetime import date, datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher
import hashlib
import os
import uuid

from sqlalchemy import func, or_
import yaml

from app.services.auth_service import AuthService
from app.services.learning_service import LearningService
from app.services.user_service import UserService
from werkzeug.utils import secure_filename
from app.api.v1.auth_utils import admin_required
from app.extensions import db
from app.models.user import User
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension, InterviewProfile
from app.models.job import Job
from app.models.question import Question
# from app.models.knowledge import KnowledgeItem
from app.models.learning import KnowledgeTag, Resource, UserLearning, UserKnowledgeMastery
from app.models.example import Example
from app.models.prompt import AiPrompt
from app.models.learning import Resource, UserLearning, KnowledgeTag
from app.models.resume import Resume


admin_bp = Blueprint('admin', __name__)

_JOB_MAPPING_CACHE = None
_KNOWLEDGE_POINT_CATALOG_CACHE = None

# 适配 Question 新增字段 source, status 及多对多关联 knowledge_tags
def _serialize_question(question):
    # question.knowledge_points 可能不存在（数据库使用 question.knowledge_tags 关联）
    knowledge_points = None
    if hasattr(question, 'knowledge_points'):
        knowledge_points = question.knowledge_points
    else:
        knowledge_points = [tag.name for tag in getattr(question, 'knowledge_tags', [])]

    job_id = None
    if hasattr(question, 'job_id'):
        job_id = question.job_id
    elif hasattr(question, 'jobs'):
        first_job = question.jobs.first() if hasattr(question.jobs, 'first') else None
        job_id = first_job.id if first_job else None

    return {
        'id': question.id,
        'job_id': job_id,
        'content': question.content,
        'type': question.type,
        'difficulty': question.difficulty,
        'keywords': question.keywords,
        'reference_answer': question.reference_answer,
        'follow_up_templates': question.follow_up_templates,
        'required_skills_meta': question.required_skills_meta,
        'source': getattr(question, 'source', None),
        'status': getattr(question, 'status', 'draft'),
        'knowledge_points': knowledge_points
    }


def _serialize_knowledge(tag):
    return {
        'id': tag.id,
        'name': tag.name,
        'category': tag.category,
        'complexity': tag.complexity,
        'estimated_hours': tag.estimated_hours
    }

# 序列化 Example 优秀回答范例
def _serialize_example(example):
    return {
        'id': example.id,
        'job_id': example.job_id,
        'question': example.question,
        'framework': example.framework,
        'answer': example.answer
    }


def _serialize_resource(resource):
    knowledge_tag_names = [tag.name for tag in getattr(resource, 'knowledge_tags', [])]
    return {
        'id': resource.id,
        'title': resource.title,
        'type': resource.type,
        'url': resource.url,
        'content': resource.content,
        'source': resource.source,
        'difficulty': resource.difficulty,
        'tag_id': getattr(resource, 'tag_id', None),
        'tags': knowledge_tag_names,
        'knowledge_tags': knowledge_tag_names
    }


def _serialize_interview_profile(profile):
    return {
        'id': profile.id,
        'job_id': profile.job_id,
        'job_name': profile.job.name if profile.job else None,
        'round': profile.round,
        'technique_percentage': profile.technique_percentage,
        'scenario_percentage': profile.scenario_percentage,
        'project_deep_dive_percentage': profile.project_deep_dive_percentage,
        'behavioral_percentage': profile.behavioral_percentage,
        'difficulty_low_percentage': profile.difficulty_low_percentage,
        'difficulty_medium_percentage': profile.difficulty_medium_percentage,
        'difficulty_high_percentage': profile.difficulty_high_percentage,
        'is_dynamic_adjust': profile.is_dynamic_adjust,
        'interviewer_style': profile.interviewer_style,
        'custom_personality_json': profile.custom_personality_json,
        'voice_id': profile.voice_id,
        'speech_speed': profile.speech_speed,
        'tone_descriptor': profile.tone_descriptor,
        'enabled_dimensions': profile.enabled_dimensions,
        'difficulty_level': profile.difficulty_level,
        'target_source': profile.target_source or '通用',
        'created_at': profile.created_at.isoformat() if profile.created_at else None,
        'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _parse_json_field(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        import json
        return json.loads(value)
    except Exception:
        return None


def _get_profile_payload(data):
    return {
        'job_id': data.get('job_id'),
        'round': data.get('round'),
        'technique_percentage': data.get('technique_percentage'),
        'scenario_percentage': data.get('scenario_percentage'),
        'project_deep_dive_percentage': data.get('project_deep_dive_percentage'),
        'behavioral_percentage': data.get('behavioral_percentage'),
        'difficulty_low_percentage': data.get('difficulty_low_percentage'),
        'difficulty_medium_percentage': data.get('difficulty_medium_percentage'),
        'difficulty_high_percentage': data.get('difficulty_high_percentage'),
        'is_dynamic_adjust': data.get('is_dynamic_adjust', True),
        'interviewer_style': data.get('interviewer_style'),
        'custom_personality_json': _parse_json_field(data.get('custom_personality_json')),
        'voice_id': data.get('voice_id'),
        'speech_speed': data.get('speech_speed'),
        'tone_descriptor': data.get('tone_descriptor'),
        'enabled_dimensions': data.get('enabled_dimensions'),
        'difficulty_level': data.get('difficulty_level'),
        'target_source': data.get('target_source', '通用'),
    }


def _get_default_text_embedding(text):
    normalized = (text or '').strip()
    if not normalized:
        normalized = 'knowledge_tag'

    try:
        from app.services.interview_service import InterviewService
        return InterviewService.get_embedding(normalized)
    except Exception:
        digest = hashlib.sha256(normalized.encode('utf-8')).digest()
        return [(digest[i % len(digest)] / 255.0) for i in range(512)]


def _load_knowledge_point_catalog():
    global _KNOWLEDGE_POINT_CATALOG_CACHE
    if _KNOWLEDGE_POINT_CATALOG_CACHE is not None:
        return _KNOWLEDGE_POINT_CATALOG_CACHE

    backend_root = Path(__file__).resolve().parents[3]
    knowledge_dir = backend_root / 'FuChuangTiKu' / 'data' / 'knowledge_points'
    catalog = {}

    if knowledge_dir.exists():
        for yaml_path in sorted(knowledge_dir.glob('*.yaml')):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as fp:
                    payload = yaml.safe_load(fp) or {}
            except Exception:
                continue

            for module in payload.get('modules', []) or []:
                category = (module.get('name') or '').strip()
                for point in module.get('points', []) or []:
                    if isinstance(point, str):
                        point_name = point.strip()
                        complexity = 'Medium'
                        estimated_hours = 1
                    else:
                        point_name = (point.get('point') or '').strip()
                        complexity = point.get('complexity', 'Medium')
                        estimated_hours = point.get('estimated_hours', 1)

                    if not point_name:
                        continue

                    catalog[point_name.lower()] = {
                        'name': point_name,
                        'category': category or None,
                        'complexity': complexity or 'Medium',
                        'estimated_hours': int(estimated_hours or 1)
                    }

    _KNOWLEDGE_POINT_CATALOG_CACHE = catalog
    return _KNOWLEDGE_POINT_CATALOG_CACHE


def _find_best_existing_parent(name):
    target = (name or '').strip()
    if not target:
        return None

    root_tags = KnowledgeTag.query.filter(
        KnowledgeTag.category.isnot(None),
        KnowledgeTag.category != ''
    ).all()
    if not root_tags:
        return None

    target_lower = target.lower()
    best_tag = None
    best_score = 0.0

    for tag in root_tags:
        candidate = (tag.name or '').strip()
        if not candidate:
            continue
        candidate_lower = candidate.lower()
        score = SequenceMatcher(None, target_lower, candidate_lower).ratio()
        if target_lower in candidate_lower or candidate_lower in target_lower:
            score += 0.2
        if score > best_score:
            best_score = score
            best_tag = tag

    return best_tag


def _apply_knowledge_tag_defaults(tag, raw_name=None):
    name = (raw_name or tag.name or '').strip()
    if not name:
        return tag

    catalog = _load_knowledge_point_catalog()
    catalog_item = catalog.get(name.lower())

    if catalog_item:
        tag.category = tag.category or catalog_item.get('category')
        tag.complexity = tag.complexity or catalog_item.get('complexity') or 'Medium'
        tag.estimated_hours = tag.estimated_hours or catalog_item.get('estimated_hours') or 1
        if tag.embedding is None:
            tag.embedding = _get_default_text_embedding(f"模块: {tag.category or ''} 知识点: {name}")
        return tag

    parent = _find_best_existing_parent(name)
    if parent:
        if not tag.parent_id:
            tag.parent_id = parent.id
        if not tag.category:
            tag.category = parent.category or parent.name
        if not tag.complexity:
            tag.complexity = parent.complexity or 'Medium'
        if not tag.estimated_hours:
            base_hours = parent.estimated_hours or 1
            tag.estimated_hours = max(1, int(round(float(base_hours) * 0.5)))
        if tag.embedding is None:
            tag.embedding = _get_default_text_embedding(f"{name} {tag.category or ''} {parent.name or ''}")
        return tag

    if not tag.category:
        tag.category = '未分类'
    if not tag.complexity:
        tag.complexity = 'Medium'
    if not tag.estimated_hours:
        tag.estimated_hours = 1
    if tag.embedding is None:
        tag.embedding = _get_default_text_embedding(f"{name} {tag.category}")
    return tag


def _resolve_knowledge_tags(tags):
    if tags is None:
        return None
    if not isinstance(tags, list):
        raise ValueError('knowledge_tags 必须是数组或 null')

    normalized = []
    for t in tags:
        if t is None:
            continue
        if isinstance(t, int):
            kt = KnowledgeTag.query.get(t)
            if kt:
                normalized.append(kt)
            continue

        name = str(t).strip()
        if len(name) > 100:
            name = name[:97] + "..."
            
        if not name:
            continue

        kt = KnowledgeTag.query.filter(func.lower(KnowledgeTag.name) == name.lower()).first()
        if not kt:
            kt = KnowledgeTag(name=name)
            _apply_knowledge_tag_defaults(kt, name)
            db.session.add(kt)
            db.session.flush()
        else:
            updated = False
            before = (kt.category, kt.complexity, kt.estimated_hours, kt.embedding is not None, kt.parent_id)
            _apply_knowledge_tag_defaults(kt, name)
            after = (kt.category, kt.complexity, kt.estimated_hours, kt.embedding is not None, kt.parent_id)
            updated = before != after
            if updated:
                db.session.flush()

        normalized.append(kt)

    return normalized


def _resolve_entity():
    entity = (request.args.get('entity') or '').strip().lower()
    if not entity:
        body = request.get_json(silent=True) or {}
        entity = str(body.get('entity', 'question')).strip().lower()

    # 加入合法实体白名单检验
    allowed_entities = {'question', 'resource', 'tag', 'example'}

    # 如果传了不支持的 entity，直接降级兜底为默认的 'question'
    # （或者你也可以选择在这里直接 raise ValueError 让前端报错）
    if entity not in allowed_entities:
        return 'question'

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
        'max_tokens': getattr(prompt, 'max_tokens', 500),
        'is_active': prompt.is_active,
        'created_at': getattr(prompt, 'created_at', None).isoformat() if getattr(prompt, 'created_at', None) else None
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

        try:
            today_new_jobs = (
                db.session.query(func.count(Job.id))
                .filter(func.date(Job.created_at) == date.today())
                .scalar() or 0
            )
        except Exception:
            today_new_jobs = 0

        try:
            today_new_questions = (
                db.session.query(func.count(Question.id))
                .filter(func.date(Question.created_at) == date.today())
                .scalar() or 0
            )
        except Exception:
            today_new_questions = 0
        total_published_questions = (
            db.session.query(func.count(Question.id)).filter(Question.status == 'published').scalar() or 0
        )
        total_resources = db.session.query(func.count(Resource.id)).scalar() or 0

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
                'today_new_jobs': int(today_new_jobs),
                'total_questions': int(total_questions),
                'today_new_questions': int(today_new_questions),
                'total_published_questions': int(total_published_questions),
                'total_resources': int(total_resources),
                'top_jobs': top_jobs,
                'top_users': user_rankings,
                'recent_events': recent_events,
                'usage_trend': usage_trend
            },
            '获取管理大盘数据成功'
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    try:
        data = request.get_json(silent=True) or {}
        result = UserService.create_user(data)
        return success_response(result, '创建用户成功')
    except ValueError as exc:
        return error_response(str(exc), 400)
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
            .order_by(User.id.asc())
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


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    try:
        data = request.get_json(silent=True) or {}
        result = UserService.update_profile(user_id, data)
        return success_response(result, '更新用户信息成功')
    except ValueError as exc:
        return error_response(str(exc), 400)
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
        query = Job.query
        keyword = request.args.get('q', '').strip()
        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Job.name.ilike(like_pattern),
                    Job.description.ilike(like_pattern)
                )
            )

        jobs = query.order_by(Job.id.asc()).all()
        return success_response({'list': [job.to_dict() for job in jobs], 'total': query.count()}, '获取岗位列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/jobs/icon-upload', methods=['POST'])
@admin_required
def upload_job_icon():
    try:
        icon_file = request.files.get('file') or request.files.get('icon')
        if not icon_file:
            return error_response('请上传图标文件', 400)

        filename = secure_filename(icon_file.filename or '')
        if not filename or '.' not in filename:
            return error_response('文件名无效', 400)

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            return error_response('仅支持 png/jpg/jpeg/gif/webp 格式', 400)

        upload_root = current_app.config.get('UPLOAD_ROOT') or os.path.join(current_app.root_path, 'uploads')
        icon_dir = os.path.join(upload_root, 'job_icons')
        os.makedirs(icon_dir, exist_ok=True)

        saved_name = f"job_icon_{uuid.uuid4().hex}.{ext}"
        saved_path = os.path.join(icon_dir, saved_name)
        icon_file.save(saved_path)

        icon_url = f"/uploads/job_icons/{saved_name}"
        return success_response({'icon_url': icon_url}, '图标上传成功')
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

        if 'knowledge_tags' in data:
            raw_tags = data.get('knowledge_tags')
            if raw_tags is not None and not isinstance(raw_tags, list):
                return error_response('knowledge_tags 必须是数组或 null', 400)
            try:
                # _resolve_knowledge_tags returns a list of tag objects or None
                resolved_tags = _resolve_knowledge_tags(raw_tags)
                # Assign the list to the dynamic relationship. SQLAlchemy handles the append.
                job.knowledge_tags = resolved_tags or []
            except ValueError as exc:
                db.session.rollback()
                return error_response(str(exc), 400)

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
        if 'knowledge_tags' in data:
            raw_tags = data.get('knowledge_tags')
            if raw_tags is not None and not isinstance(raw_tags, list):
                return error_response('knowledge_tags 必须是数组或 null', 400)
            try:
                # _resolve_knowledge_tags returns a list of tag objects or None
                resolved_tags = _resolve_knowledge_tags(raw_tags)
                # For updates, this replaces the entire collection.
                job.knowledge_tags = resolved_tags or []
            except ValueError as exc:
                db.session.rollback()
                return error_response(str(exc), 400)

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

        # 方案一：如果岗位下还有题目，禁止删除
        if job.questions.count() > 0:
            return error_response(f'无法删除，请先处理该岗位下的 {job.questions.count()} 道关联题目', 400)

        # 方案二：级联清空关联关系（更常用）
        # 在删除岗位前，清空其与所有 Question 的关联
        job.questions = []
        
        # 清空其与所有 KnowledgeTag 的关联
        job.knowledge_tags = []

        # 删除与该岗位关联的所有 AiPrompt
        AiPrompt.query.filter_by(job_id=job.id).delete()

        db.session.delete(job)
        db.session.commit()

        return success_response(None, '岗位删除成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


def _get_entity_model_and_serializer(entity):
    if entity == 'resource':
        return Resource, _serialize_resource
    if entity == 'question':
        return Question, _serialize_question
    return None, None


def _infer_job_domain_from_path(path):
    path = (path or '').lower()
    for key in ['backend', 'frontend', 'cv', 'network', 'qa']:
        if key in path:
            return key
    return None


def _import_questions_from_yaml(data, file_path=None, status='draft'):
    imported = 0
    skipped = 0
    for item in (data.get('items') or []):
        content = (item.get('question') or item.get('content') or '').strip()
        if not content:
            skipped += 1
            continue

        question_type = (item.get('type') or 'technical').strip()
        question = Question(
            content=content,
            type=question_type,
            difficulty=item.get('difficulty'),
            source=item.get('source') or data.get('source') or None,
            status=status,
            keywords=item.get('tags') or item.get('keywords') or None,
            reference_answer=item.get('key_points') or item.get('reference_answer') or None,
            follow_up_templates=item.get('follow_up_templates') or item.get('follow_up_templates') or None,
            required_skills_meta=item.get('required_skills_meta') or None
        )
        if question.embedding is None:
            question.embedding = _get_default_text_embedding(question.content)

        if item.get('tags'):
            try:
                question.knowledge_tags = _resolve_knowledge_tags(item.get('tags')) or []
            except ValueError:
                question.knowledge_tags = []

        domain = _infer_job_domain_from_path(file_path)
        if domain:
            job = _get_or_create_job_by_domain(domain)
            if job:
                question.jobs = [job]

        db.session.add(question)
        imported += 1

    return imported, skipped


def _import_resources_from_yaml(data, file_path=None):
    imported = 0
    skipped = 0

    modules = data.get('modules') or []
    for module in modules:
        points = module.get('points') or []
        for point in points:
            point_name = (point.get('point') or '').strip()
            raw_tags = point.get('tags') or []
            tags = raw_tags if isinstance(raw_tags, list) else [str(raw_tags).strip()] if raw_tags else []
            point_resources = point.get('resources') or []
            for item in point_resources:
                title = (item.get('name') or item.get('title') or '').strip()
                if not title:
                    skipped += 1
                    continue
                resource = Resource(
                    title=title,
                    type=item.get('type') or 'article',
                    url=item.get('url'),
                    content=item.get('description') or item.get('content') or None,
                    source=item.get('source') or None,
                    difficulty=item.get('complexity') or item.get('difficulty') or None
                )
                if resource.embedding is None:
                    resource.embedding = _get_default_text_embedding(resource.title or resource.content)

                knowledge_tag_values = []
                if point_name:
                    knowledge_tag_values.append(point_name)
                knowledge_tag_values.extend(tags)
                if knowledge_tag_values:
                    try:
                        resolved = _resolve_knowledge_tags(knowledge_tag_values)
                        resource.knowledge_tags = resolved or []
                        resource.tag_id = resolved[0].id if resolved else None
                    except ValueError:
                        resource.knowledge_tags = []
                        resource.tag_id = None

                db.session.add(resource)
                imported += 1

    return imported, skipped


def _resolve_import_source(entity, file_obj=None):
    backend_root = Path(__file__).resolve().parents[3]
    if file_obj is not None:
        try:
            return yaml.safe_load(file_obj), None
        except Exception:
            return None, '上传的 YAML 文件格式不正确'

    if entity == 'question':
        index_path = backend_root / 'FuChuangTiKu' / 'index.yaml'
        if not index_path.exists():
            return None, '未找到 FuChuangTiKu/index.yaml'
        try:
            index_data = yaml.safe_load(index_path)
        except Exception:
            return None, '无法解析 index.yaml'

        datasets = index_data.get('datasets') or []
        combined = []
        for item in datasets:
            path = item.get('path')
            if not path:
                continue
            yaml_path = backend_root / 'FuChuangTiKu' / path
            if not yaml_path.exists():
                continue
            try:
                file_data = yaml.safe_load(open(yaml_path, 'r', encoding='utf-8'))
            except Exception:
                continue
            combined.append((file_data, str(yaml_path)))
        return combined, None

    if entity == 'resource':
        resource_dir = backend_root / 'resourcesKu'
        if not resource_dir.exists():
            return None, '未找到 resourcesKu 目录'
        files = []
        for yaml_path in sorted(resource_dir.glob('*.yaml')):
            try:
                file_data = yaml.safe_load(open(yaml_path, 'r', encoding='utf-8'))
            except Exception:
                continue
            files.append((file_data, str(yaml_path)))
        return files, None

    return None, '不支持的实体类型'


@admin_bp.route('/questions', methods=['GET'])
@admin_required
def list_entities():
    try:
        entity = _resolve_entity()
        model, serializer = _get_entity_model_and_serializer(entity)
        if model is None:
            return error_response('Unsupported entity', 400)

        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)
        keyword = (request.args.get('q', default='', type=str) or '').strip()
        filter_type = (request.args.get('type', default=None, type=str) or '').strip()
        filter_difficulty = (request.args.get('difficulty', default=None, type=str) or '').strip()
        filter_status = (request.args.get('status', default=None, type=str) or '').strip().lower()

        if page < 1:
            return error_response('page 必须大于等于 1', 400)
        if size < 1:
            return error_response('size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        query = model.query
        if entity == 'question':
            job_id = request.args.get('job_id', default=None, type=int)
            if job_id:
                query = query.filter(Question.jobs.any(Job.id == job_id))
            if filter_status:
                query = query.filter(Question.status == filter_status)

        if filter_type:
            query = query.filter(model.type == filter_type)
        if filter_difficulty:
            query = query.filter(model.difficulty == filter_difficulty)
        if keyword:
            pattern = f'%{keyword}%'
            if entity == 'question':
                query = query.filter(
                    or_(
                        Question.content.ilike(pattern),
                        Question.source.ilike(pattern),
                        func.cast(Question.keywords, JSONB).cast(db.Text).ilike(pattern),
                        func.cast(Question.reference_answer, JSONB).cast(db.Text).ilike(pattern)
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Resource.title.ilike(pattern),
                        Resource.content.ilike(pattern),
                        Resource.source.ilike(pattern),
                        Resource.url.ilike(pattern)
                    )
                )

        total = query.count()
        items = (
            query.order_by(model.id.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return success_response({'list': [serializer(item) for item in items], 'page': page, 'size': size, 'total': total}, '获取列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/questions', methods=['POST'])
@admin_required
def create_entity():
    try:
        entity = _resolve_entity()
        data = request.get_json(silent=True) or {}
        if entity == 'question':
            job_id = data.get('job_id')
            if not job_id:
                return error_response('请选择关联岗位', 400)
            job = Job.query.get(job_id)
            if not job:
                return error_response('岗位不存在', 404)

            content = (data.get('content') or '').strip()
            if not content:
                return error_response('题目内容不能为空', 400)

            question = Question(
                content=content,
                type=(data.get('type') or 'technical').strip(),
                difficulty=data.get('difficulty'),
                source=data.get('source'),
                status=data.get('status') or 'draft',
                keywords=data.get('keywords') if isinstance(data.get('keywords'), list) else data.get('keywords'),
                reference_answer=data.get('reference_answer'),
                follow_up_templates=data.get('follow_up_templates'),
                required_skills_meta=_parse_json_field(data.get('required_skills_meta')) if data.get('required_skills_meta') else None
            )
            if question.embedding is None:
                question.embedding = _get_default_text_embedding(question.content)

            if 'knowledge_points' in data:
                try:
                    question.knowledge_tags = _resolve_knowledge_tags(data.get('knowledge_points')) or []
                except ValueError as exc:
                    return error_response(str(exc), 400)

            question.jobs = [job]
            db.session.add(question)
            db.session.commit()
            return success_response(_serialize_question(question), '题目创建成功')

        if entity == 'resource':
            title = (data.get('title') or '').strip()
            if not title:
                return error_response('资源标题不能为空', 400)
            resource = Resource(
                title=title,
                type=(data.get('type') or 'article').strip(),
                url=data.get('url'),
                content=data.get('content'),
                source=data.get('source'),
                difficulty=data.get('difficulty')
            )
            if resource.embedding is None:
                resource.embedding = _get_default_text_embedding(resource.title or resource.content)

            raw_tags = data.get('knowledge_tags') if data.get('knowledge_tags') is not None else data.get('tags')
            if raw_tags is not None:
                try:
                    resolved = _resolve_knowledge_tags(raw_tags)
                    resource.knowledge_tags = resolved or []
                    resource.tag_id = resolved[0].id if resolved else None
                except ValueError as exc:
                    return error_response(str(exc), 400)

            db.session.add(resource)
            db.session.commit()
            return success_response(_serialize_resource(resource), '资源创建成功')

        return error_response('不支持的实体类型', 400)
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/<int:item_id>', methods=['PUT'])
@admin_required
def update_entity(item_id):
    try:
        entity = _resolve_entity()
        data = request.get_json(silent=True) or {}
        model, serializer = _get_entity_model_and_serializer(entity)
        if model is None:
            return error_response('Unsupported entity', 400)

        item = model.query.get(item_id)
        if not item:
            return error_response('记录不存在', 404)

        if entity == 'question':
            if 'job_id' in data:
                job_id = data.get('job_id')
                if job_id is None:
                    item.jobs = []
                else:
                    job = Job.query.get(job_id)
                    if not job:
                        return error_response('岗位不存在', 404)
                    item.jobs = [job]
            if 'content' in data:
                if not (data.get('content') or '').strip():
                    return error_response('题目内容不能为空', 400)
                item.content = data.get('content')
            if 'type' in data:
                item.type = data.get('type')
            if 'difficulty' in data:
                item.difficulty = data.get('difficulty')
            if 'source' in data:
                item.source = data.get('source')
            if 'status' in data:
                item.status = data.get('status')
            if 'keywords' in data:
                item.keywords = data.get('keywords') if isinstance(data.get('keywords'), list) else data.get('keywords')
            if 'reference_answer' in data:
                item.reference_answer = data.get('reference_answer')
            if 'follow_up_templates' in data:
                item.follow_up_templates = data.get('follow_up_templates')
            if 'required_skills_meta' in data:
                item.required_skills_meta = _parse_json_field(data.get('required_skills_meta')) if data.get('required_skills_meta') else None
            if 'knowledge_points' in data:
                try:
                    item.knowledge_tags = _resolve_knowledge_tags(data.get('knowledge_points')) or []
                except ValueError as exc:
                    return error_response(str(exc), 400)
            if item.embedding is None:
                item.embedding = _get_default_text_embedding(item.content)

        elif entity == 'resource':
            if 'title' in data:
                if not (data.get('title') or '').strip():
                    return error_response('资源标题不能为空', 400)
                item.title = data.get('title')
            if 'type' in data:
                item.type = data.get('type')
            if 'url' in data:
                item.url = data.get('url')
            if 'content' in data:
                if not (data.get('content') or '').strip():
                    return error_response('内容简介不能为空', 400)
                item.content = data.get('content')
            if 'source' in data:
                item.source = data.get('source')
            if 'difficulty' in data:
                item.difficulty = data.get('difficulty')
            if 'knowledge_tags' in data or 'tags' in data:
                raw_tags = data.get('knowledge_tags') if data.get('knowledge_tags') is not None else data.get('tags')
                try:
                    resolved = _resolve_knowledge_tags(raw_tags)
                    item.knowledge_tags = resolved or []
                    item.tag_id = resolved[0].id if resolved else None
                except ValueError as exc:
                    return error_response(str(exc), 400)
            if item.embedding is None:
                item.embedding = _get_default_text_embedding(item.title or item.content)

        db.session.commit()
        return success_response(serializer(item), '更新成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_entity(item_id):
    try:
        entity = _resolve_entity()
        model, _ = _get_entity_model_and_serializer(entity)
        if model is None:
            return error_response('Unsupported entity', 400)

        item = model.query.get(item_id)
        if not item:
            return error_response('记录不存在', 404)

        db.session.delete(item)
        db.session.commit()

        return success_response({'deleted_id': item_id}, '删除成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/bulk-update-status', methods=['POST'])
@admin_required
def bulk_update_question_status():
    try:
        data = request.get_json(silent=True) or {}
        ids = data.get('ids')
        status = data.get('status')
        if not isinstance(ids, list) or not ids:
            return error_response('ids 必须是非空数组', 400)
        if status not in ['draft', 'published']:
            return error_response('status 必须是 draft 或 published', 400)

        updated = Question.query.filter(Question.id.in_(ids)).update({'status': status}, synchronize_session=False)
        db.session.commit()
        return success_response({'updated': int(updated)}, '批量更新状态成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/questions/import', methods=['POST'])
@admin_required
def import_questions():
    try:
        status = (request.form.get('status') or request.json.get('status') if request.is_json else request.form.get('status')) or 'draft'
        entity = _resolve_entity()
        clear_existing = (request.form.get('clear_existing') or request.json.get('clear_existing') or '').lower() in ['true', '1', 'yes', 'on']
        file_obj = request.files.get('file')

        if clear_existing:
            if entity == 'question':
                db.session.query(Question).delete(synchronize_session=False)
            elif entity == 'resource':
                db.session.query(Resource).delete(synchronize_session=False)
            db.session.flush()

        import_items = []
        if file_obj is not None:
            result = yaml.safe_load(file_obj)
            if result is None:
                return error_response('上传的 YAML 文件为空或格式错误', 400)
            import_items = [(result, getattr(file_obj, 'filename', None))]
        else:
            imported_list, err = _resolve_import_source(entity)
            if err:
                return error_response(err, 400)
            import_items = imported_list

        total_imported = 0
        total_skipped = 0
        files_report = []
        for data_item, source_path in import_items:
            if entity == 'question':
                imported, skipped = _import_questions_from_yaml(data_item, source_path, status=status)
            else:
                imported, skipped = _import_resources_from_yaml(data_item, source_path)
            total_imported += imported
            total_skipped += skipped
            files_report.append({'type': entity, 'job_name': source_path or 'uploaded', 'count': imported})

        db.session.commit()
        return success_response({'imported_total': total_imported, 'skipped': total_skipped, 'files': files_report}, '导入完成')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/interview-profiles', methods=['GET'])
@admin_required
def list_interview_profiles():
    try:
        page = request.args.get('page', default=1, type=int)
        size = request.args.get('size', default=10, type=int)
        if page < 1:
            return error_response('page 必须大于等于 1', 400)
        if size < 1:
            return error_response('size 必须大于等于 1', 400)
        if size > 100:
            size = 100

        query = InterviewProfile.query
        job_id = request.args.get('job_id', type=int)
        round_value = request.args.get('round', type=int)
        if job_id:
            query = query.filter(InterviewProfile.job_id == job_id)
        if round_value:
            query = query.filter(InterviewProfile.round == round_value)
        total = query.count()
        items = (
            query.order_by(InterviewProfile.id.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return success_response({'list': [_serialize_interview_profile(item) for item in items], 'page': page, 'size': size, 'total': total}, '获取面试预设列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/interview-profiles/<int:profile_id>', methods=['GET'])
@admin_required
def get_interview_profile(profile_id):
    try:
        profile = InterviewProfile.query.get(profile_id)
        if not profile:
            return error_response('面试预设不存在', 404)
        return success_response(_serialize_interview_profile(profile), '获取面试预设详情成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/interview-profiles', methods=['POST'])
@admin_required
def create_interview_profile():
    try:
        data = request.get_json(silent=True) or {}
        payload = _get_profile_payload(data)
        if not payload.get('job_id'):
            return error_response('job_id 不能为空', 400)
        profile = InterviewProfile(**payload)
        db.session.add(profile)
        db.session.commit()
        return success_response(_serialize_interview_profile(profile), '创建面试预设成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/interview-profiles/<int:profile_id>', methods=['PUT'])
@admin_required
def update_interview_profile(profile_id):
    try:
        profile = InterviewProfile.query.get(profile_id)
        if not profile:
            return error_response('面试预设不存在', 404)

        data = request.get_json(silent=True) or {}
        payload = _get_profile_payload(data)
        for key, value in payload.items():
            setattr(profile, key, value)
        db.session.commit()
        return success_response(_serialize_interview_profile(profile), '更新面试预设成功')
    except Exception as exc:
        db.session.rollback()
        return error_response(str(exc), 500)


@admin_bp.route('/interview-profiles/<int:profile_id>', methods=['DELETE'])
@admin_required
def delete_interview_profile(profile_id):
    try:
        profile = InterviewProfile.query.get(profile_id)
        if not profile:
            return error_response('面试预设不存在', 404)
        db.session.delete(profile)
        db.session.commit()
        return success_response({'deleted_id': profile_id}, '删除面试预设成功')
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
        if 'created_at' in data:
            # 前端不应更新 created_at，但如果传了则尝试解析并更新
            try:
                parsed_time = datetime.fromisoformat(data.get('created_at').rstrip('Z'))
                prompt.created_at = parsed_time
            except Exception:
                return error_response('created_at 格式无效，必须是 ISO 8601 字符串', 400)
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

        user_id = request.args.get('user_id', type=int)

        base_query = (
            db.session.query(Interview, User, Job)
            .join(User, User.id == Interview.user_id)
            .join(Job, Job.id == Interview.job_id)
        )

        if user_id is not None:
            base_query = base_query.filter(Interview.user_id == user_id)

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
        # 维度名与 UserService 统一（数据初始化中是技术正确性/逻辑严谨性等）
        name_map = {
            '技术正确性': 'knowledge',
            '逻辑严谨性': 'logic',
            '表达沟通': 'expression',
            '表达沟通力': 'expression',
            '岗位匹配度': 'problemSolving',
            '应变能力': 'coding',
            '学习能力': 'learning',
            # 兼容旧字段映射
            '专业知识': 'knowledge',
            '逻辑思维': 'logic',
            '问题解决': 'problemSolving',
            '代码能力': 'coding'
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

        # 学习能力以已计算维度平均值为准（兼容历史维度字段）
        core_scores = [abilities[k] for k in ['knowledge', 'logic', 'expression', 'problemSolving', 'coding'] if abilities.get(k, 0) > 0]
        if core_scores:
            abilities['learning'] = int(round(sum(core_scores) / len(core_scores)))

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


@admin_bp.route('/users/<int:user_id>/resumes', methods=['GET'])
@admin_required
def list_user_resumes(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)

        resumes = (
            Resume.query
            .filter_by(user_id=user_id)
            .order_by(Resume.is_main.desc(), Resume.created_at.asc())
            .all()
        )

        return success_response([
            r.to_dict(include_content=False) for r in resumes
        ], '获取用户简历列表成功')
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route('/users/<int:user_id>/resumes/<int:resume_id>', methods=['GET'])
@admin_required
def get_user_resume(user_id, resume_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)

        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not resume:
            return error_response('简历不存在', 404)

        return success_response(resume.to_dict(include_content=True), '获取简历详情成功')
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
                'dimension_description': dim.description,
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
