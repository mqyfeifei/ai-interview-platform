from functools import wraps

from itsdangerous import BadSignature, SignatureExpired
from flask import g, request

from app.models.user import User
from app.services.auth_service import AuthService


def extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise ValueError('缺少登录凭证')

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        raise ValueError('缺少登录凭证')
    return token


def get_current_user(required_role=None):
    token = extract_bearer_token()

    try:
        payload = AuthService.verify_token_payload(token)
    except SignatureExpired as exc:
        raise ValueError('登录已过期，请重新登录') from exc
    except BadSignature as exc:
        raise ValueError('登录凭证无效') from exc

    user_id = payload.get('user_id')
    token_role = payload.get('role')
    user = User.query.get(user_id)

    if not user:
        raise ValueError('用户不存在')
    if not user.is_active:
        raise ValueError('账号已被禁用，请联系管理员')

    current_role = user.role or token_role or 'user'
    if required_role and current_role != required_role:
        raise ValueError('无管理员访问权限')

    return user, payload


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user, payload = get_current_user(required_role='admin')
        g.current_user = user
        g.token_payload = payload
        return fn(*args, **kwargs)

    return wrapper
