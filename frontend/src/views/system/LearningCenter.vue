
<!--
  =============================================
  frontend/src/views/system/LearningCenter.vue
  学习中心页组件
  ============================================= -->
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

        <div v-if="enableCharts">
          <!-- 维度切换 -->
          <div class="curve-tabs">
            <button
              v-for="tab in curveTabs"
              :key="tab.key"
              :class="['curve-tab', { active: activeCurveTab === tab.key }]"
              @click="switchCurveTab(tab.key)"
            >{{ tab.label }}</button>
          </div>

          <div class="chart-card" style="position:relative">
            <div ref="lineChart" class="line-chart" />
            <div v-if="!growthData" class="chart-loading chart-loading--overlay">
              <div class="mini-spinner" />
            </div>
          </div>
        </div>
        <div v-else class="chart-card chart-card--disabled">
          <p>能力成长曲线图表暂时关闭，不影响其它学习功能使用。</p>
        </div>
      </section>

      <!-- 技能短板分析 -->
      <section class="section">
        <div class="section-header clickable weakness-header" @click="toggleWeakness">
          <h2 class="section-title">
            <span class="section-title__icon">🎯</span>
            技能短板
            <span class="weakness-count">{{ (weaknesses || []).length }} 项待提升</span>
          </h2>
          <svg class="collapse-icon" :class="{ open: showWeaknessSection }" viewBox="0 0 24 24">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        <transition name="collapse">
        <div v-if="showWeaknessSection">
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

        <!-- 掌握度可视化图 -->
        <div class="weakness-chart-card" v-if="enableCharts">
          <div class="weakness-chart-header">
            <span class="weakness-chart-title">📊 掌握度分布</span>
            <span class="weakness-chart-hint">数值越低 = 越需提升</span>
          </div>
          <div ref="weaknessChart" class="weakness-chart" :style="{ height: Math.max(180, (weaknesses || []).length * 36 + 24) + 'px' }" />
          <div v-if="!weaknesses || weaknesses.length === 0" class="chart-empty chart-loading--overlay">
            <span style="font-size:36px">📊</span>
            <p>暂无短板数据</p>
          </div>
        </div>
        <div class="weakness-chart-card chart-card--disabled" v-else>
          <p>掌握度可视化图表暂时关闭，您仍可通过上面的短板标签进行学习资源筛选。</p>
        </div>

        <div class="weakness-legend">
          <span class="legend-dot" style="background:#EF4444" />薄弱 (&lt;40)
          <span class="legend-dot" style="background:#F59E0B;margin-left:12px" />一般 (40-70)
          <span class="legend-dot" style="background:#10B981;margin-left:12px" />良好 (70-90)
          <span class="legend-dot" style="background:#6366F1;margin-left:12px" />优秀 (≥90)
        </div>
        </div> <!-- end collapsible wrapper -->
        </transition>
      </section>

      <!-- 个性化推荐 -->
      <section class="section">
        <div class="section-header clickable resource-header" @click="toggleResources">
          <h2 class="section-title">
            <span class="section-title__icon">💡</span>
            推荐学习资源
          </h2>
          <span v-if="activeWeaknessFilter" class="filter-chip" @click.stop="clearWeaknessFilter">
            {{ activeWeaknessFilter }} ✕
          </span>
          <svg class="collapse-icon" :class="{ open: showResourceSection }" viewBox="0 0 24 24">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        <transition name="collapse">
        <div v-if="showResourceSection">
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

        <!-- 资源卡片列表 (带排序动画) -->
        <transition-group
          v-if="filteredRecommendations.length > 0"
          name="resource-move"
          tag="div"
          class="resource-list"
        >
          <div
            v-for="(res, idx) in filteredRecommendations"
            :key="res.id"
            :class="['resource-card', { 'resource-card--completed': res.completed, 'match-weakness': activeWeaknessFilter && (res.relatedWeakness === activeWeaknessFilter || (res.tags || []).includes(activeWeaknessFilter)) }]"
            :style="{ animationDelay: idx * 0.05 + 's' }"
            @click="openResource(res)"
          >
            <!-- 类型图标 + 难度 -->
            <div class="resource-card__top">
              <div :class="['resource-type-icon', 'type-' + res.type]">
                {{ typeIcon(res.type) }}
              </div>
              <span :class="['difficulty-badge', 'diff-' + res.difficulty]">{{ res.difficulty }}</span>
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

            <!-- 完成标志徽章 -->
            <div v-if="res.completed" class="resource-card__completed-badge">✓ 已完成</div>
          </div>
        </transition-group>

        <!-- 空态 -->
        <div v-else class="empty-state-wrap">
          <span style="font-size:44px">📭</span>
          <p>暂无匹配的学习资源</p>
          <button class="btn btn-ghost btn-sm" @click="activeTypeFilter = 'all'; clearWeaknessFilter()">清空筛选</button>
        </div>
        </div> <!-- end showResourceSection wrapper -->
        </transition>
      </section>

    </div>

    <!-- 资源详情弹窗 -->
    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="showResourceDetail" class="resource-modal-overlay" @click.self="closeResource">
          <div class="resource-modal">
            <!-- 头部 -->
            <div class="resource-modal__header">
              <div :class="['resource-type-icon', 'type-' + (selectedResource.type || 'article')]">
                {{ typeIcon(selectedResource.type) }}
              </div>
              <div class="resource-modal__header-text">
                <span :class="['difficulty-badge', 'diff-' + (selectedResource.difficulty || '')]">{{ selectedResource.difficulty }}</span>
                <span class="resource-modal__time">⏱ {{ selectedResource.readTime }}</span>
              </div>
              <button class="resource-modal__close" @click="closeResource">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            <!-- 标题 -->
            <h2 class="resource-modal__title">{{ selectedResource.title }}</h2>

            <!-- 来源 -->
            <div class="resource-modal__source">
              <span>来源：{{ selectedResource.source || '未知' }}</span>
              <span v-if="selectedResource.relatedWeakness" class="resource-modal__weakness">
                ⚡ 针对短板：{{ selectedResource.relatedWeakness }}
              </span>
            </div>

            <!-- 摘要/内容 -->
            <div class="resource-modal__content">
              <p>{{ selectedResource.summary || '暂无详细内容' }}</p>
            </div>

            <!-- 标签 -->
            <div v-if="selectedResource.tags && selectedResource.tags.length" class="resource-modal__tags">
              <span v-for="tag in selectedResource.tags" :key="tag" class="res-tag">{{ tag }}</span>
            </div>

            <!-- 操作按钮 -->
            <div class="resource-modal__actions">
              <button class="modal-btn modal-btn--primary" @click="goToResource(selectedResource)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                {{ selectedResource.url ? '前往学习' : '开始学习' }}
              </button>
              <button
                :class="['modal-btn', selectedResource.bookmarked ? 'modal-btn--bookmarked' : 'modal-btn--outline']"
                @click="handleBookmark(selectedResource)"
              >
                {{ selectedResource.bookmarked ? '★ 已收藏' : '☆ 收藏' }}
              </button>
              <button
                v-if="!selectedResource.completed"
                class="modal-btn modal-btn--success"
                @click="handleComplete(selectedResource); closeResource()"
              >✓ 标记完成</button>
              <span v-else class="modal-done-label">✓ 已完成</span>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

  </div>
