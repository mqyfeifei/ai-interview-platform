<template>
  <div class="am-layout">

    <div class="am-main">
      <div class="am-content">
        <div class="am-header">
          <div class="am-header__left">
            <h1 class="am-header__title">用户管理</h1>
            <p class="am-header__sub">共 <strong>{{ total }}</strong> 位用户</p>
          </div>
          <div class="am-header__actions">
            <button class="btn btn-primary btn-image" @click="addUser">新增用户</button>
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
          <input v-model="schoolFilter" class="filter-input" type="text" placeholder="按学校搜索" @input="onSearch" />
          <input v-model="majorFilter" class="filter-input" type="text" placeholder="按专业搜索" @input="onSearch" />
          <input v-model="usernameFilter" class="filter-input" type="text" placeholder="按用户名搜索" @input="onSearch" />
          <input v-model="emailFilter" class="filter-input" type="text" placeholder="按邮箱搜索" @input="onSearch" />
          <select v-model="createdRangeFilter" class="filter-select" @change="onFilterChange">
            <option value="">注册时间</option>
            <option value="7">近7天</option>
            <option value="30">近30天</option>
            <option value="all">全部</option>
          </select>
          <button v-if="hasFilters" class="btn-clear" @click="clearFilters">清空筛选</button>
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

          <transition name="fade">
            <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal" style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:2500;">
              <div class="modal" style="background:#fff;border-radius:10px;max-width:720px;width:calc(100% - 40px);padding:24px;box-shadow:0 10px 30px rgba(0,0,0,.25);">
                <h3 style="margin-top:0;margin-bottom:16px;font-size:18px;font-weight:700;">{{ editUserForm.id ? '编辑用户信息' : '新增用户' }}</h3>
                <div class="edit-user-form" style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;">
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>用户名<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.username" class="form-control" />
                    <small v-if="editUserErrors.username" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.username }}</small>
                  </label>
                  <label class="input-group"><span>真实姓名</span><input v-model="editUserForm.real_name" class="form-control" /></label>
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>邮箱<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.email" class="form-control" type="email" />
                    <small v-if="editUserErrors.email" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.email }}</small>
                  </label>
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>手机号</span>
                    <input v-model="editUserForm.phone" class="form-control" />
                    <small v-if="editUserErrors.phone" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.phone }}</small>
                  </label>
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>学校<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.school" class="form-control" />
                    <small v-if="editUserErrors.school" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.school }}</small>
                  </label>
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>专业<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.major" class="form-control" />
                    <small v-if="editUserErrors.major" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.major }}</small>
                  </label>
                  <label class="input-group" style="display:flex;flex-direction:column;">
                    <span>年级<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.grade" class="form-control" />
                    <small v-if="editUserErrors.grade" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.grade }}</small>
                  </label>
                  <label v-if="!editUserForm.id" class="input-group" style="display:flex;flex-direction:column;">
                    <span>密码<span style="color:#f43f5e;margin-left:4px;">*</span></span>
                    <input v-model="editUserForm.password" type="password" class="form-control" placeholder="请输入密码" />
                    <small v-if="editUserErrors.password" style="color:#f43f5e;margin-top:4px;">{{ editUserErrors.password }}</small>
                  </label>
                  <label class="input-group" style="display:flex;flex-direction:column;"><span>默认岗位</span>
                    <select v-model="editUserForm.default_job" class="form-control">
                      <option value="">（无）</option>
                      <option v-for="job in jobs" :key="job.id" :value="job.id">{{ job.name }}</option>
                    </select>
                  </label>
                  <div style="grid-column:1/-1;display:flex;align-items:center;gap:10px;">
                    <input type="checkbox" id="edit-user-active" v-model="editUserForm.is_active" />
                    <label for="edit-user-active" style="margin:0;">账号可用</label>
                  </div>
                </div>
                <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:18px;">
                  <button class="btn btn-ghost" @click="closeEditModal" type="button" style="min-width:100px;">取消</button>
                  <button class="btn btn-primary" @click="submitEditUser" :disabled="editLoading" type="button" style="min-width:100px;">
                    {{ editLoading ? '保存中...' : '保存' }}
                  </button>
                </div>
              </div>
            </div>
          </transition>

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
                    <h3 class="dsec__title">用户简历</h3>
                    <div class="info-grid" style="align-items: center;">
                      <div class="info-card" style="flex:1; min-width:220px;">
                        <span class="info-card__label">选中简历</span>
                        <div style="display:flex; align-items:center; gap:8px;">
                          <select
                            v-model="selectedResumeId"
                            @change="onSelectedResumeChange(detailUser.id)"
                            :disabled="resumeLoading || resumeList.length===0"
                            class="filter-select"
                            style="flex: 1;"
                          >
                            <option value="" disabled>请选择简历</option>
                            <option v-for="resume in resumeList" :key="resume.id" :value="resume.id">{{ resume.title }}</option>
                          </select>
                          <span style="white-space:nowrap;">（{{ resumeList.length }}份）</span>
                        </div>
                      </div>
                      <div class="info-card" style="flex:0 0 auto;">
                        <button
                          class="btn btn-sm resume-detail-btn"
                          @click="openResumeModal"
                          :disabled="resumeLoading || !selectedResume"
                        >
                          查看简历详情
                        </button>
                      </div>
                    </div>
                  </section>

                  <section class="dsec">
                    <h3 class="dsec__title">面试记录（共 {{ interviewTotal || userInterviewList.length }} 条）</h3>
                    <div class="history-list">
                      <div v-if="interviewLoading" class="history-empty">加载中...</div>
                      <div v-else-if="!userInterviewList || userInterviewList.length === 0" class="history-empty">暂无面试记录</div>
                      <div v-else-if="!showAllInterviews" class="history-empty">面试记录已折叠，点击下方按钮展开全部。</div>
                      <ul v-else>
                        <li v-for="item in displayedInterviews" :key="item.interview_id">
                          <span>{{ formatDate(item.start_time) || '—' }}</span>
                          <strong>{{ item.job_name || '未知岗位' }}</strong>
                          <span>得分：{{ item.total_score != null ? item.total_score : item.score != null ? item.score : '—' }}</span>
                          <span :class="['status-badge', item.status === 'completed' ? 'status-badge--success' : 'status-badge--danger']">{{ item.status }}</span>
                        </li>
                      </ul>
                      <button
                        v-if="(interviewTotal || userInterviewList.length) > 0"
                        @click="showAllInterviews = !showAllInterviews"
                        class="btn btn-text"
                        style="margin-top: 8px;"
                      >
                        {{ showAllInterviews ? '收起面试记录' : '展开全部面试记录' }}（{{ interviewTotal || userInterviewList.length }}）
                      </button>
                    </div>
                  </section>

                  <transition name="fade">
                    <div v-if="showResumeModal" class="modal-overlay" @click.self="closeResumeModal" style="position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:2000;">
                      <div class="modal" style="background:#fff;border-radius:8px;max-width:960px;width:calc(100vw - 40px);max-height:88vh;overflow:auto;padding:20px;box-shadow:0 8px 24px rgba(0,0,0,.25);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                          <h4 style="margin:0;">简历详情</h4>
                          <button class="btn btn-text" @click="closeResumeModal">关闭</button>
                        </div>
                        <div v-if="resumeLoading">加载中...</div>
                        <div v-else-if="!selectedResume">暂无选中简历</div>
                        <div v-else>
                          <ResumePreview
                            :content="selectedResume.content || {}"
                            :blockOrder="resumeBlockOrder"
                            :config="resumeConfig"
                          />
                        </div>
                      </div>
                    </div>
                  </transition>

                  <section class="dsec">
                  <h3 class="dsec__title">面试综合能力曲线</h3>
                      <div v-if="!hasPerformanceData" class="history-empty">暂无曲线数据</div>
                    <div v-else class="line-chart" ref="performanceLineChart"></div>
                    <div class="curve-labels" style="margin-top:8px;">已完成 {{ (userPerformance && userPerformance.growth_curve ? userPerformance.growth_curve.length : 0) }} 次面试</div>
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
import ResumePreview from '@/components/common/ResumePreview.vue'
import { listAdminUsers, updateAdminUserStatus, updateAdminUser, createAdminUser, deleteAdminUser, getAdminUserPerformance, listInterviews, listAdminUserResumes, getAdminUserResume, listAdminJobs } from '@/api/admin'
import { fetchJobs } from '@/api/job'

