// =============================================
// frontend/src/api/admin.js
// 管理后台 API — 题库、面试记录、AI Prompt
// =============================================
// request.js 拦截器：config.admin = true 时自动把 URL 改写为 /api/v1/admin/*

import request from '@/utils/request'

// ─────────────────────────────────────────────
// 题库 / 知识库（entity: 'question' | 'knowledge'）
// ─────────────────────────────────────────────

/** 获取题目列表（分页 + 过滤） */
export function listQuestions(params = {}) {
  const entity = params.entity || 'question'
  return request.get('/questions', {
    params: { entity, ...params },
    admin: true
  })
}

/**
 * 获取管理员后台统计大盘数据
 */
export function getAdminDashboardStats() {
  return request.get('/dashboard', { admin: true })
}

/** 创建题目/知识项 */
export function createQuestion(data, entity = 'question') {
  return request.post('/questions', { entity, ...data }, { admin: true })
}

/** 更新题目/知识项 */
export function updateQuestion(id, data, entity = 'question') {
  return request.put(`/questions/${id}`, { entity, ...data }, { admin: true })
}

/** 删除题目/知识项 */
export function deleteQuestion(id, entity = 'question') {
  return request.delete(`/questions/${id}`, {
    params: { entity },
    admin: true
  })
}

/** 批量更新题目状态 */
export function bulkUpdateQuestionStatus(data) {
  return request.post('/questions/bulk-update-status', data, { admin: true })
}

/**
 * 批量导入题库（从服务器 YAML 文件）
 * @param {{ dry_run: boolean, clear_existing: boolean, base_dir?: string }} data
 */
export function importQuestions(data) {
  if (data instanceof FormData) {
    return request.post('/questions/import', data, {
      admin: true,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
  return request.post('/questions/import', data, { admin: true })
}

// ─────────────────────────────────────────────
// 面试记录（只读 + 详情）
// ─────────────────────────────────────────────

/** 获取面试记录列表（分页） */
export function listInterviews(params = {}) {
  return request.get('/interviews', { params, admin: true })
}

export function getInterviewDetail(id) {
  return request.get(`/interviews/${id}/details`, { admin: true })
}

// ─────────────────────────────────────────────
// AI Prompt
// ─────────────────────────────────────────────

/** 获取 Prompt 列表 */
export function listPrompts(params = {}) {
  return request.get('/prompts', { params, admin: true })
}

/** 创建 Prompt */
export function createPrompt(data) {
  return request.post('/prompts', data, { admin: true })
}

/** 获取 Prompt 详情 */
export function getPromptDetail(id) {
  return request.get(`/prompts/${id}`, { admin: true })
}

/** 更新 Prompt */
export function updatePrompt(id, data) {
  return request.put(`/prompts/${id}`, data, { admin: true })
}

/** 删除 Prompt */
export function deletePrompt(id) {
  return request.delete(`/prompts/${id}`, { admin: true })
}

// ─────────────────────────────────────────────
// 用户管理
// ─────────────────────────────────────────────

/** 获取用户列表（管理员） */
export function listAdminUsers(params = {}) {
  return request.get('/users', { params, admin: true })
}

/** 更新用户状态 */
export function updateAdminUserStatus(userId, data) {
  return request.put(`/users/${userId}/status`, data, { admin: true })
}

/** 删除用户（管理员） */
export function deleteAdminUser(userId) {
  return request.delete(`/users/${userId}`, { admin: true })
}

/** 获取用户面试与学习绩效（Admin） */
export function getAdminUserPerformance(userId) {
  return request.get(`/users/${userId}/performance`, { admin: true })
}

/** 获取指定用户简历列表（Admin） */
export function listAdminUserResumes(userId) {
  return request.get(`/users/${userId}/resumes`, { admin: true })
}

/** 获取指定用户简历详情（Admin） */
export function getAdminUserResume(userId, resumeId) {
  return request.get(`/users/${userId}/resumes/${resumeId}`, { admin: true })
}

/** 更新用户信息（Admin） */
export function updateAdminUser(userId, data) {
  return request.put(`/users/${userId}`, data, { admin: true })
}

/** 创建用户（Admin） */
export function createAdminUser(data) {
  return request.post('/users', data, { admin: true })
}

// ─────────────────────────────────────────────
// 岗位管理
// ─────────────────────────────────────────────

/** 获取全部岗位（用于下拉选择） */
export function listAdminJobs() {
  return request.get('/jobs', { admin: true })
}

/** 获取岗位列表（分页） */
export function listJobs(params = {}) {
  return request.get('/jobs', { params, admin: true })
}

/** 创建岗位 */
export function createJob(data) {
  return request.post('/jobs', data, { admin: true })
}

/** 更新岗位 */
export function updateJob(id, data) {
  return request.put(`/jobs/${id}`, data, { admin: true })
}

/** 删除岗位 */
export function deleteJob(id) {
  return request.delete(`/jobs/${id}`, { admin: true })
}

/** 上传岗位图标 */
export function uploadJobIcon(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/jobs/icon-upload', formData, {
    admin: true,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
