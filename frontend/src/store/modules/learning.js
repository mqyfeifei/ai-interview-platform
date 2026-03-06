// =============================================
// frontend/src/store/modules/learning.js
// Vuex 学习中心模块
// =============================================

import {
  getGrowthCurve, getWeaknesses, getRecommendations,
  toggleBookmark, markCompleted, getDailyPlan, updateTaskStatus
} from '@/api/learning'

const state = () => ({
  growthData: null,
  weaknesses: [],
  recommendations: [],
  dailyPlan: null,
  loading: false,
  // 推荐筛选状态
  activeFilter: 'all'
})

const mutations = {
  SET_GROWTH_DATA(state, data) { state.growthData = data },
  SET_WEAKNESSES(state, data) { state.weaknesses = data },
  SET_RECOMMENDATIONS(state, data) { state.recommendations = data },
  SET_DAILY_PLAN(state, data) { state.dailyPlan = data },
  SET_LOADING(state, v) { state.loading = v },
  SET_ACTIVE_FILTER(state, v) { state.activeFilter = v },

  TOGGLE_BOOKMARK(state, { resourceId, bookmarked }) {
    const r = state.recommendations.find(x => x.id === resourceId)
    if (r) r.bookmarked = bookmarked
  },
  MARK_COMPLETED(state, resourceId) {
    const r = state.recommendations.find(x => x.id === resourceId)
    if (r) r.completed = true
  },
  UPDATE_TASK_STATUS(state, { taskId, done }) {
    if (!state.dailyPlan) return
    const t = state.dailyPlan.tasks.find(x => x.id === taskId)
    if (t) t.done = done
  }
}

const actions = {
  async loadAll({ dispatch }) {
    await Promise.all([
      dispatch('loadGrowthData'),
      dispatch('loadWeaknesses'),
      dispatch('loadRecommendations'),
      dispatch('loadDailyPlan')
    ])
  },

  async loadGrowthData({ commit }) {
    try {
      const data = await getGrowthCurve()
      commit('SET_GROWTH_DATA', data)
    } catch (e) { console.warn('加载成长曲线失败', e) }
  },

  async loadWeaknesses({ commit }) {
    try {
      const data = await getWeaknesses()
      commit('SET_WEAKNESSES', data)
    } catch (e) { console.warn('加载技能短板失败', e) }
  },

  async loadRecommendations({ commit }, params = {}) {
    try {
      const { list } = await getRecommendations(params)
      commit('SET_RECOMMENDATIONS', list)
    } catch (e) { console.warn('加载推荐失败', e) }
  },

  async loadDailyPlan({ commit }) {
    try {
      const data = await getDailyPlan()
      commit('SET_DAILY_PLAN', data)
    } catch (e) { console.warn('加载每日计划失败', e) }
  },

  async toggleBookmark({ commit }, { resourceId, bookmarked }) {
    commit('TOGGLE_BOOKMARK', { resourceId, bookmarked })
    try {
      await toggleBookmark(resourceId, bookmarked)
    } catch (e) {
      // 回滚
      commit('TOGGLE_BOOKMARK', { resourceId, bookmarked: !bookmarked })
    }
  },

  async markCompleted({ commit }, resourceId) {
    commit('MARK_COMPLETED', resourceId)
    try {
      await markCompleted(resourceId)
    } catch (e) { console.warn('标记完成失败', e) }
  },

  async updateTaskStatus({ commit }, { taskId, done }) {
    commit('UPDATE_TASK_STATUS', { taskId, done })
    try {
      await updateTaskStatus(taskId, done)
    } catch (e) {
      commit('UPDATE_TASK_STATUS', { taskId, done: !done })
    }
  }
}

const getters = {
  growthData: s => s.growthData,
  weaknesses: s => s.weaknesses,
  recommendations: s => s.recommendations,
  dailyPlan: s => s.dailyPlan,
  isLoading: s => s.loading,
  activeFilter: s => s.activeFilter,
  completedTaskCount: s => s.dailyPlan?.tasks?.filter(t => t.done).length || 0,
  totalTaskCount: s => s.dailyPlan?.tasks?.length || 0
}

export default { namespaced: true, state, mutations, actions, getters }