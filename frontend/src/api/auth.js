// =============================================
// frontend/src/api/auth.js
// 认证相关API
// 目前使用Mock数据，对接后端时替换为真实request调用即可
// =============================================

import request from '@/utils/request'

// ---- Mock工具（开发阶段用，后端就绪后移除） ----
const mockDelay = (ms = 800) => new Promise(resolve => setTimeout(resolve, ms))

const MOCK_USERS = [
  {
    id: 1,
    username: '张三',
    email: 'test@example.com',
    phone: '13800138000',
    password: '123456',
    school: '北京大学',
    major: '计算机科学与技术',
    grade: '大三',
    avatar: null,
    defaultJob: 'java-backend',
    totalInterviews: 12,
    avgScore: 78,
    createdAt: '2024-09-01'
  }
]

// 开发模式标识 - 对接后端时设为 false
const USE_MOCK = process.env.VUE_APP_USE_MOCK !== 'false'

/**
 * 用户登录
 * @param {Object} data - { loginId: string, password: string, loginType: 'email'|'phone' }
 * @returns {Promise<{ token: string, user: Object }>}
 */
export const login = async (data) => {
  if (USE_MOCK) {
    await mockDelay()
    const user = MOCK_USERS.find(
      u => (u.email === data.loginId || u.phone === data.loginId) && u.password === data.password
    )
    if (!user) throw new Error('账号或密码错误')
    // const { password: _, ...safeUser } = user
    const { ...safeUser } = user

    return { token: 'mock_token_' + Date.now(), user: safeUser }
  }
  return request.post('/auth/login', data)
}

/**
 * 用户注册
 * @param {Object} data - { username, email, phone, password, school, major, grade }
 * @returns {Promise<{ token: string, user: Object }>}
 */
export const register = async (data) => {
  if (USE_MOCK) {
    await mockDelay(1000)
    const exists = MOCK_USERS.find(u => u.email === data.email || u.phone === data.phone)
    if (exists) throw new Error('该邮箱或手机号已被注册')
    const newUser = {
      id: MOCK_USERS.length + 1,
      ...data,
      avatar: null,
      defaultJob: null,
      totalInterviews: 0,
      avgScore: 0,
      createdAt: new Date().toISOString().split('T')[0]
    }
    MOCK_USERS.push(newUser)
    // const { password: _, ...safeUser } = newUser
    const { ...safeUser } = newUser
    return { token: 'mock_token_' + Date.now(), user: safeUser }
  }
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
  if (USE_MOCK) {
    await mockDelay(500)
    return { success: true, message: '验证码已发送（Mock: 888888）' }
  }
  return request.post('/auth/send-code', data)
}

/**
 * 退出登录
 */
export const logout = async () => {
  if (USE_MOCK) {
    await mockDelay(300)
    return { success: true }
  }
  return request.post('/auth/logout')
}