// =============================================
// frontend/src/api/interview.js
// 面试相关 API
// Mock数据支持完整面试流程
// =============================================

import request from '@/utils/request'

const mockDelay = (ms = 700) => new Promise(resolve => setTimeout(resolve, ms))
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'


/**
 * 开始面试
 * @param {Object} data - { jobId, questionCount, timeLimit }
 * @returns {Promise<{ sessionId, firstQuestion, isFinished }>}
 */
export const startInterview = async (data) => {
  const res = await request.post('/interviews/start', {
    user_id: data.userId,   // 暂时从 data 传入，待JWT完善后从拦截器注入
    job_id: data.jobDbId,
    resume_id: data.resumeId,
    voice_mode: !!data.voiceMode,
    interview_style: data.interviewStyle,
    interview_round: data.interviewRound || data.sessionConfig?.interview_round || data.sessionConfig?.round || null,
    target_source: data.interviewSource || data.sessionConfig?.target_source || '通用',
    profile_id: data.profileId || null,
    session_config: data.sessionConfig || null,
    voice_role: data.voiceRole,
    voice: data.voice || null
  }, {
    timeout: 60000  // 单独设置 60 秒，确保 TTS 初始化和音频生成有充足时间
  })
  // 响应拦截器已解包，res 就是后端返回的 data 对象
  // 统一适配为前端期望的格式
  return {
    sessionId: String(res.interview_id),
    firstQuestion: res.question,
    firstQuestionAudio: res.audio_b64 || null,
    isFinished: false
  }
}

export const fetchInterviewProfiles = async (jobId) => {
  const res = await request.get('/interviews/profiles', {
    params: { job_id: jobId }
  })
  return res?.list || []
}

export const fetchInterviewSourceOptions = async (jobId) => {
  const res = await request.get('/interviews/source-options', {
    params: { job_id: jobId }
  })
  return Array.isArray(res) ? res : []
}


/**
 * 发送回答，获取下一题或追问
 * @param {string} sessionId
 * @param {string} answer - 用户回答文本
 * @returns {Promise<{ nextQuestion, isFinished, questionIndex }>}
 */
export const sendAnswer = async (sessionId, answer) => {
  return request.post(`/interviews/${sessionId}/answer`, { answer })
}

/**
 * 语音面试专用接口（SSE流式）
 * @param {string} sessionId - 面试ID
 * @param {string} answer - ASR识别后的文本
 * @param {Object} callbacks - 回调函数
 * @param {Function} callbacks.onChunk - 文本分片回调
 * @param {Function} callbacks.onFinish - 面试结束回调
 * @param {Function} callbacks.onStreamEnd - 流结束回调
 * @param {Function} callbacks.onError - 错误回调
 * @param {Function} callbacks.onAudio - TTS音频回调
 * @param {string} callbacks.voice - 音色名称
 */
