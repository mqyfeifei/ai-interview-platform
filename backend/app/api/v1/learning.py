# backend/app/api/v1/learning.py
from flask import Blueprint, request, jsonify
from app.services.learning_service import LearningService

learning_bp = Blueprint('learning', __name__)


@learning_bp.route('/growth-curve', methods=['GET'])
def get_growth_curve():
    """获取成长曲线"""
    user_id = request.args.get('user_id', type=int)  # 实际应从 JWT token 获取
    dimension_id = request.args.get('dimension_id', type=int, default=None)

    try:
        data = LearningService.get_growth_curve(user_id, dimension_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/weaknesses', methods=['GET'])
def get_weaknesses():
    """获取技能短板"""
    user_id = request.args.get('user_id', type=int)
    report_id = request.args.get('report_id', type=int)

    try:
        data = LearningService.get_weaknesses(user_id, report_id=report_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """获取个性化学习推荐（基于向量检索）"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', type=int, default=5)
    report_id = request.args.get('report_id', type=int)

    try:
        data = LearningService.get_personalized_recommendations(user_id, limit, report_id=report_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/daily-plan', methods=['GET'])
def get_daily_plan():
    """获取每日学习计划"""
    user_id = request.args.get('user_id', type=int)
    daily_hours = request.args.get('daily_hours', type=float)
    report_id = request.args.get('report_id', type=int)

    try:
        data = LearningService.get_daily_plan(user_id, daily_hours=daily_hours, report_id=report_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/study-plan', methods=['GET'])
def get_study_plan():
    """获取学习规划（含优先级与预计完成日期）"""
    user_id = request.args.get('user_id', type=int)
    daily_hours = request.args.get('daily_hours', type=float)
    report_id = request.args.get('report_id', type=int)
    try:
        data = LearningService.get_study_plan(user_id, daily_hours=daily_hours, report_id=report_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/records/start', methods=['POST'])
def start_learning_record():
    """记录：开始学习资源"""
    data = request.get_json()
    user_id = data.get('user_id')
    resource_id = data.get('resource_id')

    try:
        res = LearningService.start_learning(user_id, resource_id)
        return jsonify({"code": 200, "data": res, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/records/finish', methods=['POST'])
def finish_learning_record():
    """记录：完成学习资源并结算时间"""
    data = request.get_json()
    user_id = data.get('user_id')
    resource_id = data.get('resource_id')

    try:
        res = LearningService.finish_learning(user_id, resource_id)
        return jsonify({"code": 200, "data": res, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})

@learning_bp.route('/records/completed', methods=['GET'])
def get_completed_records():
    """查询某用户所有已完成的学习资源 ID 列表"""
    user_id = request.args.get('user_id', type=int)
    try:
        ids = LearningService.get_completed_resource_ids(user_id)
        return jsonify({"code": 200, "data": ids, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/tasks/<task_id>/status', methods=['POST'])
def update_task_status(task_id):
    """更新每日计划任务状态"""
    data = request.get_json() or {}
    done = bool(data.get('done', False))
    user_id = data.get('user_id')

    try:
        res = LearningService.update_task_status(user_id=user_id, task_id=task_id, done=done)
        return jsonify({"code": 200, "data": res, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/settings', methods=['GET'])
def get_learning_settings():
    user_id = request.args.get('user_id', type=int)
    try:
        data = LearningService.get_learning_settings(user_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/settings', methods=['POST'])
def update_learning_settings():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    daily_hours = data.get('daily_hours')
    selected_day_index = data.get('selected_day_index')
    try:
        res = LearningService.update_learning_settings(
            user_id=user_id,
            daily_hours=daily_hours,
            selected_day_index=selected_day_index
        )
        return jsonify({"code": 200, "data": res, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/resources/<int:resource_id>/bookmark', methods=['POST'])
def toggle_resource_bookmark(resource_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    bookmarked = bool(data.get('bookmarked', False))
    try:
        res = LearningService.toggle_bookmark(user_id=user_id, resource_id=resource_id, bookmarked=bookmarked)
        return jsonify({"code": 200, "data": res, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})
