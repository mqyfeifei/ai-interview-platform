// =============================================
// frontend/src/store/modules/interview.js
// Vuex 面试模块
// =============================================

import { startInterview, sendAnswer, finishInterview } from '@/api/interview'

const state = () => ({
  currentSession: null,    // { sessionId, totalQuestions }
  selectedJob: null,       // 选中的岗位对象（来自 constants.js JOB_TYPES）
  messages: [],            // { id, role:'ai'|'user', content, timestamp, isFollowUp? }
  questionIndex: 0,        // 当前是第几题（0-based）
  isFinished: false,
  reportId: null,
  isLoading: false,        // AI 正在"思考"中
  elapsedSeconds: 0,        // 已用时（秒）
  jobDbId: null  // 后端数据库真实岗位id
})

const mutations = {
  SET_JOB_DB_ID(state, id) { state.jobDbId = id },
  SET_SESSION(state, session) { state.currentSession = session },
  SET_SELECTED_JOB(state, job) { state.selectedJob = job },
  ADD_MESSAGE(state, msg) { state.messages.push(msg) },
  SET_MESSAGES(state, msgs) { state.messages = msgs },
  SET_QUESTION_INDEX(state, idx) { state.questionIndex = idx },
  SET_FINISHED(state, reportId) {
    state.isFinished = true
    state.reportId = reportId
  },

  APPEND_AI_CHUNK(state, chunk) {
  const last = state.messages[state.messages.length - 1]
  if (last && last.role === 'ai') last.content += chunk
},
MARK_STREAM_DONE(state) {
  const last = state.messages[state.messages.length - 1]
  if (last) last.streaming = false
},
  SET_LOADING(state, v) { state.isLoading = v },
  SET_ELAPSED(state, v) { state.elapsedSeconds = v },
  RESET_INTERVIEW(state) {
    state.currentSession = null
    state.messages = []
    state.questionIndex = 0
    state.isFinished = false
    state.reportId = null
    state.isLoading = false
    state.elapsedSeconds = 0
  }
}

const actions = {
  // 选择岗位（从岗位选择页调用）
  selectJob({ commit }, job) {
    commit('SET_SELECTED_JOB', job)
  },

  // 开始面试（从面试主界面初始化时调用）
async startSession({ commit, state, rootGetters }, options = {}) {
  commit('SET_LOADING', true)
  try {
    // 从 user 模块拿数字 id
    const userInfo = rootGetters['user/userInfo']
    const userId = userInfo?.id  // 数字，如 1

    const res = await startInterview({
      userId,                    // 传给后端的 user_id
      jobDbId: state.jobDbId     // 传给后端的 job_id（数字）
    })
    commit('SET_SESSION', { sessionId: res.sessionId, totalQuestions: 10 })
    commit('ADD_MESSAGE', {
      id: Date.now(),
      role: 'ai',
      content: res.firstQuestion,
      timestamp: new Date()
    })
    commit('SET_QUESTION_INDEX', 1)
    return res
  } finally {
    commit('SET_LOADING', false)
  }
},
  // 用户提交回答
async submitAnswer({ commit, state, dispatch }, answerText) {
  commit('ADD_MESSAGE', { role: 'user', content: answerText, timestamp: Date.now() })
  commit('SET_LOADING', true)
  commit('ADD_MESSAGE', { role: 'ai', content: '', timestamp: Date.now(), streaming: true })

  const { sendAnswerStream } = await import('@/api/interview')
  sendAnswerStream(state.currentSession.sessionId, answerText, {
    onChunk(chunk) {
      commit('APPEND_AI_CHUNK', chunk)
    },
    onFinish() {
      commit('SET_LOADING', false)
      commit('MARK_STREAM_DONE')
      dispatch('endInterview')   // ← 现在 dispatch 有了
    },
    onError(err) {
      commit('SET_LOADING', false)
      console.error('SSE error', err)
    }
  })
},
  // 手动结束面试
  async endInterview({ commit, state }) {
    if (!state.currentSession) return
    commit('SET_LOADING', true)
    try {
      const res = await finishInterview(state.currentSession.sessionId)
      commit('ADD_MESSAGE', {
        id: Date.now(),
        role: 'ai',
        content: '好的，面试提前结束。感谢你的参与，正在为你生成评估报告...',
        timestamp: new Date()
      })
      commit('SET_FINISHED', res.reportId)
      return res
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 重置（回到岗位选择重新开始时调用）
  resetInterview({ commit }) {
    commit('RESET_INTERVIEW')
  },

  updateElapsed({ commit }, seconds) {
    commit('SET_ELAPSED', seconds)
  }
}

const getters = {
  selectedJob: s => s.selectedJob,
  currentSession: s => s.currentSession,
  messages: s => s.messages,
  questionIndex: s => s.questionIndex,
  totalQuestions: s => s.currentSession?.totalQuestions || 10,
  progressText: s => `${s.questionIndex} / ${s.currentSession?.totalQuestions || 10}`,
  isFinished: s => s.isFinished,
  reportId: s => s.reportId,
  isLoading: s => s.isLoading,
  elapsedSeconds: s => s.elapsedSeconds
}

export default { namespaced: true, state, mutations, actions, getters }








// // 面试模块 - 管理当前面试会话状态
// const state = () => ({
//   currentSession: null,   // 当前面试会话信息
//   selectedJob: null,      // 选中的岗位
//   messages: [],           // 对话消息列表
//   isFinished: false,      // 是否已结束
//   reportId: null          // 生成的报告ID
// })

// const mutations = {
//   SET_SESSION(state, session) { state.currentSession = session },
//   SET_SELECTED_JOB(state, job) { state.selectedJob = job },
//   ADD_MESSAGE(state, msg) { state.messages.push(msg) },
//   SET_MESSAGES(state, msgs) { state.messages = msgs },
//   SET_FINISHED(state, reportId) { state.isFinished = true; state.reportId = reportId },
//   RESET_INTERVIEW(state) {
//     state.currentSession = null
//     state.messages = []
//     state.isFinished = false
//     state.reportId = null
//   }
// }

// const actions = {
//   selectJob({ commit }, job) { commit('SET_SELECTED_JOB', job) },
//   resetInterview({ commit }) { commit('RESET_INTERVIEW') }
// }

// const getters = {
//   selectedJob: s => s.selectedJob,
//   currentSession: s => s.currentSession,
//   messages: s => s.messages,
//   isFinished: s => s.isFinished,
//   reportId: s => s.reportId
// }

// export default { namespaced: true, state, mutations, actions, getters }