let echarts = null

export default {
  name: 'AdminUsers',
  components: { AdminSideNav, ResumePreview },
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
      userInterviewList: [],
      interviewTotal: 0,
      interviewLoading: false,
      showAllInterviews: false,
      activeCurveTab: 'overall',
      curveTabs: [],
      resumeList: [],
      selectedResumeId: '',
      selectedResume: null,
      resumeLoading: false,
      showResumeModal: false,
      resumeBlockOrder: ['profile', 'objective', 'education', 'campus', 'internship', 'work', 'project', 'prices', 'skills'],
      resumeConfig: { titleColor: '#2B2B2B', bodyColor: '#4F4F4F', fontSize: 14, padding: 20 },
      performanceChartInstance: null,
      showEditModal: false,
      jobs: [],
      editUserForm: {
        id: null,
        username: '',
        real_name: '',
        email: '',
        phone: '',
        school: '',
        major: '',
        grade: '',
        default_job: '',
        is_active: true
      },
      editUserErrors: {},
      editLoading: false
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
      if (!this.userInterviewList || this.userInterviewList.length === 0) return []
      if (!this.showAllInterviews) return []
      return this.userInterviewList
    },
    resumeData() {
      const content = (this.selectedResume && this.selectedResume.content) || {}
      return {
        personal: content.personal || {},
        objective: content.objective || {},
        education: Array.isArray(content.education) ? content.education : [],
        skills: Array.isArray(content.skills) ? content.skills : [],
        prices: Array.isArray(content.prices) ? content.prices : [],
      }
    },
    resumeProfile() {
      return this.resumeData.personal || {}
    },
    resumeObjective() {
      return this.resumeData.objective || {}
    },
    resumeEducation() {
      return this.resumeData.education || []
    },
    resumeSkills() {
      return this.resumeData.skills || []
    },
    resumePrices() {
      return this.resumeData.prices || []
    },
    hasPerformanceData() {
      if (!this.userPerformance) return false
      const curve = this.userPerformance.growth_curve || []
      const abilities = this.userPerformance.abilities || {}
      return (curve.length > 0) || Object.keys(abilities).length > 0
    }
  },
  created() {
    this.loadUsers()
    this.loadJobs()
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
          this.users = (data.list || []).slice().sort((a, b) => Number(a.id || 0) - Number(b.id || 0))
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
    async loadJobs() {
      try {
        let res = await listAdminJobs()
        if (res && Array.isArray(res.list) && res.list.length > 0) {
          this.jobs = res.list
          return
        }

        // fallback to public jobs endpoint if admin jobs is empty or unavailable
        const fallback = await fetchJobs()
        this.jobs = Array.isArray(fallback) ? fallback : (fallback && fallback.list ? fallback.list : [])
      } catch (err) {
        console.error('获取岗位列表失败', err)
        this.jobs = []
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
      this.userInterviewList = []
      this.interviewTotal = 0
      this.interviewLoading = true
      this.showAllInterviews = false
      this.activeCurveTab = 'overall'

      try {
        const perfPromise = getAdminUserPerformance(user.id)
        const interviewPromise = this.loadUserInterviews(user.id)
        const resumePromise = this.loadUserResumes(user.id)

        const res = await perfPromise
        this.userPerformance = res || null

        await Promise.all([interviewPromise, resumePromise])
        this.$nextTick(() => {
          this.initPerformanceChart()
        })
      } catch (e) {
        console.error('加载用户绩效、面试记录或简历失败', e)
      } finally {
        this.detailLoading = false
        this.interviewLoading = false
        this.resumeLoading = false
      }
    },
    closeUserDetail() {
      this.showDetail = false
      this.detailUser = null
      this.userPerformance = null
      this.userInterviewList = []
      this.interviewTotal = 0
      this.interviewLoading = false
      if (this.performanceChartInstance && !this.performanceChartInstance.isDisposed()) {
        this.performanceChartInstance.dispose()
      }
      this.performanceChartInstance = null
    },
    async loadUserInterviews(userId) {
      const pageSize = 50
      let page = 1
      let allInterviews = []
      this.interviewLoading = true

      try {
        while (true) {
          const appear = await listInterviews({ user_id: userId, page, size: pageSize })
          if (!appear || !Array.isArray(appear.list)) break

          allInterviews = allInterviews.concat(appear.list)
          this.interviewTotal = appear.total || allInterviews.length
          if (allInterviews.length >= this.interviewTotal || appear.list.length < pageSize) {
            break
          }
          page += 1
        }
      } catch (err) {
        console.error('加载用户面试记录失败', err)
      } finally {
        this.userInterviewList = allInterviews
        this.interviewLoading = false
      }
    },

    async loadUserResumes(userId) {
      this.resumeLoading = true
      this.resumeList = []
      this.selectedResumeId = ''
      this.selectedResume = null

      try {
        const res = await listAdminUserResumes(userId)
        this.resumeList = Array.isArray(res) ? res : []
        if (this.resumeList.length > 0) {
          this.selectedResumeId = this.resumeList[0].id
          await this.loadResumeDetails(userId, this.selectedResumeId)
        }
      } catch (err) {
        console.error('加载用户简历列表失败', err)
      } finally {
        this.resumeLoading = false
      }
    },

    async loadResumeDetails(userId, resumeId) {
      if (!resumeId) return
      this.resumeLoading = true

      try {
        const resume = await getAdminUserResume(userId, resumeId)
        this.selectedResume = resume || null
        this.selectedResumeId = resumeId
      } catch (err) {
        console.error('加载简历详情失败', err)
      } finally {
        this.resumeLoading = false
      }
    },

    onSelectedResumeChange(userId) {
      if (!this.selectedResumeId) {
        this.selectedResume = null
        return
      }
      this.loadResumeDetails(userId, this.selectedResumeId)
    },

    switchCurveTab(tabKey) {
      this.activeCurveTab = tabKey
      this.initPerformanceChart()
    },

    openResumeModal() {
      this.showResumeModal = true
    },
    closeResumeModal() {
      this.showResumeModal = false
    },
    async initPerformanceChart() {
      if (!this.userPerformance) return

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

      const curve = Array.isArray(this.userPerformance.growth_curve) ? this.userPerformance.growth_curve : []
      const abilities = this.userPerformance.abilities || {}
      const dimensionCurves = this.userPerformance.dimension_curves || {}
      const activeTab = this.activeCurveTab || 'overall'
      const CURVE_COLORS = {
        overall: '#4338CA',
        knowledge: '#F59E0B',
        logic: '#3B82F6',
        expression: '#8B5CF6',
        problemSolving: '#EF4444',
        coding: '#10B981',
        learning: '#6366F1'
      }
      const dimLabels = {
        overall: '综合得分',
        knowledge: '专业知识',
        logic: '逻辑',
        expression: '表达',
        problemSolving: '问题解决',
        coding: '代码能力',
        learning: '学习能力'
      }

      let xData = []
      let yData = []
      let seriesName = dimLabels[activeTab] || '得分'
      let color = CURVE_COLORS[activeTab] || '#4338CA'

      if (activeTab === 'overall') {
        xData = curve.map((item) => item.date || '')
        yData = curve.map((item) => Number(item.score) || 0)
      } else {
        const deCurve = Array.isArray(dimensionCurves[activeTab]) ? dimensionCurves[activeTab] : []
        if (deCurve.length > 0) {
          xData = deCurve.map((item) => item.date || '')
          yData = deCurve.map((item) => Number(item.score) || 0)
        } else {
          const point = Number(abilities[activeTab] || 0)
          if (curve && curve.length) {
            xData = curve.map((item) => item.date || '')
            yData = curve.map(() => point)
          } else {
            xData = ['暂无']
            yData = [point]
          }
        }
      }
      if (!xData.length) {
        xData = ['暂无']
        yData = [0]
      }

      const validScores = yData.filter((v) => typeof v === 'number')
      const minScore = validScores.length ? Math.min(...validScores) : 0
      const maxScore = validScores.length ? Math.max(...validScores) : 100
      const yMin = Math.max(0, Math.floor((minScore - 10) / 10) * 10)
      const yMax = Math.min(100, Math.ceil((maxScore + 10) / 10) * 10)

      this.performanceChartInstance.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          confine: true,
          triggerOn: 'mousemove|click',
          backgroundColor: '#1E293B',
          borderColor: 'transparent',
          textStyle: { color: '#F8FAFC', fontSize: 12 },
          formatter: (params) => {
            const p = params[0]
            return `<div style="padding:4px 8px"><b style="font-size:16px;color:${color}">${p.value}</b> 分</div>`
          }
        },
        xAxis: {
          type: 'category',
          data: xData,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#E2E8F0' } },
          axisTick: { show: false },
          axisLabel: { color: '#94A3B8', fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          min: yMin,
          max: yMax,
          splitNumber: 4,
          axisLabel: { color: '#94A3B8', fontSize: 11 },
          splitLine: { lineStyle: { color: '#F1F5F9', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false }
        },
        grid: { left: '12%', right: '12%', top: '16%', bottom: '20%' },
        series: [
          {
            name: seriesName,
            type: 'line',
            data: yData,
            smooth: false,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: { color, borderColor: 'white', borderWidth: 2 },
            lineStyle: { color, width: 2.5 },
            areaStyle: { color: color + '22' },
            markPoint: {
              data: [
                { type: 'max', name: '最高' },
                { type: 'min', name: '最低' }
              ],
              label: { color: 'white', fontSize: 10 },
              itemStyle: { color },
              symbolSize: 40
            }
          }
        ],
        animation: true,
        animationDuration: 600,
        animationEasing: 'cubicOut'
      }, true)
    },
    addUser() {
      this.editUserForm = {
        id: null,
        username: '',
        real_name: '',
        email: '',
        phone: '',
        school: '',
        major: '',
        grade: '',
        default_job: '',
        is_active: true,
        password: ''
      }
      this.editUserErrors = {}
      this.showEditModal = true
    },
    editUser(user) {
      let defaultJobValue = user.default_job_id || ''
      if (!defaultJobValue && user.default_job) {
        const matchedJob = this.jobs.find((job) =>
          String(job.id) === String(user.default_job) || job.name === user.default_job
        )
        if (matchedJob) {
          defaultJobValue = matchedJob.id
        }
      }

      this.editUserForm = {
        id: user.id,
        username: user.username || '',
        real_name: user.real_name || '',
        email: user.email || '',
        phone: user.phone || '',
        school: user.school || '',
        major: user.major || '',
        grade: user.grade || '',
        default_job: defaultJobValue || '',
        is_active: user.is_active !== false,
        password: ''
      }
      this.editUserErrors = {}
      this.showEditModal = true
    },
    closeEditModal() {
      this.showEditModal = false
      this.editLoading = false
    },
    async submitEditUser() {
      const emailValue = (this.editUserForm.email || '').trim()
      const phoneValue = (this.editUserForm.phone || '').trim()
      this.editUserErrors = {}

      if (!this.editUserForm.username || !this.editUserForm.username.trim()) {
        this.editUserErrors.username = '用户名不能为空'
      }

      if (!this.editUserForm.id && !this.editUserForm.password) {
        this.editUserErrors.password = '密码不能为空'
      }

      if (!emailValue) {
        this.editUserErrors.email = '邮箱不能为空'
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
        this.editUserErrors.email = '邮箱格式不正确，请输入有效邮箱地址'
      }

      if (!this.editUserForm.school || !this.editUserForm.school.trim()) {
        this.editUserErrors.school = '学校不能为空'
      }
      if (!this.editUserForm.major || !this.editUserForm.major.trim()) {
        this.editUserErrors.major = '专业不能为空'
      }
      if (!this.editUserForm.grade || !this.editUserForm.grade.trim()) {
        this.editUserErrors.grade = '年级不能为空'
      }

      if (phoneValue && !/^1[3-9]\d{9}$/.test(phoneValue)) {
        this.editUserErrors.phone = '手机号格式不正确，请输入11位手机号'
      }

      if (Object.keys(this.editUserErrors).length > 0) {
        return
      }

      this.editUserForm.email = emailValue
      this.editUserForm.phone = phoneValue

      this.editLoading = true
      try {
        let updated
        if (this.editUserForm.id) {
          updated = await updateAdminUser(this.editUserForm.id, {
            username: this.editUserForm.username,
            real_name: this.editUserForm.real_name,
            email: this.editUserForm.email,
            phone: this.editUserForm.phone,
            school: this.editUserForm.school,
            major: this.editUserForm.major,
            grade: this.editUserForm.grade,
            default_job: this.editUserForm.default_job,
            is_active: this.editUserForm.is_active
          })
        } else {
          if (!this.editUserForm.password) {
            this.editUserErrors.password = '密码不能为空'
            return
          }
          updated = await createAdminUser({
            username: this.editUserForm.username,
            real_name: this.editUserForm.real_name,
            email: this.editUserForm.email,
            phone: this.editUserForm.phone,
            school: this.editUserForm.school,
            major: this.editUserForm.major,
            grade: this.editUserForm.grade,
            default_job: this.editUserForm.default_job,
            is_active: this.editUserForm.is_active,
            password: this.editUserForm.password
          })
          this.total += 1
          // 新用户加入列表最前，为方便查看
          this.users.unshift(updated)
        }

        // 更新列表中的用户信息
        const idx = this.users.findIndex((u) => u.id === updated.id)
        if (idx !== -1 && this.editUserForm.id) {
          this.users.splice(idx, 1, updated)
        }
        // 若详情页打开，刷新当前用户数据
        if (this.detailUser && this.detailUser.id === updated.id) {
          this.detailUser = updated
        }

        this.showToast(this.editUserForm.id ? '用户信息已更新' : '新增用户成功', 'success')
        this.closeEditModal()
      } catch (err) {
        console.error('保存用户信息失败', err)
        const msg = err.message || (err.response && err.response.data && err.response.data.msg) || '保存用户信息失败'
        if (/该邮箱已注册/.test(msg)) {
          this.editUserErrors.email = '该邮箱已注册'
        } else if (/该手机号已注册/.test(msg)) {
          this.editUserErrors.phone = '该手机号已注册'
        } else if (/用户名已存在/.test(msg)) {
          this.editUserErrors.username = '用户名已存在'
        } else {
          this.showToast(msg, 'error')
        }
      } finally {
        this.editLoading = false
      }
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
  max-width: 1400px;
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
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  padding: 0 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}
.btn-primary {
  background: #4338ca;
  color: #fff;
}
.btn-primary:hover {
  background: #3730a3;
}
.btn-image {
  padding-left: 44px;
  position: relative;
}
.btn-image::before {
  content: '';
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='5' x2='12' y2='19'/%3E%3Cline x1='5' y1='12' x2='19' y2='12'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: contain;
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
  padding: 6px 12px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
}
.btn-clear:hover {
  background: #fef2f2;
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
.line-chart {
  width: 100%;
  min-height: 200px;
  height: 200px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
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

.resume-detail-btn {
  background: linear-gradient(90deg, #7c3aed, #6d28d9);
  color: #fff;
  border-color: #7c3aed;
  font-size: 14px;
  font-weight: 600;
  min-width: 120px;
  padding: 8px 10px;
  border-radius: 6px;
}
.resume-detail-btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #5b21b6, #6d28d9);
  border-color: #5b21b6;
}
.resume-detail-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>