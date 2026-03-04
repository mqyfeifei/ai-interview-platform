<template>
  <div class="learning-page">
    <!-- 顶部 Header -->
    <div class="page-header">
      <div class="page-header__inner">
        <div class="page-header__text">
          <h1>学习中心</h1>
          <p>持续学习，突破短板</p>
        </div>
        <div class="page-header__badge" v-if="dailyPlan">
          <span class="progress-badge">
            {{ completedTaskCount }}/{{ totalTaskCount }}
            <span class="progress-badge__label">今日完成</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 主体 -->
    <div class="page-body">

      <!-- 每日学习计划 -->
      <section class="section" v-if="dailyPlan">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-title__icon">📅</span>
            今日学习计划
          </h2>
          <span class="plan-date">{{ todayLabel }}</span>
        </div>

        <!-- 整体进度条 -->
        <div class="plan-progress-bar">
          <div
            class="plan-progress-bar__fill"
            :style="{ width: planProgressPct + '%' }"
          />
        </div>

        <div class="plan-card">
          <div
            v-for="task in dailyPlan.tasks"
            :key="task.id"
            :class="['plan-task', { done: task.done }]"
            @click="toggleTask(task)"
          >
            <div :class="['plan-task__check', { done: task.done }]">
              <svg v-if="task.done" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <div class="plan-task__body">
              <p class="plan-task__title">{{ task.title }}</p>
              <p class="plan-task__desc">{{ task.desc }}</p>
            </div>
            <div class="plan-task__meta">
              <span :class="['task-type-tag', 'task-type-' + task.type]">{{ taskTypeLabel(task.type) }}</span>
              <span class="task-time">{{ task.estimatedMinutes }}min</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 能力成长曲线 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-title__icon">📈</span>
            能力成长曲线
          </h2>
        </div>

        <!-- 维度切换 -->
        <div class="curve-tabs">
          <button
            v-for="tab in curveTabs"
            :key="tab.key"
            :class="['curve-tab', { active: activeCurveTab === tab.key }]"
            @click="switchCurveTab(tab.key)"
          >{{ tab.label }}</button>
        </div>

        <div class="chart-card">
          <div v-if="!growthData" class="chart-loading">
            <div class="mini-spinner" />
          </div>
          <div v-else ref="lineChart" class="line-chart" />
        </div>
      </section>

      <!-- 技能短板分析 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-title__icon">🎯</span>
            技能短板
          </h2>
          <span class="weakness-count">{{ weaknesses.length }} 项待提升</span>
        </div>

        <div class="weakness-cloud">
          <span
            v-for="w in weaknesses"
            :key="w.id"
            :class="['weakness-tag', 'weakness-' + w.level]"
            @click="filterByWeakness(w)"
          >
            {{ w.tag }}
            <span class="weakness-tag__level-dot" />
          </span>
        </div>

        <div class="weakness-legend">
          <span class="legend-dot legend-dot--high" />高频短板
          <span class="legend-dot legend-dot--medium" style="margin-left:12px" />中频短板
          <span class="legend-dot legend-dot--low" style="margin-left:12px" />低频短板
        </div>
      </section>

      <!-- 个性化推荐 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-title__icon">💡</span>
            推荐学习资源
          </h2>
          <span v-if="activeWeaknessFilter" class="filter-chip" @click="clearWeaknessFilter">
            {{ activeWeaknessFilter }} ✕
          </span>
        </div>

        <!-- 类型筛选 -->
        <div class="type-filters">
          <button
            v-for="f in typeFilters"
            :key="f.key"
            :class="['type-filter-btn', { active: activeTypeFilter === f.key }]"
            @click="activeTypeFilter = f.key"
          >
            <span>{{ f.icon }}</span>
            <span>{{ f.label }}</span>
          </button>
        </div>

        <!-- 资源卡片列表 -->
        <div v-if="filteredRecommendations.length > 0" class="resource-list">
          <div
            v-for="(res, idx) in filteredRecommendations"
            :key="res.id"
            class="resource-card"
            :style="{ animationDelay: idx * 0.05 + 's' }"
          >
            <!-- 类型图标 + 难度 -->
            <div class="resource-card__top">
              <div :class="['resource-type-icon', 'type-' + res.type]">
                {{ typeIcon(res.type) }}
              </div>
              <span :class="['difficulty-badge', 'diff-' + res.difficulty]">{{ res.difficulty }}</span>
              <span class="resource-card__time">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ res.readTime }}
              </span>
            </div>

            <!-- 标题 + 摘要 -->
            <h3 class="resource-card__title">{{ res.title }}</h3>
            <p class="resource-card__summary">{{ res.summary }}</p>

            <!-- 标签 -->
            <div class="resource-card__tags">
              <span v-for="tag in res.tags.slice(0, 3)" :key="tag" class="res-tag">{{ tag }}</span>
              <span class="res-source">来源：{{ res.source }}</span>
            </div>

            <!-- 关联短板 -->
            <div v-if="res.relatedWeakness" class="resource-card__weakness">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;flex-shrink:0">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              针对短板：{{ res.relatedWeakness }}
            </div>

            <!-- 操作按钮 -->
            <div class="resource-card__actions">
              <button
                :class="['action-bookmark', { active: res.bookmarked }]"
                @click.stop="handleBookmark(res)"
                :title="res.bookmarked ? '取消收藏' : '收藏'"
              >
                <svg viewBox="0 0 24 24" :fill="res.bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                </svg>
                {{ res.bookmarked ? '已收藏' : '收藏' }}
              </button>

              <button
                v-if="!res.completed"
                class="action-complete"
                @click.stop="handleComplete(res)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                标记完成
              </button>
              <span v-else class="action-done">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                已完成
              </span>
            </div>
          </div>
        </div>

        <!-- 空态 -->
        <div v-else class="empty-state-wrap">
          <span style="font-size:44px">📭</span>
          <p>暂无匹配的学习资源</p>
          <button class="btn btn-ghost btn-sm" @click="activeTypeFilter = 'all'; clearWeaknessFilter()">清空筛选</button>
        </div>
      </section>

      <div style="height: 80px;" />
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import BottomNav from '@/components/common/BottomNav.vue'
// import { INTERVIEW_DIMENSIONS } from '@/utils/constants'

