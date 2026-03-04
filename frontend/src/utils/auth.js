// =============================================
// 认证工具 - Token管理
// =============================================

import { TOKEN_KEY, USER_INFO_KEY } from './constants'

/**
 * 获取Token
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 存储Token
 */
export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 移除Token
 */
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * 判断是否已登录
 */
export const isLoggedIn = () => {
  return !!getToken()
}

/**
 * 获取本地缓存的用户信息
 */
export const getCachedUser = () => {
  try {
    const raw = localStorage.getItem(USER_INFO_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

/**
 * 缓存用户信息
 */
export const setCachedUser = (user) => {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(user))
}

/**
 * 清除本地缓存的用户信息
 */
export const removeCachedUser = () => {
  localStorage.removeItem(USER_INFO_KEY)
}

/**
 * 完全清除认证信息（登出时调用）
 */
export const clearAuth = () => {
  removeToken()
  removeCachedUser()
}   