import re
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.extensions import db
from app.models.user import User


class AuthService:
    @staticmethod
    def _is_email(value):
        if not value:
            return False
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))

    @staticmethod
    def _is_phone(value):
        if not value:
            return False
        return bool(re.match(r"^1\d{10}$", value))

    @staticmethod
    def _find_user_by_login_id(login_id):
        if not login_id:
            return None
        normalized = str(login_id).strip()
        return User.query.filter(
            (User.email == normalized) |
            (User.phone == normalized) |
            (User.username == normalized)
        ).first()

    @staticmethod
    def _generate_unique_username(email=None, phone=None, real_name=None):
        base = None
        if email:
            base = email.split('@')[0]
        elif phone:
            base = f"user_{phone[-4:]}"
        elif real_name:
            base = f"user_{real_name}"
        else:
            base = "user"

        candidate = base
        index = 1
        while User.query.filter_by(username=candidate).first():
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    @staticmethod
    def _generate_token(user_id):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({"user_id": user_id}, salt="auth-token")

    @staticmethod
    def verify_token(token, max_age=7 * 24 * 3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        payload = serializer.loads(token, salt="auth-token", max_age=max_age)
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("无效的登录凭证")
        return user_id

    @staticmethod
    def _serialize_user(user):
        default_job_name = user.default_job.name if user.default_job else ''
        default_job = None
        if default_job_name:
            lowered = default_job_name.lower()
            if 'java' in lowered:
                default_job = 'java-backend'
            elif '前端' in default_job_name or 'frontend' in lowered or 'web' in lowered:
                default_job = 'web-frontend'
            elif 'python' in lowered or '算法' in default_job_name:
                default_job = 'python-algorithm'
            elif '全栈' in default_job_name:
                default_job = 'fullstack'
            elif 'android' in lowered:
                default_job = 'android'
            elif 'devops' in lowered:
                default_job = 'devops'

        return {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "school": user.school,
            "major": user.major,
            "grade": user.grade,
            "email": user.email,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "avatar": user.avatar_url,
            "avatarUrl": user.avatar_url,
            "defaultJob": default_job,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "createdAt": user.created_at.isoformat() if user.created_at else None
        }

    @classmethod
    def register(cls, data):
        email = (data.get('email') or '').strip() or None
        phone = (data.get('phone') or '').strip() or None
        password = data.get('password')
        real_name = data.get('real_name') or data.get('name')
        school = data.get('school')
        major = data.get('major')
        grade = data.get('grade')
        username = data.get('username')

        if not password:
            raise ValueError('密码不能为空')
        if not email and not phone:
            raise ValueError('手机号或邮箱至少填写一项')
        if email and not cls._is_email(email):
            raise ValueError('邮箱格式不正确')
        if phone and not cls._is_phone(phone):
            raise ValueError('手机号格式不正确')
        if not real_name or not school or not major or not grade:
            raise ValueError('请完整填写姓名、学校、专业、年级')

        if email and User.query.filter_by(email=email).first():
            raise ValueError('该邮箱已注册')
        if phone and User.query.filter_by(phone=phone).first():
            raise ValueError('该手机号已注册')

        final_username = username or cls._generate_unique_username(email, phone, real_name)
        if User.query.filter_by(username=final_username).first():
            raise ValueError('用户名已存在')

        user = User(
            username=final_username,
            email=email,
            phone=phone,
            real_name=real_name,
            school=school,
            major=major,
            grade=grade
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        token = cls._generate_token(user.id)
        return {"token": token, "user": cls._serialize_user(user)}

    @classmethod
    def login_with_password(cls, login_id, password):
        if not login_id or not password:
            raise ValueError('账号和密码不能为空')
        user = cls._find_user_by_login_id(login_id)
        if not user or not user.check_password(password):
            raise ValueError('账号或密码错误')
        token = cls._generate_token(user.id)
        return {"token": token, "user": cls._serialize_user(user)}

