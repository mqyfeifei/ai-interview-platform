// =============================================
// Vuex 用户模块
// =============================================

import { login, register, logout } from '@/api/auth'
import { getUserInfo, updateUserInfo, changePassword, updateDefaultJob } from '@/api/user'
import { setToken, getToken, clearAuth, getCachedUser, setCachedUser } from '@/utils/auth'

const state = () => ({
  token: getToken() || '',
  userInfo: getCachedUser() || null,
  loading: false
})

const mutations = {
  SET_TOKEN(state, token) {
    state.token = token
    setToken(token)
  },
  SET_USER_INFO(state, info) {
    state.userInfo = info
    setCachedUser(info)
  },
  UPDATE_USER_INFO(state, partial) {
    state.userInfo = { ...state.userInfo, ...partial }
    setCachedUser(state.userInfo)
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  CLEAR_AUTH(state) {
    state.token = ''
    state.userInfo = null
    clearAuth()
  }
}

const actions = {
  // 登录
  async login({ commit }, credentials) {
    commit('SET_LOADING', true)
    try {
      const { token, user } = await login(credentials)
      commit('SET_TOKEN', token)
      commit('SET_USER_INFO', user)
      return user
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 注册
  async register({ commit }, formData) {
    commit('SET_LOADING', true)
    try {
      const { token, user } = await register(formData)
      commit('SET_TOKEN', token)
      commit('SET_USER_INFO', user)
      return user
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取最新用户信息
  async fetchUserInfo({ commit }) {
    try {
      const user = await getUserInfo()
      commit('SET_USER_INFO', user)
      return user
    } catch (err) {
      console.error('获取用户信息失败', err)
    }
  },

  // 更新用户信息
  async updateUserInfo({ commit }, data) {
    commit('SET_LOADING', true)
    try {
      const updated = await updateUserInfo(data)
      commit('UPDATE_USER_INFO', updated)
      return updated
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 修改密码
  async changePassword({ commit }, data) {
    commit('SET_LOADING', true)
    try {
      return await changePassword(data)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 更新默认岗位
  async updateDefaultJob({ commit }, jobId) {
    const result = await updateDefaultJob(jobId)
    commit('UPDATE_USER_INFO', { defaultJob: jobId })
    return result
  },

  // 退出登录
  async logout({ commit }) {
    try {
      await logout()
    } catch (e) {
      // 即使接口失败也清除本地状态
    } finally {
      commit('CLEAR_AUTH')
    }
  }
}

const getters = {
  isLoggedIn: state => !!state.token,
  userInfo: state => state.userInfo,
  userName: state => state.userInfo?.username || '用户',
  userAvatar: state => state.userInfo?.avatar || null,
  defaultJob: state => state.userInfo?.defaultJob || null,
  isLoading: state => state.loading
}

export default { namespaced: true, state, mutations, actions, getters }