// =============================================
// frontend/src/router/index.js
// 路由配置
// =============================================

import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, getCachedUser } from '@/utils/auth'

// 懒加载路由组件，提高首屏性能
const routes = [
  // ---- 认证路由（无需登录）----
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/users/Login.vue'),
    meta: { hideNavigation: true, requiresAuth: false, title: '登录' }
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
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '管理后台' }
  },
  {
    path: '/profile',
    name: 'PersonalCenter',
    component: () => import('@/views/users/PersonalCenter.vue'),
    meta: { requiresAuth: true, title: '简历', showBottomNav: true }
  },

  // ---- 面试相关路由 ----
  {
    path: '/interview/select',
    name: 'JobSelection',
    component: () => import('@/views/interview/JobSelection.vue'),
    meta: { requiresAuth: true, title: '面试' }
  },
  {
    path: '/interview/session',
    name: 'InterviewSession',
    component: () => import('@/views/interview/InterviewSession.vue'),
    meta: { hideNavigation: true, requiresAuth: true, title: '模拟面试', hideNav: true }
  },
  {
    path: '/interview/voice-session',
    name: 'VoiceInterviewSession',
    component: () => import('@/views/interview/VoiceInterviewSession.vue'),
    meta: { hideNavigation: true, requiresAuth: true, title: '语音面试', hideNav: true }
  },
  {
    path: '/interview/voice-demo',
    name: 'VoiceMicDemo',
    component: () => import('@/views/interview/VoiceMicDemo.vue'),
    meta: { requiresAuth: false, title: '语音输入 Demo' }
  },
  {
    path: '/interview/report/:reportId',
    name: 'InterviewReport',
    component: () => import('@/views/interview/InterviewReport.vue'),
    meta: { requiresAuth: true, title: '面试报告', hideNavigation: true }
  },
  // ----管理员页面相关路由----
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '用户管理' }
  },
  {
    path: '/admin/questions',
    name: 'AdminQuestions',
    component: () => import('@/views/admin/QuestionManager.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '题库管理' }
  },
  {
    path: '/admin/jobs',
    name: 'AdminJobs',
    component: () => import('@/views/admin/JobManager.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '岗位管理' }
  },
  {
    path: '/admin/interviews',
    name: 'AdminInterviews',
    component: () => import('@/views/admin/InterviewManager.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '面试记录' }
  },
  {
    path: '/admin/interview-profiles',
    name: 'AdminInterviewProfiles',
    component: () => import('@/views/admin/AdminInterviewProfiles.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: '面试配置预设' }
  },
  {
    path: '/admin/prompts',
    name: 'AdminPrompts',
    component: () => import('@/views/admin/PromptManager.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, showAdminNav: true, title: 'AI Prompt' }
  },
  // ---- 其他功能路由 ----
  {
    path: '/learning',
    name: 'LearningCenter',
    component: () => import('@/views/system/LearningCenter.vue'),
    meta: { requiresAuth: true, title: '学习', showBottomNav: true }
  },
  {
    path: '/learning/plan',
    name: 'StudyPlanner',
    component: () => import('@/views/system/StudyPlanner.vue'),
    meta: { requiresAuth: true, title: '智能练习规划', hideNavigation: true }
  },
  {
    path: '/resume',
    name: 'ResumeBuilder',
    component: () => import('@/views/system/ResumeBuilder.vue'),
    meta: { requiresAuth: true, title: '简历制作', hideNavigation: true }
  },
  {
    path: '/history',
    name: 'HistoryRecords',
    component: () => import('@/views/system/HistoryRecords.vue'),
    meta: { requiresAuth: true, title: '报告', showBottomNav: true }
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
  } else if (to.meta.requiresAdmin) {
    const user = getCachedUser()
    if (!user) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    if (user.is_active === false) {
      alert('账号被禁用')
      next({ name: 'Login' })
      return
    }
    if (user.role !== 'admin') {
      alert('无管理员权限')
      next({ name: 'Dashboard' })
      return
    }
    next()
  } else if (!requiresAuth && isLoggedIn() && (to.name === 'Login' || to.name === 'Register')) {
    // 已登录用户访问登录/注册页，重定向到首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
