
<!--
  =============================================
  frontend/src/views/system/HistoryRecords.vue
  历史记录页组件
  ============================================= -->
<template>
  <div class="history-page">
    <!-- 顶部 Header -->
    <div class="page-header">
      <div class="page-header__top">
        <div class="page-header__text">
          <h1>历史记录</h1>
          <p>共 {{ totalCount }} 次面试练习</p>
        </div>
        <!-- 统计概览徽章 -->
        <div class="header-stats">
          <div class="header-stat">
            <span class="header-stat__value">{{ bestScore || '--' }}</span>
            <span class="header-stat__label">最高分</span>
          </div>
          <div class="header-stat-divider" />
          <div class="header-stat">
            <span class="header-stat__value">{{ avgScore || '--' }}</span>
            <span class="header-stat__label">平均分</span>
          </div>
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <span class="search-box__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索岗位名称..."
          class="search-box__input"
        />
        <button v-if="searchQuery" class="search-box__clear" @click="searchQuery = ''">✕</button>
      </div>
    </div>

    <!-- 主体 -->
    <div class="page-body">

      <!-- 岗位筛选 -->
      <div class="filter-row">
        <div class="filter-tabs">
          <button
            v-for="tab in jobFilterTabs"
            :key="tab.key"
            :class="['filter-tab', { active: activeJobFilter === tab.key }]"
            @click="activeJobFilter = tab.key"
          >{{ tab.label }}</button>
        </div>

        <!-- 排序 -->
        <div class="sort-select-wrap">
          <select v-model="sortOrder" class="sort-select">
            <option value="desc">最新优先</option>
            <option value="asc">最早优先</option>
            <option value="score_desc">分数最高</option>
            <option value="score_asc">分数最低</option>
          </select>
          <svg class="sort-select-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-wrap">
        <div class="skeleton-card" v-for="n in 3" :key="n" />
      </div>

      <!-- 历史列表 -->
      <template v-else-if="filteredList.length > 0">
        <!-- 分组（按月） -->
        <div
          v-for="group in groupedList"
          :key="group.month"
          class="month-group"
        >
          <div class="month-label">{{ group.month }}</div>

          <div class="record-list">
            <div
              v-for="(record, idx) in group.records"
              :key="record.id"
              class="record-card"
              :style="{ animationDelay: idx * 0.05 + 's' }"
              @click="goToReport(record)"
            >
              <!-- 左侧：得分圆环 -->
              <div class="record-score">
                <svg class="score-svg" viewBox="0 0 48 48">
                  <circle cx="24" cy="24" r="19" fill="none" stroke="#F1F5F9" stroke-width="4"/>
                  <circle
                    cx="24" cy="24" r="19"
                    fill="none"
                    :stroke="scoreColor(record.totalScore)"
                    stroke-width="4"
                    stroke-linecap="round"
                    :stroke-dasharray="scoreCircumference"
                    :stroke-dashoffset="computeOffset(record.totalScore)"
                    transform="rotate(-90 24 24)"
                    style="transition: stroke-dashoffset 0.8s ease"
                  />
                </svg>
                <span class="score-num" :style="{ color: scoreColor(record.totalScore) }">{{ record.totalScore }}</span>
              </div>

              <!-- 中间：信息 -->
              <div class="record-info">
                <div class="record-info__top">
                  <span class="record-job-icon" :style="{ background: jobInfo(record.jobId).colorBg }">
                    {{ jobInfo(record.jobId).icon }}
                  </span>
                  <h3 class="record-job-name">{{ record.jobName }}</h3>
                  <span :class="['grade-pill', gradePill(record.totalScore).cls]">
                    {{ gradePill(record.totalScore).label }}
                  </span>
                </div>

                <div class="record-info__meta">
                  <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                    {{ formatDuration(record.duration) }}
                  </span>
                  <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    {{ record.questionCount }} 题
                  </span>
                  <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    {{ formatDate(record.createdAt) }}
                  </span>
                </div>
              </div>

              <!-- 右侧：箭头 -->
              <svg class="record-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore" class="load-more">
          <button class="load-more-btn" :disabled="loadingMore" @click="loadMore">
            <span v-if="loadingMore" class="mini-spinner" />
            {{ loadingMore ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </template>

      <!-- 空态 -->
      <div v-else-if="!loading" class="empty-state-wrap">
        <template v-if="searchQuery || activeJobFilter !== 'all'">
          <span style="font-size:48px">🔍</span>
          <p>没有匹配的记录</p>
          <button class="btn btn-ghost btn-sm" @click="clearFilters">清空筛选</button>
        </template>
        <template v-else>
          <span style="font-size:52px">🎯</span>
          <p class="empty-title">还没有面试记录</p>
          <p class="empty-sub">完成第一次模拟面试，开始记录你的成长轨迹</p>
          <button class="btn btn-primary" style="margin-top:16px" @click="$router.push('/interview/select')">
            开始第一次面试
          </button>
        </template>
      </div>

    </div>
  </div>
</template>

<script>
import { getHistoryList } from '@/api/report'
import { JOB_TYPES } from '@/utils/constants'

const PAGE_SIZE = 10

export default {
  name: 'HistoryRecords',
  data() {
    return {
      list: [],
      total: 0,
      loading: true,
      loadingMore: false,
      page: 1,
      searchQuery: '',
      activeJobFilter: 'all',
      sortOrder: 'desc'
    }
  },
  computed: {
    jobFilterTabs() {
      // 动态生成出现过的岗位筛选Tab
      const appeared = [...new Set(this.list.map(r => r.jobId))]
      const tabs = [{ key: 'all', label: '全部' }]
      appeared.forEach(id => {
        const info = JOB_TYPES.find(j => j.id === id)
        if (info) tabs.push({ key: id, label: info.icon + ' ' + info.name.replace('开发', '').replace('工程师', '') })
      })
      return tabs
    },

    filteredList() {
      let arr = [...this.list]

      if (this.activeJobFilter !== 'all') {
        arr = arr.filter(r => r.jobId === this.activeJobFilter)
      }

      if (this.searchQuery.trim()) {
        const q = this.searchQuery.toLowerCase()
        arr = arr.filter(r => r.jobName.toLowerCase().includes(q))
      }

      // 排序
      arr.sort((a, b) => {
        if (this.sortOrder === 'desc') return new Date(b.createdAt) - new Date(a.createdAt)
        if (this.sortOrder === 'asc') return new Date(a.createdAt) - new Date(b.createdAt)
        if (this.sortOrder === 'score_desc') return b.totalScore - a.totalScore
        if (this.sortOrder === 'score_asc') return a.totalScore - b.totalScore
        return 0
      })

      return arr
    },

    groupedList() {
      const groups = {}
      this.filteredList.forEach(r => {
        const d = new Date(r.createdAt)
        const key = `${d.getFullYear()}年${d.getMonth() + 1}月`
        if (!groups[key]) groups[key] = []
        groups[key].push(r)
      })
      return Object.entries(groups).map(([month, records]) => ({ month, records }))
    },

    totalCount() { return this.total },

    bestScore() {
      if (!this.list.length) return null
      return Math.max(...this.list.map(r => r.totalScore))
    },

    avgScore() {
      if (!this.list.length) return null
      return Math.round(this.list.reduce((s, r) => s + r.totalScore, 0) / this.list.length)
    },

    hasMore() {
      return this.list.length < this.total
    },

    scoreCircumference() {
      return 2 * Math.PI * 19
    }
  },
  async created() {
    await this.loadList()
  },
  methods: {
    async loadList() {
      this.loading = true
      try {
        const { list, total } = await getHistoryList({ page: 1, pageSize: PAGE_SIZE })
        this.list = list
        this.total = total
        this.page = 1
      } catch (e) {
        console.error('加载历史记录失败', e)
      } finally {
        this.loading = false
      }
    },

    async loadMore() {
      if (this.loadingMore || !this.hasMore) return
      this.loadingMore = true
      try {
        const nextPage = this.page + 1
        const { list } = await getHistoryList({ page: nextPage, pageSize: PAGE_SIZE })
        this.list.push(...list)
        this.page = nextPage
      } finally {
        this.loadingMore = false
      }
    },

    clearFilters() {
      this.searchQuery = ''
      this.activeJobFilter = 'all'
    },

    goToReport(record) {
      this.$router.push(`/interview/report/${record.id}`)
    },

    jobInfo(jobId) {
      return JOB_TYPES.find(j => j.id === jobId) || { icon: '🎯', colorBg: '#EEF2FF' }
    },

    scoreColor(score) {
      if (score >= 85) return '#10B981'
      if (score >= 75) return '#3B82F6'
      if (score >= 65) return '#F59E0B'
      return '#EF4444'
    },

    computeOffset(score) {
      return this.scoreCircumference * (1 - score / 100)
    },

    gradePill(score) {
      if (score >= 90) return { label: '优秀', cls: 'grade-excellent' }
      if (score >= 80) return { label: '良好', cls: 'grade-good' }
      if (score >= 70) return { label: '中等', cls: 'grade-average' }
      if (score >= 60) return { label: '及格', cls: 'grade-pass' }
      return { label: '待提升', cls: 'grade-fail' }
    },

    formatDuration(seconds) {
      if (!seconds) return '--'
      const m = Math.floor(seconds / 60)
      const s = seconds % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },

    formatDate(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      const now = new Date()
      const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24))
      if (diffDays === 0) return '今天'
      if (diffDays === 1) return '昨天'
      if (diffDays < 7) return `${diffDays}天前`
      return `${d.getMonth() + 1}/${d.getDate()}`
    }
  }
}
</script>

