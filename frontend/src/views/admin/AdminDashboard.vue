<template>
  <div class="admin-shell">
    <!-- ── 侧边导航 ── 替换为 AdminSideNav 组件 -->
    <AdminSideNav />

    <!-- ── 主内容区 ── -->
    <main class="admin-main">
      <section class="top-cards">
        <div class="metric-card">
          <div class="metric-title">用户总数</div>
          <div class="metric-ring-wrap">
            <div class="metric-value">{{ stats.total_users }}</div>
            <svg viewBox="0 0 36 36" class="metric-ring">
              <path
                class="metric-ring-bg"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="metric-ring-fill"
                :stroke-dasharray="userGrowthPercentage + ', 100'"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <text x="18" y="20.5" class="metric-ring-text">{{ userGrowthPercentage.toFixed(1) }}%</text>
            </svg>
          </div>
          <div class="metric-sub">今日新增 {{ stats.today_new_users }} 人</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">面试总数</div>
          <div class="metric-ring-wrap">
            <div class="metric-value">{{ stats.total_interviews }}</div>
            <svg viewBox="0 0 36 36" class="metric-ring">
              <path
                class="metric-ring-bg"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="metric-ring-fill"
                :stroke-dasharray="interviewGrowthPercentage + ', 100'"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <text x="18" y="20.5" class="metric-ring-text">{{ interviewGrowthPercentage.toFixed(1) }}%</text>
            </svg>
          </div>
          <div class="metric-sub">今日新增 {{ stats.today_new_interviews }} 次</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">岗位总数</div>
          <div class="metric-value">{{ stats.total_jobs }}</div>
          <div class="job-bubble-container">
            <div v-for="(job, idx) in top_jobs" :key="job.job_id || idx" class="job-bubble-wrap">
              <div class="job-bubble" :style="{ width: getBubbleSize(job.interview_count) + 'px', height: getBubbleSize(job.interview_count) + 'px', background: getBubbleColor(idx) }" :title="job.job_name">
                {{ job.job_name || '无' }}
              </div>
            </div>
            <div v-if="!top_jobs.length" class="bubble-empty">暂无岗位排行</div>
          </div>
        </div>
        <div class="metric-card">
          <div class="metric-title">题库总数</div>
          <div class="metric-value">{{ stats.total_questions }}</div>
        </div>
      </section>

      <section class="dashboard-grid">
        <div class="card chart-card">
          <div class="card-header">系统一周使用次数总览</div>
          <div class="chart-placeholder" ref="usageChart"></div>
        </div>

        <div class="card rank-card">
          <div class="card-header">岗位排行榜</div>
          <div class="rank-list" v-if="top_jobs.length">
            <div class="rank-item" v-for="(item, index) in top_jobs" :key="item.job_id || index">
              <div class="rank-left">
                <span class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
                <span class="job-name">{{ item.job_name || '未知岗位' }}</span>
              </div>
              <div class="rank-right">
                <span class="interview-count">{{ item.interview_count }} 次面试</span>
                <span class="stars">{{ getRankStars(index + 1) }}</span>
              </div>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无排行数据</div>
        </div>

        <div class="card rank-card user-rank-card">
          <div class="card-header">用户排行榜（综合）</div>
          <div class="rank-list" v-if="top_users.length">
            <div class="rank-item" v-for="(item, index) in top_users" :key="item.user_id || index">
              <div class="rank-left">
                <span class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
                <span class="job-name">{{ item.username || '匿名' }}</span>
              </div>
              <div class="rank-right">
                <span class="interview-count">分数 {{ item.score }}</span>
                <span class="stars">{{ item.interview_count }} 次 / {{ item.avg_score }} 分 / {{ item.streak_days }}天</span>
              </div>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无用户排行数据</div>
        </div>

        <div class="card event-card">
          <div class="card-header">最新动态</div>
          <div class="event-list" v-if="recent_events.length">
            <div v-for="(event, idx) in recent_events" :key="idx" class="event-item" @click="openEventDetail(event)">
              <div class="event-text">{{ event.text }}</div>
              <div class="event-time">{{ formatTime(event.time) }}</div>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无系统动态</div>
        </div>
      </section>

    </main>
  </div>
</template>

<script>
import AdminSideNav from '@/components/admin/AdminSideNav.vue'
import request from '@/utils/request'

