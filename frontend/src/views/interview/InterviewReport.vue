
<!--
  =============================================
  frontend/src/views/interview/InterviewReport.vue
  面试报告页组件
  ============================================= -->
<template>
  <div class="report-page">
    <!-- 顶部导航：修复返回按钮 -->
    <div class="report-nav">
      <button class="back-btn" @click="$router.back()">  <!-- ← 修复：back()替代push('/dashboard') -->
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <span class="report-nav__title">面试报告</span>
      <button class="share-btn" @click="handleShare">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrap">
      <div class="loading-spinner" />
      <p>正在加载面试报告...</p>
    </div>

    <template v-else-if="report">


      <!-- 内容区 -->
      <div class="report-body page-container">
      <!-- 总体得分区 -->
      <div class="report-hero">
          <div class="section-header" style="width:100%; margin-bottom: 0;">
            <h1 class="section-title">
              综合得分
            </h1>
          </div>
        <div class="hero-content">

          <div class="hero-meta">
            <span class="job-badge">{{ report.jobName }}</span>
            <span class="date-text">{{ formatDateTime(report.createdAt) }}</span>
            <span v-if="report.sessionConfig?.interviewRoundText" class="date-text">{{ report.sessionConfig.interviewRoundText }}</span>
            <span v-if="report.sessionConfig?.interviewStyleText" class="date-text">{{ report.sessionConfig.interviewStyleText }}</span>
            <span v-if="report.sessionConfig?.targetSourceText" class="date-text">{{ report.sessionConfig.targetSourceText }}</span>
          </div>
          <div class="hero-score-block">
            <div class="score-number">{{ animatedScore }}</div>
            <div class="score-right">
              <span class="grade-badge" :class="'grade-' + grade.key">{{ grade.label }}</span>
              <span class="grade-desc">{{ grade.desc }}</span>
            </div>
          </div>
          <div class="hero-stats">
            <div class="hero-stat">
              <span class="hero-stat__value">{{ formatDuration(report.duration) }}</span>
              <span class="hero-stat__label">面试时长</span>
            </div>
            <div class="hero-stat-divider" />
            <div class="hero-stat">
              <span class="hero-stat__value">{{ report.questions ? report.questions.length : 0 }}</span>
              <span class="hero-stat__label">回答题目</span>
            </div>
            <!-- <div class="hero-stat-divider" />
            <div class="hero-stat">
              <span class="hero-stat__value">{{ followUpCount }}</span>
              <span class="hero-stat__label">追问次数</span>
            </div> -->
            <!-- 新增：亮点数 -->
<div class="hero-stat-divider" />
<div class="hero-stat">
  <span class="hero-stat__value">{{ report.highlights ? report.highlights.length : 0 }}</span>
  <span class="hero-stat__label">回答亮点</span>
</div>

<!-- 新增：待提升数 -->
<div class="hero-stat-divider" />
<div class="hero-stat">
  <span class="hero-stat__value">{{ report.improvements ? report.improvements.length : 0 }}</span>
  <span class="hero-stat__label">待提升项</span>
</div>
<div class="hero-stat-divider" />
<div class="hero-stat">
  <span class="hero-stat__value">{{ formatDateTime(report.startTime || report.createdAt) }}</span>
  <span class="hero-stat__label">开始时间</span>
</div>
<!-- <div class="hero-stat">
  <span class="hero-stat__value">{{ formatDateTime(report.createdAt) }}</span>
  <span class="hero-stat__label">面试时间</span>