let echarts = null
const CURVE_COLORS = {
  overall: '#4338CA',
  technical: '#F59E0B',
  logic: '#3B82F6',
  matching: '#10B981',
  expression: '#8B5CF6',
  adaptability: '#EF4444'
}

export default {
  name: 'LearningCenter',
  components: { BottomNav },
  data() {
    return {
      activeCurveTab: 'overall',
      activeTypeFilter: 'all',
      activeWeaknessFilter: null,
      chartInstance: null,
      curveTabs: [
        { key: 'overall', label: '综合' },
        { key: 'technical', label: '技术' },
        { key: 'logic', label: '逻辑' },
        { key: 'matching', label: '匹配' },
        { key: 'expression', label: '表达' },
        { key: 'adaptability', label: '应变' }
      ],
      typeFilters: [
        { key: 'all', label: '全部', icon: '🌐' },
        { key: 'article', label: '文章', icon: '📄' },
        { key: 'video', label: '视频', icon: '🎬' },
        { key: 'practice', label: '练习', icon: '✏️' },
        { key: 'example', label: '范例', icon: '⭐' }
      ]
    }
  },
  computed: {
    ...mapGetters('learning', [
      'growthData', 'weaknesses', 'recommendations',
      'dailyPlan', 'completedTaskCount', 'totalTaskCount'
    ]),

    todayLabel() {
      const d = new Date()
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    planProgressPct() {
      if (!this.totalTaskCount) return 0
      return Math.round(this.completedTaskCount / this.totalTaskCount * 100)
    },

    filteredRecommendations() {
      let list = this.recommendations
      if (this.activeTypeFilter !== 'all') {
        list = list.filter(r => r.type === this.activeTypeFilter)
      }
      if (this.activeWeaknessFilter) {
        list = list.filter(r => r.relatedWeakness === this.activeWeaknessFilter || r.tags.includes(this.activeWeaknessFilter))
      }
      return list
    }
  },
  async created() {
    
    if (!this.growthData) {
      this.$store.dispatch('learning/loadAll')
    }
  },
  mounted() {
    
    this.initECharts()
  },
  beforeUnmount() {
    if (this.chartInstance) { this.chartInstance.dispose(); this.chartInstance = null }
  },
  watch: {
    growthData() {
      this.$nextTick(() => this.renderChart())
    },
    activeCurveTab() {
      this.$nextTick(() => this.renderChart())
    }
  },
  methods: {
    ...mapActions('learning', ['toggleBookmark', 'markCompleted', 'updateTaskStatus']),

    async initECharts() {
      if (!echarts) {
        try {
          echarts = await import('echarts')
        } catch (e) {
          console.warn('ECharts 未安装，折线图不可用。运行: npm install echarts', e)
          return
        }
      }
      this.$nextTick(() => { if (this.growthData) this.renderChart() })

    },

    renderChart() {
      if (!echarts || !this.$refs.lineChart || !this.growthData) return
      if (!this.chartInstance) {
        this.chartInstance = echarts.init(this.$refs.lineChart)
        const ro = new ResizeObserver(() => this.chartInstance?.resize())
        ro.observe(this.$refs.lineChart)
      }

      const isOverall = this.activeCurveTab === 'overall'
      const color = CURVE_COLORS[this.activeCurveTab]

      const dimLabels = { technical: '技术正确性', logic: '逻辑严谨性', matching: '岗位匹配度', expression: '表达沟通', adaptability: '应变能力' }

      let xData, seriesData
      if (isOverall) {
        xData = this.growthData.overall.map(d => d.date)
        seriesData = [{
          name: '综合得分',
          data: this.growthData.overall.map(d => d.score),
          color
        }]
      } else {
        xData = this.growthData.dates
        seriesData = [{
          name: dimLabels[this.activeCurveTab] || this.activeCurveTab,
          data: this.growthData.dimensions[this.activeCurveTab] || [],
          color
        }]
      }

      this.chartInstance.setOption({
        backgroundColor: 'transparent',
        grid: { top: 20, right: 16, bottom: 32, left: 40 },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#1E293B',
          borderColor: 'transparent',
          textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: "'Noto Sans SC'" },
          formatter: params => {
            const p = params[0]
            return `<div style="padding:4px 8px">${p.name}<br/><b style="font-size:16px;color:${color}">${p.value}</b> 分</div>`
          }
        },
        xAxis: {
          type: 'category', data: xData,
          axisLine: { lineStyle: { color: '#E2E8F0' } },
          axisTick: { show: false },
          axisLabel: { color: '#94A3B8', fontSize: 11, fontFamily: "'Noto Sans SC'" }
        },
        yAxis: {
          type: 'value', min: 40, max: 100, splitNumber: 4,
          axisLabel: { color: '#94A3B8', fontSize: 11 },
          splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } },
          axisLine: { show: false }, axisTick: { show: false }
        },
        series: seriesData.map(s => ({
            name: s.name, type: 'line', data: s.data,
            smooth: true, symbol: 'circle', symbolSize: 7,
            itemStyle: { color: s.color, borderColor: 'white', borderWidth: 2 },
            lineStyle: { color: s.color, width: 2.5 },
            areaStyle: { color: s.color + '28' },
            // })),
        // series: seriesData.map(s => ({
        //   name: s.name, type: 'line', data: s.data,
        //   smooth: true, symbol: 'circle', symbolSize: 7,
        //   itemStyle: { color: s.color, borderColor: 'white', borderWidth: 2 },
        //   lineStyle: { color: s.color, width: 2.5 },
        //   areaStyle: {
        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        //       { offset: 0, color: s.color + '40' },
        //       { offset: 1, color: s.color + '00' }
        //     ])
        //   },
          markPoint: {
            data: [{ type: 'max', name: '最高' }],
            label: { color: 'white', fontSize: 10 },
            itemStyle: { color: s.color }
          }
        })),
        animation: true,
        animationDuration: 800,
        animationEasing: 'cubicOut'
      }, true)
    },

    switchCurveTab(key) {
      this.activeCurveTab = key
    },

    async toggleTask(task) {
      await this.updateTaskStatus({ taskId: task.id, done: !task.done })
    },

    filterByWeakness(weakness) {
      this.activeWeaknessFilter = this.activeWeaknessFilter === weakness.tag ? null : weakness.tag
    },

    clearWeaknessFilter() {
      this.activeWeaknessFilter = null
    },

    async handleBookmark(res) {
      await this.toggleBookmark({ resourceId: res.id, bookmarked: !res.bookmarked })
    },

    async handleComplete(res) {
      await this.markCompleted(res.id)
    },

    typeIcon(type) {
      const map = { article: '📄', video: '🎬', practice: '✏️', example: '⭐' }
      return map[type] || '📚'
    },

    taskTypeLabel(type) {
      const map = { review: '复习', practice: '练习', exercise: '训练' }
      return map[type] || type
    }
  }
}
</script>

