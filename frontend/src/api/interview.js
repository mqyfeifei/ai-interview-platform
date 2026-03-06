// =============================================
// frontend/src/api/interview.js
// 面试相关 API
// Mock数据支持完整面试流程
// =============================================

import request from '@/utils/request'

const mockDelay = (ms = 700) => new Promise(resolve => setTimeout(resolve, ms))
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'

// Mock 题库 - 按岗位分类
const MOCK_QUESTION_BANKS = {
  'java-backend': [
    '请先做个自我介绍，重点介绍你的Java相关技术背景。',
    '请介绍一下JVM内存模型，各区域分别存储什么内容？',
    '你提到了JVM，能讲讲GC垃圾回收机制吗？常用的收集器有哪些？',
    'Spring Boot的自动配置原理是什么？@SpringBootApplication注解做了哪些事？',
    'MyBatis的一级缓存和二级缓存有什么区别？如何禁用二级缓存？',
    'Redis的数据类型有哪些？你在项目中是如何使用Redis做缓存的？',
    '请讲讲你对分布式事务的理解，以及常见的解决方案有哪些？',
    'MySQL的索引类型有哪些？B+树索引和Hash索引分别适合什么场景？',
    '如果一个接口响应很慢，你会从哪些方面进行排查和优化？',
    '你在项目中遇到过最有挑战性的技术问题是什么？如何解决的？'
  ],
  'web-frontend': [
    '请先做个自我介绍，介绍一下你的前端技术栈。',
    'Vue3和Vue2相比有哪些重大变化？Composition API解决了什么问题？',
    '请解释一下浏览器从输入URL到页面渲染完成的全过程。',
    '什么是虚拟DOM？Vue的diff算法是如何工作的？',
    '如何优化前端页面的性能？请从网络、渲染、代码等多个维度来说。',
    'Promise、async/await和Generator有什么区别和联系？',
    'CSS的BFC是什么？哪些情况下会创建BFC？有什么用途？',
    'Webpack的构建流程是怎样的？loader和plugin有什么区别？',
    '如何实现前端的权限控制？请结合Vue Router讲一讲。',
    '你做过哪些印象最深的前端性能优化项目？效果如何？'
  ],
  'python-algorithm': [
    '请先做个自我介绍，重点介绍你的算法和机器学习背景。',
    '请解释一下Python中的GIL（全局解释器锁），它有什么影响？',
    '快速排序的平均时间复杂度是多少？最坏情况如何优化？',
    '请介绍一下你对梯度下降算法的理解，以及常见优化器的区别。',
    'Pandas中如何高效处理大数据集？有哪些性能优化技巧？',
    '什么是过拟合？如何防止？正则化和Dropout有什么区别？',
    '请解释一下反向传播算法的原理。',
    '如何设计一个推荐系统？请描述整体架构和关键技术点。',
    'Python的装饰器原理是什么？如何用装饰器实现缓存功能？',
    '你做过最有挑战性的机器学习项目是什么？遇到了哪些问题？'
  ],
  'default': [
    '请先做个自我介绍。',
    '请描述一下你最近做的一个项目，你在其中承担了哪些工作？',
    '你是如何学习新技术的？能举个例子吗？',
    '你认为团队协作中最重要的是什么？',
    '你遇到过技术难题时是怎么处理的？请举一个具体的例子。',
    '你对这个岗位的理解是什么？为什么选择这个方向？',
    '如果项目需求临时变更，你会如何应对？',
    '你平时如何保持技术学习的积极性？',
    '你有什么职业规划？未来3-5年希望达到什么水平？',
    '你还有什么想问我的吗？'
  ]
}

// 动态追问逻辑 Mock
const FOLLOW_UP_TRIGGERS = [
  { keywords: ['Redis', 'redis'], followUp: '你提到了Redis，能具体说说它的持久化机制RDB和AOF的区别吗？' },
  { keywords: ['Vue3', 'vue3', 'Composition'], followUp: '你提到了Composition API，能说说它相比Options API在大型项目中的优势吗？' },
  { keywords: ['JVM', 'jvm', 'GC'], followUp: '你提到了JVM，在生产环境中你是如何进行JVM调优的？' },
  { keywords: ['MySQL', 'mysql', '索引'], followUp: '关于MySQL索引，你能说说索引失效的常见情况有哪些吗？' },
  { keywords: ['微服务', '分布式'], followUp: '你提到了微服务，能说说服务间调用如何处理网络超时和熔断降级吗？' },
  { keywords: ['Docker', 'K8s', 'kubernetes'], followUp: '你提到了容器化，能说说K8s中Pod的生命周期管理吗？' }
]

/**
 * 开始面试
 * @param {Object} data - { jobId, questionCount, timeLimit }
 * @returns {Promise<{ sessionId, firstQuestion, totalQuestions }>}
 */
