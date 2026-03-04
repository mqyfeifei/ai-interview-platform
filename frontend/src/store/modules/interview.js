// =============================================
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
  elapsedSeconds: 0        // 已用时（秒）
})

const mutations = {
  SET_SESSION(state, session) { state.currentSession = session },
  SET_SELECTED_JOB(state, job) { state.selectedJob = job },
  ADD_MESSAGE(state, msg) { state.messages.push(msg) },
  SET_MESSAGES(state, msgs) { state.messages = msgs },
  SET_QUESTION_INDEX(state, idx) { state.questionIndex = idx },
  SET_FINISHED(state, reportId) {
    state.isFinished = true
    state.reportId = reportId
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
  async startSession({ commit, state }, options = {}) {
    commit('SET_LOADING', true)
    try {
      const res = await startInterview({
        jobId: state.selectedJob?.id,
        questionCount: options.questionCount || 10,
        timeLimit: options.timeLimit || 120
      })
      commit('SET_SESSION', { sessionId: res.sessionId, totalQuestions: res.totalQuestions || 10 })
      // 推入AI第一个问题
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
  async submitAnswer({ commit, state }, answerText) {
    if (!state.currentSession) return

    // 先推入用户消息
    commit('ADD_MESSAGE', {
      id: Date.now(),
      role: 'user',
      content: answerText,
      timestamp: new Date()
    })

    commit('SET_LOADING', true)
    try {
      const res = await sendAnswer(state.currentSession.sessionId, answerText)

      // 推入 AI 下一个问题或结束语
      commit('ADD_MESSAGE', {
        id: Date.now() + 1,
        role: 'ai',
        content: res.nextQuestion,
        timestamp: new Date(),
        isFollowUp: res.isFollowUp || false
      })

      if (res.isFinished) {
        // 自动结束时生成报告
        const finishRes = await finishInterview(state.currentSession.sessionId)
        commit('SET_FINISHED', finishRes.reportId)
      } else {
        commit('SET_QUESTION_INDEX', (res.questionIndex || state.questionIndex) + 1)
      }

      return res
    } finally {
      commit('SET_LOADING', false)
    }
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