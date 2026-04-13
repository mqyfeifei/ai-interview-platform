import concurrent.futures
import requests as http_requests

# 技术热榜聚合 —— 多平台公开 API，实时获取技术社区热门话题
JUEJIN_FEED_API = 'https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed'
JUEJIN_ARTICLE_BASE = 'https://juejin.cn/post/'
DEVTO_API = 'https://dev.to/api/articles'

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
                'hasContent': False,
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
                'hasContent': True,
            })
        return result
    except Exception:
        return []


class TrendingService:
    @staticmethod
    def get_trending_topics(job_key='default', limit=9):
        limit = min(int(limit or 9), 20)
        categories = JOB_CATEGORY_PRIORITY.get(job_key, JOB_CATEGORY_PRIORITY['default'])
        per_cat = max(2, limit // (len(categories) + 1))

        all_articles = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_fetch_juejin_category, cat, per_cat): cat for cat in categories}
            futures[executor.submit(_fetch_devto, per_cat)] = 'devto'
            for future in concurrent.futures.as_completed(futures):
                try:
                    all_articles.extend(future.result())
                except Exception:
                    pass

        seen_titles = set()
        unique = []
        for art in all_articles:
            title = (art.get('title') or art.get('text') or '').strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique.append(art)

        unique.sort(key=lambda x: x.get('likes', 0) * 2 + x.get('comments', 0) * 3, reverse=True)
        return unique[:limit]
