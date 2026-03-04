// =============================================
// 学习中心相关 API
// =============================================

import request from '@/utils/request'
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'
const mockDelay = (ms = 600) => new Promise(resolve => setTimeout(resolve, ms))

// ---- Mock 数据 ----

const MOCK_GROWTH_CURVE = {
  // 综合得分折线
  overall: [
    { date: '11/25', score: 58 },
    { date: '12/01', score: 63 },
    { date: '12/05', score: 67 },
    { date: '12/10', score: 70 },
    { date: '12/15', score: 70 },
    { date: '12/18', score: 75 },
    { date: '12/20', score: 82 }
  ],
  // 各维度折线（最近5次）
  dimensions: {
    technical:    [65, 70, 74, 78, 85],
    logic:        [60, 65, 68, 72, 78],
    matching:     [72, 75, 78, 82, 88],
    expression:   [55, 60, 64, 68, 72],
    adaptability: [58, 63, 68, 72, 80]
  },
  dates: ['12/01', '12/05', '12/10', '12/18', '12/20']
}

const MOCK_WEAKNESSES = [
  { id: 'w1', tag: 'Redis持久化', level: 'high', jobId: 'java-backend' },
  { id: 'w2', tag: 'GC收集器', level: 'high', jobId: 'java-backend' },
  { id: 'w3', tag: '表达结构化', level: 'high', jobId: null },
  { id: 'w4', tag: '分布式事务', level: 'medium', jobId: 'java-backend' },
  { id: 'w5', tag: '性能调优', level: 'medium', jobId: 'java-backend' },
  { id: 'w6', tag: 'Vue3响应式原理', level: 'medium', jobId: 'web-frontend' },
  { id: 'w7', tag: 'Webpack配置', level: 'low', jobId: 'web-frontend' },
  { id: 'w8', tag: '算法复杂度', level: 'low', jobId: 'python-algorithm' },
  { id: 'w9', tag: 'MySQL索引优化', level: 'medium', jobId: 'java-backend' },
  { id: 'w10', tag: 'STAR回答法', level: 'low', jobId: null }
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
    id: 'r3', type: 'practice',
    title: '面试结构化表达专题：STAR法则实战训练',
    summary: '通过10道经典情景题练习STAR法则，提升回答逻辑性与说服力，附优秀答案范例。',
    source: 'AI面试助手',
    tags: ['表达技巧', '通用能力'],
    readTime: '20分钟',
    difficulty: '初级',
    relatedWeakness: '表达结构化',
    bookmarked: false,
    completed: false
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

// ---- API 函数 ----

/**
 * 获取能力成长曲线数据
 * @param {string} dimension - 'overall' | 'technical' | 'logic' | 'matching' | 'expression' | 'adaptability'
 */
export const getGrowthCurve = async (dimension = 'overall') => {
  if (USE_MOCK) {
    await mockDelay(400)
    return MOCK_GROWTH_CURVE
  }
  return request.get('/v1/learning/growth-curve', { params: { dimension } })
}

/**
 * 获取技能短板列表
 */
export const getWeaknesses = async () => {
  if (USE_MOCK) {
    await mockDelay(300)
    return MOCK_WEAKNESSES
  }
  return request.get('/v1/learning/weaknesses')
}

/**
 * 获取个性化推荐资源列表
 * @param {Object} params - { type, jobId, page, pageSize }
 */
export const getRecommendations = async (params = {}) => {
  if (USE_MOCK) {
    await mockDelay(500)
    let list = [...MOCK_RECOMMENDATIONS]
    if (params.type && params.type !== 'all') {
      list = list.filter(r => r.type === params.type)
    }
    return { list, total: list.length }
  }
  return request.get('/v1/learning/recommendations', { params })
}

/**
 * 收藏/取消收藏资源
 * @param {string} resourceId
 * @param {boolean} bookmarked
 */
export const toggleBookmark = async (resourceId, bookmarked) => {
  if (USE_MOCK) {
    await mockDelay(200)
    return { resourceId, bookmarked }
  }
  return request.post(`/v1/learning/resources/${resourceId}/bookmark`, { bookmarked })
}

/**
 * 标记资源已完成
 * @param {string} resourceId
 */
export const markCompleted = async (resourceId) => {
  if (USE_MOCK) {
    await mockDelay(200)
    return { resourceId, completed: true }
  }
  return request.post(`/v1/learning/resources/${resourceId}/complete`)
}

/**
 * 获取今日学习计划
 */
export const getDailyPlan = async () => {
  if (USE_MOCK) {
    await mockDelay(300)
    return MOCK_DAILY_PLAN
  }
  return request.get('/v1/learning/daily-plan')
}

/**
 * 更新每日任务完成状态
 * @param {string} taskId
 * @param {boolean} done
 */
export const updateTaskStatus = async (taskId, done) => {
  if (USE_MOCK) {
    await mockDelay(200)
    return { taskId, done }
  }
  return request.patch(`/v1/learning/tasks/${taskId}`, { done })
}