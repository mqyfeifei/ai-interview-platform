// =============================================
// frontend/src/store/modules/learning.js
// Vuex 学习中心模块
// =============================================

import {
  getGrowthCurve,
  getWeaknessTags,
  getCompletedResourceIds,
  getRecommendedResources,
  getDailyPlan,
  toggleBookmark as apiToggleBookmark,
  markCompleted as apiMarkCompleted,
  updateTaskStatus as apiUpdateTaskStatus
} from '@/api/learning'

const state = () => ({
  growthData: null,
  weaknesses: [],
  recommendations: [],
  dailyPlan: null,
  completedResourceIds: [],
  loading: false
})

const mutations = {
  SET_LOADING(state, v) { state.loading = v },
  SET_GROWTH_DATA(state, data) { state.growthData = data },
  SET_WEAKNESSES(state, list) { state.weaknesses = list || [] },
  SET_RECOMMENDATIONS(state, list) { state.recommendations = list || [] },
  SET_DAILY_PLAN(state, plan) { state.dailyPlan = plan || null },
  SET_COMPLETED_IDS(state, ids) { state.completedResourceIds = Array.isArray(ids) ? ids : [] },
  UPDATE_RECOMMENDATION(state, { resourceId, patch }) {
    state.recommendations = state.recommendations.map(item =>
      item.id === resourceId ? { ...item, ...patch } : item
    )
  },
  UPDATE_DAILY_TASK(state, { taskId, done }) {
    if (!state.dailyPlan || !Array.isArray(state.dailyPlan.tasks)) return
    state.dailyPlan.tasks = state.dailyPlan.tasks.map(task =>
      task.id === taskId ? { ...task, done } : task
    )
  }
}

const actions = {
  async loadAll({ commit }) {
    commit('SET_LOADING', true)
    try {
      const [growthData, weaknesses, recommendations, dailyPlan, completedIds] = await Promise.all([
        getGrowthCurve(),
        getWeaknessTags(),
        getRecommendedResources(),
        getDailyPlan(),
        getCompletedResourceIds()
      ])
      commit('SET_GROWTH_DATA', growthData)
      commit('SET_WEAKNESSES', weaknesses)
      commit('SET_RECOMMENDATIONS', recommendations)
      commit('SET_DAILY_PLAN', dailyPlan)
      commit('SET_COMPLETED_IDS', completedIds)
      return { growthData, weaknesses, recommendations, dailyPlan, completedIds }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async toggleBookmark({ commit }, { resourceId, bookmarked }) {
    const normalizedBookmarked = bookmarked === undefined ? true : bookmarked
    try {
      await apiToggleBookmark(resourceId, normalizedBookmarked)
      commit('UPDATE_RECOMMENDATION', { resourceId, patch: { bookmarked: normalizedBookmarked } })
      return { success: true }
    } catch (e) {
      console.warn('[learning] toggleBookmark 失败', e)
      return { success: false }
    }
  },

  async markCompleted({ commit }, resourceId) {
    try {
      const result = await apiMarkCompleted(resourceId)
      commit('UPDATE_RECOMMENDATION', { resourceId, patch: { completed: true } })
      return result
    } catch (e) {
      console.warn('[learning] markCompleted 失败', e)
      return { success: false }
    }
  },

  async updateTaskStatus({ commit }, { taskId, done }) {
    try {
      const result = await apiUpdateTaskStatus(taskId, done)
      commit('UPDATE_DAILY_TASK', { taskId, done })
      return result
    } catch (e) {
      console.warn('[learning] updateTaskStatus 失败', e)
      throw e
    }
  }
}

const getters = {
  growthData: state => state.growthData,
  weaknesses: state => state.weaknesses,
  recommendations: state => state.recommendations,
  dailyPlan: state => state.dailyPlan,
  completedTaskCount: state => {
    if (!state.dailyPlan || !Array.isArray(state.dailyPlan.tasks)) return 0
    return state.dailyPlan.tasks.filter(t => t.done).length
  },
  totalTaskCount: state => (state.dailyPlan?.tasks?.length || 0),
  isLoading: state => state.loading
}

export default { namespaced: true, state, mutations, actions, getters }