export default {
  name: 'AdminDashboard',
  components: {
    AdminSideNav  // 注册侧边导航组件
  },
  data() {
    return {
      stats: {
        total_users: 0,
        today_new_users: 0,
        total_interviews: 0,
        today_new_interviews: 0,
        total_jobs: 0,
        today_new_jobs: 0,
        total_questions: 0,
        total_visits: 0,
        unique_visitors: 0,
        unique_visitors_today: 0,
        today_new_orders: 230,
        new_orders_ratio: 8,
        today_copy_sold: 3490,
        copy_sold_ratio: 19,
        total_revenue: 22014,
        revenue_target: 30000
      },
      top_jobs: [],
      top_users: [],
      recent_events: [],
      usageTrend: {
        dates: [],
        total_users: [],
        total_interviews: []
      },
      echartsInstance: null
    }
  },
  filters: {
    currency(value) {
      if (typeof value !== 'number') return value
      return '￥' + value.toLocaleString()
    }
  },
  computed: {
    userGrowthPercentage() {
      if (!this.stats.total_users || this.stats.total_users <= 0) return 0
      return Math.min(100, (this.stats.today_new_users / this.stats.total_users) * 100)
    },
    interviewGrowthPercentage() {
      if (!this.stats.total_interviews || this.stats.total_interviews <= 0) return 0
      return Math.min(100, (this.stats.today_new_interviews / this.stats.total_interviews) * 100)
    }
  },
  methods: {
    getBubbleSize(count) {
      if (!this.top_jobs.length) return 28
      const counts = this.top_jobs.map((j) => j.interview_count || 0)
      const maxCount = Math.max(...counts, 1)
      const minCount = Math.min(...counts)
      const minSize = 40
      const maxSize = 62

      if (minCount === maxCount) {
        return (minSize + maxSize) / 2
      }

      const clamped = Math.min(maxCount, Math.max(0, count))
      return Math.round(minSize + ((clamped - minCount) / (maxCount - minCount)) * (maxSize - minSize))
    },
    getBubbleColor(idx) {
      const colors = ['#3f2f9f', '#6a5fd2', '#8f7fe3', '#b6abe9', '#d6c9f4']
      return colors[idx] || colors[colors.length - 1]
    },
    async fetchDashboard() {
      try {
        const data = await request.get('/dashboard', { admin: true })
        console.log('[AdminDashboard] dashboard API response', data)
        this.stats = {
          total_users: data.total_users || 0,
          today_new_users: data.today_new_users || 0,
          total_interviews: data.total_interviews || 0,
          today_new_interviews: data.today_new_interviews || 0,
          total_jobs: data.total_jobs || 0,
          today_new_jobs: data.today_new_jobs || 0,
          total_questions: data.total_questions || 0,
          total_visits: data.total_visits || data.unique_visitors || 0,
          unique_visitors: data.unique_visitors || 0,
          unique_visitors_today: data.unique_visitors_today || 0
        }
        this.top_jobs = Array.isArray(data.top_jobs) ? data.top_jobs.slice(0, 6) : []
        this.top_users = Array.isArray(data.top_users) ? data.top_users.slice(0, 8) : []
        this.recent_events = Array.isArray(data.recent_events) ? data.recent_events.slice(0, 10) : []
        if (Array.isArray(data.usage_trend)) {
          this.usageTrend.dates = data.usage_trend.map(item => item.date)
          this.usageTrend.total_users = data.usage_trend.map(item => item.total_users)
          this.usageTrend.total_interviews = data.usage_trend.map(item => item.total_interviews)
        } else {
          this.usageTrend = { dates: [], total_users: [], total_interviews: [] }
        }
        this.renderUsageChart()
      } catch (err) {
        console.error('获取管理员大盘数据失败', err)
      }
    },
    getRankStars(rank) {
      const starCount = Math.max(1, Math.min(5, 6 - rank))
      return '★'.repeat(starCount).padEnd(5, '☆')
    },
    formatTime(time) {
      if (!time) return ''
      const d = new Date(time)
      return d.toLocaleString()
    },
    openEventDetail(event) {
      alert(`事件详情:\n${event.text}\n时间：${event.time || '未知'}`)
    },
    async renderUsageChart() {
      if (!this.usageTrend.dates.length) return
      let echarts = null
      try {
        echarts = await import('echarts')
      } catch (e) {
        console.warn('ECharts 未安装，折线图不可用。运行: npm install echarts', e)
        return
      }

      const chartElement = this.$refs.usageChart
      if (!chartElement) return

      if (!this.echartsInstance) {
        this.echartsInstance = echarts.init(chartElement)
      }

      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['用户总数', '面试总数'],
          textStyle: { color: '#4e3c99' }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '8%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: this.usageTrend.dates,
          axisLabel: {
            formatter: (value) => value.replace(/^-/, ''),
            rotate: 35
          }
        },
        yAxis: {
          type: 'value',
          name: '数目'
        },
        series: [
          {
            name: '用户总数',
            type: 'line',
            smooth: true,
            data: this.usageTrend.total_users
          },
          {
            name: '面试总数',
            type: 'line',
            smooth: true,
            data: this.usageTrend.total_interviews
          }
        ]
      }

      this.echartsInstance.setOption(option)
      window.addEventListener('resize', () => {
        if (this.echartsInstance) this.echartsInstance.resize()
      })
    }
  },
  mounted() {
    this.fetchDashboard()
  }
}
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #f5f6fa;
}

