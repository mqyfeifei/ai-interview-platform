// =============================================
// frontend/src/api/user.js
// 用户相关API
// =============================================

import request from '@/utils/request'

const mockDelay = (ms = 600) => new Promise(resolve => setTimeout(resolve, ms))
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'

/**
 * 获取当前用户信息
 */
export const getUserInfo = async () => {
  if (USE_MOCK) {
    await mockDelay()
    return {
      id: 1,
      username: '张三',
      email: 'test@example.com',
      phone: '13800138000',
      school: '北京大学',
      major: '计算机科学与技术',
      grade: '大三',
      avatar: null,
      defaultJob: 'java-backend',
      totalInterviews: 12,
      avgScore: 78,
      lastInterviewScore: 82,
      lastInterviewAt: '2024-12-20',
      createdAt: '2024-09-01'
    }
  }
  return request.get('/users/me')
}

/**
 * 更新用户基本信息
 * @param {Object} data - 可包含 username, school, major, grade, avatar
 */
export const updateUserInfo = async (data) => {
  if (USE_MOCK) {
    await mockDelay(800)
    return { ...data, updatedAt: new Date().toISOString() }
  }
  return request.put('/v1/users/me', data)
}

/**
 * 修改密码
 * @param {Object} data - { oldPassword, newPassword }
 */
export const changePassword = async (data) => {
  if (USE_MOCK) {
    await mockDelay(800)
    if (data.oldPassword !== '123456') throw new Error('原密码错误')
    return { success: true }
  }
  return request.post('/v1/users/me/change-password', data)
}

/**
 * 更新默认岗位偏好
 * @param {string} jobId
 */
export const updateDefaultJob = async (jobId) => {
  if (USE_MOCK) {
    await mockDelay(400)
    return { defaultJob: jobId }
  }
  return request.patch('/v1/users/me/preferences', { defaultJob: jobId })
}

/**
 * 上传头像
 * @param {FormData} formData
 */
export const uploadAvatar = async (formData) => {
  if (USE_MOCK) {
    await mockDelay(1200)
    return { avatarUrl: 'https://via.placeholder.com/100' }
  }
  return request.post('/v1/users/me/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 获取首页统计数据
 */
export const getDashboardStats = async () => {
  if (USE_MOCK) {
    await mockDelay(500)
    return {
      totalInterviews: 12,
      avgScore: 78,
      lastInterviewScore: 82,
      lastInterviewAt: '2024-12-20',
      lastInterviewJob: 'Java后端开发',
      scoreImprovement: +8,
      weeklyPractice: 3,
      hotJobs: ['java-backend', 'web-frontend', 'python-algorithm']
    }
  }
  return request.get('/v1/users/me/dashboard')
}