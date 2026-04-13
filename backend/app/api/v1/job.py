from flask import Blueprint, jsonify, request as flask_request
from sqlalchemy import func
import requests as http_requests
import traceback

from app.extensions import db
from app.models.interview import Interview
from app.models.job import Job
from app.models.user import User

DEVTO_ARTICLE_API = 'https://dev.to/api/articles/'


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


# =============================================
# 技术热榜聚合 —— 多平台公开 API，实时获取技术社区热门话题
# =============================================
from app.services.trending_service import TrendingService

@job_bp.route('/trending', methods=['GET'])
def get_trending_topics():
    """
    多平台聚合技术热榜：掘金（多分类）+ Dev.to
    """
    job_key = flask_request.args.get('jobId', 'default')
    limit = min(int(flask_request.args.get('limit', 9)), 20)
    return success_response(TrendingService.get_trending_topics(job_key, limit))


@job_bp.route('/trending/detail', methods=['GET'])
def get_article_detail():
    """
    获取文章全文内容（目前支持 Dev.to 源）
    """
    article_id = flask_request.args.get('id', '')
    source = flask_request.args.get('source', '')

    if source == 'devto' and article_id.startswith('devto_'):
        devto_id = article_id.replace('devto_', '')
        try:
            resp = http_requests.get(
                DEVTO_ARTICLE_API + devto_id,
                headers={'User-Agent': 'AI-Interview-Platform/1.0'},
                timeout=8
            )
            resp.raise_for_status()
            data = resp.json()
            return success_response({
                'id': article_id,
                'title': data.get('title', ''),
                'body_markdown': data.get('body_markdown', ''),
                'body_html': data.get('body_html', ''),
                'url': data.get('url', ''),
                'tags': data.get('tag_list', []),
                'cover_image': data.get('cover_image', ''),
                'user': data.get('user', {}).get('name', ''),
                'reading_time': data.get('reading_time_minutes', 0),
                'published_at': data.get('published_at', ''),
            })
        except Exception:
            traceback.print_exc()
            return success_response(None, msg='文章获取失败')

    # 掘金文章无法获取全文，返回提示
    return success_response({
        'id': article_id,
        'title': '',
        'body_html': '',
        'body_markdown': '',
        'fallback': True,
        'msg': '该来源暂不支持全文阅读，请点击原文链接查看'
    })