</template>

<script>
import { markRaw } from 'vue'
import { mapGetters, mapActions } from 'vuex'
// import { INTERVIEW_DIMENSIONS } from '@/utils/constants'

// 图表渲染总开关
// 如再次出现浏览器侧 ECharts 报错，可临时改为 false 关闭图表，仅保留其它学习功能
const ENABLE_CHARTS = true
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
  data() {
    return {
      enableCharts: ENABLE_CHARTS,
      activeCurveTab: 'overall',
      activeTypeFilter: 'all',
      activeWeaknessFilter: null,
      // collapse flags for sections
      showWeaknessSection: false,
      showResourceSection: false,
      chartInstance: null,
      weaknessChartInstance: null,
      showResourceDetail: false,
      selectedResource: {},
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
        // "book" 类型已统一为 "course"（课程）
        { key: 'course', label: '书籍', icon: '📖' },
        { key: 'bookmarked', label: '收藏', icon: '⭐' }
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
      let list = this.recommendations || []
      // 收藏筛选
      if (this.activeTypeFilter === 'bookmarked') {
        list = list.filter(r => r.bookmarked)
      } else if (this.activeTypeFilter !== 'all') {
        // 兼容后端可能仍返回 type='book' 的情况，把它映射到 course
        const filterType = this.activeTypeFilter === 'course' ? 'course' : this.activeTypeFilter
        list = list.filter(r => (r.type === filterType) || (filterType === 'course' && r.type === 'book'))
      }
      // 短板筛选
      if (this.activeWeaknessFilter) {
        const tag = this.activeWeaknessFilter
        list = list.filter(r => {
          // exact relatedWeakness match
          if (r.relatedWeakness === tag) return true
          // any tag equals or contains the weakness text
          if ((r.tags || []).some(t => t === tag || t.includes(tag))) return true
          // fallback: try matching title/summary body text
          if (r.title && r.title.includes(tag)) return true
          if (r.summary && r.summary.includes(tag)) return true
          return false
        })
      }
      // 排序：未完成的在前，已完成的在后（带动画效果）
      return [...list].sort((a, b) => {
        if (a.completed === b.completed) return 0
        return a.completed ? 1 : -1
      })
    }
  },
  async created() {
    
    if (!this.growthData) {
      this.$store.dispatch('learning/loadAll')
    }
  },
  mounted() {
    this.initECharts()
    this.updateHeights()
    window.addEventListener('resize', this.updateHeights)
  },
  beforeUnmount() {
    if (this.chartInstance) { this.chartInstance.dispose(); this.chartInstance = null }
    if (this.weaknessChartInstance) { this.weaknessChartInstance.dispose(); this.weaknessChartInstance = null }
    window.removeEventListener('resize', this.updateHeights)
  },
  watch: {
    growthData(newVal) {
      if (newVal && echarts && this.enableCharts) this.safeRenderChart()
    },
    activeCurveTab() {
      if (echarts && this.growthData && this.enableCharts) this.safeRenderChart()
    },
    weaknesses(newVal) {
      if (newVal && newVal.length && echarts && this.enableCharts) this.safeRenderWeaknessChart()
    }
  },
  methods: {
    ...mapActions('learning', ['toggleBookmark', 'markCompleted', 'updateTaskStatus']),
    toggleWeakness() {
      const opening = !this.showWeaknessSection;
      this.showWeaknessSection = opening;
      if (!opening) {
        // dispose existing chart when collapsing so it will be recreated
        if (this.weaknessChartInstance && !this.weaknessChartInstance.isDisposed()) {
          this.weaknessChartInstance.dispose();
        }
        this.weaknessChartInstance = null;
      }
      this.$nextTick(() => {
        this.updateHeights();
        if (opening && this.enableCharts && this.weaknesses && this.weaknesses.length) {
          // second tick to ensure DOM layout is complete
          this.$nextTick(() => {
            this.safeRenderWeaknessChart();
          });
        }
      });
    },
    toggleResources() {
      this.showResourceSection = !this.showResourceSection;
      this.$nextTick(() => this.updateHeights());
    },

    updateHeights() {
      this.$nextTick(() => {
        const header = this.$el.querySelector('.page-header');
        if (header) {
          header.style.setProperty('--header-height', header.offsetHeight + 'px');
        }
      });
    },

    async initECharts() {
      if (!this.enableCharts) return
      if (!echarts) {
        try {
          echarts = await import('echarts')
        } catch (e) {
          console.warn('ECharts 未安装，折线图不可用。运行: npm install echarts', e)
          return
        }
      }
      // ECharts 加载完成后，如果数据已经就绪，则触发渲染
      if (this.growthData) this.safeRenderChart()
      if (this.weaknesses && this.weaknesses.length) this.safeRenderWeaknessChart()
    },

    /**
     * 安全渲染：确保容器有有效尺寸后再调用 ECharts
     * ECharts 在容器尺寸为 0 时会导致 coordinateSystem 为 undefined
     */
    safeRenderChart(retries = 0) {
      const el = this.$refs.lineChart
      if (!el || !echarts || retries > 10) return
      if (el.clientWidth === 0 || el.clientHeight === 0) {
        // 容器尚未完成布局，下一帧重试
        requestAnimationFrame(() => this.safeRenderChart(retries + 1))
        return
      }
      this.renderChart()
    },

    safeRenderWeaknessChart(retries = 0) {
      const el = this.$refs.weaknessChart
      if (!el || !echarts || retries > 10) return
      if (el.clientWidth === 0 || el.clientHeight === 0) {
        requestAnimationFrame(() => this.safeRenderWeaknessChart(retries + 1))
        return
      }
      this.renderWeaknessChart()
    },

    renderChart() {
      const el = this.$refs.lineChart
      if (!echarts || !el || !this.growthData) return
      if (el.clientWidth === 0 || el.clientHeight === 0) return
      
      // 防御性检查：确保数据结构完整
      const { overall, dimensions, dates, realDates } = this.growthData
      if (!overall || !dimensions || !dates) return
      if (!overall.length && !dates.length) return
      
      // 复用实例或创建新实例（使用 markRaw 避免被 Vue3 响应式代理）
      if (!this.chartInstance || this.chartInstance.isDisposed()) {
        this.chartInstance = markRaw(echarts.init(el))
        new ResizeObserver(() => { if (this.chartInstance && !this.chartInstance.isDisposed()) this.chartInstance.resize() }).observe(el)
      }

      const isOverall = this.activeCurveTab === 'overall'
      const color = CURVE_COLORS[this.activeCurveTab]

      const dimLabels = { technical: '技术正确性', logic: '逻辑严谨性', matching: '岗位匹配度', expression: '表达沟通', adaptability: '应变能力' }

      let xData, scoreData, dateData, seriesName
      if (isOverall) {
        scoreData = (overall || []).map(d => d.score)
        dateData = (overall || []).map(d => d.date || d.label || '')
        xData = dateData
        seriesName = '综合得分'
      } else {
        scoreData = (dimensions && dimensions[this.activeCurveTab]) || []
        dateData = realDates || dates || []
        xData = dateData
        seriesName = dimLabels[this.activeCurveTab] || this.activeCurveTab
      }

      // 检查是否有有效数据，避免 ECharts 渲染空系列报错
      if (!xData.length || !scoreData.length) {
        console.warn('图表数据为空，跳过渲染')
        return
      }

      // Y轴自适应范围
      const allScores = scoreData.filter(v => typeof v === 'number')
      const minScore = allScores.length ? Math.min(...allScores) : 0
      const maxScore = allScores.length ? Math.max(...allScores) : 100
      const yMin = Math.max(0, Math.floor((minScore - 10) / 10) * 10)
      const yMax = Math.min(100, Math.ceil((maxScore + 10) / 10) * 10)

      this.chartInstance.setOption({
        backgroundColor: 'transparent',
        grid: { top: 24, right: 16, bottom: 32, left: 40 },
        tooltip: {
          show: true,
          trigger: 'axis',
          confine: true,
          triggerOn: 'mousemove|click',
          backgroundColor: '#1E293B',
          borderColor: 'transparent',
          textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: "'Noto Sans SC'" },
          formatter: params => {
            const p = params[0]
            return `<div style="padding:4px 8px"><b style="font-size:16px;color:${color}">${p.value}</b> 分</div>`
          }
        },
        xAxis: {
          type: 'category', data: xData,
          name: '日期', nameLocation: 'middle', nameGap: 30,
          axisLine: { lineStyle: { color: '#E2E8F0' } },
          axisTick: { show: false },
          axisLabel: { color: '#94A3B8', fontSize: 11, fontFamily: "'Noto Sans SC'" }
        },
        yAxis: {
          type: 'value', min: yMin, max: yMax, splitNumber: 4,
          name: '成绩', nameLocation: 'middle', nameGap: 44, nameTextStyle: { color: '#94A3B8', fontSize: 12 },
          axisLabel: { color: '#94A3B8', fontSize: 11 },
          splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } },
          axisLine: { show: false }, axisTick: { show: false }
        },
        series: [{
          name: seriesName, type: 'line', data: scoreData,
          smooth: false, symbol: 'circle', symbolSize: 8,
          itemStyle: { color: color, borderColor: 'white', borderWidth: 2 },
          lineStyle: { color: color, width: 2.5 },
          areaStyle: { color: color + '18' },
          markPoint: {
            data: [
              { type: 'max', name: '最高' },
              { type: 'min', name: '最低' }
            ],
            label: { color: 'white', fontSize: 10 },
            itemStyle: { color: color },
            symbolSize: 40
          }
        }],
        animation: true,
        animationDuration: 600,
        animationEasing: 'cubicOut'
      }, true)
    },

    switchCurveTab(key) {
      this.activeCurveTab = key
    },

    renderWeaknessChart() {
      const el = this.$refs.weaknessChart
      if (!echarts || !el) return
      if (el.clientWidth === 0 || el.clientHeight === 0) return
      const list = this.weaknesses || []
      if (!list.length) return

      // 复用实例或创建新实例（使用 markRaw 避免被 Vue3 响应式代理）
      if (!this.weaknessChartInstance || this.weaknessChartInstance.isDisposed()) {
        this.weaknessChartInstance = markRaw(echarts.init(el))
        new ResizeObserver(() => { if (this.weaknessChartInstance && !this.weaknessChartInstance.isDisposed()) this.weaknessChartInstance.resize() }).observe(el)
      }

      // 按掌握度升序排列（最弱排最上方）
      const sorted = [...list]
        .filter(w => w.mastery_level !== undefined && w.mastery_level !== null)
        .sort((a, b) => a.mastery_level - b.mastery_level)
      if (!sorted.length) return

      const names = sorted.map(w => w.tag || w.name || '未知')
      const values = sorted.map(w => w.mastery_level)
      const getColor = v => v < 40 ? '#EF4444' : v < 70 ? '#F59E0B' : v < 90 ? '#10B981' : '#6366F1'

      this.weaknessChartInstance.setOption({
        backgroundColor: 'transparent',
        grid: { top: 8, right: 50, bottom: 8, left: 90 },
        tooltip: {
          show: true,
          trigger: 'axis',
          confine: true,
          triggerOn: 'mousemove|click',
          axisPointer: { type: 'shadow' },
          backgroundColor: '#1E293B',
          borderColor: 'transparent',
          textStyle: { color: '#F8FAFC', fontSize: 12, fontFamily: "'Noto Sans SC'" },
          formatter: params => {
            const p = params[params.length - 1]
            const label = p.value < 40 ? '薄弱' : p.value < 70 ? '一般' : p.value < 90 ? '良好' : '优秀'
            const c = getColor(p.value)
            return `<div style="padding:4px 8px">${p.name}<br/>掌握度 <b style="font-size:16px;color:${c}">${p.value}%</b> <span style="color:#94A3B8">(${label})</span></div>`
          }
        },
        xAxis: {
          type: 'value', max: 100, min: 0,
          axisLabel: { show: false },
          splitLine: { show: false },
          axisLine: { show: false },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'category',
          data: names,
          inverse: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: {
            color: '#475569', fontSize: 12,
            width: 78, overflow: 'truncate',
            fontFamily: "'Noto Sans SC'"
          }
        },
        series: [
          {
            type: 'bar', z: 1,
            data: names.map(() => 100),
            barWidth: 14, barGap: '-100%',
            itemStyle: { color: '#F1F5F9', borderRadius: [0, 7, 7, 0] },
            silent: true, animation: false
          },
          {
            type: 'bar', z: 2,
            data: values.map(v => ({
              value: v,
              itemStyle: { color: getColor(v), borderRadius: [0, 7, 7, 0] }
            })),
            barWidth: 14,
            label: {
              show: true, position: 'right',
              color: '#64748B', fontSize: 11, fontWeight: 'bold',
              formatter: '{c}%'
            },
            animationDuration: 1000,
            animationEasing: 'cubicOut'
          }
        ]
      }, true)
    },

    async toggleTask(task) {
      await this.updateTaskStatus({ taskId: task.id, done: !task.done })
    },

    filterByWeakness(weakness) {
      const tag = weakness.tag
      this.activeWeaknessFilter = this.activeWeaknessFilter === tag ? null : tag
      if (this.activeWeaknessFilter) {
        // 展开推荐资源区并滚动到资源列表，提升交互感
        this.showResourceSection = true
        this.$nextTick(() => {
          this.updateHeights()
          const el = this.$el.querySelector('.resource-list')
          if (el && el.scrollIntoView) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        })
      }
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
      // 兼容老数据：book 也视为 course
      const map = { article: '📄', video: '🎬', book: '📖', course: '📖', example: '⭐', bookmarked: '⭐' }
      return map[type] || '📚'
    },

    taskTypeLabel(type) {
      const map = { review: '复习', practice: '练习', exercise: '训练' }
      return map[type] || type
    },

    openResource(res) {
      this.selectedResource = res
      this.showResourceDetail = true
    },

    closeResource() {
      this.showResourceDetail = false
    },

    goToResource(res) {
      // 之前 book 类型被认为需要购买，现在全部视为在线课程
      if (res.url) {
        window.open(res.url, '_blank', 'noopener')
      } else {
        // 无外链时标记为完成
        this.$store.dispatch('learning/markCompleted', res.id)
        this.closeResource()
      }
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

.section { margin-bottom: $spacing-lg; }

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

.chart-loading--overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  display: flex; align-items: center; justify-content: center; flex-direction: column;
  background: white; z-index: 2; border-radius: inherit;
}

