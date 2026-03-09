// =============================================
// frontend/src/api/learning.js
// 学习中心相关 API
// =============================================

import request from '@/utils/request'
// disable mocking: always fetch from backend database
const USE_MOCK = false
const mockDelay = (ms = 600) => new Promise(resolve => setTimeout(resolve, ms))

// ---- 常量 ----

/** 后端 dimension_id → 前端 key 映射 */
const DIMENSION_ID_MAP = {
  1: 'technical',    // 技术正确性
  2: 'logic',        // 逻辑严谨性
  3: 'matching',     // 岗位匹配度
  4: 'expression',   // 表达沟通
  5: 'adaptability'  // 应变能力
}

/** 日期格式转换 "2024-12-15" → "12/15" */
const fmtDate = d => {
  const [, m, day] = d.split('-')
  return `${parseInt(m)}/${parseInt(day)}`
}

// ---- API 函数 ----

/**
 * 获取能力成长曲线数据
 * 对后端发起 6 次并行请求（1 次总分 + 5 次各维度），
 * 组装为前端 renderChart() 需要的 {overall, dimensions, dates} 结构。
 * 若后端不可用或无数据则降级为 Mock。
 */
export const getGrowthCurve = async () => {
  try {
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[GrowthCurve] 未找到用户ID')
      return { overall: [], dimensions: {}, dates: [], realDates: [] }
    }
    const dimIds = Object.keys(DIMENSION_ID_MAP)
    const [overallRaw, ...dimRawList] = await Promise.all([
      request.get('/learning/growth-curve', { params: { user_id: userId } }),
      ...dimIds.map(did =>
        request.get('/learning/growth-curve', { params: { user_id: userId, dimension_id: did } })
      )
    ])
    const overall = (overallRaw || []).map((item, idx) => ({
      label: `第${idx + 1}次`,
      date: fmtDate(item.date),
      score: item.score
    }))
    const dimensions = {}
    let dates = []
    let realDates = []
    dimIds.forEach((did, idx) => {
      const key = DIMENSION_ID_MAP[did]
      const raw = dimRawList[idx] || []
      dimensions[key] = raw.map(r => r.score)
      if (idx === 0 && raw.length) {
        dates = raw.map((r, i) => `第${i + 1}次`)
        realDates = raw.map(r => fmtDate(r.date))
      }
    })
    return { overall, dimensions, dates, realDates }
  } catch (err) {
    console.warn('[GrowthCurve] 请求失败', err)
    return { overall: [], dimensions: {}, dates: [], realDates: [] }
  }
}

/**
 * 获取薄弱知识点标签
 */
export const getWeaknessTags = async () => {
  try {
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[Weaknesses] 未找到用户ID')
      return []
    }
    const data = await request.get('/learning/weaknesses', { params: { user_id: userId } })
    if (!Array.isArray(data) || !data.length) return []
    return data.map((item, idx) => ({
      id: `w${item.tag_id || idx}`,
      tag: item.name,
      mastery_level: item.mastery_level,
      level: item.mastery_level < 40 ? 'high' : item.mastery_level < 70 ? 'medium' : item.mastery_level < 90 ? 'good' : 'excellent'
    }))
  } catch (err) {
    console.warn('[Weaknesses] 请求失败', err)
    return []
  }
}

// 为了兼容 store 中的导入名称
export const getWeaknesses = getWeaknessTags

/**
 * 获取推荐学习资源（基于后端向量检索 + 薄弱知识点匹配）
 * 后端返回: [{id, title, type, source, difficulty}, ...]
 * 前端补全展示所需字段
 */
