from flask import Blueprint, request, Response, stream_with_context, jsonify
from app.services.interview_service import InterviewService
from app.services.asr_service import ASRService
from app.services.auth_service import AuthService
from app.models.job import Job, DEFAULT_JOBS
from app.services.resume_service import ResumeService

interview_bp = Blueprint('interview', __name__)

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

    lowered_input = str(job_id_input).lower()

    # 1. 尝试通过集中维护的映射查找岗位名称
    job_info = DEFAULT_JOBS.get(lowered_input)
    if job_info:
        job = Job.query.filter_by(name=job_info['name']).first()
        if job:
            return job.id

    # 2. 如果映射中没有（或者前端直接传了中文名），尝试直接作为岗位名称查找
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
    voice_mode = bool(data.get('voice_mode', False))

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
        result = InterviewService.start_interview(user_id, job_id, voice_mode=voice_mode)
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

@interview_bp.route('/check-resume', methods=['GET'])
def check_resume():
    """检测当前用户简历是否已填写，供前端岗位选择页使用"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"code": 401, "msg": "请先登录"}), 401

    try:
        resume_data = ResumeService.get_main_resume(user_id)
        content = resume_data.get('content', {})
        has_experience = bool(
            content.get('workExperiences') or
            content.get('internshipExperiences') or
            content.get('campusExperiences')
        )
        has_skills = bool(content.get('skills'))
        has_resume = has_experience or has_skills

        return jsonify({
            "code": 200,
            "data": {
                "has_resume": has_resume,
                "warning": None if has_resume else "简历未完善，AI 将无法根据您的经历进行个性化提问，建议先完善简历。"
            },
            "msg": "success"
        }), 200

    except Exception:
        # 查不到简历（用户从未填写），统一返回 false
        return jsonify({
            "code": 200,
            "data": {
                "has_resume": False,
                "warning": "未检测到简历，请前往「简历制作」页面填写。"
            },
            "msg": "success"
        }), 200

#注：前端开发人员需配合，在接收 SSE 流的过程中监听 [INTERVIEW_OVER]，一旦匹配到，立刻终止录音/输入，并请求 /finish 接口生成报告。
@interview_bp.route('/<int:interview_id>/chat/stream', methods=['POST'])
def chat_stream(interview_id):
    data = request.get_json()
    user_answer = data.get('answer')
    voice_mode = bool(data.get('voice_mode', False))

    # 返回 SSE 响应
    return Response(
        stream_with_context(InterviewService.process_chat_round_stream(interview_id, user_answer, voice_mode=voice_mode)),
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
        return jsonify({"code": 500, "msg": "报告生成失败，请稍后重试"}), 500
