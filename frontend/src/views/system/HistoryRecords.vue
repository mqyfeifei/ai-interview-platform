
<!--
  =============================================
  frontend/src/views/system/HistoryRecords.vue
  历史记录页组件
  ============================================= -->
<template>
  <div class="history-page">
    <!-- 顶部 Header -->
      <div class="page-header" :style="{ left: isDesktop ? sidebarWidth + 'px' : '0', right: '0' }">
        <div class="page-container">
      <!-- 筛选条放在头部容器中 -->
      <div class="filter-row">
        <div class="filter-tabs">
          <button
            v-for="tab in jobFilterTabs"
            :key="tab.key"
            :class="['filter-tab', { active: activeJobFilter === tab.key }]"
            @click="activeJobFilter = tab.key"
          >{{ tab.label }}</button>
        </div>
        <div class="sort-select-wrap">
          <select v-model="sortOrder" class="sort-select">
            <option value="desc">最新优先</option>
            <option value="duration_desc">时长最长</option>
            <option value="duration_asc">时长最短</option>
            <option value="score_desc">分数最高</option>
            <option value="score_asc">分数最低</option>
          </select>
          <svg class="sort-select-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>
      </div>
    </div>

    <!-- 主体 -->
    <div class="page-body page-container">
      <section class="trend-card">
        <div class="trend-card__head">
          <div class="trend-card__title-wrap">
            <h3>能力成长曲线</h3>
            <span>{{ list.length }} 次面试</span>
          </div>
          <div class="trend-stats">
            <span class="trend-stat">最高分 {{ bestScore || '--' }}</span>
            <span class="trend-stat">平均分 {{ avgScore || '--' }}</span>
          </div>
        </div>
        <div class="curve-tabs">
          <button
            v-for="tab in curveTabs"
            :key="tab.key"
            :class="['curve-tab', { active: activeCurveTab === tab.key }]"
            @click="activeCurveTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div ref="trendChart" class="trend-card__chart" />
      </section>

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
                  <span
                    class="record-job-icon"
                    :style="{ background: jobInfo(record.jobId).colorBg }"
                  >
                    <img
                      v-if="jobInfo(record.jobId).iconUrl"
                      :src="jobInfo(record.jobId).iconUrl"
                      :alt="record.jobName"
                      class="record-job-icon__img"
                    />
                    <span v-else>{{ jobInfo(record.jobId).icon }}</span>
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
                    {{ formatDateTime(record.startTime || record.createdAt) }}
                  </span>
                  <span
                    v-for="(cfgText, cfgIndex) in sessionConfigInlineTexts(record.sessionConfig)"
                    :key="`${record.id}-cfg-${cfgIndex}`"
                    class="meta-item meta-item--plain"
                  >
                    {{ cfgText }}
                  </span>
                </div>
                <div class="record-info__tags">
                  <span v-for="tag in (record.highlightTags || [])" :key="`h-${record.id}-${tag}`" class="tag-chip tag-chip--good">{{ tag }}</span>
                  <span v-for="tag in (record.weaknessTags || [])" :key="`w-${record.id}-${tag}`" class="tag-chip tag-chip--weak">{{ tag }}</span>
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
        <template v-if="activeJobFilter !== 'all'">
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
import { fetchJobs } from '@/api/job'  // 从后端获取岗位列表
import { getGrowthCurve } from '@/api/learning'
import { JOB_TYPES } from '@/utils/constants'
let echarts = null

const PAGE_SIZE = 10

