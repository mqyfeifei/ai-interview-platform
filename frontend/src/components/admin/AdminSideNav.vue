<!--
  frontend/src/components/admin/AdminSideNav.vue
  管理后台专用侧边导航栏
  用法：在所有 admin 页面中替换顶部 admin-bar，引入此组件放在布局左侧
-->
<template>
  <aside class="admin-side-nav" :class="{ collapsed: isCollapsed }">

    <!-- 品牌区 -->
    <div class="asn-brand">
      <div class="asn-brand__logo">
        <img src="@/assets/logo1.jpg" alt="码上offer" />
      </div>
      <transition name="fade-text">
        <div v-if="!isCollapsed" class="asn-brand__text">
          <p class="asn-brand__title">码上offer</p>
          <p class="asn-brand__sub">管理控制台</p>
        </div>
      </transition>
      <!-- 折叠按钮 -->
      <button class="asn-collapse-btn" @click="toggleCollapse" :title="isCollapsed ? '展开' : '收起'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round">
          <polyline v-if="isCollapsed" points="9 18 15 12 9 6"/>
          <polyline v-else points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>

    <!-- 主导航菜单 -->
    <nav class="asn-menu">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="asn-menu__item"
        :class="{ active: isActive(item) }"
        :title="isCollapsed ? item.label : ''"
      >
        <span class="asn-menu__icon" v-html="item.icon" />
        <transition name="fade-text">
          <span v-if="!isCollapsed" class="asn-menu__label">{{ item.label }}</span>
        </transition>
        <span v-if="isActive(item)" class="asn-menu__active-bar" />
      </router-link>
    </nav>

    <!-- 底部管理员身份 -->
    <div class="asn-footer">
      <div class="asn-admin-badge">
        <span class="asn-admin-badge__dot" />
        <transition name="fade-text">
          <span v-if="!isCollapsed" class="asn-admin-badge__text">管理员已登录</span>
        </transition>
      </div>
      
      <!-- 退出登录按钮 -->
      <button class="asn-logout-btn" @click="showLogoutConfirm" :title="isCollapsed ? '退出登录' : ''">
        <span class="asn-logout-btn__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </span>
        <transition name="fade-text">
          <span v-if="!isCollapsed" class="asn-logout-btn__text">退出登录</span>
        </transition>
      </button>
    </div>
    
    <!-- 退出确认对话框 -->
    <div v-if="showLogoutDialog" class="asn-logout-dialog">
      <div class="asn-logout-dialog__content">
        <h3 class="asn-logout-dialog__title">确认退出</h3>
        <p class="asn-logout-dialog__message">您确定要退出登录吗？</p>
        <div class="asn-logout-dialog__actions">
          <button class="asn-logout-dialog__btn asn-logout-dialog__btn--cancel" @click="showLogoutDialog = false">取消</button>
          <button class="asn-logout-dialog__btn asn-logout-dialog__btn--confirm" @click="handleLogout">确认退出</button>
        </div>
      </div>
    </div>

  </aside>
</template>

