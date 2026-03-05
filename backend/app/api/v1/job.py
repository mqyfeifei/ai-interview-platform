from flask import Blueprint, jsonify
from sqlalchemy import func

from app.extensions import db
from app.models.interview import Interview
from app.models.job import Job
from app.models.user import User


job_bp = Blueprint('job', __name__)


def success_response(data=None, msg='success', status_code=200):
    return jsonify({"code": 200, "data": data, "msg": msg, "message": msg}), status_code


@job_bp.route('', methods=['GET'])
def list_jobs():
    jobs = Job.query.order_by(Job.id.asc()).all()
    result = [job.to_dict() for job in jobs]
    return success_response(result)


@job_bp.route('/popular', methods=['GET'])
def list_popular_jobs():
    rows = db.session.query(
        Job,
        func.count(User.id).label('selected_count')
    ).join(
        User, User.default_job_id == Job.id
    ).group_by(
        Job.id
    ).order_by(
        func.count(User.id).desc(),
        Job.id.asc()
    ).limit(5).all()

    result = []
    for job, selected_count in rows:
        item = job.to_dict()
        item['selected_count'] = int(selected_count or 0)
        result.append(item)

    return success_response(result)


@job_bp.route('/avg-scores', methods=['GET'])
def list_job_average_scores():
    rows = db.session.query(
        Job,
        func.avg(Interview.total_score).label('avg_score'),
        func.count(Interview.id).label('interview_count'),
        func.count(func.distinct(Interview.user_id)).label('user_count')
    ).outerjoin(
        Interview,
        (Interview.job_id == Job.id)
        & (Interview.status == 'completed')
        & (Interview.total_score.isnot(None))
    ).group_by(
        Job.id
    ).order_by(
        Job.id.asc()
    ).all()

    result = []
    for job, avg_score, interview_count, user_count in rows:
        item = job.to_dict()
        item['avg_score'] = int(round(float(avg_score))) if avg_score is not None else 0
        item['interview_count'] = int(interview_count or 0)
        item['user_count'] = int(user_count or 0)
        result.append(item)

    return success_response(result)
