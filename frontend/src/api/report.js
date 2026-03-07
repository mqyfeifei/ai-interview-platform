// =============================================
// frontend/src/api/report.js
// 报告相关 API
// =============================================

import request from '@/utils/request'
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'
const mockDelay = (ms = 800) => new Promise(resolve => setTimeout(resolve, ms))

// Mock 完整报告数据
const buildMockReport = (reportId) => ({
  id: reportId,
  sessionId: 'mock_session',
  jobId: 'java-backend',
  jobName: 'Java后端开发',
  totalScore: 82,
  duration: 1840, // 秒
  createdAt: new Date().toISOString(),

  // 五维雷达图数据（0-100）
  dimensions: {
    technical: 85,    // 技术正确性
    logic: 78,        // 逻辑严谨性
    matching: 88,     // 岗位匹配度
    expression: 72,   // 表达沟通
    adaptability: 80  // 应变能力
  },

  // 平均水平（用于雷达图对比）
  avgDimensions: {
    technical: 70,
    logic: 68,
    matching: 72,
    expression: 66,
    adaptability: 65
  },

  // 亮点
  highlights: [
    '对JVM内存模型（堆/栈/方法区/程序计数器）的描述准确且完整',
    'Spring Boot自动配置原理阐述清晰，提到了@EnableAutoConfiguration和SPI机制',
    '回答分布式事务时主动比较了2PC、TCC和Saga，体现了系统性思维',
    'MySQL索引回答中准确区分了聚簇索引和非聚簇索引'
  ],

  // 待改进点
  improvements: [
    { point: '回答缺乏结构化，建议使用"首先/其次/最后"等连接词', resource: 'STAR法则表达技巧' },
    { point: 'Redis持久化机制（RDB vs AOF）的描述不够准确，混淆了两者的触发方式', resource: 'Redis持久化深度解析' },
    { point: '对GC收集器（G1/ZGC/CMS）的适用场景区分不够清晰', resource: 'JVM垃圾收集器对比' },
    { point: '回答性能优化问题时缺乏具体的量化指标', resource: '性能优化方法论' }
  ],

  // 逐题详情
  questions: [
    {
      id: 1,
      question: '请先做个自我介绍，重点介绍你的Java相关技术背景。',
      answer: '我叫张三，是北京大学计算机专业大三学生。熟悉Java SE、Spring Boot、MyBatis等后端技术栈，有两年的项目经验，主要做过电商和社区类系统的后端开发。对JVM调优和高并发有一定了解，平时喜欢研究开源项目。',
      score: 88,
      comment: '自我介绍完整，技术背景清晰，但可以更多强调核心技术深度和典型项目成果。',
      isFollowUp: false
    },
    {
      id: 2,
      question: '请介绍一下JVM内存模型，各区域分别存储什么内容？',
      answer: '堆存放对象实例，栈存放局部变量和方法调用，方法区（元空间）存放类信息、常量池，程序计数器记录当前线程执行位置，本地方法栈用于native方法。',
      score: 85,
      comment: '各区域描述基本正确，但未提及直接内存（Direct Memory）和逃逸分析，可进一步深化。',
      isFollowUp: false
    },
    {
      id: 3,
      question: '能讲讲GC垃圾回收机制吗？常用的收集器有哪些？',
      answer: 'GC主要分为Minor GC和Full GC。收集器有Serial、Parallel、CMS、G1等。G1适合低延迟场景，CMS是并发收集器但会有内存碎片问题。',
      score: 75,
      comment: '覆盖了主流收集器，但对各收集器的适用场景和ZGC/Shenandoah等新一代收集器没有提及。',
      isFollowUp: false
    },
    {
      id: 4,
      question: '你提到了JVM，在生产环境中你是如何进行JVM调优的？',
      answer: '主要通过jstat、jmap、jstack等工具分析内存使用和线程状态，然后调整-Xmx、-Xms参数。遇到OOM会dump heap分析对象引用。',
      score: 78,
      comment: '提到了常用诊断工具，但缺乏具体的调优案例和参数调整依据说明。',
      isFollowUp: true
    },
    {
      id: 5,
      question: 'Spring Boot的自动配置原理是什么？',
      answer: '@SpringBootApplication包含@EnableAutoConfiguration，它通过SpringFactoriesLoader读取META-INF/spring.factories文件，加载各种AutoConfiguration类，再通过@Conditional注解按条件装配Bean。',
      score: 90,
      comment: '原理描述准确，SPI机制和条件装配都点到了，是本次面试的亮点回答之一。',
      isFollowUp: false
    },
    {
      id: 6,
      question: 'Redis的数据类型有哪些？你在项目中是如何使用Redis做缓存的？',
      answer: '有String、Hash、List、Set、ZSet，还有BitMap和HyperLogLog。我在项目中用String缓存用户Session，用ZSet做排行榜，用Hash存商品详情。',
      score: 82,
      comment: '数据类型覆盖全面，应用场景举例具体，但未提及缓存穿透/击穿/雪崩的防护策略。',
      isFollowUp: false
    },
    {
      id: 7,
      question: '你提到了Redis，能具体说说它的持久化机制RDB和AOF的区别吗？',
      answer: 'RDB是定时快照，AOF记录每次写操作。RDB恢复快但可能丢数据，AOF更安全但文件大。',
      score: 65,
      comment: 'RDB和AOF基本概念理解正确，但触发方式描述不够准确，AOF重写机制和混合持久化未提及。',
      isFollowUp: true
    },
    {
      id: 8,
      question: '请讲讲你对分布式事务的理解，以及常见的解决方案有哪些？',
      answer: '分布式事务是跨库或跨服务的数据一致性问题。常见方案有2PC（两阶段提交），TCC（Try-Confirm-Cancel），还有基于消息队列的最终一致性方案，以及Saga模式。',
      score: 86,
      comment: '系统性地列举了多种方案，并能区分强一致性和最终一致性，表现出色。',
      isFollowUp: false
    },
    {
      id: 9,
      question: 'MySQL的索引类型有哪些？B+树索引和Hash索引分别适合什么场景？',
      answer: 'B+树适合范围查询和排序，Hash索引只适合等值查询。B+树是InnoDB默认，Hash是Memory引擎用的。聚簇索引和非聚簇索引的区别在于数据和索引是否存在一起。',
      score: 84,
      comment: '准确区分了两种索引类型，聚簇索引的补充说明加分，但可以再提联合索引的最左匹配原则。',
      isFollowUp: false
    },
    {
      id: 10,
      question: '你在项目中遇到过最有挑战性的技术问题是什么？如何解决的？',
      answer: '之前做电商系统时遇到了库存超卖问题。我们通过Redis分布式锁加乐观锁双重保障，配合数据库事务来解决，同时加了消息队列削峰，最终将下单失败率从5%降到了0.01%。',
      score: 88,
      comment: 'STAR结构完整，有具体的量化数据（5%→0.01%），技术方案也合理，是本次面试较好的回答。',
      isFollowUp: false
    }
  ]
})

