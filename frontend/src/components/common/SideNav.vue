<template>
  <aside class="side-nav">
    <div class="side-nav__brand" @click="$router.push('/dashboard')">
      <!-- <img class="brand-logo" src="@/assets/logo5.png" alt="码上offer" /> -->
      <img class="brand-logo" src="@/assets/logo1.jpg" alt="码上offer" />
      <div class="brand-text">
        <p class="brand-title">码上offer</p>
        <p class="brand-sub">AI模拟面试与能力提升软件</p>
      </div>
    </div>

    <nav class="side-nav__menu">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="side-nav__item"
        :class="{ active: isActive(item) }"
      >
        <span class="side-nav__icon" v-html="item.icon" />
        <span class="side-nav__label">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
export default {
  name: 'SideNav',
  data() {
    return {
      navItems: [
        {
          name: 'Dashboard',
          path: '/dashboard',
          label: '首页',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`
        },
        {
          name: 'LearningCenter',
          path: '/learning',
          label: '学习中心',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`
        },
        {
          name: 'HistoryRecords',
          path: '/history',
          label: '历史记录',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`
        },
        {
          name: 'PersonalCenter',
          path: '/profile',
          label: '个人中心',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
        }
      ]
    }
  },
  methods: {
    isActive(item) {
      return this.$route.name === item.name
    }
  }
}
</script>

<style lang="scss" scoped>
.side-nav {
  height: 100%;
  min-height: 100vh;
  background: rgba(230, 234, 254, 0.95);
  border-right: 1px solid $border-color;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding:  $spacing-xl $spacing-xl;
  box-shadow: $shadow-sm;

  &__brand {
    display: flex;
    align-items: center;
    gap:  $spacing-2xl;
    margin-bottom: $spacing-4xl;
    margin-top: $spacing-base;
    cursor: pointer;
  }

  &__menu {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: 12px;
    border-radius: $border-radius;
    color: $text-secondary;
    text-decoration: none;
    transition: all $transition-base;

    &:hover {
      background: $gray-100;
      color: $text-primary;
    }

    &.active {
      background: $gradient-primary-soft;
      color: $primary;
      box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.2);
    }
  }

  &__icon {
    width: 32px;
    height: 32px;
    border-radius: $border-radius-sm;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(67, 56, 202, 0.08);

    :deep(svg) {
      width: 18px;
      height: 18px;
    }
  }

  &__label {
    font-size: $font-size-md;
    font-weight: $font-weight-semibold;
  }
}

.brand-logo {
  width: 48px;
  height: 48px;
  border-radius: 14px;        // 改成圆角方形，像 App 图标
  object-fit: cover;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);  // 紫色光晕，更融合
  transform: scale(1.5);            // 去掉 scale(1.9)
  flex-shrink: 0;
  
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #4f51be 0%, #6644b4 50%, #3629c4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

.brand-sub {
  font-size: 11px;
  color: #8795da;             // 淡紫色，比 $text-muted 更有品牌感
  letter-spacing: 0.2px;
  margin-top: 1px;
}
</style>
