<template>
  <div class="am-layout">
    <AdminSideNav />

    <div class="am-main">
      <div class="am-content">
        <div class="am-header">
          <div class="am-header__left">
            <h1 class="am-header__title">用户管理</h1>
            <p class="am-header__sub">共 <strong>{{ total }}</strong> 位用户</p>
          </div>
        </div>

        <div v-if="toastText" :class="['toast', toastType === 'error' ? 'toast--error' : 'toast--success']">
          {{ toastText }}
        </div>

        <div class="am-filters">
          <select v-model="statusFilter" class="filter-select" @change="onFilterChange">
            <option value="">全部状态</option>
            <option value="true">已启用</option>
            <option value="false">已禁用</option>
          </select>
          <select v-model="gradeFilter" class="filter-select" @change="onFilterChange">
            <option value="">全部年级</option>
            <option value="大一">大一</option>
            <option value="大二">大二</option>
            <option value="大三">大三</option>
            <option value="大四">大四</option>
            <option value="研一">研一</option>
            <option value="研二">研二</option>
            <option value="研三">研三</option>
            <option value="其它">其它</option>
          </select>
          <input v-model="schoolFilter" class="filter-input" type="text" placeholder="按学校搜索" @keyup.enter="onSearch" />
          <input v-model="majorFilter" class="filter-input" type="text" placeholder="按专业搜索" @keyup.enter="onSearch" />
          <input v-model="usernameFilter" class="filter-input" type="text" placeholder="按用户名搜索" @keyup.enter="onSearch" />
          <input v-model="emailFilter" class="filter-input" type="text" placeholder="按邮箱搜索" @keyup.enter="onSearch" />
          <select v-model="createdRangeFilter" class="filter-select" @change="onFilterChange">
            <option value="">注册时间</option>
            <option value="7">近7天</option>
            <option value="30">近30天</option>
            <option value="all">全部</option>
          </select>
          <button class="btn btn-primary" @click="onSearch">搜索</button>
          <button v-if="hasFilters" class="btn-text" @click="clearFilters">清空筛选</button>
        </div>

        <div class="table-card">
          <div v-if="loading" class="table-loading">
            <span class="spinner"></span> 加载中...
          </div>

          <div v-else-if="errorMsg" class="table-empty table-error">
            <p>获取用户失败：{{ errorMsg }}</p>
          </div>

          <div v-else-if="users.length === 0" class="table-empty">
            <p>暂无用户数据</p>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th style="width:60px">ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>学校</th>
                <th>专业</th>
                <th>年级</th>
                <th>默认岗位</th>
                <th style="width:80px">状态切换</th>
                <th style="width:80px">状态</th>
                <th style="width:100px">注册时间</th>
                <th style="width:170px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id" class="data-table__row">
                <td>#{{ user.id }}</td>
                <td>
                  <div class="user-name-cell">
                    <template v-if="user.avatar_url">
                      <img :src="resolveAvatarSrc(user.avatar_url)" alt="avatar" class="user-avatar" />
                    </template>
                    <template v-else>
                      <span class="user-avatar user-avatar--fallback">{{ getAvatarLetter(user) }}</span>
                    </template>
                    <div class="user-name-content">
                      <div class="username">{{ user.username || '-' }}</div>
                      <div v-if="user.real_name" class="real-name">{{ user.real_name }}</div>
                    </div>
                  </div>
                </td>
                <td>{{ user.email || '-' }}</td>
                <td>{{ user.school || '-' }}</td>
                <td>{{ user.major || '-' }}</td>
                <td>{{ user.grade || '-' }}</td>
                <td>{{ user.default_job || '-' }}</td>
                <td>
                  <label class="switch">
                    <input
                      type="checkbox"
                      :checked="user.is_active"
                      @change="onStatusSwitchChange(user, $event)"
                    />
                    <span class="slider"></span>
                  </label>
                </td>
                <td>
                  <span :class="['badge', user.is_active ? 'badge--success' : 'badge--danger']">
                    {{ user.is_active ? '正常' : '禁用' }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td class="action-cell">
                  <button class="action-btn" @click.prevent="viewUser(user)">查看</button>
                  <button class="action-btn" @click.prevent="editUser(user)">编辑</button>
                  <button class="action-btn action-btn--danger" @click.prevent="deleteUser(user)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="total > 0" class="pagination">
            <span class="pagination__info">共 {{ total }} 条，第 {{ page }}/{{ totalPages }} 页</span>
            <div class="pagination__btns">
              <button class="pg-btn" :disabled="page <= 1" @click="goPage(page - 1)">‹ 上一页</button>
              <button
                v-for="p in pageList"
                :key="p"
                class="pg-btn"
                :class="{ 'pg-btn--active': p === page, 'pg-btn--ellipsis': p === '...' }"
                :disabled="p === '...'"
                @click="p !== '...' && goPage(p)"
              >{{ p }}</button>
              <button class="pg-btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页 ›</button>
            </div>
          </div>

          <transition name="drawer">
            <div v-if="showDetail" class="drawer-overlay" @click.self="closeUserDetail">
              <div class="drawer">
                <div class="drawer-head">
                  <div class="drawer-head__avatar">
                    <template v-if="detailUser && detailUser.avatar_url">
                      <img :src="resolveAvatarSrc(detailUser.avatar_url)" alt="avatar" />
                    </template>
                    <template v-else>
                      <span>{{ getAvatarLetter(detailUser) }}</span>
                    </template>
                  </div>
                  <div class="drawer-head__info">
                    <div class="drawer-head__badge">用户详情</div>
                    <h2 class="drawer-head__title">
                      {{ detailUser ? (detailUser.username || '-') : '未选择' }}
                      <span class="drawer-head__id">#{{ detailUser ? detailUser.id : '' }}</span>
                    </h2>
                    <p class="drawer-head__sub">{{ detailUser ? (detailUser.real_name || '—') : '—' }}</p>
                  </div>
                  <button class="drawer-close" @click="closeUserDetail">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <div v-if="detailLoading" class="drawer-loading">
                  <span class="spinner spinner--lg" />
                  <span>加载用户详情...</span>
                </div>
                <div v-else-if="detailUser" class="drawer-body">
                  <section class="dsec">
                    <h3 class="dsec__title">基本信息</h3>
                    <div class="info-grid">
                      <div class="info-card"><span class="info-card__label">用户名</span><span>{{ detailUser.username || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">姓名</span><span>{{ detailUser.real_name || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">邮箱</span><span>{{ detailUser.email || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">学校</span><span>{{ detailUser.school || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">专业</span><span>{{ detailUser.major || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">年级</span><span>{{ detailUser.grade || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">默认岗位</span><span>{{ detailUser.default_job || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">手机号</span><span>{{ detailUser.phone || '-' }}</span></div>
                      <div class="info-card"><span class="info-card__label">状态</span><span :class="['status-badge', detailUser.is_active ? 'status-badge--success' : 'status-badge--danger']">{{ detailUser.is_active ? '正常' : '禁用' }}</span></div>
                      <div class="info-card"><span class="info-card__label">注册时间</span><span>{{ formatDate(detailUser.created_at) }}</span></div>
                    </div>
                  </section>

                  <section class="dsec">
                    <h3 class="dsec__title">面试记录（最近 5 条）</h3>
                    <div class="history-list">
                      <div v-if="!userPerformance || !userPerformance.interviews || userPerformance.interviews.length === 0" class="history-empty">暂无面试记录</div>
                      <ul v-else>
                        <li v-for="item in displayedInterviews" :key="item.interview_id">
                          <span>{{ formatDate(item.start_time) || '—' }}</span>
                          <strong>{{ item.job_name || '未知岗位' }}</strong>
                          <span>得分：{{ item.score != null ? item.score : '—' }}</span>
                          <span :class="['status-badge', item.status === 'completed' ? 'status-badge--success' : 'status-badge--danger']">{{ item.status }}</span>
                        </li>
                      </ul>
                      <button
                        v-if="userPerformance && userPerformance.interviews && userPerformance.interviews.length > 5"
                        @click="showAllInterviews = !showAllInterviews"
                        class="btn btn-text"
                        style="margin-top: 8px;"
                      >
                        {{ showAllInterviews ? '收起面试记录' : '展开全部面试记录' }}（{{ userPerformance.interviews.length }}）
                      </button>
                    </div>
                  </section>

                  <section class="dsec">
                    <h3 class="dsec__title">面试曲线</h3>
                    <div v-if="userPerformance && userPerformance.growth_curve && userPerformance.growth_curve.length" class="line-chart" ref="performanceLineChart"></div>
                    <div v-else class="history-empty">暂无曲线数据</div>
                    <div v-if="userPerformance && userPerformance.growth_curve" class="curve-labels">已完成 {{ userPerformance.growth_curve.length }} 次面试</div>
                  </section>

                  <section class="dsec">
                    <h3 class="dsec__title">能力雷达图</h3>
                    <div class="radar-preview">
                      <svg viewBox="0 0 200 200" class="radar-chart">
                        <polygon class="radar-grid" points="100,20 168,65 168,135 100,180 32,135 32,65" />
                        <polygon class="radar-grid" points="100,40 152,72 152,128 100,160 48,128 48,72" />
                        <polygon class="radar-grid" points="100,60 136,80 136,120 100,140 64,120 64,80" />
                        <polygon class="radar-area" :points="performanceRadarPoints()" />
                        <circle v-for="(point, idx) in performanceRadarDots()" :key="idx" :cx="point.x" :cy="point.y" r="4" class="radar-dot" />
                      </svg>
                      <div class="radar-labels">
                        <span class="radar-label" style="top: 0; left: 50%; transform: translateX(-50%)">专业知识</span>
                        <span class="radar-label" style="top: 25%; right: 0">逻辑思维</span>
                        <span class="radar-label" style="bottom: 25%; right: 0">表达能力</span>
                        <span class="radar-label" style="bottom: 0; left: 50%; transform: translateX(-50%)">问题解决</span>
                        <span class="radar-label" style="bottom: 25%; left: 0">代码能力</span>
                        <span class="radar-label" style="top: 25%; left: 0">学习能力</span>
                      </div>
                    </div>
                  </section>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import AdminSideNav from '@/components/admin/AdminSideNav.vue'
import { listAdminUsers, updateAdminUserStatus, deleteAdminUser, getAdminUserPerformance } from '@/api/admin'

let echarts = null

export default {
  name: 'AdminUsers',
  components: { AdminSideNav },
  data() {
    return {
      users: [],
      page: 1,
      size: 10,
      total: 0,
      keyword: '',
      statusFilter: '',
      gradeFilter: '',
      schoolFilter: '',
      majorFilter: '',
      usernameFilter: '',
      emailFilter: '',
      createdRangeFilter: '',
      loading: false,
      totalPages: 1,
      errorMsg: '',
      toastText: '',
      toastType: 'success',
      showDetail: false,
      detailUser: null,
      detailLoading: false,
      userPerformance: null,
      showAllInterviews: false,
      performanceChartInstance: null
    }
  },
  computed: {
    hasFilters() {
      return (
        this.keyword.trim() !== '' ||
        this.statusFilter !== '' ||
        this.gradeFilter !== '' ||
        this.schoolFilter.trim() !== '' ||
        this.majorFilter.trim() !== '' ||
        this.usernameFilter.trim() !== '' ||
        this.emailFilter.trim() !== '' ||
        this.createdRangeFilter !== ''
      )
    },
    pageList() {
      const pages = []
      const count = this.totalPages
      if (count <= 7) {
        for (let i = 1; i <= count; i++) pages.push(i)
      } else {
        if (this.page <= 4) {
          pages.push(1, 2, 3, 4, 5, '...', count)
        } else if (this.page >= count - 3) {
          pages.push(1, '...', count - 4, count - 3, count - 2, count - 1, count)
        } else {
          pages.push(1, '...', this.page - 1, this.page, this.page + 1, '...', count)
        }
      }
      return pages
    },
    displayedInterviews() {
      if (!this.userPerformance || !this.userPerformance.interviews) return []
      if (this.showAllInterviews) return this.userPerformance.interviews
      return this.userPerformance.interviews.slice(0, 5)
    }
  },
  created() {
    this.loadUsers()
  },
  methods: {
    async loadUsers() {
      try {
        this.loading = true
        const params = {
          page: this.page,
          size: this.size
        }

        if (this.keyword.trim()) {
          params.keyword = this.keyword.trim()
        }
        if (this.statusFilter !== '') {
          params.is_active = this.statusFilter === 'true'
        }
        if (this.gradeFilter !== '') {
          params.grade = this.gradeFilter
        }
        if (this.schoolFilter.trim()) {
          params.school = this.schoolFilter.trim()
        }
        if (this.majorFilter.trim()) {
          params.major = this.majorFilter.trim()
        }
        if (this.usernameFilter.trim()) {
          params.username = this.usernameFilter.trim()
        }
        if (this.emailFilter.trim()) {
          params.email = this.emailFilter.trim()
        }
        if (this.createdRangeFilter && this.createdRangeFilter !== 'all') {
          params.created_range = parseInt(this.createdRangeFilter, 10)
        }

        const data = await listAdminUsers(params)
        if (data) {
          this.users = data.list || []
          this.total = data.total || 0
          this.totalPages = Math.max(1, Math.ceil(this.total / this.size))
        }
      } catch (err) {
        console.error('获取用户列表失败', err)
        this.errorMsg = err.message || '获取用户列表失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    onSearch() {
      this.page = 1
      this.errorMsg = ''
      this.loadUsers()
    },
    onFilterChange() {
      this.page = 1
      this.errorMsg = ''
      this.loadUsers()
    },
    clearFilters() {
      this.keyword = ''
      this.statusFilter = ''
      this.gradeFilter = ''
      this.schoolFilter = ''
      this.majorFilter = ''
      this.usernameFilter = ''
      this.emailFilter = ''
      this.createdRangeFilter = ''
      this.errorMsg = ''
      this.onSearch()
    },
    async onStatusSwitchChange(user, event) {
      const newStatus = event.target.checked
      const actionText = newStatus ? '开启' : '关闭'
      if (!window.confirm(`确定要${actionText}该用户?`)) {
        // 恢复开关状态
        event.target.checked = user.is_active
        return
      }
      await this.updateStatus(user, newStatus)
    },
    async updateStatus(user, newStatus) {
      try {
        await updateAdminUserStatus(user.id, { is_active: newStatus })
        user.is_active = newStatus
        this.showToast(`用户已成功${newStatus ? '开启' : '关闭'}`, 'success')
      } catch (err) {
        console.error('更新用户状态失败', err)
        this.showToast('更新用户状态失败，请稍后重试', 'error')
      }
    },
    viewUser(user) {
      this.openUserDetail(user)
    },
    async openUserDetail(user) {
      this.detailUser = user
      this.showDetail = true
      this.detailLoading = true
      this.userPerformance = null
      this.showAllInterviews = false
      try {
        const res = await getAdminUserPerformance(user.id)
        this.userPerformance = res || null
        this.$nextTick(() => {
          this.initPerformanceChart()
        })
      } catch (e) {
        console.error('加载用户绩效失败', e)
      } finally {
        this.detailLoading = false
      }
    },
    closeUserDetail() {
      this.showDetail = false
      this.detailUser = null
      this.userPerformance = null
      if (this.performanceChartInstance && !this.performanceChartInstance.isDisposed()) {
        this.performanceChartInstance.dispose()
      }
      this.performanceChartInstance = null
    },
    async initPerformanceChart() {
      if (!this.userPerformance || !this.userPerformance.growth_curve || this.userPerformance.growth_curve.length === 0) {
        return
      }

      if (!echarts) {
        try {
          echarts = await import('echarts')
        } catch (e) {
          console.warn('ECharts 未安装，折线图不可用。', e)
          return
        }
      }

      const el = this.$refs.performanceLineChart
      if (!el) return

      if (!this.performanceChartInstance || this.performanceChartInstance.isDisposed()) {
        this.performanceChartInstance = markRaw(echarts.init(el))
        new ResizeObserver(() => {
          if (this.performanceChartInstance && !this.performanceChartInstance.isDisposed()) {
            this.performanceChartInstance.resize()
          }
        }).observe(el)
      }

      const curve = this.userPerformance.growth_curve
      const xData = curve.map((item) => item.date || '')
      const yData = curve.map((item) => Number(item.score) || 0)

      this.performanceChartInstance.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: xData,
          boundaryGap: false,
          axisLabel: {
            rotate: 30,
            formatter: (value) => value
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}'
          }
        },
        grid: {
          left: '12%',
          right: '12%',
          top: '16%',
          bottom: '20%'
        },
        series: [
          {
            name: '得分',
            type: 'line',
            data: yData,
            smooth: true,
            lineStyle: { color: '#3b82f6' },
            itemStyle: { color: '#3b82f6' },
            areaStyle: { color: 'rgba(59, 130, 246, 0.16)' }
          }
        ]
      })
    },
    editUser(user) {
      this.showToast(`编辑用户：${user.username || '-'}（ID ${user.id}）`, 'success')
      // 这里可以跳转至用户编辑页面，例如：this.$router.push({ name: 'AdminUserEdit', params: { id: user.id } })
    },
    async deleteUser(user) {
      if (!window.confirm(`确定要删除用户 ${user.username || user.email || user.id} 吗？`)) {
        return
      }

      try {
        await deleteAdminUser(user.id)
        this.users = this.users.filter((u) => u.id !== user.id)
        this.total = Math.max(0, this.total - 1)
        this.showToast('用户已删除', 'success')
      } catch (err) {
        console.error('删除用户失败', err)
        this.showToast('删除用户失败，请稍后重试', 'error')
      }
    },
    showToast(message, type = 'success') {
      this.toastText = message
      this.toastType = type
      if (this.toastTimer) {
        clearTimeout(this.toastTimer)
      }
      this.toastTimer = setTimeout(() => {
        this.toastText = ''
        this.toastType = 'success'
        this.toastTimer = null
      }, 2500)
    },
    goPage(pageNum) {
      if (pageNum < 1 || pageNum > this.totalPages || pageNum === this.page) return
      this.page = pageNum
      this.loadUsers()
    },
    resolveAvatarSrc(raw) {
      if (!raw) return ''
      const str = String(raw)
      if (/^https?:\/\//i.test(str)) return str
      const origin = (process.env.VUE_APP_BACKEND_ORIGIN || '').replace(/\/$/, '')
      if (origin) {
        return `${origin}${str.startsWith('/') ? '' : '/'}${str}`
      }
      return str
    },
    getAvatarLetter(user) {
      const name = user && (user.real_name || user.username) ? (user.real_name || user.username) : '用'
      return name.charAt(0)
    },

    performanceCurveData() {
      if (!this.userPerformance || !this.userPerformance.growth_curve) return []
      return this.userPerformance.growth_curve.map((item) => ({
        date: item.date,
        score: Number(item.score) || 0
      }))
    },
    performanceCurvePointsArr() {
      const data = this.performanceCurveData()
      if (!data.length) return []

      const width = 260
      const height = 90
      const offsetX = 20
      const offsetY = 15
      const series = data.slice(-8)
      const maxScore = Math.max(100, ...series.map((i) => Number(i.score) || 0))
      const count = series.length
      if (count < 2) {
        return series.map((_, idx) => ({ x: offsetX + idx * (width / Math.max(count, 1)), y: offsetY + height / 2 }))
      }

      return series.map((item, idx) => {
        const x = offsetX + (idx * width) / (count - 1)
        const value = Number(item.score) || 0
        const y = offsetY + height - (value / maxScore) * height
        return { x, y }
      })
    },
    performanceCurvePoints() {
      return this.performanceCurvePointsArr().map((p) => `${p.x},${p.y}`).join(' ')
    },

    performanceRadarValues() {
      const abilities = this.userPerformance && this.userPerformance.abilities ? this.userPerformance.abilities : {}
      return {
        knowledge: Number(abilities.knowledge) || 0,
        logic: Number(abilities.logic) || 0,
        expression: Number(abilities.expression) || 0,
        problemSolving: Number(abilities.problemSolving) || 0,
        coding: Number(abilities.coding) || 0,
        learning: Number(abilities.learning) || 0
      }
    },
    performanceRadarPoints() {
      const a = this.performanceRadarValues()
      const center = 100
      const maxRadius = 80
      const angles = [-90, -30, 30, 90, 150, 210].map((d) => (d * Math.PI) / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]
      const hasData = values.some((v) => Number(v) > 0)
      const defaultValue = hasData ? 0 : 10

      return values
        .map((v, i) => {
          const actualValue = Number(v) > 0 ? Number(v) : defaultValue
          const r = (actualValue / 100) * maxRadius
          const x = center + r * Math.cos(angles[i])
          const y = center + r * Math.sin(angles[i])
          return `${x},${y}`
        })
        .join(' ')
    },
    performanceRadarDots() {
      const a = this.performanceRadarValues()
      const center = 100
      const maxRadius = 80
      const angles = [-90, -30, 30, 90, 150, 210].map((d) => (d * Math.PI) / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]
      const hasData = values.some((v) => Number(v) > 0)
      const defaultValue = hasData ? 0 : 10

      return values.map((v, i) => {
        const actualValue = Number(v) > 0 ? Number(v) : defaultValue
        const r = (actualValue / 100) * maxRadius
        return {
          x: center + r * Math.cos(angles[i]),
          y: center + r * Math.sin(angles[i])
        }
      })
    },

    formatDate(val) {
      if (!val) return '-'
      const text = String(val)
      const matched = text.match(/^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2}:\d{2})/)
      if (matched) return `${matched[1]} ${matched[2]}`
      const cleaned = text.replace(/\.\d+/, '').replace(/Z$/, '').replace(/T/, ' ')
      return cleaned
    }
  }
}
</script>

<style scoped>
.am-layout {
  display: flex;
  min-height: 100vh;
}
.am-main {
  flex: 1;
  background: #f8fafc;
}
.am-content {
  max-width: 1180px;
  margin: 20px auto;
  padding: 10px;
}
.am-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.am-header__title {
  font-size: 24px;
  margin: 0;
}
.am-header__sub {
  color: #666;
  margin-top: 8px;
}
.am-header__actions {
  display: flex;
  gap: 8px;
}
.search-input {
  width: 220px;
  height: 36px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 0 12px;
}
.am-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
/* 使搜索按钮与筛选控件在同一高度并紧靠注册时间筛选框 */
.am-filters > .btn.btn-primary {
  height: 34px;
  padding: 0 12px;
  margin-left: 4px;
}
.filter-select,
.filter-input,
.filter-date {
  height: 34px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 0 8px;
  font-size: 12px;
}
.filter-select {
  min-width: 120px;
}
.filter-input {
  min-width: 170px;
}
.filter-date {
  min-width: 150px;
}
.table-card {
  background: #fff;
  border: 1px solid #e0e6ed;
  border-radius: 10px;
  overflow: hidden;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}
.data-table th,
.data-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #f1f4f8;
  text-align: left;
  font-size: 12px;
}
.data-table th {
  font-size: 12px;
  font-weight: 600;
  background: #fafbfc;
}
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: #fff;
}
.badge--success { background: #27ae60; }
.badge--danger { background: #ee544b; }

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  color: #fff;
  font-size: 12px;
  min-width: 44px;
  text-align: center;
}
.status-badge--success { background: #22c55e; }
.status-badge--danger { background: #f43f5e; }

.act-btn {
  border: 1px solid #c6cdd8;
  border-radius: 6px;
  border: 0;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.act-btn--success { color: #1f8a54; background: #effbf3; }
.act-btn--danger { color: #c7483b; background: #fff3f2; }
.status-btn {
  border: 1px solid #c6cdd8;
  border-radius: 16px;
  padding: 4px 14px;
  font-size: 12px;
  cursor: pointer;
  min-width: 64px;
}
.status-btn--on {
  color: #1f8a54;
  background: #effbf3;
  border-color: #1f8a54;
}
.status-btn--off {
  color: #c7483b;
  background: #fff3f2;
  border-color: #c7483b;
}
.pagination {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pagination__info { color: #666; }
.pagination__btns {
  display: flex;
  gap: 4px;
}
.action-cell {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.action-btn {
  border: 1px solid #d9e2f3;
  background: #fff;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: #1f4ed8;
  cursor: pointer;
}
.action-btn:hover {
  background: #f2f6ff;
}
.action-btn--danger {
  color: #c93b3b;
  border-color: #f2d5d5;
}
.pg-btn {
  border: 1px solid #d9dfee;
  background: #fff;
  line-height: 1.2;
  border-radius: 4px;
  padding: 5px 10px;
  cursor: pointer;
}
.pg-btn--active { background: #2f80ed; color: #fff; border-color: #2f80ed; }
.pg-btn--ellipsis { cursor: default; }
.table-loading,
.table-empty { padding: 36px; text-align: center; color: #888; }
.toast {
  position: relative;
  padding: 8px 14px;
  margin-bottom: 12px;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  min-width: 150px;
}
.toast--success { background: #27ae60; }
.toast--error { background: #c7483b; }
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
  width: 580px;
  max-width: 92vw;
  height: 100%;
  background: white;
  display: flex;
  flex-direction: column;
  box-shadow: -12px 0 48px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px 18px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  color: white;
}

.drawer-head__avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
  flex-shrink: 0;
}

.drawer-head__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.drawer-head__avatar span {
  color: #fff;
  font-weight: 700;
  font-size: 18px;
}

.drawer-head__info {
  flex: 1;
}


.drawer-head__badge {
  display: inline-flex;
  padding: 2px 9px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 0.3px;
  margin-bottom: 6px;
}

.drawer-head__title {
  font-size: 17px;
  font-weight: 700;
  color: white;
  margin: 0 0 4px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.drawer-head__id {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 400;
}

.drawer-head__sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
}

.drawer-close {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.drawer-close svg {
  width: 14px;
  height: 14px;
}

.drawer-close:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
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

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 32px;
}

.drawer-body::-webkit-scrollbar {
  width: 5px;
}

.drawer-body::-webkit-scrollbar-track {
  background: transparent;
}

.drawer-body::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 3px;
}

.dsec {
  padding: 20px 0;
  border-bottom: 1px solid #f3f4f6;
}

.dsec:last-child {
  border-bottom: none;
}

.dsec__title {
  font-size: 12.5px;
  font-weight: 700;
  color: #374151;
  margin: 0 0 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card__label {
  color: #64748b;
  font-size: 12px;
}

.history-list {
  margin-top: 8px;
}
.history-list ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.history-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #edf2f7;
  font-size: 12px;
}
.history-empty {
  color: #9ca3af;
  font-size: 12px;
  padding: 10px 0;
}
.chart-line {
  position: relative;
  min-height: 150px;
}
.line-chart-svg {
  width: 100%;
  height: 120px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}
.curve-labels {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}
.radar-preview {
  position: relative;
  width: 100%;
  max-width: 260px;
  margin: 0 auto;
}
.radar-chart {
  width: 100%;
  height: auto;
}
.radar-grid {
  fill: none;
  stroke: #cbd5e1;
  stroke-width: 1;
}
.radar-area {
  fill: rgba(59, 130, 246, 0.35);
  stroke: #3b82f6;
  stroke-width: 2;
}
.radar-dot {
  fill: #3b82f6;
}
.radar-labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.radar-label {
  position: absolute;
  font-size: 11px;
  color: #334155;
  font-weight: 500;
}

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

.switch {  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;  border: 1px solid #ced4da;
  border-radius: 999px;
  background: #f1f3f5;}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.user-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #e6ebf3;
}
.user-avatar--fallback {
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  line-height: 1.2;
}
.username {
  font-weight: 600;
  color: #1f2d3d;
}
.real-name {
  font-size: 12px;
  color: #888;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .2s;
  border-radius: 26px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .2s;
  border-radius: 50%;
}
.switch input:checked + .slider {
  background-color: #27ae60;
}
.switch input:checked + .slider:before {
  transform: translateX(24px);
}
</style>