export const sendVoiceAnswerStream = (sessionId, answer, { onChunk, onFinish, onStreamEnd, onError, onAudio, voice = null }) => {
  const API_BASE = process.env.VUE_APP_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('ai_interview_token')

  const readErrorMessage = async (response) => {
    const contentType = response.headers.get('content-type') || ''
    try {
      if (contentType.includes('application/json')) {
        const data = await response.clone().json()
        return data?.message || data?.msg || data?.error || `请求失败（${response.status}）`
      }

      const text = await response.clone().text()
      return text?.trim() || `请求失败（${response.status}）`
    } catch (err) {
      return `请求失败（${response.status}）`
    }
  }

  // ✅ 使用专用的语音面试接口
  fetch(`${API_BASE}/interviews/${sessionId}/voice-chat/stream`, {
    method: 'POST',
    headers: {
      'Accept': 'text/event-stream',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    cache: 'no-store',
    body: JSON.stringify({ answer, voice: voice || null })
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(await readErrorMessage(response))
    }

    if (!response.body) {
      throw new Error('服务器未返回可读取的流响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let isOver = false

    const handleSseEvent = (rawEvent) => {
      if (!rawEvent) return

      const dataLines = rawEvent
        .split('\n')
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart())

      if (!dataLines.length) return

      try {
        const json = JSON.parse(dataLines.join('\n'))
        const chunk = json.chunk || ''
        fullText += chunk

        // ✅ 处理TTS音频
        if (json.audio_b64 && onAudio) {
          onAudio(json.audio_b64)
        }

        // ✅ 检测面试结束标记
        if (!isOver && fullText.includes('[INTERVIEW_OVER]')) {
          isOver = true
          const cleanChunk = chunk.replace('[INTERVIEW_OVER]', '')
          if (cleanChunk && onChunk) onChunk(cleanChunk)
          return
        }

        if (!isOver && chunk && onChunk) {
          onChunk(chunk)
        }
      } catch {
        // 忽略无法解析的事件，保证主流不中断
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')

      let delimiterIndex = buffer.indexOf('\n\n')
      while (delimiterIndex !== -1) {
        const rawEvent = buffer.slice(0, delimiterIndex)
        buffer = buffer.slice(delimiterIndex + 2)
        handleSseEvent(rawEvent)
        delimiterIndex = buffer.indexOf('\n\n')
      }
    }

    const tail = decoder.decode()
    if (tail) {
      buffer += tail.replace(/\r\n/g, '\n')
    }

    if (buffer.trim()) {
      handleSseEvent(buffer)
    }

    if (isOver) {
      onFinish && onFinish()
    } else {
      onStreamEnd && onStreamEnd()
    }
  }).catch(onError)
}


// ---- 新增：SSE 流式聊天（替换原 sendAnswer）----
// 原 sendAnswer 返回 { reply, nextQuestion, isFinished }
// 后端是 SSE 流，通过 fetch 手动处理，检测 [INTERVIEW_OVER] 标记
// api/interview.js  sendAnswerStream
export const sendAnswerStream = (sessionId, answer, { onChunk, onFinish, onStreamEnd, onError, onAudio, voiceMode = false, voice = null }) => {
  const API_BASE = process.env.VUE_APP_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('ai_interview_token')

  const readErrorMessage = async (response) => {
    const contentType = response.headers.get('content-type') || ''
    try {
      if (contentType.includes('application/json')) {
        const data = await response.clone().json()
        return data?.message || data?.msg || data?.error || `请求失败（${response.status}）`
      }

      const text = await response.clone().text()
      return text?.trim() || `请求失败（${response.status}）`
    } catch (err) {
      return `请求失败（${response.status}）`
    }
  }

  fetch(`${API_BASE}/interviews/${sessionId}/chat/stream`, {
    method: 'POST',
    headers: {
      'Accept': 'text/event-stream',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    cache: 'no-store',
    body: JSON.stringify({ answer, voice_mode: !!voiceMode, voice: voice || null })
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(await readErrorMessage(response))
    }

    if (!response.body) {
      throw new Error('服务器未返回可读取的流响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let isOver = false

    const handleSseEvent = (rawEvent) => {
      if (!rawEvent) return

      const dataLines = rawEvent
        .split('\n')
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart())

      if (!dataLines.length) return

      try {
        const json = JSON.parse(dataLines.join('\n'))
        const chunk = json.chunk || ''
        fullText += chunk

        if (json.audio_b64 && onAudio) {
          onAudio(json.audio_b64)
        }

        if (!isOver && fullText.includes('[INTERVIEW_OVER]')) {
          isOver = true
          const cleanChunk = chunk.replace('[INTERVIEW_OVER]', '')
          if (cleanChunk && onChunk) onChunk(cleanChunk)
          return
        }

        if (!isOver && chunk && onChunk) {
          onChunk(chunk)
        }
      } catch {
        // 忽略无法解析的事件，保证主流不中断
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')

      let delimiterIndex = buffer.indexOf('\n\n')
      while (delimiterIndex !== -1) {
        const rawEvent = buffer.slice(0, delimiterIndex)
        buffer = buffer.slice(delimiterIndex + 2)
        handleSseEvent(rawEvent)
        delimiterIndex = buffer.indexOf('\n\n')
      }
    }

    const tail = decoder.decode()
    if (tail) {
      buffer += tail.replace(/\r\n/g, '\n')
    }

    if (buffer.trim()) {
      handleSseEvent(buffer)
    }

    if (isOver) {
      onFinish && onFinish()
    } else {
      onStreamEnd && onStreamEnd()
    }
  }).catch(onError)
}

/**
 * 主动结束面试
 * @param {string} sessionId
 * @returns {Promise<{ reportId }>}
 */
export const finishInterview = async (sessionId) => {

  // const res = await request.post(`/interviews/${sessionId}/finish`)
  const res = await request.post(`/interviews/${sessionId}/finish`, {}, {
    timeout: 120000  // ← 单独给这个接口设置 120 秒，覆盖全局的 15 秒
  })
  // 把后端报告存到 sessionStorage，供报告页读取（后端暂无 GET /report/:id 接口）
  sessionStorage.setItem(`report_${sessionId}`, JSON.stringify(res.data))

  return { reportId: res.reportId || sessionId }
}
/**
 * 获取面试历史列表（用于历史记录页）
 * @param {Object} params - { page, pageSize, jobId }
 */
export const getInterviewList = async (params = {}) => {
  return request.get('/interviews', { params })
}


// ---- uploadAudio（对接 ASR）----
// 注意：Whisper 模型在 CPU 上运行，首次调用时需加载模型，耗时可能超过 15s。
// 这里单独设置 timeout: 60000（60秒），覆盖全局的 15s，避免超时报错。
export const uploadAudio = async (audioBlob) => {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.wav')
  const res = await request.post('/interviews/upload-audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000  // ASR 单独设置 60s 超时，Whisper CPU 推理首次加载较慢
  })
  console.log('ASR识别结果：', res)
  return res
}


/**
 * 检测当前用户简历是否已填写
 * @returns {Promise<{ has_resume: boolean, warning: string|null }>}
 */
export const checkResume = async () => {
  return request.get('/interviews/check-resume')
}
