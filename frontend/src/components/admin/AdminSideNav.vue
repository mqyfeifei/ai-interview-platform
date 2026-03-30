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

    <!-- 回到前台入口 -->
    <div class="asn-back-wrap">
      <router-link to="/dashboard" class="asn-back-btn">
        <span class="asn-back-btn__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
        </span>
        <span v-if="!isCollapsed" class="asn-back-btn__label">返回前台</span>
      </router-link>
    </div>

    <!-- 分隔线 -->
    <div class="asn-divider">
      <span v-if="!isCollapsed" class="asn-divider__label">功能模块</span>
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
    </div>

  </aside>
</template>

<script>
export default {
  name: 'AdminSideNav',

  data() {
    return {
      isCollapsed: false,
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
          name: 'AdminQuestions',
          path: '/admin/questions',
          label: '岗位与题库管理',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
        },
        {
          name: 'AdminInterviews',
          path: '/admin/interviews',
          label: '面试记录',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`
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
    isActive(item) {
      return this.$route.name === item.name || this.$route.path === item.path
    },
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
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
    }

    .asn-brand__logo img {
      margin: 0 auto;
    }

    .asn-back-wrap {
      padding: 10px 8px 6px;
    }

    .asn-menu__item {
      color: $nav-text;
      border-radius: 8px;
      margin: 6px 8px;
      padding: 10px 14px;
      transition: all 0.2s;
    }

    .asn-menu__item:hover {
      background: $nav-bg-hover;
    }

    .asn-back-btn {
      justify-content: center;
      padding: 10px 0;
    }

    .asn-admin-badge {
      justify-content: center;
    }

    .asn-divider {
      padding: 12px 0 6px;
      display: flex;
      justify-content: center;
    }
  }
}

// ── 品牌区 ──
.asn-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 14px 14px;
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
    font-size: 15px;
    font-weight: 800;
    color: #fff;
    white-space: nowrap;
    letter-spacing: -0.2px;
    background: linear-gradient(135deg, #a5b4fc 0%, #c4b5fd 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }

  &__sub {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.3);
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

// ── 返回前台 ──
.asn-back-wrap {
  padding: 10px 10px 6px;
  flex-shrink: 0;
  transition: padding $nav-transition;
}

.asn-back-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 10px;
  border-radius: 9px;
  color: $nav-text;
  text-decoration: none;
  font-size: 12.5px;
  font-weight: 500;
  transition: all $nav-transition;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);

  &__icon {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: rgba(255, 255, 255, 0.07);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    svg {
      width: 15px;
      height: 15px;
    }
  }

  &__label {
    overflow: hidden;
    white-space: nowrap;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.09);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.14);
  }
}

// ── 分隔线 ──
.asn-divider {
  padding: 14px 16px 6px;
  flex-shrink: 0;
  transition: padding $nav-transition;

  &__label {
    font-size: 10px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.22);
    letter-spacing: 0.9px;
    text-transform: uppercase;
    white-space: nowrap;
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
    gap: 11px;
    padding: 10px 12px;
    border-radius: 10px;
    color: $nav-text;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    transition: all $nav-transition;
    white-space: nowrap;
    position: relative;
    overflow: hidden;

    &:hover {
      background: $nav-bg-hover;
      color: rgba(255, 255, 255, 0.9);
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
      background: $nav-bg-active;
      color: $nav-text-active;
      font-weight: 700;
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
    font-size: 11.5px;
    color: rgba(255, 255, 255, 0.35);
    white-space: nowrap;
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