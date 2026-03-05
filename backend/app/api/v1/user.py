from itsdangerous import BadSignature, SignatureExpired
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.services.user_service import UserService


user_bp = Blueprint('user', __name__)


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


def error_response(msg, status_code=400):
    return jsonify({"code": status_code, "msg": msg, "message": msg}), status_code


def get_current_user_id():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise ValueError('缺少登录凭证')

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        raise ValueError('缺少登录凭证')

    try:
        return AuthService.verify_token(token)
    except SignatureExpired as exc:
        raise ValueError('登录已过期，请重新登录') from exc
    except BadSignature as exc:
        raise ValueError('登录凭证无效') from exc


@user_bp.route('/me', methods=['GET'])
def get_me():
    try:
        user_id = get_current_user_id()
        result = UserService.get_profile(user_id)
        return success_response(result)
    except ValueError as exc:
        return error_response(str(exc), 401)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me', methods=['PUT'])
def update_me():
    data = request.get_json(silent=True) or {}
    try:
        user_id = get_current_user_id()
        result = UserService.update_profile(user_id, data)
        return success_response(result, '个人信息更新成功')
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me/change-password', methods=['POST'])
def change_password():
    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password') or data.get('oldPassword')
    new_password = data.get('new_password') or data.get('newPassword')

    try:
        user_id = get_current_user_id()
        result = UserService.change_password(user_id, old_password, new_password)
        return success_response(result, '密码修改成功')
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me/bind-phone', methods=['POST'])
def bind_phone():
    data = request.get_json(silent=True) or {}
    phone = data.get('phone') or data.get('target')

    try:
        user_id = get_current_user_id()
        result = UserService.bind_phone(user_id, phone)
        return success_response(result, '手机号绑定成功')
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me/dashboard', methods=['GET'])
def get_dashboard():
    try:
        user_id = get_current_user_id()
        result = UserService.get_dashboard_stats(user_id)
        return success_response(result)
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me/preferences', methods=['PATCH'])
def update_preferences():
    data = request.get_json(silent=True) or {}
    default_job = data.get('defaultJob') or data.get('default_job') or data.get('jobId')

    try:
        user_id = get_current_user_id()
        result = UserService.update_default_job_preference(user_id, default_job)
        return success_response(result, '默认岗位更新成功')
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route('/me/avatar', methods=['POST'])
def upload_avatar():
    avatar_file = request.files.get('file') or request.files.get('avatar')

    try:
        user_id = get_current_user_id()
        result = UserService.upload_avatar(user_id, avatar_file)
        return success_response(result, '头像上传成功')
    except ValueError as exc:
        if str(exc) in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(str(exc), 401)
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)
