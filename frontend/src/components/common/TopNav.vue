<!-- frontend/src/components/common/TopNav.vue -->
<template>
  <header class="top-nav">
    <!-- 左侧：品牌 -->
    <div class="top-nav__brand" @click="$router.push('/dashboard')">
      <img class="brand-logo" src="@/assets/logo1.jpg" alt="码上offer" />
      <span class="brand-name">码上offer</span>
    </div>

    <!-- 中间：导航菜单 -->
    <nav class="top-nav__menu">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="top-nav__item"
        :class="{ active: isActive(item) }"
      >
        <span class="top-nav__icon" v-html="item.icon" />
        <span class="top-nav__label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 右侧：用户信息 -->
    <div class="top-nav__user" @click="$router.push('/profile')">
      <template v-if="userInfo">
        <img
          v-if="userInfo.avatar"
          :src="resolvedAvatarSrc"
          class="user-avatar"
          alt="头像"
        />
        <span v-else class="user-avatar user-avatar--fallback">
          {{ avatarLetter }}
        </span>
        <span class="user-name">{{ userName }}</span>
      </template>
      <template v-else>
        <span class="user-guest" @click.stop="$router.push('/login')">登录</span>
      </template>
    </div>
  </header>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'TopNav',
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
  computed: {
    ...mapGetters('user', ['userInfo', 'userName']),

    avatarLetter() {
      const name = this.userName || '用'
      return name.charAt(0)
    },

    resolvedAvatarSrc() {
      const raw = this.userInfo && this.userInfo.avatar
      if (!raw) return ''
      const asString = String(raw)
      const stamp = Date.now()
      const withStamp = (url) =>
        url.includes('?') ? `${url}&t=${stamp}` : `${url}?t=${stamp}`
      if (/^https?:\/\//i.test(asString)) return withStamp(asString)
      const origin = (process.env.VUE_APP_BACKEND_ORIGIN || '').replace(/\/$/, '')
      if (origin) {
        return withStamp(`${origin}${asString.startsWith('/') ? '' : '/'}${asString}`)
      }
      return withStamp(asString)
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
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 56px;
  display: grid;
  grid-template-columns: 200px 1fr 200px;  // 左中右三列布局
  align-items: center;
  padding: 0 24px;
  background: #f4f3ff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  gap: 0;

  // 品牌区
  &__brand {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    flex-shrink: 0;
    margin-right: 0;
    text-decoration: none;

    &:hover .brand-name {
      color: #4f46e5;
    }
  }

  // 中间导航
  &__menu {
    display: flex;
    align-items: center;
    gap: 4px;
    justify-content: center; 
    // flex: 1;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 6px;
    color: #6b7280;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.15s ease;
    white-space: nowrap;

    &:hover {
      color: #111827;
      background: #f3f4f6;
    }

    &.active {
      color: #6366f1;
      background: #eef2ff;
      font-weight: 600;
    }
  }

  &__icon {
    display: flex;
    align-items: center;
    flex-shrink: 0;

    :deep(svg) {
      width: 16px;
      height: 16px;
    }
  }

  &__label {
    line-height: 1;
  }

  // 右侧用户区
  &__user {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    cursor: pointer;
    padding: 5px 10px;
    border-radius: 6px;
    transition: background 0.15s;
      justify-content: flex-end; // ← 靠右对齐
  margin-left: 0;

    &:hover {
      background: #f3f4f6;
    }
  }
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #4f51be 0%, #6644b4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  transition: color 0.15s;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;

  &--fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e0e7ff;
    color: #4f46e5;
    font-size: 13px;
    font-weight: 600;
  }
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-guest {
  font-size: 14px;
  font-weight: 500;
  color: #6366f1;
  padding: 4px 12px;
  border: 1px solid #6366f1;
  border-radius: 6px;
  transition: all 0.15s;

  &:hover {
    background: #6366f1;
    color: white;
  }
}
</style>