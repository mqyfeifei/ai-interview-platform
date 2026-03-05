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

    try:
        data = LearningService.get_weaknesses(user_id)
        return jsonify({"code": 200, "data": data, "msg": "success"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@learning_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """获取个性化学习推荐（基于向量检索）"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', type=int, default=5)

    try:
        data = LearningService.get_personalized_recommendations(user_id, limit)
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