export const startInterview = async (data) => {
  if (USE_MOCK) {
    await mockDelay()
    const questions = MOCK_QUESTION_BANKS[data.jobId] || MOCK_QUESTION_BANKS['default']
    const sessionId = 'mock_session_' + Date.now()
    // 把题目列表存进 sessionStorage 供后续 mock 使用
    sessionStorage.setItem(sessionId, JSON.stringify({ questions, index: 0, jobId: data.jobId }))
    return {
      sessionId,
      firstQuestion: questions[0],
      totalQuestions: data.questionCount || 10
    }
  }
  const res = await request.post('/interviews/start', {
    user_id: data.userId,   // 整数，来自 userInfo.id
    job_id: data.jobDbId    // 整数，来自数据库 jobs.id
  })
  return {
    sessionId: String(res.interview_id),
    firstQuestion: res.question,
    isFinished: false
  }
}


/**
 * 发送回答，获取下一题或追问
 * @param {string} sessionId
 * @param {string} answer - 用户回答文本
 * @returns {Promise<{ nextQuestion, isFinished, questionIndex }>}
 */
export const sendAnswer = async (sessionId, answer) => {
  if (USE_MOCK) {
    await mockDelay(1400)
    const raw = sessionStorage.getItem(sessionId)
    if (!raw) return { nextQuestion: '感谢你的回答。', isFinished: true }

    const session = JSON.parse(raw)
    session.index += 1

    // 检测追问触发词
    const followUp = FOLLOW_UP_TRIGGERS.find(t =>
      t.keywords.some(kw => answer.includes(kw))
    )
    if (followUp && Math.random() > 0.4) {
      sessionStorage.setItem(sessionId, JSON.stringify(session))
      return { nextQuestion: followUp.followUp, isFinished: false, questionIndex: session.index, isFollowUp: true }
    }

    if (session.index >= session.questions.length) {
      sessionStorage.removeItem(sessionId)
      return { nextQuestion: '好的，面试到此结束，感谢你的参与！请稍等，我来为你生成报告。', isFinished: true, questionIndex: session.index }
    }

    sessionStorage.setItem(sessionId, JSON.stringify(session))
    return {
      nextQuestion: session.questions[session.index],
      isFinished: false,
      questionIndex: session.index
    }
  }
  return request.post(`/v1/interviews/${sessionId}/answer`, { answer })
}


// ---- 新增：SSE 流式聊天（替换原 sendAnswer）----
// 原 sendAnswer 返回 { reply, nextQuestion, isFinished }
// 后端是 SSE 流，通过 fetch 手动处理，检测 [INTERVIEW_OVER] 标记
export const sendAnswerStream = (sessionId, answer, { onChunk, onFinish, onError }) => {
  const API_BASE = process.env.VUE_APP_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('ai_interview_token')

  fetch(`${API_BASE}/interviews/${sessionId}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ answer })
  }).then(async (response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const rawChunk = decoder.decode(value, { stream: true })
      // SSE 格式: "data: {...}\n\n"
      const lines = rawChunk.split('\n').filter(l => l.startsWith('data: '))
      for (const line of lines) {
        try {
          const json = JSON.parse(line.slice(6))
          const chunk = json.chunk || ''
          fullText += chunk

          if (chunk.includes('[INTERVIEW_OVER]')) {
            // 检测到结束标记，通知组件
            onChunk(chunk.replace('[INTERVIEW_OVER]', ''))
            onFinish()
            return
          } else {
            onChunk(chunk)
          }
        } catch {}
      }
    }
    // 流正常结束但没有 [INTERVIEW_OVER]（继续追问）
    // 不调用 onFinish，等下一轮
  }).catch(onError)
}

/**
 * 主动结束面试
 * @param {string} sessionId
 * @returns {Promise<{ reportId }>}
 */
export const finishInterview = async (sessionId) => {
  if (USE_MOCK) {
    await mockDelay(2000)
    sessionStorage.removeItem(sessionId)
    return { reportId: 'mock_report_' + Date.now() }
  }

  const res = await request.post(`/interviews/${sessionId}/finish`)
  // 把后端报告存到 sessionStorage，供报告页读取（后端暂无 GET /report/:id 接口）
  sessionStorage.setItem(`report_${sessionId}`, JSON.stringify(res.data))
  return { reportId: sessionId }
}
/**
 * 获取面试历史列表（用于历史记录页）
 * @param {Object} params - { page, pageSize, jobId }
 */
export const getInterviewList = async (params = {}) => {
  if (USE_MOCK) {
    await mockDelay()
    return {
      list: [
        { id: 'r1', jobId: 'java-backend', jobName: 'Java后端开发', totalScore: 82, duration: 1840, createdAt: '2024-12-20T14:30:00Z' },
        { id: 'r2', jobId: 'web-frontend', jobName: 'Web前端开发', totalScore: 75, duration: 1620, createdAt: '2024-12-18T10:00:00Z' },
        { id: 'r3', jobId: 'java-backend', jobName: 'Java后端开发', totalScore: 70, duration: 1500, createdAt: '2024-12-15T09:15:00Z' }
      ],
      total: 3
    }
  }
  return request.get('/v1/interviews', { params })
}


// ---- uploadAudio（新增，对接 ASR）----
export const uploadAudio = async (audioBlob) => {
  if (USE_MOCK) {
    await mockDelay(800)
    return { text: '（语音识别暂时不可用，请使用文字输入）' }
  }
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.wav')
  const res = await request.post('/interviews/upload-audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}