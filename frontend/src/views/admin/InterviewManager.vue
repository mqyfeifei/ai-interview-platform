<!--
  frontend/src/views/admin/InterviewManager.vue
  面试记录管理 — 侧边导航布局 + 列表查看 + 聊天记录/评分报告详情抽屉
-->
<template>
  <div class="im-layout">


    <!-- ── 主内容区 ── -->
    <div class="im-main">

      <!-- 页头 -->
      <div class="im-topbar">
        <div class="im-topbar__left">
          <h1 class="im-topbar__title">面试记录</h1>
          <p class="im-topbar__sub">
            共 <strong>{{ total }}</strong> 条记录
            <span v-if="filterStatus || filterJobId" class="im-topbar__filtered">（已过滤）</span>
          </p>
        </div>
        <div class="im-topbar__right">
          <!-- 统计徽章 -->
          <div class="stat-chip stat-chip--purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87"/>
              <path d="M16 3.13a4 4 0 010 7.75"/>
            </svg>
            总计 {{ total }} 场面试
          </div>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="im-filters">
        <div class="filter-group">
          <span class="filter-group__label">状态</span>
          <div class="filter-pills">
            <button
              v-for="opt in statusOptions"
              :key="opt.value"
              class="filter-pill"
              :class="{ active: filterStatus === opt.value }"
              @click="setStatusFilter(opt.value)"
            >
              <span v-if="opt.dot" class="pill-dot" :class="'pill-dot--' + opt.value" />
              {{ opt.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-group__label">岗位</span>
          <select v-model="filterJobId" class="filter-select" @change="onFilterChange">
            <option value="">全部岗位</option>
            <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
          </select>
        </div>

        <button v-if="filterStatus || filterJobId" class="btn-clear" @click="clearFilters">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
            stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
          清空筛选
        </button>
      </div>

      <!-- 表格卡片 -->
      <div class="table-card">

        <!-- 加载态 -->
        <div v-if="loading" class="table-state">
          <span class="spinner" />
          <span>加载中...</span>
        </div>

        <!-- 空态 -->
        <div v-else-if="items.length === 0" class="table-state table-state--empty">
          <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" class="empty-svg">
            <circle cx="40" cy="40" r="32" fill="#f3f4f6"/>
            <path d="M28 40h24M40 28v24" stroke="#d1d5db" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
          <p class="table-state__title">暂无面试记录</p>
          <p class="table-state__sub">{{ filterStatus || filterJobId ? '尝试调整筛选条件' : '还没有任何面试数据' }}</p>
        </div>

        <!-- 数据表格 -->
        <div v-else class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:68px">ID</th>
                <th style="width:140px">用户</th>
                <th style="width:130px">岗位</th>
                <th style="width:96px">状态</th>
                <th style="width:76px">得分</th>
                <th style="width:72px">题数</th>
                <th style="width:88px">用时</th>
                <th style="width:160px">开始时间</th>
                <th style="width:88px; text-align:center">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in items"
                :key="item.interview_id"
                class="data-table__row"
              >
                <td>
                  <span class="td-id">#{{ item.interview_id }}</span>
                </td>
                <td class="td-center">
                  <div class="user-cell">
                    <span class="user-avatar">{{ avatarChar(item.username) }}</span>
                    <div class="user-info">
                      <div class="user-info__name">{{ item.username }}</div>
                      <div v-if="item.real_name" class="user-info__real">{{ item.real_name }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="job-tag">{{ item.job_name || '—' }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="'status--' + item.status">
                    {{ labelStatus(item.status) }}
                  </span>
                </td>
                <td>
                  <span v-if="item.total_score != null" class="score-pill" :class="scoreClass(item.total_score)">
                    {{ item.total_score }}
                  </span>
                  <span v-else class="td-dash">—</span>
                </td>
                <td class="td-center">
                  <span class="count-badge">{{ item.question_count || '—' }}</span>
                </td>
                <td class="td-center">
                  <span class="time-text">{{ formatDuration(item.used_time) }}</span>
                </td>
                <td class="td-center">{{ formatDate(item.start_time) }}</td>
                <td class="td-center">
                  <div class="action-cell">
                    <button class="act-btn" @click.stop="openDetail(item)" title="查看详情">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                      详情
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div v-if="total > pageSize" class="pagination">
          <span class="pagination__info">
            第 {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, total) }} 条，共 {{ total }} 条
          </span>
          <div class="pagination__btns">
            <button class="pg-btn" :disabled="page <= 1" @click="goPage(page - 1)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
            </button>
            <button
              v-for="p in pageList"
              :key="'page-' + p"
              class="pg-btn"
              :class="{ 'pg-btn--active': p === page, 'pg-btn--ellipsis': p === '...' }"
              :disabled="p === '...'"
              @click="p !== '...' && goPage(p)"
            >{{ p }}</button>
            <button class="pg-btn" :disabled="page >= totalPages" @click="goPage(page + 1)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- ══════════ 面试详情 Drawer ══════════ -->
    <transition name="drawer">
      <div v-if="showDetail" class="drawer-overlay" @click.self="closeDetail">
        <div class="drawer">

          <!-- 抽屉头 -->
          <div class="drawer-head">
            <div class="drawer-head__info">
              <div class="drawer-head__badge">面试详情</div>
              <h2 class="drawer-head__title">
                {{ detailData && detailData.interview ? detailData.interview.username : '—' }}
                <span class="drawer-head__id">#{{ currentItem && currentItem.interview_id }}</span>
              </h2>
              <p v-if="detailData && detailData.interview" class="drawer-head__sub">
                {{ detailData.interview.job_name }}
                · {{ labelStatus(detailData.interview.status) }}
              </p>
            </div>
            <button class="drawer-close" @click="closeDetail">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- 加载 -->
          <div v-if="detailLoading" class="drawer-loading">
            <span class="spinner spinner--lg" />
            <span>加载详情...</span>
          </div>

          <!-- 详情内容 -->
          <div v-else-if="detailData" class="drawer-body">

            <!-- 基本信息 -->
            <section class="dsec">
              <h3 class="dsec__title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                基本信息
              </h3>
              <div class="info-grid">
                <div class="info-card">
                  <span class="info-card__label">状态</span>
                  <span class="status-badge" :class="'status--' + detailData.interview.status">
                    {{ labelStatus(detailData.interview.status) }}
                  </span>
                </div>
                <div class="info-card info-card--highlight">
                  <span class="info-card__label">综合得分</span>
                  <span class="score-big" :class="scoreClass(detailData.report && detailData.report.total_score)">
                    {{ (detailData.report && detailData.report.total_score != null)
                        ? detailData.report.total_score : '—' }}
                    <span v-if="detailData.report && detailData.report.total_score != null" class="score-big__unit">分</span>
                  </span>
                </div>
                <div class="info-card">
                  <span class="info-card__label">题目数</span>
                  <span class="info-card__val">{{ detailData.interview.question_count || '—' }}</span>
                </div>
                <div class="info-card">
                  <span class="info-card__label">用时</span>
                  <span class="info-card__val">{{ formatDuration(detailData.interview.used_time) }}</span>
                </div>
                <div class="info-card">
                  <span class="info-card__label">开始时间</span>
                  <span class="info-card__val info-card__val--sm">{{ formatDate(detailData.interview.start_time) }}</span>
                </div>
                <div class="info-card">
                  <span class="info-card__label">结束时间</span>
                  <span class="info-card__val info-card__val--sm">{{ formatDate(detailData.interview.end_time) }}</span>
                </div>
              </div>
            </section>

            <!-- 维度评分 -->
            <section
              v-if="detailData.report && detailData.report.dimension_scores && detailData.report.dimension_scores.length"
              class="dsec"
            >
              <h3 class="dsec__title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                维度评分
              </h3>
              <div class="dim-list">
                <div
                  v-for="dim in detailData.report.dimension_scores"
                  :key="dim.dimension_id"
                  class="dim-row"
                >
                  <div class="dim-row__head">
                    <span class="dim-row__name">{{ dim.dimension_name }}</span>
                    <span class="dim-row__score" :class="scoreClass(dim.score)">{{ dim.score }}</span>
                  </div>
                  <div class="dim-bar">
                    <div
                      class="dim-bar__fill"
                      :style="{ width: dim.score + '%' }"
                      :class="scoreClass(dim.score)"
                    />
                  </div>
                  <p v-if="dim.comment" class="dim-row__comment">{{ dim.comment }}</p>
                </div>
              </div>
            </section>

            <!-- AI 评估报告 -->
            <section
              v-if="detailData.report && (detailData.report.highlights || detailData.report.improvements || detailData.report.suggestions)"
              class="dsec"
            >
              <h3 class="dsec__title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                AI 评估报告
              </h3>

              <div v-if="detailData.report.highlights" class="report-block report-block--green">
                <div class="report-block__title">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                    stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  亮点表现
                </div>
                <p>{{ detailData.report.highlights }}</p>
              </div>

              <div v-if="detailData.report.improvements" class="report-block report-block--orange">
                <div class="report-block__title">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  待改进项
                </div>
                <p>{{ detailData.report.improvements }}</p>
              </div>

              <div v-if="detailData.report.suggestions" class="report-block report-block--blue">
                <div class="report-block__title">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                  改进建议
                </div>
                <p>{{ detailData.report.suggestions }}</p>
              </div>
            </section>

            <!-- 对话记录 -->
            <section
              v-if="detailData.chat_history && detailData.chat_history.length"
              class="dsec"
            >
              <h3 class="dsec__title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
                对话记录
                <span class="dsec__count">{{ detailData.chat_history.length }} 条</span>
              </h3>

              <div class="chat-list">
                <div
                  v-for="msg in detailData.chat_history"
                  :key="msg.id"
                  class="chat-msg"
                  :class="'chat-msg--' + msg.role"
                >
                  <div class="chat-msg__avatar" :class="'avatar--' + msg.role">
                    {{ msg.role === 'ai' ? 'AI' : '候' }}
                  </div>
                  <div class="chat-msg__body">
                    <p class="chat-msg__text">{{ msg.content }}</p>
                    <span class="chat-msg__time">{{ formatDate(msg.timestamp) }}</span>
                  </div>
                </div>
              </div>
            </section>

          </div>

          <!-- 无数据兜底 -->
          <div v-else-if="!detailLoading" class="drawer-empty">
            <p>详情加载失败，请重试</p>
          </div>

        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import { listInterviews, getInterviewDetail, listAdminJobs } from '@/api/admin'

export default {
  name: 'InterviewManager',

  data() {
    return {
      // 列表数据
      items: [],
      total: 0,
      page: 1,
      pageSize: 15,
      loading: false,

      // 筛选
      jobs: [],
      filterStatus: '',
      filterJobId: '',

      statusOptions: [
        { value: '', label: '全部', dot: false },
        { value: 'in_progress', label: '进行中', dot: true },
        { value: 'evaluating', label: '评估中', dot: true },
        { value: 'completed', label: '已完成', dot: true }
      ],

      // 详情抽屉
      showDetail: false,
      detailLoading: false,
      detailData: null,
      currentItem: null
    }
  },

  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.total / this.pageSize))
    },
    pageList() {
      const total = this.totalPages
      const cur = this.page
      if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
      if (cur <= 4) return [1, 2, 3, 4, 5, '...', total]
      if (cur >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
      return [1, '...', cur - 1, cur, cur + 1, '...', total]
    }
  },

  created() {
    this.loadJobs()
    this.loadData()
  },

  methods: {
    // ── 数据加载 ──
    async loadJobs() {
      try {
        const res = await listAdminJobs()
        this.jobs = Array.isArray(res) ? res : (res && res.list ? res.list : [])
      } catch (e) {
        console.warn('加载岗位列表失败', e)
      }
    },

    async loadData() {
      this.loading = true
      try {
        const params = { page: this.page, size: this.pageSize }
        if (this.filterStatus) params.status = this.filterStatus
        if (this.filterJobId) params.job_id = this.filterJobId
        const res = await listInterviews(params)
        this.items = res.list || []
        this.total = res.total || 0
      } catch (e) {
        console.error('加载面试记录失败', e)
        this.items = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },

    // ── 筛选 ──
    setStatusFilter(val) {
      this.filterStatus = val
      this.page = 1
      this.loadData()
    },

    onFilterChange() {
      this.page = 1
      this.loadData()
    },

    clearFilters() {
      this.filterStatus = ''
      this.filterJobId = ''
      this.page = 1
      this.loadData()
    },

    // ── 分页 ──
    goPage(p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.loadData()
    },

    // ── 详情抽屉 ──
    async openDetail(item) {
      this.currentItem = item
      this.showDetail = true
      this.detailData = null
      this.detailLoading = true
      try {
        this.detailData = await getInterviewDetail(item.interview_id)
      } catch (e) {
        console.error('加载面试详情失败', e)
      } finally {
        this.detailLoading = false
      }
    },

    closeDetail() {
      this.showDetail = false
      this.detailData = null
      this.currentItem = null
    },

    // ── 格式化工具 ──
    labelStatus(status) {
      const map = { in_progress: '进行中', evaluating: '评估中', completed: '已完成' }
      return map[status] || status
    },

    scoreClass(score) {
      if (score == null) return ''
      if (score >= 80) return 'score--high'
      if (score >= 60) return 'score--mid'
      return 'score--low'
    },

    formatDuration(secs) {
      if (!secs && secs !== 0) return '—'
      if (secs === 0) return '0秒'
      const m = Math.floor(secs / 60)
      const s = secs % 60
      if (m === 0) return `${s}秒`
      return `${m}分${s > 0 ? s + '秒' : ''}`
    },

    formatDate(iso) {
      if (!iso) return '—'
      const d = new Date(iso)
      if (isNaN(d.getTime())) return iso
      const pad = n => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    },

    avatarChar(name) {
      return (name || '?').charAt(0).toUpperCase()
    }
  }
}
</script>