<script>
import { mapActions } from 'vuex'
export default {
  name: 'AdminSideNav',

  data() {
    return {
      isCollapsed: false,
      showLogoutDialog: false,
      navItems: [
        {
          name: 'AdminDashboard',
          path: '/admin/dashboard',
          label: '控制台总览',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`
        },
        {
          name: 'AdminUsers',
          path: '/admin/users',
          label: '用户管理',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="7" r="4"/>
            <path d="M5.5 21a6.5 6.5 0 0113 0"/>
          </svg>`
        },
        {
          name: 'AdminJobs',
          path: '/admin/jobs',
          label: '岗位管理',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z"/><path d="M8 8h8"/><path d="M8 12h8"/><path d="M8 16h8"/></svg>`
        },
        {
          name: 'AdminQuestions',
          path: '/admin/questions',
          label: '题库与学习资源',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
        },
        {
          name: 'AdminInterviews',
          path: '/admin/interviews',
          label: '面试记录',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`
        },
        {
          name: 'AdminInterviewProfiles',
          path: '/admin/interview-profiles',
          label: '面试配置预设',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16v4H4V6z"/><path d="M4 14h16v4H4v-4z"/><path d="M7 6v12"/><path d="M17 6v12"/></svg>`
        },
        {
          name: 'AdminPrompts',
          path: '/admin/prompts',
          label: 'AI Prompt',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`
        }
      ]
    }
  },

  methods: {
    ...mapActions('user', ['logout']),
    isActive(item) {
      return this.$route.name === item.name || this.$route.path === item.path
    },
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
    },
    showLogoutConfirm() {
      this.showLogoutDialog = true
    },
    async handleLogout() {

        await this.logout()
        this.$router.push('/login')

    }
  }
}
</script>

<style lang="scss" scoped>
$nav-width: 260px;
$nav-collapsed-width: 64px;
$nav-bg:#f8f4ff; 
$nav-bg-hover: #eae4ff;
$nav-bg-active: #d9cfff;
$nav-border: #e4def5;
$nav-text: #5e4fa4;
$nav-text-active: #2f1f78;
$nav-accent: #5f4bb0;
$nav-transition: 0.22s cubic-bezier(0.4, 0, 0.2, 1);

.admin-side-nav {
  width: $nav-width;
  min-height: 100vh;
  background: $nav-bg;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid $nav-border;
  transition: width $nav-transition;
  overflow: hidden;
  position: relative;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.25);

  &.collapsed {
    width: $nav-collapsed-width;

    .asn-brand {
      padding: 18px 0 14px;
      justify-content: center;
      
      .asn-brand__logo {
        margin: 0 auto;
      }
    }

    .asn-menu__item {
      justify-content: center;
      padding: 10px 0;
      margin: 6px 8px;
    }
  .asn-menu__icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    flex-shrink: 0;
    transition: background $nav-transition;

    :deep(svg) {
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      stroke-width: 1.8;  // 稍微加粗线条
    }
  }

    .asn-admin-badge {
      justify-content: center;
    }

  }
}

// ── 品牌区 ──
.asn-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 30px 16px 40px;
  border-bottom: 1px solid $nav-border;
  min-height: 72px;
  flex-shrink: 0;
  overflow: hidden;
  transition: padding $nav-transition;

  &__logo {
    flex-shrink: 0;
    width: 36px;
    height: 36px;

    img {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      object-fit: cover;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
      display: block;
    }
  }

  &__text {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  &__title {
    font-size: 20px;
    font-weight: 800;
    color: #fff;
    white-space: nowrap;
    letter-spacing: -0.2px;
    background: linear-gradient(135deg, #5856da 0%, #6d19ac 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }

  &__sub {
    font-size: 12px;
    color: rgba(100, 83, 130, 0.8);
    white-space: nowrap;
    margin: 2px 0 0;
    letter-spacing: 0.4px;
  }
}

// ── 折叠按钮 ──
.asn-collapse-btn {
  flex-shrink: 0;
  margin-left: auto;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.85);
  color: rgba(135, 91, 189, 0.75);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all $nav-transition;
  padding: 0;

  svg {
    width: 13px;
    height: 13px;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #33204b;
    border-color: rgba(255, 255, 255, 0.2);
  }
}


// ── 主菜单 ──
.asn-menu {
  flex: 1;
  padding: 4px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar { width: 3px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }

  &__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 10px;
    color: $nav-text;
    text-decoration: none;
    font-size: 15px;
    font-weight: 500;
    transition: all $nav-transition;
    white-space: nowrap;
    position: relative;
    overflow: hidden;

    &:hover {
      background: $nav-bg-hover;
      color: #220d5b;
    }

    &.active {
      background: $nav-bg-active;
      color: $nav-text-active;
      font-weight: 600;
      box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.28);
    }
  }

  &__icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    flex-shrink: 0;
    transition: background $nav-transition;

    .asn-menu__item.active {
      .asn-menu__icon {
        background: rgba(99, 102, 241, 0.15);
      }
    }
    :deep(svg) {
      width: 16px;
      height: 16px;
    }
  }

  &__label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__active-bar {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 55%;
    background: $nav-accent;
    border-radius: 2px 0 0 2px;
  }
}

// ── 底部徽章 ──
.asn-footer {
  padding: 12px 14px;
  border-top: 1px solid $nav-border;
  flex-shrink: 0;
}

.asn-admin-badge {
  display: flex;
  align-items: center;
  gap: 8px;

  &__dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
    flex-shrink: 0;
    box-shadow: 0 0 6px rgba(52, 211, 153, 0.55);
    animation: pulse-dot 2.2s ease-in-out infinite;
  }

  &__text {
    font-size: 12px;
    color: rgba(166, 136, 237, 0.75);
    white-space: nowrap;
  }
}

// ── 退出登录按钮 ──
.asn-logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-top: 12px;
  padding: 8px 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.05);
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all $nav-transition;
  white-space: nowrap;

  &:hover {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.3);
  }

  &__icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;

    svg {
      width: 16px;
      height: 16px;
    }
  }

  &__text {
    flex: 1;
    text-align: left;
  }
}

.admin-side-nav.collapsed {
  .asn-logout-btn {
    justify-content: center;
    padding: 8px 0;
    margin-top: 8px;
  }
}

// ── 退出确认对话框 ──
.asn-logout-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  &__content {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  }

  &__title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 12px;
  }

  &__message {
    font-size: 14px;
    color: #6b7280;
    margin: 0 0 20px;
  }

  &__actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  &__btn {
    padding: 8px 16px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;

    &--cancel {
      background: #f3f4f6;
      color: #374151;

      &:hover {
        background: #e5e7eb;
      }
    }

    &--confirm {
      background: #ef4444;
      border-color: #ef4444;
      color: #fff;

      &:hover {
        background: #dc2626;
      }
    }
  }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.55; transform: scale(0.82); }
}

// ── 文字淡入淡出动画 ──
.fade-text-enter-active {
  transition: opacity 0.14s ease 0.04s, transform 0.14s ease 0.04s;
}
.fade-text-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.fade-text-enter-from {
  opacity: 0;
  transform: translateX(-8px);
}
.fade-text-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
</style>