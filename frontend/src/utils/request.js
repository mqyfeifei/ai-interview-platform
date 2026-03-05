// =============================================
// Axios请求封装 - 统一处理请求/响应/错误
// 对接后端时只需调整拦截器逻辑，业务代码无需修改
// =============================================

import axios from 'axios'
import { getToken, clearAuth } from './auth'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ---- 请求拦截器 ----
request.interceptors.request.use(
  (config) => {
    // 自动附加Token
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ---- 响应拦截器 ----
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 约定后端统一响应格式：{ code, data, message }
    // code === 200 表示成功
    if (res.code === undefined) {
      // 若后端直接返回数据（无code包装），直接返回
      return res
    }

    if (res.code === 200 || res.code === 0) {
      return res.data !== undefined ? res.data : res
    }

    // 401 - Token过期或无效，跳转登录
    if (res.code === 401) {
      clearAuth()
      router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
      return Promise.reject(new Error(res.message || '登录已过期，请重新登录'))
    }

    // 其他业务错误
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // HTTP层错误处理
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        clearAuth()
        router.push({ name: 'Login' })
      } else if (status === 403) {
        console.error('无权限访问')
      } else if (status === 500) {
        console.error('服务器内部错误')
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('请求超时，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default request