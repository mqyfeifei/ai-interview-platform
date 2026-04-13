import json
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
    resume_id = data.get('resume_id')
    voice_mode = bool(data.get('voice_mode', False))

    interview_style = data.get('interview_style')
    voice_role = data.get('voice_role')
    voice = (data.get('voice') or '').strip() or None


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
        # 后端最终校验：确保选中岗位与简历满足面试要求（若不满足则拒绝启动面试）
        try:
            if resume_id:
                # 验证用户选择的简历
                resume_data = ResumeService.get_resume(resume_id, user_id)
            else:
                # 验证主简历
                resume_data = ResumeService.get_main_resume(user_id)
            content = resume_data.get('content', {})
            ResumeService._validate_resume_content(content, job_id, user_id=user_id)
        except ValueError as ve:
            return jsonify({"code": 400, "msg": str(ve)}), 400

        result = InterviewService.start_interview(
            user_id,
            job_id,
            voice_mode=voice_mode,
            interview_style=interview_style,
            voice_role=voice_role,
            voice=voice,
        )

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
    data = request.get_json() or {}
    user_answer = data.get('answer')
    voice_mode = bool(data.get('voice_mode', False))
    voice = (data.get('voice') or '').strip() or None

    def _event_stream():
        # 首包心跳：帮助代理和浏览器尽早建立流式渲染通道。
        yield ': connected\n\n'
        try:
            for item in InterviewService.process_chat_round_stream(
                interview_id,
                user_answer,
                voice_mode=voice_mode,
                voice=voice,
            ):
                yield item
        except Exception as e:
            print(f"[SSE] chat_stream 异常: {type(e).__name__}: {e}")
            payload = {
                "chunk": "抱歉，网络波动导致本轮追问生成失败，请重试一次。",
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            yield ': done\n\n'

    response = Response(
        stream_with_context(_event_stream()),
        mimetype='text/event-stream; charset=utf-8'
    )
    response.headers['Cache-Control'] = 'no-cache, no-transform'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


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


@interview_bp.route('/asr-result/<voice_id>', methods=['GET'])
def get_asr_result(voice_id):
    """
    获取ASR识别结果（轮询接口）
    
    Args:
        voice_id: 语音ID
        
    Returns:
        {
            "code": 200,
            "data": {
                "text": "识别结果",
                "is_final": true/false,
                "timestamp": 1234567890
            }
        }
    """
    from app.ws.asr_socketio import asr_results_cache, asr_results_lock
    
    with asr_results_lock:
        result = asr_results_cache.get(voice_id)
    
    if result:
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    else:
        return jsonify({"code": 404, "msg": "未找到识别结果"}), 404


@interview_bp.route('/<int:interview_id>/voice-chat/stream', methods=['POST'])
def voice_chat_stream(interview_id):
    """
    语音面试专用接口（与文字面试隔离）
    
    流程：
    1. 接收ASR识别后的文本
    2. 启用多模态情感分析（voice_mode=True）
    3. 流式返回AI回复 + TTS音频
    """
    data = request.get_json() or {}
    user_answer = data.get('answer')
    voice = (data.get('voice') or '').strip() or None
    
    if not user_answer or not user_answer.strip():
        return jsonify({"code": 400, "msg": "回答内容不能为空"}), 400

    def _event_stream():
        # 首包心跳
        yield ': connected\n\n'
        try:
            for item in InterviewService.process_chat_round_stream(
                interview_id,
                user_answer,
                voice_mode=True,  # ✅ 强制启用语音模式
                voice=voice,
            ):
                yield item
        except Exception as e:
            print(f"[SSE] voice_chat_stream 异常: {type(e).__name__}: {e}")
            payload = {
                "chunk": "抱歉，网络波动导致本轮追问生成失败，请重试一次。",
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            yield ': done\n\n'

    response = Response(
        stream_with_context(_event_stream()),
        mimetype='text/event-stream; charset=utf-8'
    )
    response.headers['Cache-Control'] = 'no-cache, no-transform'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@interview_bp.route('/<int:interview_id>/finish', methods=['POST'])
def finish_interview(interview_id):
    try:
        result = InterviewService.finish_interview(interview_id)
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": "报告生成失败，请稍后重试"}), 500