<style lang="scss" scoped>
// =============================================
// 整体布局
// =============================================
.im-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f6fa;
  font-family: $font-family-base;
}

.im-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 24px 72px;
  overflow-y: auto;
  max-height: 100vh;
}

// =============================================
// 顶部标题栏
// =============================================
.im-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 22px;
  gap: 16px;
  flex-wrap: wrap;

  &__title {
    font-size: 22px;
    font-weight: 800;
    color: #111827;
    letter-spacing: -0.4px;
    margin: 0 0 4px;
  }

  &__sub {
    font-size: 13px;
    color: #9ca3af;
    margin: 0;

    strong {
      color: #4338ca;
      font-weight: 700;
    }
  }

  &__filtered {
    color: #f59e0b;
    font-weight: 500;
  }
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;

  svg {
    width: 15px;
    height: 15px;
  }

  &--purple {
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #e0e7ff;
  }
}

// =============================================
// 筛选栏
// =============================================
.im-filters {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;

  &__label {
    font-size: 12.5px;
    color: #9ca3af;
    font-weight: 500;
    white-space: nowrap;
  }
}

.filter-pills {
  display: flex;
  gap: 4px;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 13px;
  border-radius: 20px;
  border: 1.5px solid #e5e7eb;
  background: white;
  color: #6b7280;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  font-family: $font-family-base;

  &:hover {
    border-color: #a5b4fc;
    color: #4338ca;
    background: #f5f3ff;
  }

  &.active {
    background: #4338ca;
    border-color: #4338ca;
    color: white;
    font-weight: 600;
  }
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &--in_progress { background: #f59e0b; }
  &--evaluating { background: #3b82f6; }
  &--completed { background: #10b981; }

  .filter-pill.active & { background: rgba(255,255,255,0.8); }
}

.filter-select {
  height: 34px;
  padding: 0 28px 0 11px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 8px center;
  appearance: none;
  font-size: 12.5px;
  color: #374151;
  cursor: pointer;
  font-family: $font-family-base;
  transition: border-color 0.15s;

  &:focus {
    outline: none;
    border-color: #6366f1;
  }
}

.btn-clear {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1.5px solid #fecaca;
  color: #ef4444;
  font-size: 12.5px;
  cursor: pointer;
  padding: 5px 12px;
  border-radius: 8px;
  font-family: $font-family-base;
  font-weight: 500;
  transition: all 0.15s;

  &:hover {
    background: #fef2f2;
  }
}

// =============================================
// 表格卡片
// =============================================
.table-card {
  background: white;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 320px;
}

.table-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex: 1;
  color: #9ca3af;
  font-size: 14px;
  padding: 60px 20px;

  &--empty {
    .table-state__title {
      font-size: 15px;
      color: #6b7280;
      font-weight: 600;
      margin: 0;
    }

    .table-state__sub {
      font-size: 13px;
      color: #9ca3af;
      margin: 0;
    }
  }
}

.empty-svg {
  width: 72px;
  height: 72px;
}

.table-scroll {
  overflow-x: auto;
  flex: 1;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;

  th {
    background: #fafafa;
    color: #6b7280;
    font-weight: 600;
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 16px;
    text-align: center;
    border-bottom: 1px solid #f3f4f6;
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    padding: 13px 16px;
    color: #374151;
    border-bottom: 1px solid #f9fafb;
    vertical-align: middle;
    text-align: center;
  }

  &__row {
    cursor: pointer;
    transition: background 0.12s;

    &:hover {
      background: #fafbff;
    }

    &:last-child td {
      border-bottom: none;
    }
  }
}

// 单元格样式
.td-id {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.td-center {
  text-align: center;
}

.td-time {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}

.td-dash { color: #d1d5db; }

.user-cell {
  display: flex;
  align-items: center;
  gap: 9px;
  justify-content: center; 
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  color: white;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  &__name {
    font-size: 13px;
    font-weight: 600;
    color: #111827;
    white-space: nowrap;
  }

  &__real {
    font-size: 11px;
    color: #9ca3af;
  }
}

.job-tag {
  display: inline-block;
  padding: 2px 9px;
  background: #f3f4f6;
  border-radius: 5px;
  font-size: 12px;
  color: #374151;
  font-weight: 500;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border-radius: 5px;
  font-size: 11.5px;
  font-weight: 600;
  white-space: nowrap;
}

.status--in_progress { background: #fef7d9; color: #92400e; }
.status--evaluating { background: #e2ecfa; color: #1e40af; }
.status--completed { background: #eaf9f1; color: #065f46; }

.score-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
}

.score--high { color: #059669; background: #f2fff9; }
.score--mid { color: #d97706; background: #faf7ea; }
.score--low { color: #dc2626; background: #fef2f2; }

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 20px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.time-text {
  font-size: 12px;
  color: #6b7280;
}

.action-cell {
  display: flex;
  justify-content: center;
}

.act-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 7px;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  background: #f3f6fe;
  color: #4338ca;
  transition: all 0.15s;
  font-family: $font-family-base;

  svg { width: 13px; height: 13px; }

  &:hover { background: #e0e7ff; }
}

// =============================================
// 分页
// =============================================
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 12px;
  flex-shrink: 0;

  &__info {
    font-size: 13px;
    color: #9ca3af;
  }

  &__btns {
    display: flex;
    gap: 4px;
  }
}

.pg-btn {
  min-width: 34px;
  height: 34px;
  border: 1.5px solid #e5e7eb;
  border-radius: 7px;
  background: white;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  padding: 0 8px;
  font-family: $font-family-base;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;

  &:hover:not(:disabled) {
    border-color: #6366f1;
    color: #4338ca;
  }

  &--active {
    background: #4338ca;
    border-color: #4338ca;
    color: white;
    font-weight: 600;
  }

  &--ellipsis {
    cursor: default;
    border-color: transparent;
    background: none;
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }
}

// =============================================
// 加载动画
// =============================================
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(67, 56, 202, 0.18);
  border-top-color: #4338ca;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
  flex-shrink: 0;

  &--lg {
    width: 28px;
    height: 28px;
    border-width: 3px;
  }
}

@keyframes spin { to { transform: rotate(360deg); } }

// =============================================
// 详情 Drawer
// =============================================
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 10, 40, 0.48);
  backdrop-filter: blur(4px);
  z-index: 300;
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 680px;
  max-width: 200vw;
  height: 100%;
  background: white;
  display: flex;
  flex-direction: column;
  box-shadow: -12px 0 48px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

// 抽屉头
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 22px 24px 18px;
  border-bottom: 1px solid #e5e5e6;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f7f6ffc9 0%, #ece3f9e3 100%);
  color: rgb(70, 67, 67);

  &__badge {
    display: inline-flex;
    padding: 2px 9px;
    background: rgb(247, 239, 255);
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    color: rgba(40, 39, 39, 0.65);
    letter-spacing: 0.3px;
    margin-bottom: 6px;
  }

  &__title {
    font-size: 17px;
    font-weight: 700;
    color: rgb(30, 28, 28);
    margin: 0 0 4px;
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  &__id {
    font-size: 13px;
    color: rgba(116, 115, 115);
    font-weight: 400;
  }

  &__sub {
    font-size: 12px;
    color: rgba(65, 61, 61, 0.75);
    margin: 0;
  }

  &__info {
    flex: 1;
  }
}

.drawer-close {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: none;
  background: rgba(215, 199, 246, 0.6);
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;

  svg { width: 14px; height: 14px; }

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }
}

.drawer-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex: 1;
  color: #9ca3af;
  font-size: 14px;
}

.drawer-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #9ca3af;
  font-size: 14px;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 32px;

  &::-webkit-scrollbar { width: 5px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 3px; }
}

// ── Detail Sections ──
.dsec {
  padding: 20px 0;
  border-bottom: 1px solid #f3f4f6;

  &:last-child { border-bottom: none; }

  &__title {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12.5px;
    font-weight: 700;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 16px;

    svg {
      width: 15px;
      height: 15px;
      color: #6366f1;
      flex-shrink: 0;
    }
  }

  &__count {
    font-size: 11px;
    font-weight: 500;
    color: #9ca3af;
    background: #f3f4f6;
    padding: 1px 8px;
    border-radius: 8px;
    text-transform: none;
    letter-spacing: 0;
    margin-left: 4px;
  }
}

// ── 信息网格 ──
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.info-card {
  background: #f9fafb;
  border-radius: 10px;
  padding: 11px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  border: 1px solid #f3f4f6;

  &--highlight {
    background: #eef2ff;
    border-color: #e0e7ff;
  }

  &__label {
    font-size: 11px;
    color: #9ca3af;
    font-weight: 500;
  }

  &__val {
    font-size: 14px;
    color: #111827;
    font-weight: 600;

    &--sm {
      font-size: 12px;
    }
  }
}

.score-big {
  font-size: 24px;
  font-weight: 800;
  display: flex;
  align-items: baseline;
  gap: 3px;
  line-height: 1;

  &__unit {
    font-size: 13px;
    font-weight: 500;
    opacity: 0.7;
  }
}

// ── 维度评分 ──
.dim-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dim-row {
  &__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 7px;
  }

  &__name {
    font-size: 13px;
    color: #374151;
    font-weight: 500;
  }

  &__score {
    font-size: 14px;
    font-weight: 700;
  }

  &__comment {
    font-size: 12px;
    color: #9ca3af;
    margin: 7px 0 0;
    line-height: 1.55;
  }
}

.dim-bar {
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;

  &__fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    &.score--high { background: linear-gradient(90deg, #34d399, #10b981); }
    &.score--mid { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
    &.score--low { background: linear-gradient(90deg, #f87171, #ef4444); }

  }
}

// ── 报告块 ──
.report-block {
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;

  &:last-child { margin-bottom: 0; }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;

    svg { width: 13px; height: 13px; }
  }

  p {
    font-size: 13px;
    line-height: 1.7;
    margin: 0;
    white-space: pre-line;
  }

  &--green {
    // background: #f0fdf4;
    border: 1px solid #bbf7d0;

    .report-block__title { color: #15803d; }
    p { color: #166534; }
  }

  &--orange {
    // background: #fff7ed;
    border: 1px solid #fed7aa;

    .report-block__title { color: #c2410c; }
    p { color: #9a3412; }
  }

  &--blue {
    // background: #eff6ff;
    border: 1px solid #bfdbfe;

    .report-block__title { color: #1d4ed8; }
    p { color: #1e3a8a; }
  }
}

// ── 对话记录 ──
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 500px;
  overflow-y: auto;
  padding: 4px 0;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }
}

.chat-msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;

  &--user {
    flex-direction: row-reverse;
  }

  &__avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    font-size: 11px;
    font-weight: 700;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__body {
    max-width: 76%;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__text {
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 13px;
    line-height: 1.65;
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
  }

  &__time {
    font-size: 11px;
    color: #d1d5db;
  }

  &--ai {
    .chat-msg__avatar {
      background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
      color: white;
    }

    .chat-msg__text {
      background: #f3f4f6;
      color: #111827;
      border-top-left-radius: 4px;
    }

    .chat-msg__time {
      align-self: flex-start;
    }
  }

  &--user {
    .chat-msg__avatar {
      background: #e5e7eb;
      color: #6b7280;
    }

    .chat-msg__text {
      background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
      color: white;
      border-top-right-radius: 4px;
    }

    .chat-msg__body {
      align-items: flex-end;
    }
  }
}

// ── Drawer 动画 ──
.drawer-enter-active {
  animation: drawer-slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.drawer-leave-active {
  animation: drawer-slide-in 0.2s ease reverse both;
}

@keyframes drawer-slide-in {
  from {
    transform: translateX(100%);
    opacity: 0.6;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>