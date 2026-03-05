from flask import Blueprint, request, Response, stream_with_context, jsonify
from app.services.interview_service import InterviewService
from app.services.asr_service import ASRService

interview_bp = Blueprint('interview', __name__)


@interview_bp.route('/start', methods=['POST'])
def start_interview():
    data = request.get_json()
    user_id = data.get('user_id')  # 实际应从 JWT Token 获取
    job_id = data.get('job_id')

    try:
        result = InterviewService.start_interview(user_id, job_id)
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@interview_bp.route('/<int:interview_id>/chat', methods=['POST'])
def chat(interview_id):
    data = request.get_json()
    user_answer = data.get('answer')

    try:
        result = InterviewService.process_chat_round(interview_id, user_answer)
        return jsonify({"code": 200, "data": result, "msg": "success"}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


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