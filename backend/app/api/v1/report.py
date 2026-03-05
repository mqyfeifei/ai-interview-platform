from itsdangerous import BadSignature, SignatureExpired
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.services.report_service import ReportService


report_bp = Blueprint('report', __name__)


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


def error_response(msg, status_code=400):
    return jsonify({"code": status_code, "msg": msg, "message": msg}), status_code


def get_current_user_id_optional():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return None
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


def get_current_user_id_required():
    user_id = get_current_user_id_optional()
    if not user_id:
        raise ValueError('缺少登录凭证')
    return user_id


@report_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    try:
        user_id = get_current_user_id_required()
        data = ReportService.get_report_detail(report_id, user_id=user_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        if msg in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(msg, 401)
        if msg == '无权限访问该报告':
            return error_response(msg, 403)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@report_bp.route('', methods=['GET'])
def list_reports():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', request.args.get('page_size', 10)))
    job_id = request.args.get('jobId') or request.args.get('job_id')

    try:
        user_id = get_current_user_id_required()
        data = ReportService.list_reports(user_id=user_id, page=page, page_size=page_size, job_id=job_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        if msg in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(msg, 401)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@report_bp.route('/history', methods=['GET'])
def list_history_records():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', request.args.get('page_size', 10)))

    try:
        user_id = get_current_user_id_required()
        data = ReportService.list_history_records(user_id=user_id, page=page, page_size=page_size)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        if msg in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(msg, 401)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


@report_bp.route('/<int:report_id>/reply-analysis', methods=['GET'])
def get_reply_analysis(report_id):
    try:
        user_id = get_current_user_id_required()
        data = ReportService.analyze_reply_details(report_id=report_id, user_id=user_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        if msg in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}:
            return error_response(msg, 401)
        if msg == '无权限访问该报告':
            return error_response(msg, 403)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)