<style lang="scss" scoped>
.learning-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// ---- Header ----
.page-header {
  background: $gradient-primary;
  padding: 52px $spacing-base $spacing-xl;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 300px; height: 300px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 70%);
    top: -80px; right: -60px; pointer-events: none;
  }

  &__inner {
    display: flex; align-items: flex-start;
    justify-content: space-between;
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

.progress-badge {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: $border-radius-lg;
  padding: $spacing-sm $spacing-md;
  font-family: $font-family-display;
  font-size: $font-size-2xl; font-weight: $font-weight-extrabold;
  color: white; line-height: 1;
  min-width: 60px; text-align: center;
  backdrop-filter: blur(4px);

  &__label { font-size: $font-size-xs; color: rgba(255,255,255,0.6); font-weight: $font-weight-regular; margin-top: 4px; font-family: $font-family-base; }
}

// ---- Body ----
.page-body { padding: $spacing-base; }

.section { margin-bottom: $spacing-xl; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title {
  display: flex; align-items: center; gap: $spacing-sm;
  font-size: $font-size-lg; font-weight: $font-weight-bold; color: $text-primary;
  &__icon { font-size: 18px; }
}

// ---- 每日计划 ----
.plan-date { font-size: $font-size-sm; color: $text-muted; }

.plan-progress-bar {
  height: 5px; background: $gray-200; border-radius: 3px;
  overflow: hidden; margin-bottom: $spacing-md;

  &__fill {
    height: 100%; border-radius: 3px;
    background: $gradient-primary;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

.plan-card {
  background: white; border-radius: $border-radius-lg;
  overflow: hidden; box-shadow: $shadow-sm; border: 1px solid $border-color;
}

.plan-task {
  display: flex; align-items: flex-start; gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  border-bottom: 1px solid $gray-100;
  cursor: pointer; transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: $gray-50; }

  &.done .plan-task__title { text-decoration: line-through; color: $text-muted; }
  &.done .plan-task__desc { color: $gray-300; }

  &__check {
    width: 22px; height: 22px; border-radius: 50%;
    border: 2px solid $border-color; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    margin-top: 1px; transition: all $transition-base;
    color: white;

    &.done { background: $primary; border-color: $primary; }
    svg { width: 11px; height: 11px; }
  }

  &__body { flex: 1; min-width: 0; }
  &__title { font-size: $font-size-base; font-weight: $font-weight-medium; color: $text-primary; margin-bottom: 3px; }
  &__desc { font-size: $font-size-xs; color: $text-muted; line-height: $line-height-normal; }

  &__meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
}

.task-time { font-size: $font-size-xs; color: $text-muted; }

.task-type-tag {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 2px 8px; border-radius: $border-radius-full;
  &.task-type-review { background: $info-bg; color: $info; }
  &.task-type-practice { background: $warning-bg; color: darken($warning, 20%); }
  &.task-type-exercise { background: $success-bg; color: darken($success, 10%); }
}

// ---- 成长曲线 ----
.curve-tabs {
  display: flex; gap: $spacing-xs;
  overflow-x: auto; padding-bottom: 2px;
  margin-bottom: $spacing-md;
  &::-webkit-scrollbar { display: none; }
}

.curve-tab {
  padding: 6px 14px; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  font-size: $font-size-sm; font-weight: $font-weight-medium;
  color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  white-space: nowrap; flex-shrink: 0;

  &.active { background: $primary; border-color: $primary; color: white; box-shadow: 0 4px 12px rgba(67,56,202,0.3); }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

.chart-card {
  background: white; border-radius: $border-radius-lg;
  padding: $spacing-base; box-shadow: $shadow-sm; border: 1px solid $border-color;
  min-height: 220px; display: flex; align-items: stretch;
}

.chart-loading {
  flex: 1; display: flex; align-items: center; justify-content: center;
}

.mini-spinner {
  width: 28px; height: 28px; border-radius: 50%;
  border: 3px solid $primary-bg; border-top-color: $primary;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.line-chart { width: 100%; height: 200px; }

// ---- 技能短板 ----
.weakness-count { font-size: $font-size-sm; color: $text-muted; }

.weakness-cloud {
  display: flex; flex-wrap: wrap; gap: $spacing-sm;
  margin-bottom: $spacing-md;
}

.weakness-tag {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 7px $spacing-md; border-radius: $border-radius-full;
  font-size: $font-size-sm; font-weight: $font-weight-medium;
  cursor: pointer; transition: all $transition-base;
  border: 1.5px solid transparent;
  animation: scaleIn 0.3s $transition-spring both;

  &:hover { transform: translateY(-2px) scale(1.04); box-shadow: $shadow; }
  &:active { transform: scale(0.97); }

  &.weakness-high {
    background: $danger-bg; color: $danger; border-color: rgba($danger, 0.2);
    font-size: $font-size-base; font-weight: $font-weight-semibold;
  }
  &.weakness-medium {
    background: $warning-bg; color: darken($warning, 20%); border-color: rgba($warning, 0.2);
  }
  &.weakness-low {
    background: $gray-100; color: $text-secondary; border-color: $gray-200;
    font-size: $font-size-xs;
  }

  &__level-dot {
    width: 6px; height: 6px; border-radius: 50%;
    .weakness-high & { background: $danger; }
    .weakness-medium & { background: $warning; }
    .weakness-low & { background: $gray-400; }
  }
}

.weakness-legend {
  display: flex; align-items: center;
  font-size: $font-size-xs; color: $text-muted;
}

.legend-dot {
  width: 8px; height: 8px; border-radius: 50%; margin-right: 4px;
  &--high { background: $danger; }
  &--medium { background: $warning; }
  &--low { background: $gray-400; }
}

// ---- 推荐资源 ----
.filter-chip {
  background: $primary-bg; color: $primary;
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 4px 10px; border-radius: $border-radius-full;
  cursor: pointer; transition: background $transition-fast;
  &:hover { background: darken(#EEF2FF, 4%); }
}

.type-filters {
  display: flex; gap: $spacing-xs; overflow-x: auto;
  padding-bottom: 2px; margin-bottom: $spacing-base;
  &::-webkit-scrollbar { display: none; }
}

.type-filter-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 7px 14px; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  font-size: $font-size-sm; font-weight: $font-weight-medium;
  color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  white-space: nowrap; flex-shrink: 0;

  &.active { background: $primary; border-color: $primary; color: white; box-shadow: 0 4px 12px rgba(67,56,202,0.3); }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

.resource-list { display: flex; flex-direction: column; gap: $spacing-md; }

.resource-card {
  background: white; border-radius: $border-radius-lg;
  padding: $spacing-base; box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  transition: box-shadow $transition-base, transform $transition-base;
  animation: fadeSlideUp 0.4s ease both;

  &:hover { box-shadow: $shadow-md; transform: translateY(-1px); }
}

.resource-card__top {
  display: flex; align-items: center; gap: $spacing-sm;
  margin-bottom: $spacing-sm;
}

.resource-type-icon {
  width: 32px; height: 32px; border-radius: $border-radius-sm;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; flex-shrink: 0;

  &.type-article { background: #DBEAFE; }
  &.type-video { background: #FEE2E2; }
  &.type-practice { background: #D1FAE5; }
  &.type-example { background: #FEF3C7; }
}

.difficulty-badge {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 2px 8px; border-radius: $border-radius-full;
  &.diff-初级 { background: $success-bg; color: darken($success, 10%); }
  &.diff-中级 { background: $info-bg; color: $info; }
  &.diff-高级 { background: $warning-bg; color: darken($warning, 20%); }
}

.resource-card__time {
  display: flex; align-items: center; gap: 3px;
  font-size: $font-size-xs; color: $text-muted;
  margin-left: auto;
}

.resource-card__title {
  font-size: $font-size-base; font-weight: $font-weight-bold;
  color: $text-primary; margin-bottom: $spacing-xs;
  line-height: $line-height-tight;
}

.resource-card__summary {
  font-size: $font-size-sm; color: $text-secondary;
  line-height: $line-height-normal;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: $spacing-sm;
}

.resource-card__tags {
  display: flex; flex-wrap: wrap; align-items: center;
  gap: $spacing-xs; margin-bottom: $spacing-sm;
}

.res-tag {
  font-size: $font-size-xs; background: $gray-100;
  color: $text-secondary; padding: 2px 8px;
  border-radius: $border-radius-full; border: 1px solid $gray-200;
}

.res-source {
  font-size: $font-size-xs; color: $text-muted;
  margin-left: auto;
}

.resource-card__weakness {
  display: flex; align-items: center; gap: $spacing-xs;
  font-size: $font-size-xs; color: $primary;
  background: $primary-bg; border-radius: $border-radius-sm;
  padding: 4px 10px; margin-bottom: $spacing-md;
  font-weight: $font-weight-medium;
}

.resource-card__actions {
  display: flex; align-items: center; gap: $spacing-sm;
  padding-top: $spacing-sm; border-top: 1px solid $gray-100;
}

.action-bookmark {
  display: flex; align-items: center; gap: 4px;
  padding: 6px $spacing-md; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  font-size: $font-size-xs; font-weight: $font-weight-medium;
  color: $text-secondary; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  svg { width: 14px; height: 14px; }

  &.active { border-color: $primary; color: $primary; background: $primary-bg; }
  &:hover { border-color: $primary; color: $primary; }
}

.action-complete {
  display: flex; align-items: center; gap: 4px;
  padding: 6px $spacing-md; border-radius: $border-radius-full;
  border: 1.5px solid $success; background: white;
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  color: $success; cursor: pointer;
  font-family: $font-family-base; transition: all $transition-fast;
  svg { width: 13px; height: 13px; }
  &:hover { background: $success-bg; }
}

.action-done {
  display: flex; align-items: center; gap: 4px;
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  color: $success;
  svg { width: 13px; height: 13px; }
}

// ---- 空态 ----
.empty-state-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-3xl $spacing-xl;
  gap: $spacing-md;
  p { color: $text-muted; font-size: $font-size-base; }
}
</style>