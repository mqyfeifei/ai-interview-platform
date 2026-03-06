from flask import Blueprint, request, Response, stream_with_context, jsonify
from app.services.interview_service import InterviewService
from app.services.asr_service import ASRService
from app.services.auth_service import AuthService
from app.models.job import Job

interview_bp = Blueprint('interview', __name__)

# 前端 jobId 字符串到数据库岗位名称的映射
JOB_ID_MAP = {
    'java-backend': 'Java后端开发',
    'web-frontend': 'Web前端开发',
    'python-algorithm': 'Python算法工程师',
    'fullstack': '全栈开发工程师',
    'android': 'Android开发',
    'devops': 'DevOps工程师'
}


def get_current_user_id():
    """从 Authorization header 中获取当前用户 ID"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            return AuthService.verify_token(token)
        except Exception:
            return None
    return None


def resolve_job_id(job_id_input):
    """将前端传入的 job_id（字符串或数字）解析为数据库中的实际 job.id"""
    if job_id_input is None:
        return None
    
    # 如果是数字，直接返回
    if isinstance(job_id_input, int):
        return job_id_input
    
    # 尝试转换为整数
    try:
        return int(job_id_input)
    except (ValueError, TypeError):
        pass
    
    # 字符串类型，尝试通过映射查找岗位名称
    job_name = JOB_ID_MAP.get(job_id_input)
    if job_name:
        job = Job.query.filter_by(name=job_name).first()
        if job:
            return job.id
    
    # 如果映射中没有，尝试直接用传入的字符串作为岗位名称查找
    job = Job.query.filter_by(name=job_id_input).first()
    if job:
        return job.id
    
    return None


@interview_bp.route('/start', methods=['POST'])
def start_interview():
    data = request.get_json() or {}
    
    # 优先从 Token 获取 user_id，其次从请求体获取
    user_id = get_current_user_id() or data.get('user_id')
    job_id_input = data.get('job_id')

    # 参数验证
    if not user_id:
        return jsonify({"code": 400, "msg": "用户未登录或 user_id 缺失"}), 400
    if not job_id_input:
        return jsonify({"code": 400, "msg": "请选择面试岗位 (job_id)"}), 400
    
    # 解析 job_id
    job_id = resolve_job_id(job_id_input)
    if not job_id:
        return jsonify({"code": 400, "msg": f"无效的岗位: {job_id_input}，请确认岗位已在数据库中创建"}), 400

    try:
        result = InterviewService.start_interview(user_id, job_id)
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# @interview_bp.route('/<int:interview_id>/chat', methods=['POST'])
# def chat(interview_id):
#     data = request.get_json()
#     user_answer = data.get('answer')
#
#     try:
#         result = InterviewService.process_chat_round(interview_id, user_answer)
#         return jsonify({"code": 200, "data": result, "msg": "success"}), 200
#     except Exception as e:
#         return jsonify({"code": 500, "msg": str(e)}), 500



#注：前端开发人员需配合，在接收 SSE 流的过程中监听 [INTERVIEW_OVER]，一旦匹配到，立刻终止录音/输入，并请求 /finish 接口生成报告。
@interview_bp.route('/<int:interview_id>/chat/stream', methods=['POST'])
def chat_stream(interview_id):
    data = request.get_json()
    user_answer = data.get('answer')

    # 返回 SSE 响应
    return Response(
        stream_with_context(InterviewService.process_chat_round_stream(interview_id, user_answer)),
        mimetype='text/event-stream'
    )


@interview_bp.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"code": 400, "msg": "未找到音频文件"}), 400

    audio_file = request.files['audio']
    try:
        text = ASRService.transcribe_audio(audio_file)
        return jsonify({"code": 200, "data": {"text": text}, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@interview_bp.route('/<int:interview_id>/finish', methods=['POST'])
def finish_interview(interview_id):
    try:
        result = InterviewService.finish_interview(interview_id)
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500