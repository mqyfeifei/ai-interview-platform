// =============================================
// frontend/src/api/auth.js
// 认证相关API
// =============================================

import request from '@/utils/request'

/**
 * 用户登录
 * @param {Object} data - { loginId: string, password: string, loginType: 'email'|'phone' }
 * @returns {Promise<{ token: string, user: Object }>}
 */
export const login = async (data) => {
  return request.post('/auth/login', data)
}

/**
 * 管理员登录
 * @param {Object} data - { loginId, password }
 */
export const adminLogin = async (data) => {
  return request.post('/login', data, { admin: true })
}

/**
 * 用户注册
 * @param {Object} data - { username, email, phone, password, school, major, grade }
 * @returns {Promise<{ token: string, user: Object }>}
 */
export const register = async (data) => {
  // 将前端的 username 字段映射为后端期望的 real_name
  const submitData = {
    ...data,
    real_name: data.username || data.real_name
  }
  return request.post('/auth/register', submitData)
}

/**
 * 发送验证码
 * @param {Object} data - { target: string, type: 'email'|'phone', action: 'register'|'login' }
 */
export const sendVerifyCode = async (data) => {
  return request.post('/auth/send-code', data)
}

/**
 * 退出登录
 */
export const logout = async () => {
  return request.post('/auth/logout')
}