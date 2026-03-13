// =============================================
// frontend/src/router/index.js
// 路由配置
// =============================================

import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '@/utils/auth'

// 懒加载路由组件，提高首屏性能
const routes = [
  // ---- 认证路由（无需登录）----
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/users/Login.vue'),
    meta: {hideNavigation: true, requiresAuth: false, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/users/Register.vue'),
    meta: { hideNavigation: true, requiresAuth: false, title: '注册' }
  },

  // ---- 主应用路由（需要登录）----
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/system/Dashboard.vue'),
    meta: { requiresAuth: true, title: '首页', showBottomNav: true }
  },
  {
    path: '/profile',
    name: 'PersonalCenter',
    component: () => import('@/views/users/PersonalCenter.vue'),
    meta: { requiresAuth: true, title: '个人中心', showBottomNav: true }
  },

  // ---- 面试相关路由 ----
  {
    path: '/interview/select',
    name: 'JobSelection',
    component: () => import('@/views/interview/JobSelection.vue'),
    meta: {hideNavigation: true, requiresAuth: true, title: '选择岗位' }
  },
  {
    path: '/interview/session',
    name: 'InterviewSession',
    component: () => import('@/views/interview/InterviewSession.vue'),
    meta: {hideNavigation: true, requiresAuth: true, title: '模拟面试', hideNav: true }
  },
  {
    path: '/interview/report/:reportId',
    name: 'InterviewReport',
    component: () => import('@/views/interview/InterviewReport.vue'),
    meta: { requiresAuth: true, title: '面试报告' }
  },

  // ---- 其他功能路由 ----
  {
    path: '/learning',
    name: 'LearningCenter',
    component: () => import('@/views/system/LearningCenter.vue'),
    meta: { requiresAuth: true, title: '学习中心', showBottomNav: true }
  },
  {
    path: '/history',
    name: 'HistoryRecords',
    component: () => import('@/views/system/HistoryRecords.vue'),
    meta: { requiresAuth: true, title: '历史记录', showBottomNav: true }
  },
  {
    path: '/question/detail',
    name: 'QuestionDetail',
    component: () => import('@/views/system/QuestionDetail.vue'),
    meta: { requiresAuth: false, title: '题目详情' }
  },

  // ---- 404 ----
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

// ---- 全局路由守卫 ----
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 码上offer` : '码上offer'

  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !isLoggedIn()) {
    // 未登录，重定向到登录页并记录目标路径
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (!requiresAuth && isLoggedIn() && (to.name === 'Login' || to.name === 'Register')) {
    // 已登录用户访问登录/注册页，重定向到首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router