export const getRecommendedResources = async () => {
  try {
    // 从 localStorage 中缓存的书签和完成信息
    const bookmarks = JSON.parse(localStorage.getItem('learning_bookmarks') || '{}')
    const completed = JSON.parse(localStorage.getItem('learning_completed') || '[]')

    // always use backend recommendation endpoint
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[Recommendations] 未找到用户ID，无法加载推荐')
      return []
    }
    const data = await request.get('/learning/recommendations', {
      params: { user_id: userId, limit: 10 }
    })
    if (!Array.isArray(data) || !data.length) {
      return []
    }

    // 难度映射
    const diffMap = { easy: '初级', medium: '中级', hard: '高级' }

    let result = data.map(item => ({
      id: item.id,
      title: item.title,
      type: item.type || 'article',
      summary: item.content ? item.content.slice(0, 100) + '...' : `针对您的薄弱环节推荐的${diffMap[item.difficulty] || ''}学习资源`,
      source: item.source || 'AI面试助手',
      tags: Array.isArray(item.tags) ? item.tags.slice(0, 3) : [],
      // 使用后端返回的 difficulty 作为“时间/难度”显示，前端不再默认持续时间
      readTime: diffMap[item.difficulty] || item.difficulty || '中级',
      difficulty: diffMap[item.difficulty] || item.difficulty || '中级',
      relatedWeakness: null,
      bookmarked: bookmarks[item.id] || false,
      completed: completed.includes(item.id) || false,
      url: item.url || null
    }))

    // 缓存新拿到的资源
    _updateCacheWithList(result)

    // 如果有已收藏但本次列表不含的资源，从缓存补出来；纯完成但未收藏的仍保持隐藏
    const existingIds = new Set(result.map(r => r.id))
    const additions = []
    Object.keys(bookmarks).forEach(id => {
      if (bookmarks[id] && !existingIds.has(id)) {
        const cached = _getCachedItem(id)
        if (cached) {
          cached.bookmarked = true
          cached.completed = completed.includes(id)
          additions.push(cached)
          existingIds.add(id)
        }
      }
    })
    if (additions.length) result = result.concat(additions)

    return result
  } catch (err) {
    console.warn('[Recommendations] 请求失败', err)
    return []
  }
}

// 为了兼容 store 中的导入名称
export const getRecommendations = getRecommendedResources

// ---------- local cache helpers ----------
// 保存最近拿到过的资源基本信息，供收藏/完成时在后端不再推荐的情况下继续展示
const CACHE_KEY = 'learning_resource_cache'
function _loadCache() {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}')
  } catch (e) {
    console.warn('解析推荐资源缓存失败', e)
    return {}
  }
}
function _saveCache(cache) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
  } catch (e) {
    console.warn('保存推荐资源缓存失败', e)
  }
}
function _updateCacheWithList(list) {
  const cache = _loadCache()
  list.forEach(item => { cache[item.id] = item })
  _saveCache(cache)
}
function _getCachedItem(id) {
  return _loadCache()[id]
}

/**
 * 获取每日学习计划
 */
export const getDailyPlan = async () => {
  try {
    return await request.get('/learning/daily-plan')
  } catch (err) {
    console.warn('[DailyPlan] 请求失败', err)
    return null
  }
}

/**
 * 切换资源收藏状态
 * @param {string} resourceId - 资源ID
 * @param {boolean} bookmarked - 收藏状态
 */
export const toggleBookmark = async (resourceId, bookmarked) => {
  // 永久化到 localStorage
  const bookmarks = JSON.parse(localStorage.getItem('learning_bookmarks') || '{}')
  bookmarks[resourceId] = bookmarked
  localStorage.setItem('learning_bookmarks', JSON.stringify(bookmarks))
  // 若已在缓存中则更新标志
  const cached = _getCachedItem(resourceId)
  if (cached) {
    cached.bookmarked = bookmarked
    _updateCacheWithList([cached])
  }

  // always call backend
  return request.post(`/learning/resources/${resourceId}/bookmark`, { bookmarked }).catch(() => ({ success: true }))
}

/**
 * 标记资源为已完成
 * @param {string} resourceId - 资源ID
 */
export const markCompleted = async (resourceId) => {
  // 永久化到 localStorage
  const completed = JSON.parse(localStorage.getItem('learning_completed') || '[]')
  if (!completed.includes(resourceId)) {
    completed.push(resourceId)
    localStorage.setItem('learning_completed', JSON.stringify(completed))
  }
  // 同步缓存状态
  const cached = _getCachedItem(resourceId)
  if (cached) {
    cached.completed = true
    _updateCacheWithList([cached])
  }

  const userCached = localStorage.getItem('ai_interview_user')
  const userId = userCached ? (JSON.parse(userCached).id || JSON.parse(userCached).user_id) : null
  if (!userId) return { success: true }

  try {
    await request.post('/learning/records/start', { user_id: userId, resource_id: resourceId })
    await request.post('/learning/records/finish', { user_id: userId, resource_id: resourceId })
    return { success: true }
  } catch (err) {
    return { success: true }
  }
}

/**
 * 更新每日计划任务状态
 * @param {string} taskId - 任务ID
 * @param {boolean} done - 完成状态
 */
export const updateTaskStatus = async (taskId, done) => {
  return request.post(`/learning/tasks/${taskId}/status`, { done })
}