.weakness-chart-card {
  background: white; border-radius: $border-radius-lg;
  box-shadow: $shadow-sm; border: 1px solid $border-color;
  padding: $spacing-base; margin-bottom: $spacing-md;
  overflow: hidden;
}

.weakness-chart-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: $spacing-sm;
}

.weakness-chart-title {
  font-size: $font-size-sm; font-weight: $font-weight-semibold;
  color: $text-primary;
}

.weakness-chart-hint {
  font-size: $font-size-xs; color: $text-muted;
}

.weakness-chart { width: 100%; min-height: 180px; }

.chart-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-xl;
  p { color: $text-muted; font-size: $font-size-sm; margin-top: $spacing-sm; }
}

// ---- 技能短板 ----

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
  &.weakness-good {
    background: $success-bg; color: darken($success, 10%); border-color: rgba($success, 0.2);
    font-size: $font-size-xs;
  }
  &.weakness-excellent {
    background: #EEF2FF; color: #6366F1; border-color: rgba(#6366F1, 0.2);
    font-size: $font-size-xs;
  }

  &__level-dot {
    width: 6px; height: 6px; border-radius: 50%;
    .weakness-high & { background: $danger; }
    .weakness-medium & { background: $warning; }
    .weakness-good & { background: $success; }
    .weakness-excellent & { background: #6366F1; }
  }
}

