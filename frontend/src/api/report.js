// =============================================
// frontend/src/api/report.js
// 报告相关 API
// =============================================

import request from '@/utils/request'
/**
 * 获取面试报告详情
 * @param {string} reportId
 */
// 替换 getReport 函数
export const getReport = async (reportId) => {
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

export const getReplyAnalysis = async (reportId) => {
  try {
    const res = await request.get(`/reports/${reportId}/reply-analysis`, {
      timeout: 90000  // AI 逐题评价耗时较长，单独放宽超时
    })
    return res  // { reportId, totalRounds, items: [{index, question, answer, evaluationText, ...}] }
  } catch (e) {
    console.warn('逐题点评加载失败，跳过', e)
    return null
  }
}

export const requestExcellentAnswer = async (reportId, index) => {
  return request.post(`/reports/${reportId}/reply-analysis/${index}/excellent-answer`, {}, {
    timeout: 90000
  })
}

export const requestExcellentAnswerStream = (reportId, index, { onChunk, onDone, onError } = {}) => {
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
    } catch (_) {
      return `请求失败（${response.status}）`
    }
  }

  return new Promise((resolve, reject) => {
    fetch(`${API_BASE}/reports/${reportId}/reply-analysis/${index}/excellent-answer/stream`, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      cache: 'no-store',
      body: JSON.stringify({})
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
      let doneFlag = false

      const handleEvent = (rawEvent) => {
        if (!rawEvent) return
        const dataLines = rawEvent
          .split('\n')
          .filter(line => line.startsWith('data:'))
          .map(line => line.slice(5).trimStart())
        if (!dataLines.length) return

        try {
          const payload = JSON.parse(dataLines.join('\n'))
          if (payload.error) {
            throw new Error(payload.error)
          }
          const chunk = payload.chunk || ''
          if (chunk) {
            fullText += chunk
            onChunk && onChunk(chunk)
          }
          if (payload.done === true) {
            doneFlag = true
          }
        } catch (err) {
          throw err
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
          handleEvent(rawEvent)
          delimiterIndex = buffer.indexOf('\n\n')
        }
      }

      const tail = decoder.decode()
      if (tail) buffer += tail.replace(/\r\n/g, '\n')
      if (buffer.trim()) {
        handleEvent(buffer)
      }

      if (!doneFlag && !fullText) {
        throw new Error('未收到模型输出')
      }

      onDone && onDone(fullText)
      resolve({ referenceAnswer: fullText })
    }).catch((err) => {
      onError && onError(err)
      reject(err)
    })
  })
}


/**
 * 获取历史面试列表
 * @param {Object} params - { page, pageSize, jobId }
 */
export const getHistoryList = async (params = {}) => {
  return request.get('/reports', { params })
}


/**
 * 获取单个报告详情
 * @param {string} reportId - 报告ID
 */
export const getReportDetail = async (reportId) => {
  return request.get(`/reports/${reportId}`)
}

// 在文件末尾加适配函数
export const adaptBackendReport = (raw, reportId) => ({
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





