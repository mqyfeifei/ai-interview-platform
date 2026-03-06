// =============================================
// frontend/src/api/job.js
// 职位相关API
// Mock数据支持职位列表展示，对接后端时替换为真实request调用即可
// =============================================

import request from '@/utils/request'
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'

export const fetchJobs = async () => {
  if (USE_MOCK) return null  // Mock 模式下由 constants.js 兜底
  const res = await request.get('/jobs')
  return res  // 返回数组：[{ id:1, name:'Java后端开发', description, tech_stack, icon_url }]
}

/**
 * 获取多平台聚合技术热榜（掘金多分类 + Dev.to）
 * @param {string} jobId - 岗位key
 * @param {number} limit - 返回条数
 * @returns {Promise<Array>} 热榜文章列表
 */
export const getTrendingTopics = async (jobId = 'default', limit = 9) => {
  return request.get('/jobs/trending', { params: { jobId, limit } })
}

/**
 * 获取文章全文内容（Dev.to 源支持站内阅读）
 * @param {string} id - 文章 ID
 * @param {string} source - 来源平台
 * @returns {Promise<Object>} 包含 body_html / body_markdown 的文章详情
 */
export const getArticleDetail = async (id, source) => {
  return request.get('/jobs/trending/detail', { params: { id, source } })
}