.weakness-legend {
  display: flex; align-items: center;
  font-size: $font-size-xs; color: $text-muted;
}

.weakness-count {
  color: $danger; /* red */
  margin-left: $spacing-sm;
  font-weight: $font-weight-semibold;
  font-size: $font-size-xs;
}

/* collapsible headers */
.section-header.clickable {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md $spacing-lg; /* 增大内边距提升高度 */
  min-height: 56px;
  background: $primary-bg; /* subtle theme color */
  border: 1px solid $primary;
  border-radius: $border-radius-lg;
  transition: background $transition-fast, box-shadow $transition-fast, border-color $transition-fast, color $transition-fast;
  color: $primary;
}
.section-header.clickable:hover {
  background: lighten($primary-bg, 6%);
  box-shadow: $shadow-sm;
  border-color: darken($primary, 10%);
}
.section-header.clickable.open {
  background: $primary;
  border-color: $primary;
  color: white;
}
.section-header.clickable.open:hover {
  background: darken($primary, 7%);
}

/* specific header colors */
.weakness-header {
  background: #EFF8FF; /* very light blue */
  border-color: #7EC8FF; /* soft blue */
  color: #1E40AF; /* blue-900 text */
}
.weakness-header:hover {
  background: #D1F1FF; /* hover: deeper light blue */
  border-color: #3B82F6;
}
.weakness-header.open {
  background: #2563EB; /* open: deeper blue */
  border-color: #2563EB;
  color: white;
}