</div>
<div class="hero-stat-divider" /> -->
          </div>
        </div>
      </div>
        <!-- 能力雷达图 -->
        <section class="report-section">
          <div class="section-header">
            <h2 class="section-title">
             能力雷达图
            </h2>
            <div class="legend">
              <span class="legend-item legend-item--you">本次</span>
              <span class="legend-item legend-item--avg">平均</span>
            </div>
          </div>
          <div class="radar-card">
            <div ref="radarChart" class="radar-chart" />
            <div class="dimension-scores">
              <div v-for="dim in dimensionList" :key="dim.key" class="dim-score-item">
                <div class="dim-score-item__left">
                  <span class="dim-score-item__name">{{ dim.label }}</span>
                  <div class="dim-score-bar">
                    <div class="dim-score-bar__fill" :style="{ width: dim.score + '%', background: dim.color }" />
                  </div>
                </div>
                <div class="dim-score-item__right">
                  <span class="dim-score-item__score" :style="{ color: dim.color }">{{ dim.score }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 亮点 -->
        <section class="report-section">
          <h2 class="section-title">回答亮点</h2>
          <div class="highlight-list">
            <div v-for="(h, i) in report.highlights" :key="i" class="highlight-item" :style="{ animationDelay: i * 0.08 + 's' }">
              <div class="highlight-item__dot" />
              <p v-html="renderMarkdown(h)" />
            </div>
          </div>
        </section>

        <!-- 待改进 -->
        <section class="report-section">
          <h2 class="section-title">待提升项</h2>
          <div class="improvement-list">
            <div v-for="(imp, i) in report.improvements" :key="i" class="improvement-item" :style="{ animationDelay: i * 0.08 + 's' }">
              <div class="improvement-item__header">
                <span class="improvement-item__num">{{ i + 1 }}</span>
                <p class="improvement-item__point" v-html="renderMarkdown(imp.point)" />
              </div>
              <div v-if="imp.weaknessTag" class="resource-text" style="margin:4px 0 8px 26px">
                <span class="resource-title">{{ imp.weaknessTag }}</span>
                <span v-if="imp.estimatedHours" class="resource-source">· 预计 {{ imp.estimatedHours }}h</span>
              </div>
              <a
                v-if="imp.resource"
                class="improvement-item__resource"
                :href="imp.resource.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;flex-shrink:0">
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                </svg>
                <div class="resource-text">
                  <span class="resource-title">推荐学习：{{ imp.resource.title || imp.resource.type || '学习资源' }}</span>
                  <span class="resource-source">· {{ imp.resource.source || imp.resource.type || '资料链接' }}</span>
                </div>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;margin-left:auto;flex-shrink:0">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </a>
            </div>
          </div>
        </section>

        <section class="report-section" v-if="recommendedResources.length">
          <div class="section-header">
            <h2 class="section-title">本次面试推荐资源</h2>
            <div style="display:flex;gap:8px;">
              <button class="expand-all-btn" @click="bookmarkAll(true)">一键收藏</button>
              <button class="expand-all-btn" @click="bookmarkAll(false)">一键取消</button>
            </div>
          </div>
          <div class="recommend-row">
            <div v-for="res in recommendedResources" :key="res.id" class="recommend-card">
              <p class="recommend-card__title">{{ res.title }}</p>
              <p class="recommend-card__meta">{{ res.weaknessTag || res.matchedTag || '通用补强' }}</p>
              <div class="recommend-card__actions">
                <button class="reference-btn" @click="toggleRecommendBookmark(res, true)">{{ res.bookmarked ? '已收藏' : '收藏' }}</button>
                <button class="reference-btn" @click="toggleRecommendBookmark(res, false)">取消</button>
              </div>
            </div>
          </div>
        </section>

        <!-- 逐题回顾（含 AI 点评） -->
        <section class="report-section">
          <div class="section-header">
            <h2 class="section-title">逐题回顾</h2>
            <button class="expand-all-btn" @click="toggleAllQuestions">
              {{ allExpanded ? '全部收起' : '全部展开' }}
            </button>
          </div>

          <!-- 点评加载提示 -->
          <div v-if="analysisLoading" class="analysis-loading-tip">
            <div class="analysis-loading-tip__dot" />
            <span>AI 正在生成逐题点评，请稍候...</span>
          </div>

          <div class="question-list">
            <div
              v-for="(q, idx) in report.questions"
              :key="q.id"
              class="question-item"
              :class="{ expanded: expandedItems.includes(q.id) }"
            >
              <div class="question-item__header" @click="toggleQuestion(q.id)">
                <div class="question-item__left">
                  <div class="q-index">
                    Q{{ idx + 1 }}
                    <span v-if="q.isFollowUp" class="followup-tag">追问</span>
                    <span v-if="q.isEnterpriseQuestion" class="enterprise-tag">企业真题 · {{ q.questionSource || '企业' }}</span>
                  </div>
                  <p class="q-text" v-html="renderMarkdown((q.question || '').replace('[INTERVIEW_OVER]', ''))" />
                </div>
                <div class="question-item__right">
                  <svg class="q-chevron" :class="{ rotated: expandedItems.includes(q.id) }"
                    viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
              </div>

              <transition name="collapse">
                <div v-if="expandedItems.includes(q.id)" class="question-item__detail">
                  <div class="detail-answer">
                    <p class="detail-label">你的回答</p>
                    <p class="detail-content">{{ q.answer || '（未作答）' }}</p>
                  </div>
                  <div class="detail-comment">
                    <p class="detail-label">
                      AI 点评
                      <!-- 该题点评还在加载中 -->
                      <span v-if="analysisLoading && !q.comment" class="comment-loading-badge">生成中...</span>
                    </p>
                    <p v-if="q.comment" class="detail-content" v-html="renderMarkdown(q.comment)" />
                    <p v-else-if="!analysisLoading" class="detail-content detail-content--muted">暂无点评</p>
                    <div v-else class="comment-skeleton">
                      <div class="comment-skeleton__line" />
                      <div class="comment-skeleton__line comment-skeleton__line--short" />
                    </div>
                  </div>

                  <div class="detail-reference">
                    <div class="detail-reference__header">
                      <p class="detail-label">参考优秀回答</p>
                      <button
                        class="reference-btn"
                        :disabled="q.referenceAnswerLoading"
                        @click="requestQuestionExcellentAnswer(q, idx)"
                      >
                        {{ q.referenceAnswerLoading ? '生成中...' : (q.referenceAnswer ? '重新生成' : '申请参考优秀答案') }}
                      </button>
                    </div>
                    <p v-if="q.referenceAnswer" class="detail-content" v-html="renderMarkdown(q.referenceAnswer)" />
                    <p v-else class="detail-content detail-content--muted">点击右侧按钮生成该题参考优秀回答</p>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </section>

        <!-- 操作按钮区 -->
        <section class="report-actions">
          <button class="action-btn action-btn--primary" @click="retryInterview">
            <span>再次面试</span>
          </button>
          <button class="action-btn action-btn--outline" @click="$router.push({ path: '/learning', query: { reportId: reportId } })">
            <span>学习中心</span>
          </button>
          <button class="action-btn action-btn--ghost" @click="$router.push('/history')">
            <span>历史记录</span>
          </button>
        </section>

        <div style="height: 30px;" />
      </div>
    </template>

    <div v-else-if="!loading" class="error-state">
      <span style="font-size:48px">😕</span>
      <p>报告加载失败</p>
      <button class="btn btn-primary btn-sm" @click="loadReport">重新加载</button>
    </div>
  </div>
</template>

<script>
import { getReport, getReplyAnalysis, requestExcellentAnswer } from '@/api/report'
import { toggleBookmark } from '@/api/learning'
import { INTERVIEW_DIMENSIONS } from '@/utils/constants'
import { marked } from 'marked'
let echarts = null
const DIMENSION_COLORS = ['#4338CA', '#10B981', '#F59E0B', '#3B82F6', '#8B5CF6']

export default {
  name: 'InterviewReport',
  data() {
    return {
      loading: true,
      analysisLoading: false,   // 逐题点评单独加载状态
      analysisLoaded: false,   // 记录是否已请求过，避免重复调用
      report: null,
      recommendedResources: [],
      expandedItems: [],
      animatedScore: 0,
      scoreInterval: null,
      chartInstance: null
    }
  },
  computed: {
    reportId() { return this.$route.params.reportId },
    grade() {
      const s = this.report?.totalScore || 0
      if (s >= 90) return { key: 'excellent', label: '优秀', desc: '表现出色，大厂可期！' }
      if (s >= 80) return { key: 'good', label: '良好', desc: '整体表现不错，继续保持！' }
      if (s >= 70) return { key: 'average', label: '中等', desc: '有一定基础，还有提升空间。' }
      if (s >= 60) return { key: 'pass', label: '及格', desc: '基础薄弱，需要加强练习。' }
      return { key: 'fail', label: '待提升', desc: '建议从基础开始系统学习。' }
    },
    dimensionList() {
      if (!this.report) return []
      const dims = this.report.dimensions || {}
      const avg = this.report.avgDimensions || {}
      return INTERVIEW_DIMENSIONS.map((d, i) => ({
        key: d.key,
        label: d.label,
        score: dims[d.key] || 0,
        avg: avg[d.key] || 65,
        color: DIMENSION_COLORS[i % DIMENSION_COLORS.length]
      }))
    },
    followUpCount() {
      return (this.report?.questions || []).filter(q => q.isFollowUp).length
    },
    allExpanded() {
      return this.report?.questions?.length > 0 &&
             this.report.questions.length === this.expandedItems.length
    }
  },
  async created() {
    await this.loadReport()
  },
  beforeUnmount() {
    if (this.scoreInterval) clearInterval(this.scoreInterval)
    if (this.chartInstance) { this.chartInstance.dispose(); this.chartInstance = null }
  },
  methods: {
    async loadReport() {
      this.loading = true
      try {
        // 1. 先加载报告基础数据（含 questions，但 comment 为空）
        this.report = await getReport(this.reportId)
        this.recommendedResources = (this.report?.recommendedResources || []).map(r => ({ ...r }))

        // 2. 修复雷达图：先确保 echarts 加载完毕，再初始化图表
        await this.ensureECharts()


        // 3. 异步加载逐题 AI 点评，不阻塞报告主体渲染
        // this.loadAnalysis()
      } catch (e) {
        console.error('加载报告失败', e)
      } finally {
        this.loading = false
                this.$nextTick(() => {
          this.animateScore()
          this.initRadarChart()
        })
      }
    },
    renderMarkdown(text) {
      if (!text) return ''
      return marked.parse(text)
    },

    // 确保 echarts 已加载，修复竞态问题
    async ensureECharts() {
      if (!echarts) {
        try {
          echarts = await import('echarts')
        } catch {
          console.warn('ECharts 未安装，雷达图不可用。运行: npm install echarts')
        }
      }
    },

    // 逐题点评：单独请求，完成后逐题回写 comment
    async loadAnalysis() {
      if (!this.report?.questions?.length) return
      this.analysisLoading = true
      try {
        const data = await getReplyAnalysis(this.reportId)
        if (!data?.items?.length) return

        // 按 index 将 evaluationText 回写到对应题目的 comment 字段
        // index 从 1 开始，对应 questions 数组下标 index-1
        data.items.forEach(item => {
          const q = this.report.questions[item.index - 1]
          if (q) {
            // Vue 响应式更新：直接赋值属性
            q.comment = item.evaluationText || ''
            q.isEnterpriseQuestion = !!item.isEnterpriseQuestion
            q.questionSource = item.questionSource || ''
            if (!q.reference || !Array.isArray(q.reference) || !q.reference.length) {
              q.reference = item.reference || []
            }
          }
        })
      } catch (e) {
        console.warn('逐题点评加载失败', e)
      } finally {
        this.analysisLoading = false
        this.analysisLoaded = true // 无论成功失败都标记已请求过
      }
    },

    animateScore() {
      const target = this.report?.totalScore || 0
      this.animatedScore = 0
      const step = Math.max(1, Math.floor(target / 40))
      this.scoreInterval = setInterval(() => {
        this.animatedScore = Math.min(this.animatedScore + step, target)
        if (this.animatedScore >= target) {
          this.animatedScore = target
          clearInterval(this.scoreInterval)
        }
      }, 30)
    },

    initRadarChart() {
      if (!echarts || !this.$refs.radarChart || !this.report) return
      if (this.chartInstance) this.chartInstance.dispose()

      const chart = echarts.init(this.$refs.radarChart)
      this.chartInstance = chart

      const dims = this.dimensionList
      chart.setOption({
        backgroundColor: 'transparent',
        radar: {
          indicator: dims.map(d => ({ name: d.label, max: 100 })),
          shape: 'circle', splitNumber: 4,
          center: ['50%', '50%'], radius: '68%',
          axisName: { color: '#475569', fontSize: 11 },
          splitArea: { areaStyle: { color: ['rgba(67,56,202,0.04)', 'rgba(67,56,202,0.05)', 'rgba(67,56,202,0.07)', 'rgba(67,56,202,0.09)'] } },
          axisLine: { lineStyle: { color: '#E2E8F0' } },
          splitLine: { lineStyle: { color: '#E2E8F0' } }
        },
        series: [{
          type: 'radar',
          data: [
            {
              value: dims.map(d => d.avg),
              name: '平均水平',
              areaStyle: { color: 'rgba(148,163,184,0.15)' },
              lineStyle: { color: '#b2b9c2', width: 1.5, type: 'dashed' },
              itemStyle: { color: '#b2b9c2' }, symbol: 'circle', symbolSize: 4
            },
            {
              value: dims.map(d => d.score),
              name: '本次表现',
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(67,56,202,0.25)' },
                  { offset: 1, color: 'rgba(124,58,237,0.15)' }
                ])
              },
              lineStyle: { color: '#685ddf', width: 2.4 },
              itemStyle: { color: '#685ddf', borderColor: 'white', borderWidth: 1 },
              symbol: 'circle', symbolSize: 7
            }
          ],
          animation: true, animationDuration: 1000, animationEasing: 'cubicOut'
        }]
      })

      const resizeObs = new ResizeObserver(() => chart.resize())
      resizeObs.observe(this.$refs.radarChart)
    },

    // 点击单题展开时，若该题无点评且未请求过则触发
    toggleQuestion(id) {
      const idx = this.expandedItems.indexOf(id)
      if (idx === -1) {
        this.expandedItems.push(id)
        // 展开时：该题还没有点评 && 整体未请求过 && 当前不在加载中 → 触发
        const q = this.report.questions.find(q => q.id === id)
        if (q && !q.comment && !this.analysisLoaded && !this.analysisLoading) {
          this.loadAnalysis()
        }
      } else {
        this.expandedItems.splice(idx, 1)
      }
    },
    // 点击"全部展开"时，若未请求过则统一触发一次
    toggleAllQuestions() {
      if (this.allExpanded) {
        this.expandedItems = []
      } else {
        this.expandedItems = this.report.questions.map(q => q.id)
        if (!this.analysisLoaded && !this.analysisLoading) {
          this.loadAnalysis()
        }
      }
    },
    scoreClass(score) {
      if (score >= 85) return 'score-excellent'
      if (score >= 75) return 'score-good'
      if (score >= 60) return 'score-average'
      return 'score-poor'
    },
    formatDuration(seconds) {
      if (!seconds) return '--'
      
    
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      if (mins === 0) return `${secs}秒`        // 不足1分钟只显示秒
      if (secs === 0) return `${mins}分钟`      // 整分钟不显示0秒
      return `${mins}分${secs}秒`
      // return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    },
    formatDateTime(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    },
    async requestQuestionExcellentAnswer(q, idx) {
      if (!q) return
      q.referenceAnswerLoading = true
      try {
        const res = await requestExcellentAnswer(this.reportId, idx + 1)
        q.referenceAnswer = res?.referenceAnswer || ''
      } catch (e) {
        console.error('生成参考优秀回答失败', e)
      } finally {
        q.referenceAnswerLoading = false
      }
    },
    async toggleRecommendBookmark(resource, bookmarked) {
      if (!resource) return
      if (!bookmarked) {
        const ok = window.confirm('确认取消收藏该资源吗？')
        if (!ok) return
      }
      await toggleBookmark(resource.id, bookmarked)
      resource.bookmarked = bookmarked
    },
    async bookmarkAll(bookmarked) {
      if (!bookmarked) {
        const ok = window.confirm('确认一键取消收藏当前推荐资源吗？')
        if (!ok) return
      }
      const tasks = this.recommendedResources.map(res => toggleBookmark(res.id, bookmarked))
      await Promise.all(tasks)
      this.recommendedResources = this.recommendedResources.map(r => ({ ...r, bookmarked }))
    },
    retryInterview() {
      this.$store.dispatch('interview/resetInterview')
      this.$router.push('/interview/select')
    },
    handleShare() {
      const text = `我的${this.report.jobName}模拟面试得分：${this.report.totalScore}分！`
      if (navigator.share) {
        navigator.share({ title: 'AI面试报告', text, url: window.location.href }).catch(() => {})
      } else {
        navigator.clipboard.writeText(window.location.href).then(() => alert('链接已复制到剪贴板'))
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.report-page {
  min-height: 100vh;
  background: $bg-page;
}

// ---- 导航栏 ----
.report-nav {
  position: sticky; top: 0; z-index: 90;
  display: flex; align-items: center; justify-content: space-between;
  height: $top-nav-height;
  padding: 0 $spacing-base;
  // background: rgb(219, 225, 254);
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid $border-color;
  box-shadow: $shadow-sm;

  &__title {
    font-size: $font-size-lg; font-weight: $font-weight-semibold;
    color: $text-primary; position: absolute;
    left: 50%; transform: translateX(-50%);
  }
}

.back-btn, .share-btn {
  width: 36px; height: 36px; border-radius: 50%;
  background: $gray-100; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: $text-secondary;
  transition: all $transition-fast;
  svg { width: 18px; height: 18px; }
  &:hover { background: $gray-200; }
}

// ---- 加载 ----
.loading-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 60vh; gap: $spacing-md;
  p { color: $text-muted; font-size: $font-size-base; }
}

.loading-spinner {
  width: 44px; height: 44px; border-radius: 50%;
  border: 4px solid $primary-bg; border-top-color: $primary;
  animation: spin 0.9s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }


// ---- 报告主体 ----
.report-body {
  padding: 0;
  animation: fadeSlideUp 0.4s ease both;
}

.report-section { margin-bottom: $spacing-xl; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: $spacing-md;

}

.section-title {
  display: flex; align-items: center; gap: $spacing-sm;
  font-size: $font-size-xl; font-weight: $font-weight-bold; color: $text-primary;
  margin-left:$spacing-base;
}

.legend {
  display: flex; gap: $spacing-md;
}

.legend-item {
  display: flex; align-items: center; gap: 5px;
  font-size: $font-size-xs; 
  color: $text-secondary;
  // color: $text-secondary;

  &::before {
    content: '';
    width: 20px; height: 3px; border-radius: 2px;
  }
  &--you::before { background: #685ddf; }
  &--avg::before { background: #b2b9c2; border-top: 1px dashed #b2b9c2; }
}

// ---- Hero 得分区 ----

.hero-content {
  background: white;
  position: relative; z-index: 1;
  display: flex; flex-direction: column; align-items: flex-start; 
  gap: $spacing-md;
  padding: $spacing-xl $spacing-base $spacing-base;
  border-bottom: 1px solid $border-color;
  border-radius:12px;
  margin-bottom: $spacing-xl;
  margin-top: $spacing-md;
}

.hero-meta {
  width: 100%; display: flex;
  justify-content: space-between; align-items: center;
}

// job-badge 改为紫色轻背景风格
.job-badge {
  background: $primary-bg;
  border: 1px solid rgba(67,56,202,0.2);
  color: $primary;
  font-size: $font-size-sm; font-weight: $font-weight-semibold;
  padding: 4px $spacing-md; border-radius: $border-radius-full;
}

.date-text { font-size: $font-size-xs; color: $text-muted; }

// 等级
.score-grade {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}

.grade-badge {
  padding: 5px 20px; border-radius: $border-radius-full;
  font-size: $font-size-sm; font-weight: $font-weight-bold;
  letter-spacing: 0.05em;

  &.grade-excellent { background: rgba(245,158,11,0.25); color: #FDE68A; border: 1px solid rgba(245,158,11,0.4); }
  &.grade-good { background: rgba(16,185,129,0.2); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.35); }
  &.grade-average { background: rgba(59,130,246,0.2); color: #93C5FD; border: 1px solid rgba(59,130,246,0.35); }
  &.grade-pass { background: rgba(255,255,255,0.12); color: rgba(255,255,255,0.7); border: 1px solid rgba(255,255,255,0.2); }
  &.grade-fail { background: rgba(239,68,68,0.2); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.35); }
}

.grade-desc { font-size: $font-size-sm; color: rgba(255,255,255,0.7); }

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-sm;
  width: 100%;
}

.hero-stat {
  background: $gray-50;
  border-radius: $border-radius;
  padding: $spacing-sm;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  &__value { font-family: $font-family-display; font-size: $font-size-lg; font-weight: $font-weight-bold; color: $text-primary; }
  &__label { font-size: $font-size-xs; color: $text-muted; }
}

// 分隔线不再需要
.hero-stat-divider { display: none; }


// 雷达图卡片
.radar-card {
  background: white; border-radius: $border-radius-lg;
  padding: $spacing-base; box-shadow: $shadow-sm;
  border: 1px solid $border-color;
   
  @media (min-width: 1024px) {
    display: flex;
    align-items: center;
    // gap: $spacing-4xl;
     gap: 10%;
    .radar-chart {
      width: 300px;      // 固定雷达图宽度
      flex-shrink: 0;
      margin-bottom: 0;  // 覆盖原来的 margin-bottom
      margin-left: $spacing-2xl;
    }

    .dimension-scores {
      flex: 1;
        margin-right: $spacing-3xl;  
    }
  }
}

.radar-chart {
  width: 100%; height: 240px;
  margin-bottom: $spacing-base;
}

// 维度分数列表
.dimension-scores {
  display: flex; flex-direction: column; gap: $spacing-sm;
}

.dim-score-item {
  display: flex; align-items: center; gap: $spacing-md;

  &__left { flex: 1; }
  &__name {
    font-size: $font-size-sm; color: $text-secondary;
    font-weight: $font-weight-medium; margin-bottom: 5px;
    display: block;
  }

  &__right {
    display: flex; flex-direction: column; align-items: flex-end; gap: 2px;
    width: 40px; flex-shrink: 0;
  }

  &__score {
    font-family: $font-family-display;
    font-size: $font-size-lg; font-weight: $font-weight-extrabold;
    line-height: 1;
  }
}

.dim-score-bar {
  height: 6px; background: $gray-100; border-radius: 3px; overflow: hidden;

  &__fill {
    height: 100%; border-radius: 3px;
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

// 亮点
.highlight-list {
  background: white; border-radius: $border-radius-lg;
  overflow: hidden; box-shadow: $shadow-sm; border: 1px solid $border-color;
}

.highlight-item {
  display: flex; align-items: flex-start; gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  border-bottom: 1px solid $gray-100;
  animation: fadeSlideUp 0.3s ease both;

  &:last-child { border-bottom: none; }

  &__dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: $success; flex-shrink: 0; margin-top: 5px;
    box-shadow: 0 0 0 3px $success-bg;
  }

  p { font-size: $font-size-base; color: $text-secondary; line-height: $line-height-relaxed; }
}

// 改进项
.improvement-list {
  display: flex; flex-direction: column; gap: $spacing-md;
}

.improvement-item {
  background: white; border-radius: $border-radius-lg;
  overflow: hidden; box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  animation: fadeSlideUp 0.3s ease both;

  &__header {
    display: flex; align-items: flex-start; gap: $spacing-md;
    padding: $spacing-md $spacing-base;
  }

  &__num {
    width: 24px; height: 24px; border-radius: 50%;
    background: $warning-bg; color: darken($warning, 20%);
    font-size: $font-size-xs; font-weight: $font-weight-bold;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
  }

  &__point { font-size: $font-size-base; color: $text-secondary; line-height: $line-height-relaxed; flex: 1; }

  &__resource {
    display: flex; align-items: center; gap: $spacing-sm;
    padding: $spacing-sm $spacing-base;
    background: $primary-bg;
    border-top: 1px solid rgba(67,56,202,0.1);
    cursor: pointer;
    font-size: $font-size-xs; color: $primary; font-weight: $font-weight-medium;
    text-decoration: none;
    transition: background $transition-fast;
    &:hover { background: darken(#EEF2FF, 3%); }
  }

  .resource-text {
    display: flex; align-items: center; gap: 4px;
    min-width: 0;
    overflow: hidden;
  }

  .resource-title {
    font-size: $font-size-sm; font-weight: $font-weight-semibold;
    color: #1f1974; line-height: 1.3;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

  .resource-source {
    font-size: $font-size-xs; color: $text-muted;
    white-space: nowrap;
  }
}

// 逐题回顾
.expand-all-btn {
  background: none; border: none; cursor: pointer;
  font-size: $font-size-sm; color: $primary; font-weight: $font-weight-medium;
  font-family: $font-family-base; padding: 0;
}

.question-list {
  display: flex; flex-direction: column; gap: $spacing-sm;
}

.question-item {
  background: white; border-radius: $border-radius-lg;
  border: 1.5px solid $border-color; overflow: hidden;
  box-shadow: $shadow-sm; transition: border-color $transition-fast;

  &.expanded { border-color: $primary; }
}

.question-item__header {
  display: flex; align-items: flex-start; gap: $spacing-sm;
  padding: $spacing-md $spacing-base; cursor: pointer;
  transition: background $transition-fast;
  &:hover { background: $gray-50; }
}

.question-item__left { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.question-item__right {
  display: flex; align-items: center; gap: $spacing-sm;
  flex-shrink: 0; padding-top: 2px;
}

.q-index {
  display: flex; align-items: center; gap: $spacing-xs;
  font-size: $font-size-xs; font-weight: $font-weight-bold;
  color: $primary; text-transform: uppercase; letter-spacing: 0.05em;
}

.followup-tag {
  background: $warning-bg; color: darken($warning, 20%);
  font-size: 10px; padding: 1px 6px; border-radius: $border-radius-full;
}

.enterprise-tag {
  background: #EEF2FF;
  color: #4338CA;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: $border-radius-full;
}

.q-text {
  font-size: $font-size-base; color: $text-primary;
  line-height: $line-height-normal;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;

  .expanded & { -webkit-line-clamp: unset; }
}

.q-text, .detail-content {
  :deep(strong) { font-weight: 500; color: #1f1974; }
  :deep(code) {
    background: $gray-100; border-radius: 3px;
    padding: 1px 5px; font-size: 0.9em; color: $primary;
  }
  :deep(p) { margin: 0; }
}

.highlight-item, .improvement-item__point {
  :deep(strong) { font-weight: 600; color: #1f1974; }
  :deep(code) {
    background: $gray-100; border-radius: 3px;
    padding: 1px 5px; font-size: 0.9em; color: $primary;
  }
  :deep(p) { margin: 0; }
  :deep(ol), :deep(ul) {
    margin: 4px 0 0 16px;
    li { margin-bottom: 2px; }
  }
}
.q-score {
  font-family: $font-family-display;
  font-size: $font-size-lg; font-weight: $font-weight-extrabold;
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;

  &.score-excellent { background: $success-bg; color: darken($success, 10%); }
  &.score-good { background: $info-bg; color: $info; }
  &.score-average { background: $warning-bg; color: darken($warning, 20%); }
  &.score-poor { background: $danger-bg; color: $danger; }
}

.q-chevron {
  width: 16px; height: 16px; color: $gray-400;
  transition: transform $transition-base;
  &.rotated { transform: rotate(180deg); }
}

.question-item__detail {
  border-top: 1px solid $gray-100;
  padding: $spacing-base;
  display: flex; flex-direction: column; gap: $spacing-md;
}

.detail-label {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  color: $text-muted; text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: $spacing-xs;
}

.detail-answer .detail-content {
  background: $gray-50; border-radius: $border-radius;
  padding: $spacing-md; font-size: $font-size-base;
  color: $text-secondary; line-height: $line-height-relaxed;
  border-left: 3px solid $border-color;
}

.detail-comment .detail-content {
  background: $primary-bg; border-radius: $border-radius;
  padding: $spacing-md; font-size: $font-size-base;
  color: $primary; line-height: $line-height-relaxed;
  border-left: 3px solid $primary;
}

.detail-reference__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: $spacing-xs;
}

.reference-btn {
  border: 1px solid #C7D2FE;
  background: #EEF2FF;
  color: #4338CA;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.reference-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

// collapse 动画
.collapse-enter-active { animation: collapseIn 0.3s ease both; }
.collapse-leave-active { animation: collapseIn 0.2s ease reverse both; }
@keyframes collapseIn {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 600px; }
}

// ---- 操作按钮区 ----
.report-actions {
  display: flex; gap: $spacing-sm;
  margin-bottom: $spacing-xl;
}

.recommend-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.recommend-card {
  min-width: 220px;
  max-width: 260px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

.recommend-card__title {
  margin: 0 0 6px;
  font-weight: 700;
  color: #1f2937;
}

.recommend-card__meta {
  margin: 0 0 8px;
  font-size: 12px;
  color: #6b7280;
}

.recommend-card__actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1; height: 50px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 3px; border-radius: $border-radius;
  cursor: pointer; font-family: $font-family-base;
  font-size: $font-size-base; font-weight: $font-weight-semibold;
  transition: all $transition-base; border: none;

  span:first-child { font-size: 18px; }

  &--primary { background: $gradient-primary; color: white; box-shadow: $shadow-primary; }
  &--outline { background: white; border: 1.5px solid $primary; color: $primary; }
  &--ghost { background: white; border: 1.5px solid $primary; color: $primary;  }

  &:hover { transform: translateY(-2px); box-shadow: $shadow-md; }
  &:active { transform: scale(0.97); }
}

// ---- 错误态 ----
.error-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 60vh; gap: $spacing-md;
  p { color: $text-muted; font-size: $font-size-base; }
}

/* 点评加载提示条 */
.analysis-loading-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: #F0F9FF;
  border-radius: 10px;
  font-size: 13px;
  color: #0369A1;
}
.analysis-loading-tip__dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #0EA5E9;
  animation: pulse 1.2s ease-in-out infinite;
}

/* 点评骨架屏 */
.comment-skeleton { padding: 4px 0; }
.comment-skeleton__line {
  height: 12px;
  background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  border-radius: 6px;
  margin-bottom: 8px;
  animation: shimmer 1.5s infinite;
}
.comment-skeleton__line--short { width: 65%; }

.comment-loading-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 7px;
  background: #DBEAFE;
  color: #2563EB;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  vertical-align: middle;
}
.detail-content--muted { color: #94A3B8; font-style: italic; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}


.hero-score-block {
  display: flex; align-items: center; gap: $spacing-xl;
}

.score-number {
  font-family: $font-family-display;
  font-size: 64px; font-weight: $font-weight-extrabold;
  color: $text-primary; line-height: 1;
  letter-spacing: -0.04em;
}

.score-right {
  display: flex; flex-direction: column; gap: $spacing-sm;
}

// grade-badge 颜色也要从白色字改为彩色字
.grade-badge {
  padding: 5px 16px; border-radius: $border-radius-full;
  font-size: $font-size-sm; font-weight: $font-weight-bold;
  display: inline-block; align-self: flex-start;

  &.grade-excellent { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
  &.grade-good      { background: #ECFDF5; color: #059669; border: 1px solid #6EE7B7; }
  &.grade-average   { background: #DBEAFE; color: #1D4ED8; border: 1px solid #93C5FD; }
  &.grade-pass      { background: $gray-100; color: $text-secondary; border: 1px solid $gray-200; }
  &.grade-fail      { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }
}

.grade-desc { font-size: $font-size-sm; color: $text-muted; }
</style>
