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
    voice_mode: !!data.voiceMode
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


/**
 * 发送回答，获取下一题或追问
 * @param {string} sessionId
 * @param {string} answer - 用户回答文本
 * @returns {Promise<{ nextQuestion, isFinished, questionIndex }>}
 */
export const sendAnswer = async (sessionId, answer) => {
  return request.post(`/interviews/${sessionId}/answer`, { answer })
}


// ---- 新增：SSE 流式聊天（替换原 sendAnswer）----
// 原 sendAnswer 返回 { reply, nextQuestion, isFinished }
// 后端是 SSE 流，通过 fetch 手动处理，检测 [INTERVIEW_OVER] 标记
// api/interview.js  sendAnswerStream
export const sendAnswerStream = (sessionId, answer, { onChunk, onFinish, onStreamEnd, onError, onAudio, voiceMode = false }) => {
  const API_BASE = process.env.VUE_APP_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('ai_interview_token')

  fetch(`${API_BASE}/interviews/${sessionId}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ answer, voice_mode: !!voiceMode })
  }).then(async (response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''       // ✅ 用 buffer 拼接不完整的 SSE 行
    let fullText = ''
    let isOver = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // ✅ 把本次字节追加到 buffer，而不是直接 split
      buffer += decoder.decode(value, { stream: true })

      // 按完整行切割，保留末尾不完整的部分留到下次
      const lines = buffer.split('\n')
      buffer = lines.pop()   // 最后一段可能不完整，留给下次

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const json = JSON.parse(line.slice(6))
          const chunk = json.chunk || ''
          fullText += chunk

          // ✅ 处理音频数据（如果有）
          if (json.audio_b64 && onAudio) {
            onAudio(json.audio_b64)
          }

          // ✅ 用 fullText 判断，不再用单个 chunk
          if (!isOver && fullText.includes('[INTERVIEW_OVER]')) {
            isOver = true
            // 把干净内容（去掉标记）推给 UI
            const cleanChunk = chunk.replace('[INTERVIEW_OVER]', '')
            if (cleanChunk) onChunk(cleanChunk)
            setTimeout(() => { onFinish && onFinish() }, 3000)
            return  // 提前退出，不再触发 onStreamEnd
          }

          if (!isOver) {
            onChunk(chunk)
          }
        } catch { /* JSON 解析失败跳过 */ }
      }
    }

    if (!isOver) {
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


// ---- uploadAudio（新增，对接 ASR）----
export const uploadAudio = async (audioBlob) => {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.wav')
  const res = await request.post('/interviews/upload-audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
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