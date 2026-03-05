from flask import Blueprint, jsonify
from app.models.job import Job


job_bp = Blueprint('job', __name__)


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


@job_bp.route('', methods=['GET'])
def list_jobs():
    jobs = Job.query.order_by(Job.id.asc()).all()
    result = [job.to_dict() for job in jobs]
    return success_response(result)