/**
 * 获取面试报告详情
 * @param {string} reportId
 */
// 替换 getReport 函数
export const getReport = async (reportId) => {
  if (USE_MOCK) {
    await mockDelay(1000)
    return buildMockReport(reportId)
  }
  // 优先从 sessionStorage 读取（由 finishInterview 写入）
  // const cached = sessionStorage.getItem(`report_${reportId}`)
  // if (cached) {
  //   return adaptBackendReport(JSON.parse(cached), reportId)
  // }
  // // 若缓存不存在（如页面刷新后），暂时返回空报告，待后端提供 GET 接口后补充
  // throw new Error('报告数据不存在，请勿刷新报告页面')
  const res = await request.get(`/reports/${reportId}`)
  return res
}


/**
 * 获取历史面试列表
 * @param {Object} params - { page, pageSize, jobId }
 */
export const getHistoryList = async (params = {}) => {
  if (USE_MOCK) {
    await mockDelay()
    return {
      list: [
        { id: 'r1', jobId: 'java-backend', jobName: 'Java后端开发', totalScore: 82, duration: 1840, questionCount: 10, createdAt: '2024-12-20T14:30:00Z' },
        { id: 'r2', jobId: 'web-frontend', jobName: 'Web前端开发', totalScore: 75, duration: 1620, questionCount: 8, createdAt: '2024-12-18T10:00:00Z' },
        { id: 'r3', jobId: 'java-backend', jobName: 'Java后端开发', totalScore: 70, duration: 1500, questionCount: 10, createdAt: '2024-12-15T09:15:00Z' },
        { id: 'r4', jobId: 'python-algorithm', jobName: 'Python算法工程师', totalScore: 68, duration: 1380, questionCount: 7, createdAt: '2024-12-10T16:00:00Z' }
      ],
      total: 4
    }
  }
  return request.get('/reports', { params })
}

/**
 * 获取单个报告详情
 * @param {string} reportId - 报告ID
 */
export const getReportDetail = async (reportId) => {
  if (USE_MOCK) {
    await mockDelay()
    return buildMockReport(reportId)
  }
  return request.get(`/reports/${reportId}`)
}

// 在文件末尾加适配函数
const adaptBackendReport = (raw, reportId) => ({
  id: reportId,
  jobName: '模拟面试',   // 后端finish接口暂未返回jobName，待后端补充
  totalScore: raw.total_score,
  duration: null,        // 后端存在 used_time 字段，待 GET 接口补充
  createdAt: new Date().toISOString(),
  // 维度映射：后端用中文key，前端用英文key
  dimensions: {
    technical: raw.dimensions?.['技术正确性']?.score ?? 0,
    logic: raw.dimensions?.['逻辑严谨性']?.score ?? 0,
    matching: raw.dimensions?.['岗位匹配度']?.score ?? 0,
    expression: raw.dimensions?.['表达沟通']?.score ?? 0,
    adaptability: raw.dimensions?.['应变能力']?.score ?? 0
  },
  avgDimensions: { technical: 70, logic: 68, matching: 72, expression: 66, adaptability: 65 },
  // highlights/improvements 后端返回字符串，前端期望数组
  highlights: (raw.highlights || '').split('\n').filter(Boolean),
  improvements: (raw.improvements || '').split('\n').filter(Boolean).map(text => ({ text, resourceLink: null })),
  suggestions: raw.suggestions,
  questions: []  // 后端 finish 接口暂不返回题目列表，报告页题目回顾留空待后端补充 GET /report/:id 接口
})


