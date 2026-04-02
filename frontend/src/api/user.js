// =============================================
// frontend/src/api/user.js
// 用户相关API
// =============================================

import request from '@/utils/request'

/**
 * 获取当前用户信息
 */
export const getUserInfo = async () => {
  return request.get('/users/me')
}

/**
 * 更新用户基本信息
 * @param {Object} data - 可包含 username, school, major, grade, avatar
 */
export const updateUserInfo = async (data) => {
  return request.put('/users/me', data)
}

/**
 * 修改密码
 * @param {Object} data - { oldPassword, newPassword }
 */
export const changePassword = async (data) => {
  return request.post('/users/me/change-password', data)
}

/**
 * 更新默认岗位偏好
 * @param {string} jobId
 */
export const updateDefaultJob = async (jobId) => {
  return request.patch('/users/me/preferences', { defaultJob: jobId })
}

/**
 * 上传头像
 * @param {FormData} formData
 */
export const uploadAvatar = async (formData) => {
  return request.post('/users/me/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 绑定/更新手机号（已登录）
 * @param {string} phone
 */
export const bindPhone = async (phone) => {
  return request.post('/users/me/bind-phone', { phone })
}

// =============================================
// 以下为仪表盘、成长曲线等新版API
// =============================================

/**
 * 获取用户仪表盘数据
 */
export const getDashboardData = async () => {
  return request.get('/users/me/dashboard')
}

/**
 * 获取仪表盘统计数据（练习次数、平均分等）
 */
export const getDashboardStats = async () => {
  const res = await request.get('/users/me/dashboard')
  return res
}