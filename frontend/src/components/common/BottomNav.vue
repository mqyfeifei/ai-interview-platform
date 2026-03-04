<template>
  <nav class="bottom-nav">
    <router-link
      v-for="item in navItems"
      :key="item.name"
      :to="item.path"
      class="bottom-nav__item"
      :class="{ active: isActive(item) }"
    >
      <span class="bottom-nav__icon" v-html="item.icon" />
      <span class="bottom-nav__label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script>
export default {
  name: 'BottomNav',
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
          label: '学习',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`
        },
        {
          name: 'HistoryRecords',
          path: '/history',
          label: '历史',
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`
        },
        {
          name: 'PersonalCenter',
          path: '/profile',
          label: '我的',
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
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: $max-content-width;
  height: $bottom-nav-height;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid $border-color;
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  padding: 0 $spacing-sm;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.06);

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    flex: 1;
    height: 100%;
    color: $text-muted;
    text-decoration: none;
    transition: color $transition-base;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 8px;
      left: 50%;
      transform: translateX(-50%) scaleX(0);
      width: 32px;
      height: 3px;
      background: $gradient-primary;
      border-radius: 2px;
      transition: transform $transition-spring;
    }

    &.active {
      color: $primary;
      &::before { transform: translateX(-50%) scaleX(1); }

      .bottom-nav__icon {
        background: $primary-bg;
        transform: translateY(-1px);
      }
    }
  }

  &__icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $border-radius-sm;
    padding: 4px;
    transition: all $transition-base;

    :deep(svg) {
      width: 18px;
      height: 18px;
    }
  }

  &__label {
    font-size: $font-size-xs;
    font-weight: $font-weight-medium;
    letter-spacing: 0.02em;
  }
}
</style>