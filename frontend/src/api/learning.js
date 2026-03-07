// =============================================
// frontend/src/api/learning.js
// 学习中心相关 API
// =============================================

import request from '@/utils/request'
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'
const mockDelay = (ms = 600) => new Promise(resolve => setTimeout(resolve, ms))

// ---- Mock 数据 ----

const MOCK_GROWTH_CURVE = {
  // 综合得分折线
  overall: [
    { label: '第1次', date: '11/25', score: 58 },
    { label: '第2次', date: '12/01', score: 63 },
    { label: '第3次', date: '12/05', score: 67 },
    { label: '第4次', date: '12/10', score: 70 },
    { label: '第5次', date: '12/15', score: 70 },
    { label: '第6次', date: '12/18', score: 75 },
    { label: '第7次', date: '12/20', score: 82 }
  ],
  // 各维度折线（最近5次）
  dimensions: {
    technical: [65, 70, 74, 78, 85],
    logic: [60, 65, 68, 72, 78],
    matching: [72, 75, 78, 82, 88],
    expression: [55, 60, 64, 68, 72],
    adaptability: [58, 63, 68, 72, 80]
  },
  dates: ['第1次', '第2次', '第3次', '第4次', '第5次'],
  realDates: ['12/01', '12/05', '12/10', '12/18', '12/20']
}

const MOCK_WEAKNESSES = [
  { id: 'w1', tag: 'Redis持久化', level: 'high', mastery_level: 25, jobId: 'java-backend' },
  { id: 'w2', tag: 'GC收集器', level: 'high', mastery_level: 30, jobId: 'java-backend' },
  { id: 'w3', tag: '表达结构化', level: 'high', mastery_level: 35, jobId: null },
  { id: 'w4', tag: '分布式事务', level: 'medium', mastery_level: 45, jobId: 'java-backend' },
  { id: 'w5', tag: '性能调优', level: 'medium', mastery_level: 55, jobId: 'java-backend' },
  { id: 'w6', tag: 'Vue3响应式原理', level: 'medium', mastery_level: 60, jobId: 'web-frontend' },
  { id: 'w7', tag: 'Webpack配置', level: 'good', mastery_level: 75, jobId: 'web-frontend' },
  { id: 'w8', tag: '算法复杂度', level: 'good', mastery_level: 80, jobId: 'python-algorithm' },
  { id: 'w9', tag: 'MySQL索引优化', level: 'medium', mastery_level: 50, jobId: 'java-backend' },
  { id: 'w10', tag: 'STAR回答法', level: 'excellent', mastery_level: 92, jobId: null }
]

