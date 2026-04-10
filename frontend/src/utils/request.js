// =============================================
// frontend/src/utils/request.js
// Axios请求封装 - 统一处理请求/响应/错误
// 对接后端时只需调整拦截器逻辑，业务代码无需修改
// =============================================

import axios from 'axios'
import { getToken, clearAuth } from './auth'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api',
  timeout: 30000,  // 增加全局超时到 30 秒，避免启动面试时 TTS 初始化超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// ---- 请求拦截器 ----
request.interceptors.request.use(
  (config) => {
    // 管理后台接口前缀
    if (config.admin) {
      const raw = config.url || ''
      if (!raw.startsWith('/api/v1/admin')) {
        const cleanPath = raw.startsWith('/') ? raw : `/${raw}`
        config.url = `/api/v1/admin${cleanPath}`
      }
      // 如果系统有 `baseURL`，直接覆盖，避免变成 /api/api/v1/admin
      config.baseURL = ''
    }

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

    // 403 - 无权限
    if (res.code === 403) {
      const msg = res.message || '无管理员权限'
      return Promise.reject(new Error(msg))
    }

    // 400 - 请求参数/数据错误
    if (res.code === 400) {
      const msg = res.message || '请求参数错误'
      return Promise.reject(new Error(msg))
    }

    // 其他业务错误
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // HTTP层错误处理
    if (error.response) {
      const { status, data } = error.response
      if (status === 401 || status === 422) {
        clearAuth()
        router.push({ name: 'Login' })
        const msg = data?.message || data?.msg || '登录已过期，请重新登录'
        return Promise.reject(new Error(msg))
      } else if (status === 403) {
        const msg = data?.message || data?.msg || '无管理员权限'
        return Promise.reject(new Error(msg))
      } else if (status === 400) {
        const msg = data?.message || data?.msg || '请求参数错误'
        return Promise.reject(new Error(msg))
      } else if (status === 500) {
        console.error('服务器内部错误')
      }

      // 尝试提取后端业务错误信息（后端常见格式：{ code, msg, message }）
      const backendMsg = data?.message || data?.msg
      if (backendMsg) {
        return Promise.reject(new Error(backendMsg))
      }
    } else if (error.code === 'ECONNABORTED') {
      const url = error.config?.url || '未知接口'
      console.error(`[请求超时] ${url}，请检查网络或联系后端。`)
      return Promise.reject(new Error(`请求超时（${url}），请稍后重试`))
    }
    return Promise.reject(error)
  }
)

export default request