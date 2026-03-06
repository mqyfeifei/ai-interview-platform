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

export const fetchJobAvgScores = () => request.get('/jobs/avg-scores')