// 面试模块 - 管理当前面试会话状态
const state = () => ({
  currentSession: null,   // 当前面试会话信息
  selectedJob: null,      // 选中的岗位
  messages: [],           // 对话消息列表
  isFinished: false,      // 是否已结束
  reportId: null          // 生成的报告ID
})

const mutations = {
  SET_SESSION(state, session) { state.currentSession = session },
  SET_SELECTED_JOB(state, job) { state.selectedJob = job },
  ADD_MESSAGE(state, msg) { state.messages.push(msg) },
  SET_MESSAGES(state, msgs) { state.messages = msgs },
  SET_FINISHED(state, reportId) { state.isFinished = true; state.reportId = reportId },
  RESET_INTERVIEW(state) {
    state.currentSession = null
    state.messages = []
    state.isFinished = false
    state.reportId = null
  }
}

const actions = {
  selectJob({ commit }, job) { commit('SET_SELECTED_JOB', job) },
  resetInterview({ commit }) { commit('RESET_INTERVIEW') }
}

const getters = {
  selectedJob: s => s.selectedJob,
  currentSession: s => s.currentSession,
  messages: s => s.messages,
  isFinished: s => s.isFinished,
  reportId: s => s.reportId
}

export default { namespaced: true, state, mutations, actions, getters }