.resource-header {
  background: #FBF5FF; /* very light purple */
  border-color: #D8B4FF; /* soft purple */
  color: #6B21A8; /* purple-900 text */
}
.resource-header:hover {
  background: #F0E6FF; /* hover: deeper light purple */
  border-color: #A855F7;
}
.resource-header.open {
  background: #7C3AED; /* open: deeper purple */
  border-color: #7C3AED;
  color: white;
}
.collapse-icon {
  width: 18px; height: 18px;
  margin-left: $spacing-sm;
  transition: transform $transition-fast;
  stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
}
.collapse-icon.open { transform: rotate(180deg); }

/* collapse transition */
.collapse-enter-active, .collapse-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
}
.collapse-enter-from, .collapse-leave-to {
  max-height: 0;
  opacity: 0;
}
.collapse-enter-to, .collapse-leave-from {
  max-height: 1000px;
  opacity: 1;
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
  transition: box-shadow $transition-base, transform $transition-base, opacity $transition-base;
  animation: fadeSlideUp 0.4s ease both;
  position: relative;

  &:hover { box-shadow: $shadow-md; transform: translateY(-1px); }

  &--completed {
    opacity: 0.75;
    background: $gray-50;
    border-color: $success-bg;
  }
}

.resource-card.match-weakness {
  border-color: #3B82F6;
  box-shadow: 0 8px 24px rgba(59,130,246,0.08);
  transform: translateY(-2px);
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
  &.type-book { background: #F3E8FF; }
  &.type-example { background: #FEF3C7; }
}

.difficulty-badge {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 2px 8px; border-radius: $border-radius-full;
  &.diff-初级 { background: $success-bg; color: darken($success, 10%); }
  &.diff-中级 { background: $info-bg; color: $info; }
  /* 高难度使用红色警示 */
  &.diff-高级 { background: $danger-bg; color: $danger; }
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

.resource-card__completed-badge {
  position: absolute; top: $spacing-base; right: $spacing-base;
  background: $success; color: white;
  padding: 4px 12px; border-radius: $border-radius-full;
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  animation: slideInRight 0.3s ease;
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

// ---- 资源详情弹窗 ----
.resource-modal-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(4px);
  padding: $spacing-base;
  overflow-y: auto;
}

.resource-modal {
  background: white;
  border-radius: $border-radius-xl;
  width: 100%; max-width: 500px;
  max-height: 90vh; overflow-y: auto;
  padding: $spacing-xl $spacing-base $spacing-3xl;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  animation: zoomIn 0.3s ease;

  &__header {
    display: flex; align-items: center; gap: $spacing-sm;
    margin-bottom: $spacing-md;
  }

  &__header-text {
    display: flex; align-items: center; gap: $spacing-sm; flex: 1;
  }

  &__time {
    font-size: $font-size-xs; color: $text-muted;
  }

  &__close {
    width: 32px; height: 32px; border-radius: 50%;
    background: $gray-100; border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background $transition-fast;
    svg { width: 16px; height: 16px; color: $text-secondary; }
    &:hover { background: $gray-200; }
  }

  &__title {
    font-size: $font-size-xl; font-weight: $font-weight-bold;
    color: $text-primary; line-height: $line-height-tight;
    margin-bottom: $spacing-sm;
  }

  &__source {
    display: flex; align-items: center; gap: $spacing-md;
    font-size: $font-size-sm; color: $text-muted;
    margin-bottom: $spacing-md;
  }

  &__weakness {
    color: $primary; font-weight: $font-weight-medium;
    background: $primary-bg; padding: 2px 8px;
    border-radius: $border-radius-full; font-size: $font-size-xs;
  }

  &__content {
    background: $gray-50; border-radius: $border-radius-lg;
    padding: $spacing-base; margin-bottom: $spacing-md;
    font-size: $font-size-base; color: $text-secondary;
    line-height: $line-height-relaxed;
    border-left: 3px solid $primary;
  }

  &__tags {
    display: flex; flex-wrap: wrap; gap: $spacing-xs;
    margin-bottom: $spacing-lg;
  }

  &__actions {
    display: flex; flex-wrap: wrap; gap: $spacing-sm;
    padding-top: $spacing-md;
    border-top: 1px solid $gray-100;
  }
}

.modal-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-radius: $border-radius-full;
  font-size: $font-size-sm; font-weight: $font-weight-semibold;
  cursor: pointer; border: 1.5px solid transparent;
  font-family: $font-family-base; transition: all $transition-fast;

  &--primary {
    background: $primary; color: white; border-color: $primary;
    &:hover { background: darken(#4338CA, 8%); box-shadow: 0 4px 12px rgba(67,56,202,0.35); }
  }
  &--outline {
    background: white; color: $text-secondary; border-color: $border-color;
    &:hover { border-color: $primary; color: $primary; }
  }
  &--bookmarked {
    background: $primary-bg; color: $primary; border-color: rgba($primary, 0.3);
  }
  &--success {
    background: white; color: $success; border-color: $success;
    &:hover { background: $success-bg; }
  }
}

.modal-done-label {
  display: inline-flex; align-items: center;
  font-size: $font-size-sm; font-weight: $font-weight-semibold;
  color: $success; padding: 10px 20px;
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes zoomIn {
  from { transform: scale(0.95) translateY(-20px); opacity: 0; }
  to { transform: scale(1) translateY(0); opacity: 1; }
}

@keyframes slideInRight {
  from { transform: translateX(20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* 列表排序动画 - 已完成的资源下滑 */
.resource-move-move {
  transition: transform 0.5s ease;
}
.resource-move-enter-active {
  transition: all 0.4s ease;
}
.resource-move-leave-active {
  transition: all 0.3s ease;
  position: absolute;
}
.resource-move-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}
.resource-move-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.modal-fade-enter-active { transition: opacity 0.25s ease; }
.modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-to, .modal-fade-leave-from { opacity: 1; }
</style>