const MOCK_RECOMMENDATIONS = [
  {
    id: 'r1', type: 'article',
    title: 'Redis持久化深度解析：RDB vs AOF全面对比',
    summary: '深入分析Redis两种持久化方案的底层原理、触发机制、优缺点及混合持久化最佳实践。',
    source: '掘金',
    tags: ['Redis', '持久化', 'Java后端'],
    readTime: '8分钟',
    difficulty: '中级',
    relatedWeakness: 'Redis持久化',
    bookmarked: false,
    completed: false
  },
  {
    id: 'r2', type: 'video',
    title: 'JVM垃圾收集器全解：CMS、G1、ZGC深度对比',
    summary: '系统讲解各代GC收集器的工作原理、调优参数与生产环境选型策略。',
    source: 'B站',
    tags: ['JVM', 'GC', 'Java后端'],
    readTime: '42分钟',
    difficulty: '高级',
    relatedWeakness: 'GC收集器',
    bookmarked: true,
    completed: false
  },
  {
    id: 'r3', type: 'book',
    title: 'Java核心技术手册：非常详细的探了各种为API和配置',
    summary: '深入帮助你理解Java核心框架的每一个细节，提升技术业准。',
    source: 'O\'Reilly',
    tags: ['Java', '核心', '书籍'],
    readTime: '习题杀手',
    difficulty: '高级',
    relatedWeakness: null,
    bookmarked: false,
    completed: false,
    url: null
  },
  {
    id: 'r4', type: 'article',
    title: '分布式事务：从2PC到Saga模式的演进与实战',
    summary: '对比2PC、TCC、消息队列最终一致性、Saga等主流方案，结合电商场景分析选型依据。',
    source: 'InfoQ',
    tags: ['分布式', '事务', 'Java后端'],
    readTime: '12分钟',
    difficulty: '高级',
    relatedWeakness: '分布式事务',
    bookmarked: false,
    completed: false
  },
  {
    id: 'r5', type: 'example',
    title: 'MySQL索引失效场景精讲：8种常见情况总结',
    summary: '列举8种导致索引失效的典型场景，搭配EXPLAIN执行计划分析，附面试高频追问解答。',
    source: 'AI面试助手',
    tags: ['MySQL', '索引', 'Java后端'],
    readTime: '15分钟',
    difficulty: '中级',
    relatedWeakness: 'MySQL索引优化',
    bookmarked: false,
    completed: false
  },
  {
    id: 'r6', type: 'video',
    title: 'Vue3响应式系统原理：Proxy与Reflect深度解析',
    summary: '从源码角度分析Vue3响应式系统的实现，对比Vue2 Object.defineProperty的局限性。',
    source: 'B站',
    tags: ['Vue3', '响应式', '前端'],
    readTime: '35分钟',
    difficulty: '中级',
    relatedWeakness: 'Vue3响应式原理',
    bookmarked: false,
    completed: false
  }
]

const MOCK_DAILY_PLAN = {
  date: new Date().toISOString().split('T')[0],
  tasks: [
    {
      id: 't1',
      title: '复习Redis持久化机制',
      desc: '重点掌握RDB快照触发条件和AOF重写机制',
      type: 'review',
      estimatedMinutes: 20,
      done: false,
      resourceId: 'r1'
    },
    {
      id: 't2',
      title: '完成3道GC相关练习题',
      desc: 'G1收集器的工作原理与调优参数',
      type: 'practice',
      estimatedMinutes: 15,
      done: true,
      resourceId: null
    },
    {
      id: 't3',
      title: '练习STAR结构化回答',
      desc: '针对"最有挑战性的项目"题型进行3次口头练习',
      type: 'exercise',
      estimatedMinutes: 25,
      done: false,
      resourceId: 'r3'
    }
  ]
}

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
  if (USE_MOCK) {
    await mockDelay(400)
    return MOCK_GROWTH_CURVE
  }

  try {
    // 从本地缓存获取 user_id
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[GrowthCurve] 未找到用户ID，降级为Mock')
      return MOCK_GROWTH_CURVE
    }

    // 并行请求：总分 + 5 个维度
    const dimIds = Object.keys(DIMENSION_ID_MAP) // ['1','2','3','4','5']
    const [overallRaw, ...dimRawList] = await Promise.all([
      request.get('/learning/growth-curve', { params: { user_id: userId } }),
      ...dimIds.map(did =>
        request.get('/learning/growth-curve', { params: { user_id: userId, dimension_id: did } })
      )
    ])

    // 组装 overall: [{label:'第1次', date:'3/6', score:82}, ...]
    const overall = (overallRaw || []).map((item, idx) => ({
      label: `第${idx + 1}次`,
      date: fmtDate(item.date),
      score: item.score
    }))

    // 组装 dimensions 与共享日期轴
    const dimensions = {}
    let dates = []      // 序号标签
    let realDates = []  // 真实日期
    dimIds.forEach((did, idx) => {
      const key = DIMENSION_ID_MAP[did]
      const raw = dimRawList[idx] || []
      dimensions[key] = raw.map(r => r.score)
      if (idx === 0 && raw.length) {
        dates = raw.map((r, i) => `第${i + 1}次`)
        realDates = raw.map(r => fmtDate(r.date))
      }
    })

    // 无任何数据时降级
    if (!overall.length && !dates.length) {
      console.warn('[GrowthCurve] 后端无成长数据，降级为Mock')
      return MOCK_GROWTH_CURVE
    }

    return { overall, dimensions, dates, realDates }
  } catch (err) {
    console.warn('[GrowthCurve] 请求失败，降级为Mock', err)
    return MOCK_GROWTH_CURVE
  }
}