<style lang="scss" scoped>
.history-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// ---- Header ----
.page-header {
  background: $gradient-primary;
  padding: 52px $spacing-base $spacing-lg;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 300px; height: 300px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 70%);
    top: -80px; right: -60px; pointer-events: none;
  }

  &__top {
    display: flex; align-items: flex-start;
    justify-content: space-between;
    margin-bottom: $spacing-base;
    position: relative; z-index: 1;
  }

  &__text {
    h1 {
      font-family: $font-family-display;
      font-size: $font-size-2xl; font-weight: $font-weight-extrabold;
      color: white; margin-bottom: 4px;
    }
    p { font-size: $font-size-sm; color: rgba(255,255,255,0.65); }
  }
}

.header-stats {
  display: flex; align-items: center; gap: $spacing-lg;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-lg;
  padding: $spacing-sm $spacing-base;
}

.header-stat {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  &__value {
    font-family: $font-family-display;
    font-size: $font-size-xl; font-weight: $font-weight-extrabold;
    color: white; line-height: 1;
  }
  &__label { font-size: $font-size-xs; color: rgba(255,255,255,0.55); }
}

.header-stat-divider { width: 1px; height: 28px; background: rgba(255,255,255,0.2); }

.search-box {
  position: relative; z-index: 1;

  &__icon {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    color: $text-muted; display: flex; align-items: center; pointer-events: none;
    svg { width: 16px; height: 16px; }
  }

  &__input {
    width: 100%; height: 44px;
    padding: 0 38px 0 42px;
    background: white; border: none;
    border-radius: $border-radius-full;
    font-size: $font-size-base; color: $text-primary;
    outline: none; font-family: $font-family-base;
    box-shadow: $shadow-md;
    &::placeholder { color: $text-muted; }
  }

  &__clear {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    background: $gray-200; border: none;
    width: 20px; height: 20px; border-radius: 50%;
    cursor: pointer; font-size: $font-size-xs; color: $text-muted;
    display: flex; align-items: center; justify-content: center;
    &:hover { background: $gray-300; }
  }
}