export default {
  name: 'HistoryRecords',
  data() {
    return {
      list: [],
      jobs: [],          // 所有已注册岗位
      total: 0,
      loading: true,
      loadingMore: false,
      page: 1,
      activeJobFilter: 'all',
      sortOrder: 'desc',
      // header height handled via CSS variable
      sidebarWidth: 0,
      isDesktop: false,
      growthData: null,
      trendChart: null,
      activeCurveTab: 'overall',
      curveTabs: [
        { key: 'overall', label: '面试得分' },
        { key: 'technical', label: '技术正确性' },
        { key: 'logic', label: '逻辑严谨性' },
        { key: 'matching', label: '岗位匹配度' },
        { key: 'expression', label: '表达沟通' },
        { key: 'adaptability', label: '应变能力' }
      ]
    }
  },
  computed: {
    jobFilterTabs() {
      const tabs = [{ key: 'all', label: '全部' }]
      let arr = this.jobs
      if (!Array.isArray(arr)) {
        console.warn('HistoryRecords: jobs payload is not array', arr)
        arr = []
      }
      for (let i = 0; i < arr.length; i++) {
        const j = arr[i]
        try {
          const key = this.computeJobKey(j)
          // 使用数据库中的完整名称作为筛选标签，避免去掉关键字导致误解
          const label = j.name || ''
          tabs.push({ key, label })
        } catch (e) {
          console.error('jobFilterTabs item error', j, e)
        }
      }
      return tabs
    },

    filteredList() {
      let arr = [...this.list]

      if (this.activeJobFilter !== 'all') {
        arr = arr.filter(r => {
          let key = r.jobId
          if (!key) {
            // try match against jobs list by name to get correct key
            const jobRec = (this.jobs || []).find(j => j.name === r.jobName)
            key = jobRec ? this.computeJobKey(jobRec) : this.computeJobKey({ name: r.jobName })
          }
          return key === this.activeJobFilter
        })
      }

      // 排序
      arr.sort((a, b) => {
        if (this.sortOrder === 'desc') return new Date(b.createdAt) - new Date(a.createdAt)
        if (this.sortOrder === 'duration_desc') return (b.duration || 0) - (a.duration || 0)
        if (this.sortOrder === 'duration_asc') return (a.duration || 0) - (b.duration || 0)
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

    currentCurveScores() {
      if (this.activeCurveTab === 'overall') {
        const overall = this.growthData?.overall || []
        if (overall.length) {
          return overall.map(i => Number(i.score) || 0)
        }
        return this.list.map(r => Number(r.totalScore) || 0)
      }
      const dimensions = this.growthData?.dimensions || {}
      return (dimensions[this.activeCurveTab] || []).map(v => Number(v) || 0)
    },

    bestScore() {
      if (!this.currentCurveScores.length) return null
      return Math.max(...this.currentCurveScores)
    },

    avgScore() {
      if (!this.currentCurveScores.length) return null
      return Math.round(this.currentCurveScores.reduce((s, v) => s + v, 0) / this.currentCurveScores.length)
    },

    hasMore() {
      return this.list.length < this.total
    },

    scoreCircumference() {
      return 2 * Math.PI * 19
    }
  },
  async created() {
    await Promise.all([this.loadList(), this.loadJobs(), this.loadGrowthCurve()])
  },
  mounted() {
    this.updateHeights()
    this.updateSidebarWidth()
    this.scrollToTopContent()
    this.initTrendChart()
    window.addEventListener('resize', this.onWindowResize)
  },
  watch: {
    activeCurveTab() {
      this.renderTrendChart()
    },
    growthData() {
      this.renderTrendChart()
    },
    $route() {
      this.$nextTick(() => {
        this.updateSidebarWidth()
        this.updateHeights()
        this.scrollToTopContent()
      })
    }
  },
  beforeDestroy() {
    if (this.trendChart) {
      this.trendChart.dispose()
      this.trendChart = null
    }
    window.removeEventListener('resize', this.onWindowResize)
  },
  methods: {
    onWindowResize() {
      this.updateSidebarWidth()
      this.updateHeights()
      if (this.trendChart) this.trendChart.resize()
    },
    async loadGrowthCurve() {
      this.growthData = await getGrowthCurve()
      this.renderTrendChart()
    },
    async initTrendChart() {
      if (!echarts) {
        echarts = await import('echarts')
      }
      this.renderTrendChart()
    },
    renderTrendChart() {
      if (!echarts || !this.$refs.trendChart) return
      const overall = this.growthData?.overall || []
      const dimensions = this.growthData?.dimensions || {}
      const dateLabels = this.growthData?.realDates || this.growthData?.dates || []
      let xData = []
      let yRaw = []
      let seriesName = '面试得分'
      let lineColor = '#7c3aed'
      if (this.activeCurveTab === 'overall') {
        xData = overall.map(i => i.label)
        yRaw = overall.map(i => i.score)
      } else {
        xData = dateLabels
        yRaw = dimensions[this.activeCurveTab] || []
        const labelMap = {
          technical: '技术正确性',
          logic: '逻辑严谨性',
          matching: '岗位匹配度',
          expression: '表达沟通',
          adaptability: '应变能力'
        }
        const colorMap = {
          technical: '#f59e0b',
          logic: '#3b82f6',
          matching: '#10b981',
          expression: '#8b5cf6',
          adaptability: '#ef4444'
        }
        seriesName = labelMap[this.activeCurveTab] || this.activeCurveTab
        lineColor = colorMap[this.activeCurveTab] || '#7c3aed'
      }
      const safeLength = Math.min(xData.length, yRaw.length)
      if (!safeLength) {
        if (this.trendChart) this.trendChart.clear()
        return
      }
      const safeX = []
      const safeY = []
      for (let i = 0; i < safeLength; i++) {
        const raw = Number(yRaw[i])
        safeX.push(xData[i])
        safeY.push(Number.isFinite(raw) ? Math.max(0, Math.min(100, raw)) : 0)
      }
      if (!this.trendChart) this.trendChart = echarts.init(this.$refs.trendChart)
      this.trendChart.setOption({
        grid: { top: 36, left: 36, right: 20, bottom: 28 },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: safeX },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{
          name: seriesName,
          type: 'line',
          smooth: true,
          data: safeY,
          lineStyle: { color: lineColor, width: 3 },
          itemStyle: { color: lineColor },
          areaStyle: { color: `${lineColor}1f` },
          symbolSize: 8,
          label: {
            show: true,
            position: 'top',
            formatter: ({ value }) => `${Math.round(Number(value) || 0)}`,
            color: '#1e293b',
            fontSize: 11,
            fontWeight: 700,
            backgroundColor: 'rgba(255,255,255,0.9)',
            borderColor: lineColor,
            borderWidth: 1,
            borderRadius: 8,
            padding: [2, 6]
          }
        }]
      })
    },

    updateSidebarWidth() {
      this.isDesktop = window.innerWidth >= 1024
      if (this.isDesktop) {
        const side = document.querySelector('.app-shell__side') || document.querySelector('.side-nav')
        const w = side ? Math.round(side.getBoundingClientRect().width) : 0
        this.sidebarWidth = w
      } else {
        this.sidebarWidth = 0
      }
    },

    // when entering page, move viewport down so header doesn't cover first record
    scrollToTopContent() {
      const header = this.$el.querySelector('.page-header')
      if (header) {
        const h = header.offsetHeight
        if (window.scrollY < h) {
          window.scrollTo({ top: h, behavior: 'auto' })
        }
      }
    },
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
    async loadJobs() {
      try {
        const all = await fetchJobs()
        this.jobs = Array.isArray(all) ? all : []
      } catch (e) {
        console.warn('加载岗位列表失败', e)
        this.jobs = []
      }
    },
    clearFilters() {
      this.activeJobFilter = 'all'
    },

    goToReport(record) {
      this.$router.push(`/interview/report/${record.id}`)
    },

    // 根据岗位名称推断前端使用的 key，与后端 _job_to_front_key 同步
    computeJobKey(job) {
      if (!job) return null
      const name = (job.name || '').toLowerCase()
      if (name.includes('java')) return 'java-backend'
      if (name.includes('前端') || name.includes('frontend') || name.includes('web')) return 'web-frontend'
      if (name.includes('python') || name.includes('算法')) return 'python-algorithm'
      if (name.includes('全栈')) return 'fullstack'
      if (name.includes('android')) return 'android'
      if (name.includes('devops')) return 'devops'
      if (name.includes('视觉') || name.includes('cv')) return 'cv'
      return String(job.id)
    },

    jobInfo(jobId) {
      const normalizedKey = String(jobId)

      // 优先从数据库加载的 job 列表获取 icon_url/icon
      const dbJob = (this.jobs || []).find(j => String(j.id) === normalizedKey || this.computeJobKey(j) === normalizedKey)
      if (dbJob) {
        const iconUrl = dbJob.icon_url || dbJob.icon || null
        const icon = iconUrl ? null : (dbJob.icon || '🎯')
        const colorBg = dbJob.colorBg || dbJob.color_bg || '#EEF2FF'
        return {
          icon,
          iconUrl: iconUrl && !iconUrl.startsWith('#') ? iconUrl : null,
          colorBg
        }
      }

      // 兼容 constants 里配置（作为兜底）
      const constJob = JOB_TYPES.find(j => j.id === normalizedKey || String(j.dbId) === normalizedKey)
      if (constJob) {
        return { icon: constJob.icon || '🎯', iconUrl: null, colorBg: constJob.colorBg || '#EEF2FF' }
      }

      // 最后兜底
      return { icon: '🎯', iconUrl: null, colorBg: '#EEF2FF' }
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
    sessionConfigInlineTexts(sessionConfig) {
      if (!sessionConfig) return []
      return [
        sessionConfig.interviewRoundText || '',
        sessionConfig.interviewStyleText || '',
        sessionConfig.targetSourceText || ''
      ].filter(Boolean)
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
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    },
    formatDateTime(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hh = String(d.getHours()).padStart(2, '0')
      const mm = String(d.getMinutes()).padStart(2, '0')
      return `${y}-${m}-${day} ${hh}:${mm}`
    },

    updateHeights() {
      this.$nextTick(() => {
        const header = this.$el.querySelector('.page-header')
        if (header) {
          header.style.setProperty('--header-height', header.offsetHeight + 'px')
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.history-page {
  min-height: 100vh;
  background: #f5f7fb;
  padding-bottom: $bottom-nav-height;
}

// ---- Header ----
.page-header {
  background: #fff;
  padding: 0; /* 头部自身不额外增加高度 */
  position: sticky;
  top: 0; left: 0; right: 0;
  z-index: 45;
  border-bottom: 1px solid #eaeef3;
  box-shadow: 0 1px 8px rgba(31,45,61,.05);
  height: auto;
  max-height: none;
  --header-height: 0px;

  .page-container {
    margin: 0 auto;
    padding: 12px 20px; /* 控制内容上下间距 */
  }

  &::before {
    content: none;
  }

  &__top {
    display: flex; align-items: flex-start; /* 让标题靠上对齐 */
    justify-content: space-between;
    margin-bottom: 0;
    position: relative; z-index: 1;
  }

  &__text {
    margin-top: 0;
  }

  &__text {
    h1 {
      font-family: $font-family-base;
      font-size: 21px; font-weight: $font-weight-bold;
      color: #202b42; margin-bottom: 4px;
    }
    p { font-size: 14px; color: #738096; margin: 0; }
  }
}

// ---- Body ----
.page-body {
  padding:0;
  /* 给出一定间距，但不需要完整头部高度 */
  padding-top: $spacing-md; /* 缩减顶部间距 */
}

.filter-row {
  display: flex; align-items: center;
  justify-content: space-between;
  gap: $spacing-sm;
  margin-top: 8px;
  background: #fff;
  border: 1px solid #e4eaf2;
  border-radius: 6px;
  padding: 8px $spacing-lg;
  width: 100%;
  box-sizing: border-box;
}

/* PC端样式：在较宽屏幕上加入左右边距以避开侧边栏 */
@media (min-width: 1024px) {
  .filter-row {
    /* desktop offset handled by inline left/right binding */
  }
}

.filter-tabs {
  display: flex; gap: $spacing-sm;
  overflow-x: auto; flex: 1;
  &::-webkit-scrollbar { display: none; }
}

.filter-tab {
  padding: 8px 16px; border-radius: 8px;
  border: 1.5px solid $border-color; background: white;
  font-size: 14px; font-weight: $font-weight-medium;
  color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  white-space: nowrap; flex-shrink: 0;

  &.active { background: $primary-bg; border-color: $primary; color: $primary; }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

// 排序下拉
.sort-select-wrap {
  position: relative; flex-shrink: 0;
}

.sort-select {
  appearance: none;
  padding: 9px 30px 9px 14px;
  border: 1.5px solid $border-color; border-radius: 6px;
  background: white; font-size: 14px; color: $text-secondary;
  font-family: $font-family-base; cursor: pointer; outline: none;
  transition: border-color $transition-fast;
  &:focus { border-color: $primary; }
}

.sort-select-icon {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: $text-muted; pointer-events: none;
}

// ---- 骨架屏 ----
.loading-wrap { display: flex; flex-direction: column; gap: $spacing-lg; }

.skeleton-card {
  height: 96px; border-radius: 6px;
  background: linear-gradient(90deg, $gray-100 25%, $gray-200 37%, $gray-100 63%);
  background-size: 400px 100%;
  animation: skeleton-loading 1.4s ease infinite;
}

@keyframes skeleton-loading {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}

// ---- 月份分组 ----
.month-group { margin-bottom: $spacing-xl; }

.month-label {
  font-size: 14px; font-weight: $font-weight-bold;
  color: $text-muted; text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: $spacing-md;
  display: flex; align-items: center; gap: $spacing-sm;
  &::after { content: ''; flex: 1; height: 1px; background: $border-color; }
}

.record-list { display: flex; flex-direction: column; gap: $spacing-md; }

.trend-card {
  background: #fff;
  border: 1px solid #e8edf5;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 14px;
}

.trend-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  flex-wrap: wrap;
}

.trend-card__title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trend-card__head h3 {
  margin: 0;
  font-size: 16px;
}

.trend-stats {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.trend-stat {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.curve-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin-bottom: 10px;
}

.curve-tab {
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  padding: 4px 10px;
  cursor: pointer;
  white-space: nowrap;

  &.active {
    border-color: #7c3aed;
    color: #7c3aed;
    background: #f5f3ff;
  }
}

.trend-card__chart {
  height: 220px;
}

.record-info__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.tag-chip {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 8px;
}

.tag-chip--good {
  background: #dcfce7;
  color: #166534;
}

.tag-chip--weak {
  background: #fee2e2;
  color: #991b1b;
}

// ---- 记录卡片 ----
.record-card {
  background: white; border-radius: 6px;
  padding: $spacing-lg;
  display: flex; align-items: center; gap: $spacing-md;
  cursor: pointer; transition: all $transition-fast;
  border: 1px solid #e3e8f0; box-shadow: 0 1px 3px rgba(31,45,61,.08);
  animation: fadeSlideUp 0.3s ease both;

  &:hover {
    border-color: #6a86b8;
    box-shadow: 0 4px 12px rgba(37,72,132,.16);
    transform: translateX(2px);
  }
  &:active { transform: translateX(1px) scale(0.99); }
}

// 得分圆环
.record-score {
  position: relative; width: 52px; height: 52px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.score-svg {
  position: absolute; inset: 0; width: 100%; height: 100%;
}

.score-num {
  font-family: $font-family-display;
  font-size: 18px; font-weight: $font-weight-extrabold;
  position: relative; z-index: 1; line-height: 1;
}

// 记录信息
.record-info {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 8px;

  &__top {
    display: flex; align-items: center; gap: 10px;
    flex-wrap: wrap;
  }
}

.record-job-icon {
  width: 32px; height: 32px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; flex-shrink: 0;
  overflow: hidden;
}

.record-job-icon__img {
  width: 20px;
  height: 20px;
  object-fit: contain;
  display: block;
}
.record-job-name {
  font-size: 17px; font-weight: $font-weight-semibold;
  color: $text-primary; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.grade-pill {
  font-size: 14px; font-weight: $font-weight-semibold;
  padding: 4px 10px; border-radius: 8px; flex-shrink: 0;

  &.grade-excellent { background: $success-bg; color: darken($success, 10%); }
  &.grade-good { background: $info-bg; color: $info; }
  &.grade-average { background: $warning-bg; color: darken($warning, 20%); }
  &.grade-pass { background: $gray-100; color: $text-secondary; }
  &.grade-fail { background: $danger-bg; color: $danger; }
}

.record-info__meta {
  display: flex; align-items: center; gap: $spacing-lg; flex-wrap: wrap;
}

.meta-item {
  display: flex; align-items: center; gap: 4px;
  font-size: 14px; color: $text-muted;
  svg { width: 13px; height: 13px; }
}

.meta-item--plain {
  gap: 0;
  color: $text-muted;
}

.record-arrow {
  width: 18px; height: 18px; color: $gray-300; flex-shrink: 0;
  transition: color $transition-fast;
  .record-card:hover & { color: $primary; }
}

// ---- 加载更多 ----
.load-more {
  display: flex; justify-content: center;
  padding: $spacing-xl 0;
}

.load-more-btn {
  display: flex; align-items: center; gap: $spacing-sm;
  padding: 12px $spacing-2xl; border-radius: 8px;
  border: 1.5px solid $border-color; background: white;
  font-size: 16px; color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  &:hover { border-color: $primary; color: $primary; background: $primary-bg; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}

.mini-spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid $primary-bg; border-top-color: $primary;
  animation: spin 0.8s linear infinite; flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

// ---- 空态 ----
.empty-state-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-4xl $spacing-2xl;
  gap: $spacing-md; text-align: center;
}

.empty-title {
  font-size: 20px; font-weight: $font-weight-semibold;
  color: $text-secondary; margin-top: $spacing-sm;
}

.empty-sub { font-size: 16px; color: $text-muted; line-height: $line-height-relaxed; }
</style>
