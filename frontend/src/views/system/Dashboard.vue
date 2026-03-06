<template>
  <div class="dashboard-page">
    <!-- 顶部渐变Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-top">
          <div class="greeting">
            <p class="greeting__time">{{ timeGreeting }}</p>
            <h1 class="greeting__name">{{ userName }} 👋</h1>
          </div>
          <div class="header-avatar" @click="$router.push('/profile')">
            <img v-if="userInfo && userInfo.avatar" :src="userInfo.avatar" alt="头像" />
            <span v-else class="avatar-fallback">{{ avatarLetter }}</span>
          </div>
        </div>

        <!-- 最近面试卡片 -->
        <div class="recent-score-card" v-if="stats.lastInterviewScore">
          <div class="recent-score-card__left">
            <p class="recent-score-card__label">上次面试</p>
            <p class="recent-score-card__job">{{ stats.lastInterviewJob }}</p>
            <p class="recent-score-card__date">{{ formatDate(stats.lastInterviewAt) }}</p>
          </div>
          <div class="recent-score-card__right">
            <div class="score-ring">
              <svg viewBox="0 0 60 60">
                <circle cx="30" cy="30" r="24" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="5"/>
                <circle
                  cx="30" cy="30" r="24"
                  fill="none"
                  stroke="white"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="scoreCircumference"
                  :stroke-dashoffset="scoreOffset"
                  transform="rotate(-90 30 30)"
                  style="transition: stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)"
                />
              </svg>
              <span class="score-ring__value">{{ stats.lastInterviewScore }}</span>
            </div>
            <div
              class="score-trend"
              :class="stats.scoreImprovement >= 0 ? 'up' : 'down'"
              v-if="stats.scoreImprovement !== undefined"
            >
              <span>{{ stats.scoreImprovement >= 0 ? '↑' : '↓' }}</span>
              <span>{{ Math.abs(stats.scoreImprovement) }}分</span>
            </div>
          </div>
        </div>

        <!-- 无面试记录 -->
        <div class="no-interview-card" v-else>
          <span class="no-interview-card__icon">🎯</span>
          <div>
            <p class="no-interview-card__title">开始你的第一次面试</p>
            <p class="no-interview-card__sub">AI面试官已就位，随时开始练习</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="dashboard-body">
      <!-- 数据概览 -->
      <div class="stats-row">
        <div class="stats-card" v-for="s in statCards" :key="s.label">
          <span class="stats-card__icon">{{ s.icon }}</span>
          <span class="stats-card__value">{{ s.value }}</span>
          <span class="stats-card__label">{{ s.label }}</span>
        </div>
      </div>

      <!-- 快速开始 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">快速开始</h2>
        </div>
        <button class="start-btn" @click="startInterview">
          <div class="start-btn__icon">🚀</div>
          <div class="start-btn__content">
            <p class="start-btn__title">开始模拟面试</p>
            <p class="start-btn__sub">{{ defaultJobName || '选择岗位，开始练习' }}</p>
          </div>
          <svg class="start-btn__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>

        <div class="quick-actions">
          <button
            class="quick-action-btn"
            v-for="a in quickActions"
            :key="a.label"
            @click="$router.push(a.path)"
          >
            <span class="quick-action-btn__icon" :style="{ background: a.bgColor }">{{ a.icon }}</span>
            <span class="quick-action-btn__label">{{ a.label }}</span>
          </button>
        </div>
      </section>

      <!-- 热门岗位 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">热门岗位</h2>
          <button class="section-more" @click="$router.push('/interview/select')">
            查看全部
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;display:inline-block;vertical-align:middle">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>

        <div class="job-list">
          <div
            class="job-card"
            v-for="job in hotJobs"
            :key="job.id"
            @click="selectJobAndStart(job)"
          >
            <div class="job-card__icon" :style="{ background: job.colorBg }">
              {{ job.icon }}
            </div>
            <div class="job-card__info">
              <p class="job-card__name">{{ job.name }}</p>
              <p class="job-card__stack">{{ job.techStack.slice(0, 3).join(' · ') }}</p>
            </div>
            <div class="job-card__meta">
              <span class="job-card__avg">均分 {{ job.avgScore }}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;color:#94A3B8;flex-shrink:0">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </div>
          </div>
        </div>
      </section>

      <!-- 每日提示 -->
      <section class="section">
        <div class="daily-tip-card">
          <div class="daily-tip-card__header">
            <span>💡</span>
            <span>今日面试小贴士</span>
          </div>
          <p class="daily-tip-card__content">{{ dailyTip }}</p>
        </div>
      </section>

    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { getDashboardStats } from '@/api/user'