// ---- Body ----
.page-body { padding: $spacing-base; }

.filter-row {
  display: flex; align-items: center;
  justify-content: space-between;
  gap: $spacing-sm;
  margin-bottom: $spacing-base;
}

.filter-tabs {
  display: flex; gap: $spacing-xs;
  overflow-x: auto; flex: 1;
  &::-webkit-scrollbar { display: none; }
}

.filter-tab {
  padding: 6px 14px; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  font-size: $font-size-xs; font-weight: $font-weight-medium;
  color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  white-space: nowrap; flex-shrink: 0;

  &.active { background: $primary; border-color: $primary; color: white; }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

// 排序下拉
.sort-select-wrap {
  position: relative; flex-shrink: 0;
}

.sort-select {
  appearance: none;
  padding: 7px 28px 7px 12px;
  border: 1.5px solid $border-color; border-radius: $border-radius;
  background: white; font-size: $font-size-xs; color: $text-secondary;
  font-family: $font-family-base; cursor: pointer; outline: none;
  transition: border-color $transition-fast;
  &:focus { border-color: $primary; }
}

.sort-select-icon {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 14px; height: 14px; color: $text-muted; pointer-events: none;
}

// ---- 骨架屏 ----
.loading-wrap { display: flex; flex-direction: column; gap: $spacing-md; }

.skeleton-card {
  height: 88px; border-radius: $border-radius-lg;
  background: linear-gradient(90deg, $gray-100 25%, $gray-200 37%, $gray-100 63%);
  background-size: 400px 100%;
  animation: skeleton-loading 1.4s ease infinite;
}

@keyframes skeleton-loading {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}

// ---- 月份分组 ----
.month-group { margin-bottom: $spacing-lg; }

.month-label {
  font-size: $font-size-xs; font-weight: $font-weight-bold;
  color: $text-muted; text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: $spacing-sm;
  display: flex; align-items: center; gap: $spacing-sm;
  &::after { content: ''; flex: 1; height: 1px; background: $border-color; }
}

.record-list { display: flex; flex-direction: column; gap: $spacing-sm; }

// ---- 记录卡片 ----
.record-card {
  background: white; border-radius: $border-radius-lg;
  padding: $spacing-md $spacing-base;
  display: flex; align-items: center; gap: $spacing-md;
  cursor: pointer; transition: all $transition-base;
  border: 1.5px solid $border-color; box-shadow: $shadow-sm;
  animation: fadeSlideUp 0.4s ease both;

  &:hover {
    border-color: $primary;
    box-shadow: $shadow-md;
    transform: translateX(3px);
  }
  &:active { transform: scale(0.99); }
}

// 得分圆环
.record-score {
  position: relative; width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.score-svg {
  position: absolute; inset: 0; width: 100%; height: 100%;
}

.score-num {
  font-family: $font-family-display;
  font-size: $font-size-base; font-weight: $font-weight-extrabold;
  position: relative; z-index: 1; line-height: 1;
}

// 记录信息
.record-info {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 6px;

  &__top {
    display: flex; align-items: center; gap: $spacing-sm;
  }
}

.record-job-icon {
  width: 28px; height: 28px; border-radius: $border-radius-sm;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0;
}

.record-job-name {
  font-size: $font-size-base; font-weight: $font-weight-semibold;
  color: $text-primary; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.grade-pill {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 2px 8px; border-radius: $border-radius-full; flex-shrink: 0;

  &.grade-excellent { background: $success-bg; color: darken($success, 10%); }
  &.grade-good { background: $info-bg; color: $info; }
  &.grade-average { background: $warning-bg; color: darken($warning, 20%); }
  &.grade-pass { background: $gray-100; color: $text-secondary; }
  &.grade-fail { background: $danger-bg; color: $danger; }
}

.record-info__meta {
  display: flex; align-items: center; gap: $spacing-base; flex-wrap: wrap;
}

.meta-item {
  display: flex; align-items: center; gap: 3px;
  font-size: $font-size-xs; color: $text-muted;
  svg { width: 11px; height: 11px; }
}

.record-arrow {
  width: 16px; height: 16px; color: $gray-300; flex-shrink: 0;
  transition: color $transition-fast;
  .record-card:hover & { color: $primary; }
}

// ---- 加载更多 ----
.load-more {
  display: flex; justify-content: center;
  padding: $spacing-lg 0;
}

.load-more-btn {
  display: flex; align-items: center; gap: $spacing-sm;
  padding: 10px $spacing-xl; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  font-size: $font-size-sm; color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  &:hover { border-color: $primary; color: $primary; background: $primary-bg; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}

.mini-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid $primary-bg; border-top-color: $primary;
  animation: spin 0.8s linear infinite; flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

// ---- 空态 ----
.empty-state-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-4xl $spacing-xl;
  gap: $spacing-sm; text-align: center;
}

.empty-title {
  font-size: $font-size-lg; font-weight: $font-weight-semibold;
  color: $text-secondary; margin-top: $spacing-sm;
}

.empty-sub { font-size: $font-size-sm; color: $text-muted; line-height: $line-height-relaxed; }
</style>