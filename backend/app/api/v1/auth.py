from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService


auth_bp = Blueprint('auth', __name__)


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


def error_response(msg, status_code=400):
    return jsonify({"code": status_code, "msg": msg, "message": msg}), status_code


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    try:
        result = AuthService.register(data)
        return success_response(result, '注册成功')
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    login_id = data.get('login_id') or data.get('loginId') or data.get('target') or data.get('email') or data.get('phone')
    password = data.get('password')

    try:
        result = AuthService.login_with_password(login_id, password)
        return success_response(result, '登录成功')
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return success_response({"success": True}, '退出成功')