/**
 * 获取薄弱知识点标签
 */
export const getWeaknessTags = async () => {
  if (USE_MOCK) {
    await mockDelay()
    return MOCK_WEAKNESSES
  }
  try {
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[Weaknesses] 未找到用户ID，降级为Mock')
      return MOCK_WEAKNESSES
    }
    const data = await request.get('/learning/weaknesses', { params: { user_id: userId } })
    if (!Array.isArray(data) || !data.length) return MOCK_WEAKNESSES
    // 后端 {tag_id, name, mastery_level} → 前端 {id, tag, level, mastery_level}
    return data.map((item, idx) => ({
      id: `w${item.tag_id || idx}`,
      tag: item.name,
      mastery_level: item.mastery_level,
      level: item.mastery_level < 40 ? 'high' : item.mastery_level < 70 ? 'medium' : item.mastery_level < 90 ? 'good' : 'excellent'
    }))
  } catch (err) {
    console.warn('[Weaknesses] 请求失败，降级为Mock', err)
    return MOCK_WEAKNESSES
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
  // 从 localStorage 中缓存的书签和完成信息
  const bookmarks = JSON.parse(localStorage.getItem('learning_bookmarks') || '{}')
  const completed = JSON.parse(localStorage.getItem('learning_completed') || '[]')

  if (USE_MOCK) {
    await mockDelay()
    return MOCK_RECOMMENDATIONS.map(item => ({
      ...item,
      bookmarked: bookmarks[item.id] || false,
      completed: completed.includes(item.id) || false
    }))
  }
  try {
    const cached = localStorage.getItem('ai_interview_user')
    const userId = cached ? (JSON.parse(cached).id || JSON.parse(cached).user_id) : null
    if (!userId) {
      console.warn('[Recommendations] 未找到用户ID，降级为Mock')
      return MOCK_RECOMMENDATIONS.map(item => ({
        ...item,
        bookmarked: bookmarks[item.id] || false,
        completed: completed.includes(item.id) || false
      }))
    }
    const data = await request.get('/learning/recommendations', {
      params: { user_id: userId, limit: 10 }
    })
    if (!Array.isArray(data) || !data.length) {
      const result = MOCK_RECOMMENDATIONS.map(item => ({
        ...item,
        bookmarked: bookmarks[item.id] || false,
        completed: completed.includes(item.id) || false
      }))
      _updateCacheWithList(result)
      return result
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
    console.warn('[Recommendations] 请求失败，降级为Mock', err)
    return MOCK_RECOMMENDATIONS
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
  if (USE_MOCK) {
    await mockDelay()
    return MOCK_DAILY_PLAN
  }
  return request.get('/learning/daily-plan')
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

  if (USE_MOCK) {
    await mockDelay(300)
    return { success: true }
  }
  // 可以了触发后端扣构端类型的接口，但可选
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

  if (USE_MOCK) {
    await mockDelay(300)
    return { success: true }
  }

  const userCached = localStorage.getItem('ai_interview_user')
  const userId = userCached ? (JSON.parse(userCached).id || JSON.parse(userCached).user_id) : null
  if (!userId) return { success: true }

  try {
    // 先调 start_learning
    await request.post('/learning/records/start', { user_id: userId, resource_id: resourceId })
    // 再调 finish_learning
    await request.post('/learning/records/finish', { user_id: userId, resource_id: resourceId })
    return { success: true }
  } catch (err) {
    // 失败时保留 localStorage 的标记
    return { success: true }
  }
}

/**
 * 更新每日计划任务状态
 * @param {string} taskId - 任务ID
 * @param {boolean} done - 完成状态
 */
export const updateTaskStatus = async (taskId, done) => {
  if (USE_MOCK) {
    await mockDelay(300)
    return { success: true }
  }
  return request.post(`/learning/tasks/${taskId}/status`, { done })
}