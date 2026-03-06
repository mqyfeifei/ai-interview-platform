from flask import Blueprint, jsonify, request as flask_request
from sqlalchemy import func
import requests as http_requests
import traceback

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


# =============================================
# 技术热榜聚合 —— 多平台公开 API，实时获取技术社区热门话题
# =============================================
import concurrent.futures

JUEJIN_FEED_API = 'https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed'
JUEJIN_ARTICLE_BASE = 'https://juejin.cn/post/'
DEVTO_API = 'https://dev.to/api/articles'
DEVTO_ARTICLE_API = 'https://dev.to/api/articles/'

# 掘金分类 ID（公开信息）
JUEJIN_CATEGORIES = {
    'backend':  '6809637769959178254',
    'frontend': '6809637767543259144',
    'ai':       '6809637773935378440',
    'android':  '6809635626879549454',
}

# 岗位 → 优先拉取的掘金分类列表
JOB_CATEGORY_PRIORITY = {
    'java-backend':     ['backend', 'ai'],
    'web-frontend':     ['frontend', 'backend'],
    'python-algorithm': ['ai', 'backend'],
    'android':          ['android', 'frontend'],
    'devops':           ['backend', 'ai'],
    'fullstack':        ['frontend', 'backend', 'ai'],
    'default':          ['backend', 'frontend', 'ai'],
}

# 掘金分类中文标签映射
JUEJIN_TAG_MAP = {
    'backend': ('后端', '#DBEAFE', '#1D4ED8'),
    'frontend': ('前端', '#FEF3C7', '#B45309'),
    'ai': ('AI', '#D1FAE5', '#047857'),
    'android': ('Android', '#FDE68A', '#92400E'),
}


def _fetch_juejin_category(cat_key, limit=3):
    """抓取掘金某一分类的热门文章"""
    cat_id = JUEJIN_CATEGORIES.get(cat_key, JUEJIN_CATEGORIES['backend'])
    tag_name, tag_bg, tag_color = JUEJIN_TAG_MAP.get(cat_key, ('技术', '#DBEAFE', '#1D4ED8'))
    try:
        resp = http_requests.post(
            JUEJIN_FEED_API,
            json={"id_type": 2, "sort_type": 200, "cate_id": cat_id, "cursor": "0", "limit": limit},
            headers={'Content-Type': 'application/json', 'User-Agent': 'AI-Interview-Platform/1.0'},
            timeout=5
        )
        resp.raise_for_status()
        articles = resp.json().get('data', [])
        result = []
        for item in articles:
            info = item.get('item_info', {})
            art = info.get('article_info', {})
            tags = info.get('tags', [])
            if not art.get('title'):
                continue
            result.append({
                'id': 'juejin_' + art.get('article_id', ''),
                'title': art.get('title', ''),
                'brief': (art.get('brief_content', '') or '')[:100],
                'url': JUEJIN_ARTICLE_BASE + art.get('article_id', ''),
                'views': art.get('view_count', 0),
                'likes': art.get('digg_count', 0),
                'comments': art.get('comment_count', 0),
                'tags': [t.get('tag_name', '') for t in tags[:3]],
                'source': 'juejin',
                'sourceLabel': '掘金',
                'tag': tag_name,
                'tagBg': tag_bg,
                'tagColor': tag_color,
                'hasContent': False,  # 掘金详情 API 受限，无全文
            })
        return result
    except Exception:
        return []


def _fetch_devto(limit=3):
    """抓取 Dev.to 热门技术文章（全球最大开发者博客平台，含全文）"""
    try:
        resp = http_requests.get(
            DEVTO_API,
            params={'per_page': limit, 'top': 7, 'tag': 'programming'},
            headers={'User-Agent': 'AI-Interview-Platform/1.0'},
            timeout=5
        )
        resp.raise_for_status()
        articles = resp.json()
        result = []
        for art in articles:
            result.append({
                'id': 'devto_' + str(art.get('id', '')),
                'devtoId': art.get('id'),
                'title': art.get('title', ''),
                'brief': (art.get('description', '') or '')[:100],
                'url': art.get('url', ''),
                'views': art.get('page_views_count', 0) or art.get('positive_reactions_count', 0),
                'likes': art.get('positive_reactions_count', 0),
                'comments': art.get('comments_count', 0),
                'tags': [t for t in (art.get('tag_list', []) or [])[:3]],
                'source': 'devto',
                'sourceLabel': 'Dev.to',
                'tag': 'Global',
                'tagBg': '#E0E7FF',
                'tagColor': '#4338CA',
                'hasContent': True,  # Dev.to 有全文 API
            })
        return result
    except Exception:
        return []


@job_bp.route('/trending', methods=['GET'])
def get_trending_topics():
    """
    多平台聚合技术热榜：掘金（多分类）+ Dev.to
    """
    job_key = flask_request.args.get('jobId', 'default')
    limit = min(int(flask_request.args.get('limit', 9)), 20)

    # 确定要拉取的掘金分类
    categories = JOB_CATEGORY_PRIORITY.get(job_key, JOB_CATEGORY_PRIORITY['default'])
    per_cat = max(2, limit // (len(categories) + 1))  # 每个来源分配条数

    # 并发请求多个数据源
    all_articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for cat in categories:
            futures[executor.submit(_fetch_juejin_category, cat, per_cat)] = cat
        futures[executor.submit(_fetch_devto, per_cat)] = 'devto'

        for future in concurrent.futures.as_completed(futures):
            try:
                all_articles.extend(future.result())
            except Exception:
                pass

    # 去重（按 title 去重）
    seen_titles = set()
    unique = []
    for art in all_articles:
        if art['title'] not in seen_titles:
            seen_titles.add(art['title'])
            unique.append(art)

    # 按热度排序（点赞 + 评论权重）
    unique.sort(key=lambda x: x.get('likes', 0) * 2 + x.get('comments', 0) * 3, reverse=True)

    return success_response(unique[:limit])


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