/* 移除原来的 admin-sidebar 相关样式，因为 AdminSideNav 有自己的样式 */
.admin-main {
  flex: 1;
  padding: 24px 64px;
  overflow-y: auto;
  max-height: 100vh;
}

/* 其余样式保持不变 */
.metric-ring-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  padding: 0 6px;
}

.metric-card {
  padding: 14px 16px;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #3a2b71;
}

.metric-ring {
  width: 80px;
  height: 80px;
  transform: rotate(-90deg);
}

.metric-ring-text {
  font-size: 10px;
}

.metric-ring-bg,
.metric-ring-fill {
  fill: none;
  stroke-width: 4;
}

.job-bubble-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  justify-content: flex-end;
  padding-right: 8px;
  align-items: flex-start;
}

.job-bubble-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 64px;
  margin-right: 4px;
  color: #3a2b71;
}

.job-bubble {
  border-radius: 50%;
  background: #6a5fd2;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
  padding: 4px;
  min-width: 52px;
  min-height: 52px;
  max-width: 68px;
  max-height: 68px;
  text-align: center;
  white-space: normal;
}

.bubble-label {
  margin-top: 4px;
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.bubble-empty {
  color: #999;
  font-size: 13px;
}

.metric-ring-bg {
  stroke: #eee;
}

.metric-ring-fill {
  stroke: #5f4bb0;
  transition: stroke-dasharray 0.3s ease;
}

.metric-ring-text {
  fill: #333;
  font-size: 10px;
  text-anchor: middle;
  dominant-baseline: middle;
  transform: rotate(90deg);
}

.top-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  background: #fff;
  border: 1px solid #eae4ff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 7px rgba(58, 35, 130, 0.08);
}

.metric-title {
  color: #7f65d6;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2e1f7a;
}

.metric-sub {
  color: #7e71a8;
  font-size: 0.78rem;
  margin-top: 5px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e7def8;
  padding: 16px;
  box-shadow: 0 3px 10px rgba(131, 95, 207, 0.09);
}

.chart-card .chart-placeholder {
  height: 260px;
  background: linear-gradient(135deg, rgba(93, 75, 177, 0.08), rgba(148, 122, 227, 0.08));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5c4aa2;
  font-size: 0.95rem;
}

.card-header {
  font-size: 1.05rem;
  font-weight: 700;
  color: #5a2fa1;
  margin-bottom: 10px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  border-radius: 10px;
  border: 1px solid #efecff;
  background: #fbf8ff;
}

.rank-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.rank-badge {
  width: 24px;
  height: 24px;
  line-height: 24px;
  border-radius: 50%;
  color: #fff;
  font-weight: 700;
  text-align: center;
  font-size: 0.8rem;
}

.rank-badge.rank-1 { background: #f5b843; }
.rank-badge.rank-2 { background: #b0b0b0; }
.rank-badge.rank-3 { background: #cd7f32; }
.rank-badge.rank-4 { background: #8a6eb8; }
.rank-badge.rank-5 { background: #6d5cab; }

.job-name {
  font-size: 0.95rem;
  color: #423578;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 150px;
}

.rank-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.interview-count {
  font-size: 0.8rem;
  color: #7a6f9e;
}

.stars {
  color: #f0af2f;
  font-size: 0.85rem;
}

.empty-tip {
  color: #8468a9;
  font-size: 0.9rem;
  padding: 12px 8px;
  text-align: center;
}

.rank-card, .event-card, .user-rank-card {
  background: #fff;
  border: 1px solid #e7def8;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(128, 92, 216, 0.08);
  margin-top: 16px;
  min-height: 260px;
}

.event-list {
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}

.event-item {
  padding: 8px;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid #f0ebff;
  background: #fbf8ff;
  cursor: pointer;
}

.event-item:hover {
  background: #f5f0ff;
}

.event-text {
  font-size: 0.9rem;
  color: #4e3b97;
}

.event-time {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #7f6fa0;
}
</style>