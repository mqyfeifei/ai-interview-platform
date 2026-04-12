# backend/app/api/v1/resumes.py
"""
简历 CRUD 接口。

认证方式与项目其他接口（user.py）保持一致：
使用 AuthService.verify_token() 手动解析 Bearer Token，
Endpoints
---------
GET    /api/v1/resumes                      列出当前用户所有简历（不含 content）
POST   /api/v1/resumes                      创建新简历
GET    /api/v1/resumes/main                 获取主简历（含 content）
GET    /api/v1/resumes/<id>                 获取单份简历（含 content）
PUT    /api/v1/resumes/<id>                 更新标题 / 内容
DELETE /api/v1/resumes/<id>                 删除简历（主简历不可删除）
POST   /api/v1/resumes/<id>/copy-from-main  从主简历复制内容到该简历
"""

from itsdangerous import BadSignature, SignatureExpired
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.services.resume_service import ResumeService

bp = Blueprint('resumes', __name__)


# --------------------------------------------------------------------------- #
# 统一响应格式（与 user.py 完全一致）                                            #
# --------------------------------------------------------------------------- #

def success_response(data=None, msg='success', status_code=200):
    return jsonify({'code': 200, 'data': data, 'msg': msg, 'message': msg}), status_code


def error_response(msg, status_code=400):
    return jsonify({'code': status_code, 'msg': msg, 'message': msg}), status_code


# --------------------------------------------------------------------------- #
# 认证辅助（与 user.py 完全一致）                                                #
# --------------------------------------------------------------------------- #

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


def _auth_error(msg: str):
    """判断是否为认证类错误，决定返回 401 还是 400。"""
    return msg in {'缺少登录凭证', '登录已过期，请重新登录', '登录凭证无效'}

# --------------------------------------------------------------------------- #
# GET /api/v1/resumes                                                          #
# --------------------------------------------------------------------------- #

@bp.route('', methods=['GET'])
def list_resumes():
    """返回当前用户的所有简历（不含 content）。"""
    try:
        user_id = get_current_user_id()
        data = ResumeService.list_resumes(user_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# GET /api/v1/resumes/main                                                     #
# 注意：必须放在 /<int:resume_id> 路由之前，否则 Flask 会把 "main" 当 int 解析   #
# --------------------------------------------------------------------------- #

@bp.route('/main', methods=['GET'])
def get_main_resume():
    """返回当前用户的主简历（含 content），不存在则自动创建。"""
    try:
        user_id = get_current_user_id()
        data = ResumeService.get_main_resume(user_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# POST /api/v1/resumes                                                         #
# --------------------------------------------------------------------------- #

@bp.route('', methods=['POST'])
def create_resume():
    """
    创建新简历。
    Body: { title, isMain?, jobId?, content? }
    """
    try:
        user_id = get_current_user_id()
        body = request.get_json(silent=True) or {}

        data = ResumeService.create_resume(
            user_id=user_id,
            title=body.get('title') or '新简历',
            is_main=bool(body.get('isMain', False)),
            job_id=body.get('jobId'),
            content=body.get('content') or {},
        )
        return success_response(data, '创建成功', 201)
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# GET /api/v1/resumes/<id>                                                     #
# --------------------------------------------------------------------------- #

@bp.route('/<int:resume_id>', methods=['GET'])
def get_resume(resume_id: int):
    """返回单份简历（含 content）。"""
    try:
        user_id = get_current_user_id()
        data = ResumeService.get_resume(resume_id, user_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        if _auth_error(msg):
            return error_response(msg, 401)
        if msg == '简历不存在':
            return error_response(msg, 404)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# PUT /api/v1/resumes/<id>                                                     #
# --------------------------------------------------------------------------- #

@bp.route('/<int:resume_id>', methods=['PUT'])
def update_resume(resume_id: int):
    """
    更新简历标题、内容和/或关联岗位。
    Body: { title?, content?, job_id? }
    """
    try:
        user_id = get_current_user_id()
        body = request.get_json(silent=True) or {}

        data = ResumeService.update_resume(
            resume_id=resume_id,
            user_id=user_id,
            title=body.get('title'),
            content=body.get('content'),
            job_id=body.get('job_id'),
        )
        return success_response(data, '保存成功')
    except ValueError as exc:
        msg = str(exc)
        if _auth_error(msg):
            return error_response(msg, 401)
        if msg == '简历不存在':
            return error_response(msg, 404)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# DELETE /api/v1/resumes/<id>                                                  #
# --------------------------------------------------------------------------- #

@bp.route('/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id: int):
    """删除岗位定制简历（主简历不可删除）。"""
    try:
        user_id = get_current_user_id()
        ResumeService.delete_resume(resume_id, user_id)
        return success_response(None, '删除成功')
    except ValueError as exc:
        msg = str(exc)
        if _auth_error(msg):
            return error_response(msg, 401)
        if msg == '简历不存在':
            return error_response(msg, 404)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# POST /api/v1/resumes/<id>/copy-from-main                                     #
# --------------------------------------------------------------------------- #

@bp.route('/<int:resume_id>/copy-from-main', methods=['POST'])
def copy_from_main(resume_id: int):
    """将主简历的内容覆盖到指定定制简历，作为定制编辑的起点。"""
    try:
        user_id = get_current_user_id()
        data = ResumeService.copy_from_main(resume_id, user_id)
        return success_response(data, '已从主简历导入内容')
    except ValueError as exc:
        msg = str(exc)
        if _auth_error(msg):
            return error_response(msg, 401)
        if msg == '简历不存在':
            return error_response(msg, 404)
        return error_response(msg, 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# POST /api/v1/resumes/avatar/upload  简历头像上传
# --------------------------------------------------------------------------- #
@bp.route('/avatar/upload', methods=['POST'])
def upload_resume_avatar():
    try:
        user_id = get_current_user_id()
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)

    file = request.files.get('avatar')
    try:
        url = ResumeService.upload_resume_avatar(user_id, file)
        return success_response({"url": url})
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(f"上传失败：{str(e)}", 500)


# --------------------------------------------------------------------------- #
# GET /api/v1/resumes/guidance  获取简历必填与建议指导（用于前端右侧栏或提示气泡展示）
# --------------------------------------------------------------------------- #
@bp.route('/guidance', methods=['GET'])
def get_resume_guidance():
    """
    Query Args:
      - job_id (可选, int): 对应的岗位 ID，用于返回差异化提示
    """
    try:
        # 验证登录态
        get_current_user_id()
        job_id = request.args.get('job_id', type=int)

        data = ResumeService.get_resume_guidance(job_id)
        return success_response(data)
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)
    except Exception as exc:
        return error_response(str(exc), 500)


# --------------------------------------------------------------------------- #
# POST /api/v1/resumes/analyze  实时分析当前简历的完成度与缺失项
# --------------------------------------------------------------------------- #
@bp.route('/analyze', methods=['POST'])
def analyze_resume_completion():
    """
    Body:
    {
      "content": dict,  // 前端当前编辑器里实时的 JSON 数据
      "jobId": int      // (可选) 当前简历绑定的岗位
    }
    """
    try:
        get_current_user_id()
        body = request.get_json(silent=True) or {}
        content = body.get('content', {})
        job_id = body.get('jobId')

        # 计算完成度
        analysis_result = ResumeService.calculate_completion(content, job_id)

        return success_response(analysis_result)
    except ValueError as exc:
        msg = str(exc)
        return error_response(msg, 401 if _auth_error(msg) else 400)
    except Exception as exc:
        return error_response(str(exc), 500)