<template>
  <aside class="side-nav">
    <div class="side-nav__brand" @click="$router.push('/dashboard')">
      <div class="brand-logo">AI</div>
      <div class="brand-text">
        <p class="brand-title">AI面试助手</p>
        <p class="brand-sub">智能练习平台</p>
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
  background: rgba(255, 255, 255, 0.95);
  border-right: 1px solid $border-color;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: $spacing-xl $spacing-base;
  box-shadow: $shadow-sm;

  &__brand {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-2xl;
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
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-primary;
  color: $text-white;
  font-size: $font-size-md;
  font-family: $font-family-display;
  font-weight: $font-weight-bold;
  box-shadow: $shadow-primary;
}

.brand-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.brand-sub {
  font-size: $font-size-sm;
  color: $text-muted;
}
</style>
