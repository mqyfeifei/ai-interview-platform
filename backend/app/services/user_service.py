import re
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import func
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.user import User
from app.models.interview import Interview
from app.models.job import Job


class UserService:
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

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
        if job.name in cls.FRONT_JOB_KEY_TO_NAME.values():
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

    @classmethod
    def _resolve_job_by_front_key(cls, job_key):
        if not job_key:
            return None
        if str(job_key).isdigit():
            return db.session.get(Job, int(job_key))

        expected_name = cls.FRONT_JOB_KEY_TO_NAME.get(job_key)
        if expected_name:
            exact = Job.query.filter_by(name=expected_name).first()
            if exact:
                return exact

        lowered = str(job_key).lower()
        if lowered == 'java-backend':
            return Job.query.filter(Job.name.like('%Java%')).first()
        if lowered == 'web-frontend':
            return Job.query.filter((Job.name.like('%前端%')) | (Job.name.like('%Web%'))).first()
        if lowered == 'python-algorithm':
            return Job.query.filter((Job.name.like('%Python%')) | (Job.name.like('%算法%'))).first()
        if lowered == 'fullstack':
            return Job.query.filter(Job.name.like('%全栈%')).first()
        if lowered == 'android':
            return Job.query.filter(Job.name.like('%Android%')).first()
        if lowered == 'devops':
            return Job.query.filter(Job.name.like('%DevOps%')).first()
        return None

    @classmethod
    def _collect_dashboard_stats(cls, user_id):
        total_interviews = Interview.query.filter_by(user_id=user_id).count()

        completed_base = Interview.query.filter(
            Interview.user_id == user_id,
            Interview.status == 'completed',
            Interview.total_score.isnot(None)
        )

        avg_score_value = completed_base.with_entities(func.avg(Interview.total_score)).scalar()
        avg_score = round(float(avg_score_value), 2) if avg_score_value is not None else 0

        completed_interviews = completed_base.order_by(Interview.end_time.desc().nullslast(), Interview.start_time.desc()).all()
        latest = completed_interviews[0] if completed_interviews else None
        previous = completed_interviews[1] if len(completed_interviews) > 1 else None

        last_job_name = ''
        if latest:
            latest_job = db.session.get(Job, latest.job_id)
            last_job_name = latest_job.name if latest_job else ''

        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        weekly_practice = Interview.query.filter(
            Interview.user_id == user_id,
            Interview.start_time >= week_start
        ).count()

        hot_job_rows = db.session.query(
            Interview.job_id,
            func.count(Interview.id).label('cnt')
        ).filter(
            Interview.user_id == user_id,
            Interview.job_id.isnot(None)
        ).group_by(Interview.job_id).order_by(func.count(Interview.id).desc()).limit(3).all()

        hot_jobs = []
        for row in hot_job_rows:
            job = db.session.get(Job, row.job_id)
            key = cls._job_to_front_key(job)
            if key:
                hot_jobs.append(key)

        return {
            "totalInterviews": total_interviews,
            "avgScore": avg_score,
            "lastInterviewScore": latest.total_score if latest else 0,
            "lastInterviewAt": (latest.end_time or latest.start_time).isoformat() if latest else None,
            "lastInterviewJob": last_job_name,
            "scoreImprovement": (latest.total_score - previous.total_score) if (latest and previous) else 0,
            "weeklyPractice": weekly_practice,
            "hotJobs": hot_jobs
        }

    @staticmethod
    def _is_phone(value):
        if not value:
            return False
        return bool(re.match(r"^1\d{10}$", value))

    @classmethod
    def serialize_user(cls, user):
        dashboard_stats = cls._collect_dashboard_stats(user.id)
        default_job_key = cls._job_to_front_key(user.default_job)
        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.real_name or user.username,
            "real_name": user.real_name,
            "school": user.school,
            "major": user.major,
            "grade": user.grade,
            "email": user.email,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "avatar": user.avatar_url,
            "avatarUrl": user.avatar_url,
            "defaultJob": default_job_key,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "totalInterviews": dashboard_stats["totalInterviews"],
            "avgScore": dashboard_stats["avgScore"],
            "lastInterviewScore": dashboard_stats["lastInterviewScore"],
            "lastInterviewAt": dashboard_stats["lastInterviewAt"]
        }

    @classmethod
    def get_profile(cls, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        return cls.serialize_user(user)

    @classmethod
    def update_profile(cls, user_id, data):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')

        username = (data.get('username') or '').strip()
        real_name = (data.get('real_name') or data.get('nickname') or '').strip()
        school = (data.get('school') or '').strip()
        major = (data.get('major') or '').strip()
        grade = (data.get('grade') or '').strip()
        avatar_url = (data.get('avatar_url') or data.get('avatarUrl') or '').strip()

        if username and username != user.username:
            exists = User.query.filter_by(username=username).first()
            if exists and exists.id != user.id:
                raise ValueError('昵称已存在，请更换')
            user.username = username

        if real_name:
            user.real_name = real_name
        if school:
            user.school = school
        if major:
            user.major = major
        if grade:
            user.grade = grade
        if avatar_url:
            user.avatar_url = avatar_url

        db.session.commit()
        return cls.serialize_user(user)

    @staticmethod
    def change_password(user_id, old_password, new_password):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        if not old_password or not new_password:
            raise ValueError('旧密码和新密码不能为空')
        if not user.check_password(old_password):
            raise ValueError('旧密码错误')
        if old_password == new_password:
            raise ValueError('新密码不能与旧密码相同')

        user.set_password(new_password)
        db.session.commit()
        return {"msg": "密码修改成功"}

    @classmethod
    def bind_phone(cls, user_id, phone):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        if not cls._is_phone(phone):
            raise ValueError('手机号格式不正确')

        exists = User.query.filter_by(phone=phone).first()
        if exists and exists.id != user.id:
            raise ValueError('该手机号已被绑定')

        user.phone = phone
        db.session.commit()
        return cls.serialize_user(user)

    @classmethod
    def upload_avatar(cls, user_id, avatar_file):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        if avatar_file is None:
            raise ValueError('请上传头像文件')

        filename = secure_filename(avatar_file.filename or '')
        if not filename or '.' not in filename:
            raise ValueError('头像文件格式不正确')

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError('仅支持 png/jpg/jpeg/gif/webp 格式头像')

        upload_root = current_app.config.get('UPLOAD_ROOT')
        if not upload_root:
            upload_root = os.path.join(current_app.root_path, 'uploads')

        avatar_dir = os.path.join(upload_root, 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        saved_name = f"{user.id}_{uuid.uuid4().hex}.{ext}"
        saved_path = os.path.join(avatar_dir, saved_name)
        avatar_file.save(saved_path)

        avatar_url = f"/uploads/avatars/{saved_name}"
        user.avatar_url = avatar_url
        db.session.commit()

        return {
            "avatarUrl": avatar_url,
            "avatar_url": avatar_url,
            "user": cls.serialize_user(user)
        }

    @classmethod
    def get_dashboard_stats(cls, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        return cls._collect_dashboard_stats(user_id)

    @classmethod
    def update_default_job_preference(cls, user_id, default_job):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')

        job = cls._resolve_job_by_front_key(default_job)
        if not job:
            raise ValueError('岗位不存在或暂未初始化')

        user.default_job_id = job.id
        db.session.commit()
        return {
            "defaultJob": cls._job_to_front_key(job),
            "default_job_id": job.id,
            "job_name": job.name
        }