import { JOB_TYPES } from '@/utils/constants'

export default {
  name: 'DashboardPage',
  data() {
    return {
      stats: {
        totalInterviews: 0,
        avgScore: 0,
        lastInterviewScore: 0,
        lastInterviewJob: '',
        lastInterviewAt: '',
        scoreImprovement: 0,
        weeklyPractice: 0
      },
      quickActions: [
        { label: '历史记录', icon: '📋', path: '/history', bgColor: '#EEF2FF' },
        { label: '学习中心', icon: '📚', path: '/learning', bgColor: '#D1FAE5' },
        { label: '选择岗位', icon: '🎯', path: '/interview/select', bgColor: '#FEF3C7' },
        { label: '个人中心', icon: '👤', path: '/profile', bgColor: '#FEE2E2' }
      ],
      dailyTips: [
        '回答时采用 STAR 法则（情境-任务-行动-结果），让回答更有结构和说服力。',
        '面试前10分钟快速回顾项目亮点，准备2-3个"失败经历+如何改进"的故事。',
        '技术问题不会时，不要沉默，大声思考推理过程同样体现能力。',
        '多使用数字和具体案例，比如"优化后性能提升了40%"比"优化了很多"更有说服力。',
        '复杂问题先说结论，再展开细节，让面试官第一时间抓住重点。'
      ]
    }
  },
  computed: {
    ...mapGetters('user', ['userInfo', 'userName', 'defaultJob']),

    timeGreeting() {
      const hour = new Date().getHours()
      if (hour < 6) return '夜深了，注意休息'
      if (hour < 12) return '早上好'
      if (hour < 14) return '中午好'
      if (hour < 18) return '下午好'
      return '晚上好'
    },

    avatarLetter() {
      const name = this.userName || '用'
      return name.charAt(0)
    },

    defaultJobName() {
      if (!this.defaultJob) return ''
      const job = JOB_TYPES.find(j => j.id === this.defaultJob)
      return job ? job.name : ''
    },

    hotJobs() {
      return JOB_TYPES.slice(0, 4)
    },

    statCards() {
      return [
        { icon: '🎯', value: this.stats.totalInterviews || 0, label: '练习次数' },
        { icon: '⭐', value: this.stats.avgScore || '--', label: '平均得分' },
        { icon: '🔥', value: this.stats.weeklyPractice || 0, label: '本周练习' }
      ]
    },

    scoreCircumference() {
      return 2 * Math.PI * 24
    },

    scoreOffset() {
      const score = this.stats.lastInterviewScore || 0
      const pct = score / 100
      return this.scoreCircumference * (1 - pct)
    },

    dailyTip() {
      const idx = new Date().getDate() % this.dailyTips.length
      return this.dailyTips[idx]
    }
  },
  async created() {
    this.loadStats()
  },
  methods: {
    ...mapActions('user', ['fetchUserInfo']),
    ...mapActions('interview', ['selectJob']),

    async loadStats() {
      try {
        this.stats = await getDashboardStats()
      } catch (e) {
        console.warn('加载统计数据失败', e)
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    startInterview() {
      this.$router.push('/interview/select')
    },

    selectJobAndStart(job) {
      this.selectJob(job)
      this.$router.push('/interview/select')
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// 顶部 Header
.dashboard-header {
  background: $gradient-primary;
  padding: 0;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    top: -80px; right: -60px;
    pointer-events: none;
  }
  &::after {
    content: '';
    position: absolute;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(124,58,237,0.3) 0%, transparent 70%);
    bottom: -40px; left: -40px;
    pointer-events: none;
  }
}

.header-content {
  position: relative;
  z-index: 1;
  padding: 52px $spacing-base $spacing-xl;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-lg;
}

.greeting {
  &__time {
    font-size: $font-size-sm;
    color: rgba(255,255,255,0.65);
    margin-bottom: 4px;
  }
  &__name {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    color: white;
    letter-spacing: -0.01em;
  }
}

.header-avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: 2px solid rgba(255,255,255,0.3);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img { width: 100%; height: 100%; object-fit: cover; }
}

.avatar-fallback {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: white;
}

// 最近面试卡片
.recent-score-card {
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &__left { flex: 1; }
  &__label {
    font-size: $font-size-xs;
    color: rgba(255,255,255,0.55);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }
  &__job {
    font-weight: $font-weight-semibold;
    color: white;
    font-size: $font-size-base;
    margin-bottom: 3px;
  }
  &__date { font-size: $font-size-xs; color: rgba(255,255,255,0.5); }

  &__right {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
}

.score-ring {
  position: relative;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;

  svg { position: absolute; inset: 0; width: 100%; height: 100%; }

  &__value {
    font-family: $font-family-display;
    font-size: $font-size-xl;
    font-weight: $font-weight-extrabold;
    color: white;
    position: relative;
    z-index: 1;
  }
}

.score-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  padding: 2px 8px;
  border-radius: $border-radius-full;

  &.up { background: rgba(16,185,129,0.25); color: #6ee7b7; }
  &.down { background: rgba(239,68,68,0.25); color: #fca5a5; }
}

.no-interview-card {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  display: flex;
  align-items: center;
  gap: $spacing-md;

  &__icon { font-size: 32px; }
  &__title { font-weight: $font-weight-semibold; color: white; font-size: $font-size-base; }
  &__sub { font-size: $font-size-xs; color: rgba(255,255,255,0.6); margin-top: 3px; }
}

// 主体
.dashboard-body {
  padding: $spacing-base;
  animation: fadeSlideUp 0.4s ease both;
}

// 统计行
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-sm;
  margin-bottom: $spacing-xl;
  margin-top: -($spacing-base);
}

.stats-card {
  background: white;
  border-radius: $border-radius;
  padding: $spacing-md $spacing-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  box-shadow: $shadow;

  &__icon { font-size: 22px; }
  &__value {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-extrabold;
    color: $text-primary;
    line-height: 1;
  }
  &__label { font-size: $font-size-xs; color: $text-muted; }
}

// Section
.section {
  margin-bottom: $spacing-xl;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.section-more {
  font-size: $font-size-sm;
  color: $primary;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: $font-weight-medium;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 2px;
  font-family: $font-family-base;
}

// 开始按钮
.start-btn {
  width: 100%;
  background: $gradient-primary;
  border: none;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  cursor: pointer;
  margin-bottom: $spacing-md;
  box-shadow: $shadow-primary;
  transition: all $transition-base;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(67,56,202,0.4);
  }
  &:active { transform: translateY(0); }

  &__icon { font-size: 28px; flex-shrink: 0; }
  &__content { flex: 1; text-align: left; }
  &__title {
    font-size: $font-size-md;
    font-weight: $font-weight-bold;
    color: white;
    margin-bottom: 2px;
  }
  &__sub { font-size: $font-size-xs; color: rgba(255,255,255,0.7); }
  &__arrow { width: 20px; height: 20px; color: rgba(255,255,255,0.7); flex-shrink: 0; }
}

// 快捷操作
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-sm;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: $spacing-md $spacing-sm;
  background: white;
  border: none;
  border-radius: $border-radius;
  cursor: pointer;
  transition: all $transition-base;
  box-shadow: $shadow-sm;

  &:hover { transform: translateY(-2px); box-shadow: $shadow; }
  &:active { transform: scale(0.95); }

  &__icon {
    width: 40px;
    height: 40px;
    border-radius: $border-radius;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }

  &__label { font-size: $font-size-xs; color: $text-secondary; font-weight: $font-weight-medium; }
}

// 岗位列表
.job-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.job-card {
  background: white;
  border-radius: $border-radius;
  padding: $spacing-md;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  cursor: pointer;
  transition: all $transition-base;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;

  &:hover {
    box-shadow: $shadow;
    border-color: $primary;
    transform: translateX(2px);
  }

  &__icon {
    width: 44px;
    height: 44px;
    border-radius: $border-radius;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
  }

  &__info { flex: 1; min-width: 0; }
  &__name {
    font-weight: $font-weight-semibold;
    font-size: $font-size-base;
    color: $text-primary;
    margin-bottom: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  &__stack { font-size: $font-size-xs; color: $text-muted; }

  &__meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    flex-shrink: 0;
  }
  &__avg {
    font-size: $font-size-xs;
    color: $text-muted;
  }
}

// 每日贴士
.daily-tip-card {
  background: linear-gradient(135deg, #FEF3C7 0%, #FEF9C3 100%);
  border: 1px solid #FDE68A;
  border-radius: $border-radius-lg;
  padding: $spacing-base;

  &__header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-weight: $font-weight-semibold;
    color: #92400E;
    font-size: $font-size-sm;
    margin-bottom: $spacing-sm;
  }

  &__content {
    font-size: $font-size-base;
    color: #78350F;
    line-height: $line-height-relaxed;
  }
}
</style>