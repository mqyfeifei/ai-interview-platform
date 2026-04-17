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
  getLearningSettings,
  toggleBookmark as apiToggleBookmark,
  markCompleted as apiMarkCompleted,
  updateTaskStatus as apiUpdateTaskStatus,
  updateLearningSettings as apiUpdateLearningSettings
} from '@/api/learning'

const state = () => ({
  growthData: null,
  weaknesses: [],
  recommendations: [],
  dailyPlan: null,
  completedResourceIds: [],
  loading: false,
  reportContextId: null,
  learningSettings: { dailyHours: 2, selectedDayIndex: 1 },
})

const mutations = {
  SET_LOADING(state, v) { state.loading = v },
  SET_GROWTH_DATA(state, data) { state.growthData = data },
  SET_WEAKNESSES(state, list) { state.weaknesses = list || [] },
  SET_RECOMMENDATIONS(state, list) { state.recommendations = list || [] },
  SET_DAILY_PLAN(state, plan) { state.dailyPlan = plan || null },
  SET_COMPLETED_IDS(state, ids) { state.completedResourceIds = Array.isArray(ids) ? ids : [] },
  SET_REPORT_CONTEXT(state, reportId) { state.reportContextId = reportId || null },
  SET_LEARNING_SETTINGS(state, settings) {
    state.learningSettings = {
      dailyHours: settings?.dailyHours || 2,
      selectedDayIndex: settings?.selectedDayIndex || 1
    }
  },
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
  async loadAll({ commit }, { reportId = null, dailyHours = 2 } = {}) {
    commit('SET_LOADING', true)
    commit('SET_REPORT_CONTEXT', reportId)
    try {
      const settings = await getLearningSettings().catch(() => ({ dailyHours: 2, selectedDayIndex: 1 }))
      const effectiveDailyHours = dailyHours ?? settings.dailyHours ?? 2
      const [growthData, weaknesses, recommendations, dailyPlan, completedIds] = await Promise.all([
        getGrowthCurve(),
        getWeaknessTags({ reportId }),
        getRecommendedResources({ reportId }),
        getDailyPlan({ reportId, dailyHours: effectiveDailyHours }),
        getCompletedResourceIds()
      ])
      commit('SET_GROWTH_DATA', growthData)
      commit('SET_WEAKNESSES', weaknesses)
      commit('SET_RECOMMENDATIONS', recommendations)
      commit('SET_DAILY_PLAN', dailyPlan)
      commit('SET_COMPLETED_IDS', completedIds)
      commit('SET_LEARNING_SETTINGS', {
        dailyHours: dailyPlan?.recommendedDailyHours || effectiveDailyHours,
        selectedDayIndex: dailyPlan?.selectedDayIndex || settings?.selectedDayIndex || 1
      })
      return { growthData, weaknesses, recommendations, dailyPlan, completedIds, settings }
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
  },

  async updateLearningSettings({ commit, state, dispatch }, { dailyHours, selectedDayIndex } = {}) {
    const payload = {
      dailyHours: dailyHours ?? state.learningSettings.dailyHours,
      selectedDayIndex: selectedDayIndex ?? state.learningSettings.selectedDayIndex
    }
    const result = await apiUpdateLearningSettings(payload)
    commit('SET_LEARNING_SETTINGS', payload)
    await dispatch('loadAll', {
      reportId: state.reportContextId,
      dailyHours: payload.dailyHours
    })
    return result
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
  isLoading: state => state.loading,
  reportContextId: state => state.reportContextId,
  learningSettings: state => state.learningSettings
}

export default { namespaced: true, state, mutations, actions, getters }
