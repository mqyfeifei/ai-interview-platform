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
        {{ item.label }}
      </router-link>
    </nav>

    <!-- 右侧：用户信息 + 统计弹窗 -->
    <div class="top-nav__user-wrapper">
      <div class="top-nav__user" @click="toggleUserStats">
        <img
          v-if="userInfo && userInfo.avatar"
          :src="resolvedAvatarSrc"
          class="user-avatar"
          alt="头像"
        />
        <span v-else class="user-avatar user-avatar--fallback">{{ avatarLetter }}</span>
      </div>
      <div class="user-stats-popover" v-if="showUserStats">
        <div class="stats-row">练习次数 <strong>{{ userTotalInterviews }}</strong></div>
        <div class="stats-row">平均得分 <strong>{{ userAvgScore }}</strong></div>
        <div class="stats-row">最近得分 <strong>{{ userLastScore }}</strong></div>
        <div class="stats-row">连续天数 <strong>{{ userStreakDays }}</strong></div>
      </div>
    </div>
  </header>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'TopNav',
  data() {
    return {
      showUserStats: false,
      navItems: [
        { name: 'Dashboard', path: '/dashboard', label: '首页' },
        { name: 'LearningCenter', path: '/learning', label: '学习中心' },
        { name: 'HistoryRecords', path: '/history', label: '历史记录' },
        { name: 'JobSelection', path: '/interview/select', label: '岗位选择' },
        { name: 'PersonalCenter', path: '/profile', label: '个人中心' }
      ]
    }
  },
  computed: {
    ...mapGetters('user', ['userInfo', 'userName']),

    avatarLetter() {
      const name = this.userName || '用'
      return name.charAt(0)
    },

    userTotalInterviews() {
      return this.userInfo?.totalInterviews || this.userInfo?.total_interviews || 0
    },

    userAvgScore() {
      return this.userInfo?.avgScore || this.userInfo?.avg_score || '--'
    },

    userLastScore() {
      return this.userInfo?.lastInterviewScore || this.userInfo?.last_interview_score || '--'
    },

    userStreakDays() {
      return this.userInfo?.streakDays || this.userInfo?.streak_days || 0
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
      return this.$route.path === item.path || this.$route.name === item.name
    },
    toggleUserStats() {
      this.showUserStats = !this.showUserStats
    }
  }
}
</script>

<style lang="scss" scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 999;
  height: 64px;
  display: grid;
  grid-template-columns: 220px 1fr 220px;
  align-items: center;
  padding: 0 24px;
  background: #f4efff;
  border-bottom: 1px solid #e8deff;
  box-shadow: 0 2px 8px rgba(46, 36, 78, 0.1);
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
    gap: 12px;
    justify-content: center;
  }

  &__item {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 8px 14px;
    border-radius: 999px;
    color: #5f43d3;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s ease;
    white-space: nowrap;

    &:hover {
      color: #2a0d8b;
      background: rgba(137, 95, 255, 0.12);
    }

    &.active {
      color: #ffffff;
      background: #7f67f5;
      box-shadow: 0 6px 16px rgba(126, 95, 255, 0.26);
    }
  }

  &__user-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }

  &__user {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 2px solid #d9cbff;
    background: #ffffff;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      transform: translateY(-1px);
      border-color: #b8a1ff;
    }
  }

  .user-stats-popover {
    position: absolute;
    top: 52px;
    right: 0;
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e7d8ff;
    box-shadow: 0 10px 30px rgba(31, 21, 69, 0.17);
    padding: 10px 14px;
    width: 220px;
    z-index: 1000;

    .stats-row {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      color: #342f4b;
      font-size: 13px;
      border-bottom: 1px solid rgba(215, 204, 255, 0.4);

      &:last-child {
        border-bottom: none;
      }

      strong {
        color: #633fdd;
      }
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
  width: 34px;
  height: 34px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.brand-name {
  font-size: 18px;
  font-weight: 800;
  color: #4c3aa2;
  margin-left: 6px;
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  overflow: hidden;
  background: #ffffff;

  &--fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
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