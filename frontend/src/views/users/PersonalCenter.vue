<!--
  =============================================
  frontend/src/views/users/PersonalCenter.vue
  个人中心页组件
  ============================================= --> 
<template>
  <div class="profile-page">
    <div class="profile-body page-container">
      <div class="profile-main-grid">
        <!-- 左侧：用户信息 + 成长体系 -->
        <div class="profile-left-col">
          <div class="card user-card">
            <div class="card-header">
              <h3>个人信息</h3>
              <button class="edit-btn" @click="openEditModal">编辑</button>
            </div>
            <div class="user-card-body">
              <div class="user-center">
                <div class="user-avatar-wrap" @click="triggerAvatarUpload">
                  <div class="avatar-lg">
                    <img v-if="userInfo && userInfo.avatar" :src="resolvedAvatarSrc" alt="头像" />
                    <span v-else class="avatar-lg__fallback">{{ avatarLetter }}</span>
                  </div>
                </div>
                <input ref="avatarInput" type="file" accept="image/*" class="hidden-input" @change="handleAvatarChange" />
                <h2 class="user-name">{{ (userInfo && userInfo.username) || '用户' }}</h2>
                
        <div class="profile-stats">
          <div class="profile-stat">
            <span class="profile-stat__value">{{ memberDays }}</span>
            <span class="profile-stat__label">加入天数</span>
          </div>
          <div class="profile-stat-divider"></div>
          <div class="profile-stat">
            <span class="profile-stat__value">{{ practiceCount }}</span>
            <span class="profile-stat__label">练习次数</span>
          </div>
          <div class="profile-stat-divider"></div>
          <div class="profile-stat">
            <span class="profile-stat__value">{{ avgScoreDisplay }}</span>
            <span class="profile-stat__label">平均分数</span>
          </div>
        </div>
              </div>

              <div class="user-info-list">
                <div class="user-info-row" v-for="item in infoRows" :key="item.key">
                  <span class="user-info-key">{{ item.label }}</span>
                  <span class="user-info-value">{{ item.value || '未填写' }}</span>
                </div>
                <div class="user-info-row">
                  <span class="user-info-key">默认岗位</span>
                  <span class="user-info-value">{{ defaultJobDisplayName }}</span>
                </div>
              </div>

              <div class="resume-btn-wrap">
                <button class="resume-btn" @click="goToResume">我的简历</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 双栏布局：能力雷达 + 学习动态/成就 -->
      <section class="section two-column-section" v-if="isLoggedIn">
        <!-- 左侧：能力雷达图预览 -->
        <div class="ability-card">
          <div class="ability-card__header">
            <h3 class="ability-card__title">📊 能力概览</h3>
            <button class="ability-card__more" @click="$router.push('/history')">详情</button>
          </div>
          <div class="radar-preview">
            <svg viewBox="0 0 200 200" class="radar-chart">
              <!-- 背景网格 -->
              <polygon class="radar-grid" points="100,20 168,65 168,135 100,180 32,135 32,65" />
              <polygon class="radar-grid" points="100,40 152,72 152,128 100,160 48,128 48,72" />
              <polygon class="radar-grid" points="100,60 136,80 136,120 100,140 64,120 64,80" />
              <!-- 能力区域 -->
              <polygon class="radar-area" :points="radarPoints" />
              <!-- 能力点 -->
              <circle v-for="(point, idx) in radarDots" :key="idx" :cx="point.x" :cy="point.y" r="4" class="radar-dot" />
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
          <p class="ability-card__summary">
            综合评分 <strong>{{ stats.avgScore || '--' }}</strong> 分，{{ abilityComment }}
          </p>
        </div>

        <!-- 右侧：成就与动态 -->
        <div class="achievement-card">
          <div class="achievement-card__header">
            <h3 class="achievement-card__title">🏆 我的成就</h3>
            <div class="streak-badge">
              <span class="streak-badge__fire">🔥</span>
              <span class="streak-badge__text">{{ streakDays }}天连续</span>
            </div>
          </div>
          
          <!-- 成就徽章 -->
          <div class="badges-row">
            <div 
              class="badge-item" 
              v-for="badge in displayBadges" 
              :key="badge.id"
              :class="{ locked: !badge.unlocked }"
            >
              <span class="badge-item__icon">{{ badge.icon }}</span>
              <span class="badge-item__name">{{ badge.name }}</span>
            </div>
          </div>

          <!-- 最近动态 -->
          <div class="recent-activity">
            <h4 class="recent-activity__title">最近动态</h4>
            <div class="activity-list">
              <div class="activity-item" v-for="(act, idx) in recentActivities" :key="idx">
                <span class="activity-item__icon">{{ act.icon }}</span>
                <span class="activity-item__text">{{ act.text }}</span>
                <span class="activity-item__time">{{ act.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
      </div>

      <!-- 账号安全 -->
      <section class="profile-section">
        <h2 class="section-title" style="margin-bottom: 12px">账号安全</h2>
        <div class="menu-card menu-card--security">
          <button
            class="menu-item"
            v-for="item in securityMenu"
            :key="item.label"
            @click="item.action"
          >
            <span class="menu-item__icon" :style="{ background: item.iconBg }">{{ item.icon }}</span>
            <div class="menu-item__content">
              <span class="menu-item__label">{{ item.label }}</span>
              <span class="menu-item__sub">{{ item.sub }}</span>
            </div>
            <svg class="menu-item__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </section>

      <!-- 退出登录 -->
      <section class="profile-section">
        <button class="logout-btn" @click="confirmLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出登录
        </button>
      </section>


    </div>

    <!-- 使用帮助指南弹窗 -->
    <HelpGuideModal v-model="showHelpGuide" />

    <!-- 编辑信息弹窗 -->
    <transition name="modal">
      <div v-if="showEditModal" class="modal-overlay modal-overlay--center" @click.self="showEditModal = false">
        <div class="modal-sheet edit-modal-sheet">
          <div class="edit-modal-header">
            <span class="edit-modal-title">
              <span class="edit-modal-title-icon">📝</span>
              编辑个人信息
            </span>
            <button class="edit-modal-close" @click="showEditModal = false">✕</button>
          </div>
          <div class="edit-modal-body">
            <div class="form-row">
              <label class="form-label">真实姓名</label>
              <input v-model="editForm.realName" type="text" class="form-control" placeholder="请输入真实姓名" />
            </div>
            <div class="form-row">
              <label class="form-label">昵称</label>
              <input v-model="editForm.username" type="text" class="form-control" placeholder="请输入昵称" />
            </div>
            <!-- 邮箱和手机号由其它流程维护，此处不允许直接编辑 -->
            <div class="form-row">
              <label class="form-label">学校</label>
              <input v-model="editForm.school" type="text" class="form-control" placeholder="请输入学校名称" />
            </div>
            <div class="form-row">
              <label class="form-label">专业</label>
              <input v-model="editForm.major" type="text" class="form-control" placeholder="请输入专业名称" />
            </div>
            <div class="form-row">
              <label class="form-label">年级</label>
              <select v-model="editForm.grade" class="form-control form-select">
                <option value="">选择年级</option>
                <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
          </div>
          <div class="edit-modal-footer">
            <button class="btn btn-ghost" @click="showEditModal = false">取消</button>
            <button class="btn btn-primary" :disabled="savingInfo" @click="saveUserInfo">
              <span v-if="savingInfo" class="btn-spinner"></span>
              {{ savingInfo ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 修改密码弹窗 -->
    <transition name="modal">
      <div v-if="showPasswordModal" class="modal-overlay modal-overlay--center" @click.self="showPasswordModal = false">
        <div class="modal-sheet password-sheet">
          <div class="modal-header">
            <div class="password-header">
              <h3 class="password-header__title">修改密码</h3>
              <p class="password-header__sub">为保障账号安全，请先验证当前密码</p>
            </div>
            <button class="modal-close" @click="showPasswordModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="password-card">
              <div class="form-group">
                <label>当前密码</label>
                <input v-model="pwdForm.oldPassword" type="password" class="form-control" placeholder="请输入当前密码" autocomplete="current-password" />
                <span v-if="pwdErrors.oldPassword" class="form-error">{{ pwdErrors.oldPassword }}</span>
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input v-model="pwdForm.newPassword" type="password" class="form-control" placeholder="至少6位" autocomplete="new-password" />
                <div class="form-hint">建议使用强度较高的密码</div>
                <span v-if="pwdErrors.newPassword" class="form-error">{{ pwdErrors.newPassword }}</span>
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input v-model="pwdForm.confirmPassword" type="password" class="form-control" placeholder="再次输入新密码" autocomplete="new-password" />
                <span v-if="pwdErrors.confirmPassword" class="form-error">{{ pwdErrors.confirmPassword }}</span>
              </div>

              <div v-if="pwdError" class="global-error">{{ pwdError }}</div>
              <div v-if="pwdSuccess" class="success-float" role="status" aria-live="polite">
                <div class="success-tip success-tip--float">✅ 密码修改成功！</div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showPasswordModal = false">取消</button>
            <button class="btn btn-primary" :disabled="savingPwd" @click="savePassword">
              <span v-if="savingPwd" class="btn-spinner"></span>
              {{ savingPwd ? '保存中...' : '确认修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 绑定手机弹窗 -->
    <transition name="modal">
      <div v-if="showBindPhoneModal" class="modal-overlay modal-overlay--center" @click.self="showBindPhoneModal = false">
        <div class="modal-sheet phone-sheet">
          <div class="modal-header">
            <div class="phone-header">
              <h3 class="phone-header__title">绑定手机</h3>
              <p class="phone-header__sub">
                {{ userInfo && userInfo.phone ? '你可以更新绑定手机号' : '绑定后可使用手机号登录' }}
              </p>
            </div>
            <button class="modal-close" @click="showBindPhoneModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="phone-card">
              <div class="phone-current" v-if="userInfo && userInfo.phone">
                <span class="phone-current__label">当前绑定</span>
                <span class="phone-current__value">{{ maskPhone(userInfo.phone) }}</span>
              </div>

              <div class="form-group">
                <label>手机号</label>
                <input
                  v-model="bindPhoneForm.phone"
                  type="tel"
                  inputmode="numeric"
                  class="form-control"
                  placeholder="请输入 11 位手机号"
                  maxlength="11"
                  autocomplete="tel"
                />
                <div class="form-hint">仅支持中国大陆手机号（以 1 开头的 11 位数字）</div>
                <span v-if="bindPhoneErrors.phone" class="form-error">{{ bindPhoneErrors.phone }}</span>
              </div>

              <div v-if="bindPhoneError" class="global-error">{{ bindPhoneError }}</div>
              <div v-if="bindPhoneSuccess" class="success-float" role="status" aria-live="polite">
                <div class="success-tip success-tip--float">✅ 手机号绑定成功！</div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showBindPhoneModal = false">取消</button>
            <button class="btn btn-primary" :disabled="bindingPhone" @click="saveBindPhone">
              <span v-if="bindingPhone" class="btn-spinner"></span>
              {{ bindingPhone ? '绑定中...' : '确认绑定' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 岗位选择弹窗 -->
    <transition name="modal">
      <div v-if="showJobPicker" class="modal-overlay" @click.self="showJobPicker = false">
        <div class="modal-sheet modal-sheet--tall">
          <div class="modal-header">
            <h3>选择默认岗位</h3>
            <button class="modal-close" @click="showJobPicker = false">✕</button>
          </div>
          <div class="modal-body job-picker-body">
            <div
              class="job-picker-item"
              v-for="job in allJobs"
              :key="job.id"
              :class="{ selected: selectedJobId === job.id }"
              @click="pickJob(job)"
            >
              <div class="job-picker-item__icon" :style="{ background: job.colorBg }">{{ job.icon }}</div>
              <div class="job-picker-item__info">
                <p class="job-picker-item__name">{{ job.name }}</p>
                <p class="job-picker-item__stack">{{ job.techStack.slice(0, 3).join(' · ') }}</p>
              </div>
              <div v-if="selectedJobId === job.id" class="job-picker-item__check">✓</div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 退出确认弹窗 -->
    <transition name="modal">
      <div v-if="showLogoutConfirm" class="modal-overlay modal-overlay--center" @click.self="showLogoutConfirm = false">
        <div class="modal-sheet modal-sheet--sm">
          <div class="modal-header">
            <h3>退出登录</h3>
          </div>
          <div class="modal-body">
            <p style="color: #64748B; font-size: 14px; line-height: 1.6">确定要退出当前账号吗？你的练习数据不会丢失。</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showLogoutConfirm = false">取消</button>
            <button class="btn btn-danger" :disabled="loggingOut" @click="handleLogout">
              <span v-if="loggingOut" class="btn-spinner btn-spinner--dark"></span>
              {{ loggingOut ? '退出中...' : '确认退出' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 版本信息卡片弹窗 -->
    <transition name="modal">
      <div v-if="showVersionCard" class="modal-overlay version-modal" @click.self="showVersionCard = false">
        <div class="modal-sheet version-card">
          <div class="modal-header" style="justify-content: center; border-bottom: none; position: relative; width: 100%; padding: 0;">
            <h3 style="margin: 0 auto; font-size: 16px; font-weight: 600;">版本信息</h3>
            <button class="modal-close" @click="showVersionCard = false" style="position: absolute; right: 0; top: 0;">✕</button>
          </div>
          <div class="modal-body" style="width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center; padding: 0;">
            <p class="version-card__text">当前版本：v1.0.0</p>
            <p class="version-card__text">如需获取最新版本信息，请联系管理员。</p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { JOB_TYPES, GRADE_OPTIONS } from '@/utils/constants'
import { getDashboardStats } from '@/api/user'
import HelpGuideModal from '@/components/common/HelpGuideModal.vue'
import { ref } from 'vue';

export default {
  name: 'PersonalCenter',
  components: {
    HelpGuideModal,
  },
  data() {
    return {
      showEditModal: false,
      showPasswordModal: false,
      showBindPhoneModal: false,
      showJobPicker: false,
      showLogoutConfirm: false,
      showHelpGuide: false,
      savingInfo: false,
      savingPwd: false,
      bindingPhone: false,
      loggingOut: false,
      // 编辑表单只包含后端 PUT /users/me 支持的字段
      // 编辑表单只包含后端 PUT /users/me 支持的字段
      editForm: { realName: '', username: '', school: '', major: '', grade: '' },
      pwdForm: { oldPassword: '', newPassword: '', confirmPassword: '' },
      pwdErrors: {},
      pwdError: '',
      pwdSuccess: false,

      bindPhoneForm: { phone: '' },
      bindPhoneErrors: {},
      bindPhoneError: '',
      bindPhoneSuccess: false,

      selectedJobId: null,
      gradeOptions: GRADE_OPTIONS.map(o => o.value),
      allJobs: JOB_TYPES,

      // 仪表盘统计数据（能力雷达、成就、最近活动）
      stats: {
        totalInterviews: 0,
        avgScore: 0,
        maxScore: 0,
        lastInterviewScore: 0,
        lastInterviewJob: '',
        lastInterviewAt: '',
        scoreImprovement: 0,
        weeklyPractice: 0,
        streakDays: 0,
        abilities: {
          knowledge: 0,
          logic: 0,
          expression: 0,
          problemSolving: 0,
          coding: 0,
          learning: 0
        }
      },

      // 成就徽章 - 根据真实数据动态计算
      badges: [
        { id: 1, icon: '🌟', name: '初次面试', condition: 'firstInterview' },
        { id: 2, icon: '🔥', name: '连续3天', condition: 'streak3' },
        { id: 3, icon: '💪', name: '突破80分', condition: 'score80' },
        { id: 4, icon: '🏅', name: '面试达人', condition: 'interviews10' },
        { id: 5, icon: '👑', name: '全能王者', condition: 'score90' }
      ],

      // 新增版本卡片弹窗的响应式变量
      showVersionCard: ref(false),


    }
  },
  computed: {
    ...mapGetters('user', ['userInfo', 'userName', 'defaultJob', 'defaultJobId', 'defaultJobName', 'isLoggedIn']),

    avatarLetter() {
      return (this.userName || '用').charAt(0)
    },

    resolvedAvatarSrc() {
      const raw = this.userInfo && this.userInfo.avatar
      if (!raw) return ''

      const asString = String(raw)
      // 绝对地址直接使用
      if (/^https?:\/\//i.test(asString)) {
        return this.appendCacheBuster(asString)
      }

      // 相对地址（如 /uploads/...）补全为后端地址
      const origin = (process.env.VUE_APP_BACKEND_ORIGIN || '').replace(/\/$/, '')
      if (origin) {
        return this.appendCacheBuster(`${origin}${asString.startsWith('/') ? '' : '/'}${asString}`)
      }

      // 兜底：走当前域名（若你配置了 devServer /uploads 代理也能生效）
      return this.appendCacheBuster(asString)
    },

    infoRows() {
      const u = this.userInfo || {}
      return [
        { key: 'realName', label: '真实姓名', value: u.real_name },
        { key: 'username', label: '昵称', value: u.username },
        { key: 'email', label: '邮箱', value: u.email },
        { key: 'phone', label: '手机', value: u.phone ? u.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : null },
        { key: 'school', label: '学校', value: u.school },
        { key: 'major', label: '专业', value: u.major },
        { key: 'grade', label: '年级', value: u.grade }
      ]
    },

    // 继续保留个性统计和数据展示相关（平稳安全）
    achievementBadges() {
      return [
        { icon: '🔥', title: '连续登录', value: `${this.memberDays}天` },
        { icon: '🎯', title: '目标达成', value: `${this.practiceCount}次练习` },
        { icon: '⭐', title: '高分率', value: `${this.avgScoreDisplay}分` }
      ]
    },

    currentDefaultJob() {
      const jobId = this.defaultJob
      if (!jobId) return null
      // backend may return either the string identifier (e.g. 'java-backend')
      // or a numeric dbId; handle both cases
      return JOB_TYPES.find(j => j.id === jobId || String(j.dbId) === String(jobId)) || null
    },
    defaultJobDisplayName() {
      if (this.currentDefaultJob) return this.currentDefaultJob.name
      if (this.defaultJobName) return this.defaultJobName
      return '未设置'
    },
    userLevel() {
      const level = Math.min(10, Math.max(1, Math.floor((this.memberDays || 0) / 30) + 1))
      return level
    },
    userIntro() {
      const u = this.userInfo || {}
      const intro = u.bio || u.description || u.about || ''
      return intro ? intro : '暂无个人简介'
    },

    memberDays() {
      const u = this.userInfo
      if (!u) return 0
      const createdRaw = u.createdAt || u.created_at
      if (!createdRaw) return 0

      const created = new Date(createdRaw)
      if (Number.isNaN(created.getTime())) return 0

      const now = new Date()
      const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const startCreated = new Date(created.getFullYear(), created.getMonth(), created.getDate())

      const msPerDay = 24 * 60 * 60 * 1000
      // 包含当天，差值加1
      const days = Math.floor((startToday.getTime() - startCreated.getTime()) / msPerDay) + 1
      return Math.max(0, days)
    },

    practiceCount() {
      const u = this.userInfo || {}
      const value = u.totalInterviews ?? u.total_interviews
      const asNumber = Number(value)
      return Number.isFinite(asNumber) ? asNumber : 0
    },

    avgScoreDisplay() {
      const u = this.userInfo || {}
      const value = u.avgScore ?? u.avg_score
      const asNumber = Number(value)
      if (!Number.isFinite(asNumber)) return 0
      // 后端已 round 到两位，这里仅做展示兜底
      return (Math.round(asNumber * 100) / 100).toString()
    },

    streakDays() {
      return this.stats?.streakDays || this.stats?.weeklyPractice || 0
    },

    hasAbilityData() {
      if (!this.stats || !this.stats.abilities) return false
      return Object.values(this.stats.abilities).some(v => Number(v) > 0)
    },

    radarPoints() {
      const a = this.stats?.abilities || { knowledge: 0, logic: 0, expression: 0, problemSolving: 0, coding: 0, learning: 0 }
      const center = 100
      const maxRadius = 80
      const angles = [-90, -30, 30, 90, 150, 210].map(d => d * Math.PI / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]

      const hasData = values.some(v => Number(v) > 0)
      const defaultValue = hasData ? 0 : 10

      return values.map((v, i) => {
        const actualValue = Number(v) > 0 ? Number(v) : defaultValue
        const r = (actualValue / 100) * maxRadius
        const x = center + r * Math.cos(angles[i])
        const y = center + r * Math.sin(angles[i])
        return `${x},${y}`
      }).join(' ')
    },

    radarDots() {
      const a = this.stats?.abilities || { knowledge: 0, logic: 0, expression: 0, problemSolving: 0, coding: 0, learning: 0 }
      const center = 100
      const maxRadius = 80
      const angles = [-90, -30, 30, 90, 150, 210].map(d => d * Math.PI / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]

      const hasData = values.some(v => Number(v) > 0)
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

    abilityComment() {
      if (!this.hasAbilityData) return '完成面试后解锁能力分析'
      const avg = Number(this.stats?.avgScore || 0)
      if (avg >= 85) return '表现优秀，继续保持！'
      if (avg >= 70) return '整体良好，部分能力可加强'
      if (avg >= 60) return '有提升空间，建议多练习'
      return '建议从基础开始系统学习'
    },

    displayBadges() {
      return this.badges.map(badge => {
        let unlocked = false
        switch (badge.condition) {
          case 'firstInterview':
            unlocked = (this.stats?.totalInterviews || 0) >= 1
            break
          case 'streak3':
            unlocked = (this.streakDays || 0) >= 3
            break
          case 'score80':
            unlocked = (this.stats?.maxScore || 0) >= 80 || (this.stats?.avgScore || 0) >= 80
            break
          case 'interviews10':
            unlocked = (this.stats?.totalInterviews || 0) >= 10
            break
          case 'score90':
            unlocked = (this.stats?.maxScore || 0) >= 90 || (this.stats?.avgScore || 0) >= 90
            break
        }
        return { ...badge, unlocked }
      })
    },

    recentActivities() {
      const activities = []
      if (this.stats?.lastInterviewAt) {
        activities.push({
          icon: '🎯',
          text: `完成了 ${this.stats?.lastInterviewJob || '面试'} 面试`,
          time: this.formatDate(this.stats.lastInterviewAt)
        })
      }
      if ((this.stats?.totalInterviews || 0) > 0) {
        activities.push({
          icon: '📈',
          text: `累计面试 ${this.stats.totalInterviews} 次`,
          time: '总计'
        })
      }
      if (this.streakDays > 0) {
        activities.push({
          icon: '🔥',
          text: `连续学习 ${this.streakDays} 天`,
          time: '进行中'
        })
      }
      if (activities.length === 0) {
        activities.push({
          icon: '💡',
          text: '开始你的第一次面试练习吧',
          time: '待解锁'
        })
      }
      return activities.slice(0, 3)
    },

    securityMenu() {
      return [
        {
          label: '修改密码',
          sub: '定期修改密码，保护账号安全',
          icon: '🔒',
          iconBg: '#EEF2FF',
          action: () => { this.openPasswordModal() }
        },
        {
          label: '绑定手机',
          sub: this.userInfo && this.userInfo.phone ? '已绑定 ' + this.maskPhone(this.userInfo.phone) : '未绑定，绑定后可用手机登录',
          icon: '📱',
          iconBg: '#D1FAE5',
          action: () => { this.openBindPhoneModal() }
        }
      ]
    },

    otherMenu() {
      return [
        { label: '帮助', icon: '❓', iconBg: 'linear-gradient(135deg, #FFD600 0%, #FF9800 100%)', sub: '查看平台使用指南', action: () => { this.showHelpGuide = true } },
        {
          label: '版本',
          icon: 'ℹ️',
          iconBg: 'linear-gradient(135deg, #2196F3 0%, #21CBF3 100%)',
          sub: 'v1.0.0',
          action: () => {
            this.showVersionCard = true;
          }
        }
      ]
    }
  },
  created() {
    this.selectedJobId = this.defaultJob
    this.loadDashboardStats()
  },
  watch: {
    '$route.query.action': {
      immediate: true,
      handler(action) {
        if (!action) return
        this.handleProfileAction(action)
      }
    }
  },
  mounted() {
    // 页面加载时从数据库同步最新用户信息
    this.syncUserInfo()
  },
  methods: {
    ...mapActions('user', ['updateUserInfo', 'changePassword', 'updateDefaultJob', 'logout', 'fetchUserInfo', 'uploadAvatar', 'bindPhone']),

    appendCacheBuster(url) {
      if (!url) return url
      const stamp = Date.now()
      return url.includes('?') ? `${url}&t=${stamp}` : `${url}?t=${stamp}`
    },
    
    goToJobSelection() {
      this.$router.push('/interview/select')
    },

    goToResume() {
      this.$router.push('/resume')
    },

    // 从数据库同步用户信息
    async syncUserInfo() {
      try {
        await this.fetchUserInfo()
        this.selectedJobId = this.defaultJob
      } catch (err) {
        console.error('同步用户信息失败', err)
      }
    },

    handleProfileAction(action) {
      const normalized = String(action || '').toLowerCase()
      if (normalized === 'password') {
        this.showPasswordModal = true
      } else if (normalized === 'phone') {
        this.showBindPhoneModal = true
      } else if (normalized === 'help') {
        this.showHelpGuide = true
      } else if (normalized === 'version') {
        this.showVersionCard = true
      }
    },

    async loadDashboardStats() {
      try {
        const data = await getDashboardStats()
        this.stats = {
          ...this.stats,
          ...data,
          abilities: {
            ...this.stats.abilities,
            ...(data.abilities || {})
          }
        }
      } catch (err) {
        console.warn('加载仪表盘统计数据失败', err)
      }
    },

    maskPhone(phone) {
      return phone ? phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : ''
    },

    triggerAvatarUpload() {
      const input = this.$refs.avatarInput
      if (input && typeof input.click === 'function') {
        input.click()
      } else {
        console.warn('avatarInput ref not found')
      }
    },

    handleAvatarChange(e) {
      const file = e.target.files[0]
      if (!file) return
      if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB')
        return
      }
      // 允许重复选择同一文件也触发 change
      e.target.value = ''
      this.doUploadAvatar(file)
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    async doUploadAvatar(file) {
      try {
        await this.uploadAvatar(file)
        // 再从数据库同步一次，确保展示最新统计/字段
        await this.syncUserInfo()
      } catch (err) {
        alert(err?.message || '头像上传失败')
      }
    },

    openEditModal() {
      const u = this.userInfo || {};
      // only copy fields that are editable through the profile API
      this.editForm = {
        realName: u.real_name || '',
        username: u.username || '',
        school: u.school || '',
        major: u.major || '',
        grade: u.grade || ''
      };
      this.showEditModal = true;
    },

    copyUserId() {
      const id = this.userInfo?.id
      if (!id) {
        alert('用户ID不可用')
        return
      }
      navigator.clipboard.writeText(String(id)).then(() => {
        alert('用户ID已复制')
      }).catch(() => {
        alert('复制失败，请手动复制')
      })
    },

    async saveUserInfo() {
      // 基本校验：昵称必填
      if (!this.editForm.username || !String(this.editForm.username).trim()) {
        alert('请输入昵称')
        return
      }

      // 备注：邮箱和手机号不通过 PUT /users/me 更新。
      // 手机有专门的绑定接口，邮箱暂时不支持在线修改。


      this.savingInfo = true
      try {
        // 构建仅包含后端支持字段的 payload
        const payload = {
          real_name: this.editForm.realName,
          username: this.editForm.username,
          school: this.editForm.school,
          major: this.editForm.major,
          grade: this.editForm.grade
        }
        await this.updateUserInfo(payload)


        // 刷新用户信息
        await this.syncUserInfo()
        this.showEditModal = false
      } catch (e) {
        alert(e?.message || '保存失败')
      } finally {
        this.savingInfo = false
      }
    },

    openPasswordModal() {
      this.pwdForm = { oldPassword: '', newPassword: '', confirmPassword: '' }
      this.pwdErrors = {}
      this.pwdError = ''
      this.pwdSuccess = false
      this.showPasswordModal = true
    },

    openBindPhoneModal() {
      const current = this.userInfo && this.userInfo.phone ? String(this.userInfo.phone) : ''
      this.bindPhoneForm = { phone: current }
      this.bindPhoneErrors = {}
      this.bindPhoneError = ''
      this.bindPhoneSuccess = false
      this.showBindPhoneModal = true
    },

    async saveBindPhone() {
      this.bindPhoneErrors = {}
      this.bindPhoneError = ''
      this.bindPhoneSuccess = false

      const phone = String(this.bindPhoneForm.phone || '').trim()
      if (!phone) {
        this.bindPhoneErrors.phone = '请输入手机号'
        return
      }
      if (!/^1\d{10}$/.test(phone)) {
        this.bindPhoneErrors.phone = '手机号格式不正确'
        return
      }

      this.bindingPhone = true
      try {
        await this.bindPhone(phone)
        // 再同步一次，确保显示后端最终数据
        await this.syncUserInfo()
        this.bindPhoneSuccess = true
        setTimeout(() => { this.showBindPhoneModal = false }, 1200)
      } catch (e) {
        const msg = e?.message || '绑定失败'
        // 手机号相关错误优先显示在输入框下方
        if (/手机号|绑定/.test(msg)) {
          this.bindPhoneErrors.phone = msg
        } else {
          this.bindPhoneError = msg
        }
      } finally {
        this.bindingPhone = false
      }
    },

    async savePassword() {
      this.pwdErrors = {}
      this.pwdError = ''
      this.pwdSuccess = false

      if (!this.pwdForm.oldPassword) { this.pwdErrors.oldPassword = '请输入当前密码'; return }
      if (!this.pwdForm.newPassword || this.pwdForm.newPassword.length < 6) { this.pwdErrors.newPassword = '新密码不能少于6位'; return }
      if (this.pwdForm.newPassword !== this.pwdForm.confirmPassword) { this.pwdErrors.confirmPassword = '两次密码不一致'; return }

      this.savingPwd = true
      try {
        await this.changePassword({
          oldPassword: this.pwdForm.oldPassword,
          newPassword: this.pwdForm.newPassword
        })
        this.pwdSuccess = true
        setTimeout(() => { this.showPasswordModal = false }, 1500)
      } catch (e) {
        const msg = e?.message || '修改失败'
        // 后端校验旧密码错误时，将提示显示在旧密码输入框下方
        if (/旧密码|当前密码/.test(msg)) {
          this.pwdErrors.oldPassword = msg
        } else {
          this.pwdError = msg
        }
      } finally {
        this.savingPwd = false
      }
    },

    async pickJob(job) {
      this.selectedJobId = job.id
      try {
        await this.updateDefaultJob(job.id)
        // 保存成功后同步用户信息，确保默认岗位显示正确
        await this.syncUserInfo()
      } catch (e) {
        console.warn('更新默认岗位失败', e)
        alert('更新默认岗位失败，请重试')
      }
      setTimeout(() => { this.showJobPicker = false }, 300)
    },

    confirmLogout() {
      this.showLogoutConfirm = true
    },

    async handleLogout() {
      this.loggingOut = true
      try {
        await this.logout()
        this.$router.push('/login')
      } finally {
        this.loggingOut = false
        this.showLogoutConfirm = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// 头部
.profile-header {
  background: $gradient-primary;
  position: relative;
  overflow: hidden;
  padding-bottom: $spacing-md;

  &::before {
    content: '';
    position: absolute;
    width: 350px; height: 350px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    top: -100px; right: -80px;
  }
}

.profile-header__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px $spacing-base $spacing-md;
  text-align: center;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: $spacing-md;
  cursor: pointer;
}

.avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  border: 3px solid rgba(255,255,255,0.4);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 100%; height: 100%; object-fit: cover; }

  &__fallback {
    font-size: 36px;
    font-weight: $font-weight-bold;
    color: white;
    font-family: $font-family-display;
  }
}

.avatar-edit-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 26px;
  height: 26px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow;
  color: $primary;
  svg { width: 13px; height: 13px; }
}

.hidden-input { display: none; }

.profile-header__name {
  font-family: $font-family-display;
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: white;
  margin-bottom: 6px;
}

.profile-header__school {
  font-size: $font-size-sm;
  color: rgba(255,255,255,0.65);
  margin-bottom: $spacing-lg;
}

.text-muted-inline { color: rgba(255,255,255,0.45); }

.profile-stats {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-xl;
  padding: $spacing-sm $spacing-lg;
}

.profile-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;

  &__value {
    font-family: $font-family-display;
    font-size: $font-size-xl;
    font-weight: $font-weight-extrabold;
    color: white;
    line-height: 1;
  }
  &__label { font-size: $font-size-xs; color: rgba(255,255,255,0.55); }
}

.profile-stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(255,255,255,0.2);
}

.user-card .profile-stats {
  background: #f9f9ff;
  border: 1px solid #e8e9ff;
  border-radius: 12px;
  padding: 10px 12px;
  color: #1f2a44;
}

.user-card .profile-stat__value {
  color: #0f1531;
}

.user-card .profile-stat__label {
  color: #667085;
}

// 内容区
.profile-body {
  padding: 0;
  animation: fadeSlideUp 0.4s ease both;
}

.profile-section {
  margin-bottom: 24px;
}

.profile-main-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(420px, 2.1fr);
  gap: 24px;
  align-items: start;
}

@media (max-width: 1024px) {
  .profile-main-grid {
    grid-template-columns: minmax(220px, 1fr);
  }
}

.profile-left-col,
.profile-right-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.resume-btn-wrap {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}

.resume-btn {
  width: 100%;
  max-width: 280px;
  height: 44px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(90deg, #6b5cf4 0%, #4f46e5 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.24);
}

.resume-btn:hover {
  filter: brightness(1.05);
}

.right-widget-grid {
  display: grid;
  grid-template-columns: 1.15fr 1.6fr;
  gap: 16px;
}

.ability-card {
  background: #DDD6FE;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 20px rgba(47, 52, 72, 0.08);
  padding: 5px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 300px;
  margin-bottom:30px;
}

.ability-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ability-card__title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.ability-card__more {
  font-size: 12px;
  color: #4f46e5;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 600;
}

.ability-card__summary {
  text-align: center;
  margin-top: 8px;
  color: #4b5563;
  font-size: 14px;
}

.ability-card__summary strong {
  color: #4f46e5;
}

.ability-card .radar-preview {
  position: relative;
  width: 100%;
  max-width: 240px;
  margin: 0 auto;
  aspect-ratio: 1;
  flex: 1;
}

.radar-chart {
  width: 100%;
  height: 100%;
}

.radar-grid {
  fill: none;
  stroke: #E5E7EB;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(99, 102, 241, 0.2);
  stroke: #4f46e5;
  stroke-width: 2;
}

.radar-dot {
  fill: #4f46e5;
}

.radar-labels {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.radar-label {
  position: absolute;
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
}

.achievement-card {
  min-height: 300px;
  background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #DDD6FE;
}

.achievement-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.achievement-card__title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.streak-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid #F59E0B;
}

.streak-badge__fire {
  font-size: 14px;
}

.streak-badge__text {
  font-size: 11px;
  font-weight: 600;
  color: #B45309;
}

.badges-row {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.badges-row::-webkit-scrollbar {
  display: none;
}

.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 52px;
  padding: 8px 6px;
  background: white;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  transition: all 0.2s ease;
}

.badge-item__icon {
  font-size: 20px;
}

.badge-item__name {
  font-size: 9px;
  color: #6B7280;
  white-space: nowrap;
}

.badge-item.locked {
  opacity: 0.4;
  filter: grayscale(1);
}

.badge-item:not(.locked):hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  border-color: #4F46E5;
}

.recent-activity {
  margin-top: 12px;
}

.recent-activity__title {
  font-size: 12px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  padding: 6px 10px;
}

.activity-item__icon {
  margin-right: 8px;
}

.activity-item__text {
  flex: 1;
  color: #374151;
  font-size: 13px;
}

.activity-item__time {
  color: #9CA3AF;
  font-size: 12px;
}

.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.user-card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-avatar-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.user-avatar-section .avatar-lg {
  width: 70px;
  height: 70px;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
}

.user-info-list {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}

.user-info-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.user-info-row:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.user-info-key {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.user-info-value {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  word-break: break-word;
}

.user-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.user-avatar-wrap {
  position: relative;
  width: 100px;
  height: 100px;
  border: 3px solid #6366f1;
  border-radius: 50%;
  padding: 3px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
  overflow: hidden;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-avatar-wrap:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.15);
}

.user-avatar-wrap .avatar-lg {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.user-avatar-wrap .avatar-lg img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  text-align: center;
}

.user-level {
  background: linear-gradient(90deg, #ffab00, #ffcc54);
  color: #fff;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 700;
}

.user-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: #444;
}

.user-meta-row--id {
  padding: 8px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fff7e6;
}

.copy-btn {
  border: 1px solid #ffcc54;
  background: #fff;
  color: #ff8c00;
  border-radius: 100px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.ability-list .ability-item,
.data-grid .data-item,
.badges-row .badge-item,
.growth-content .growth-item {
  margin-bottom: 10px;
}

.ability-row {
  display: flex;
  justify-content: space-between;
  font-weight: 500;
  margin-bottom: 6px;
}

.ability-bar {
  height: 8px;
  border-radius: 6px;
  background: #f0f0f0;
  overflow: hidden;
}

.ability-fill {
  height: 100%;
  background: linear-gradient(90deg, #5e9dff, #3d6eff);
}

.badges-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.badge-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.badge-icon {
  font-size: 18px;
}

.badge-name {
  font-weight: bold;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.data-item {
  background: #f8f9fc;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.growth-content {
  display: grid;
  gap: 8px;
}

.growth-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #2b2b2b;
}

// 编辑按钮样式调整
.edit-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #fff;
  border: none;
  border-radius: 16px;
  padding: 6px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
  margin-left: 8px;
}
.edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  opacity: 0.95;
}

// 编辑弹窗图片卡片风格
.edit-modal-sheet {
  min-width: 320px;
  max-width: 400px;
  padding: 0 0 16px 0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 6px 32px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}
.edit-modal-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 24px 14px 24px;
}
.edit-modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 6px;
}
.edit-modal-title .edit-modal-title-icon {
  font-size: 18px;
}
.edit-modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #6b7280;
}
.edit-modal-body {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px 0 24px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-label {
  min-width: 80px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}

.form-control {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s ease;
  background: #fff;
}

.form-control:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.form-select {
  cursor: pointer;
}
.edit-modal-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding: 0 24px;
}

/* compact form styling inside edit modal */
.edit-modal-sheet {
  min-width: 320px;
  max-width: 420px;
  padding: 0 0 14px 0;
}
.edit-modal-header {
  padding: 16px 24px 12px 24px;
}
.edit-modal-title {
  font-size: 16px;
}
.edit-modal-body {
  padding: 20px 24px 0 24px;
  gap: 10px;
}
.edit-modal-body .form-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.edit-modal-body .form-group label {
  display: flex;
  align-items: center;
  white-space: nowrap;
  font-size: 13px;
  letter-spacing: 0.03em;
  margin: 0;
  min-width: 64px;
}
.edit-modal-body .form-group .field-icon {
  display: inline-block;
  width: 18px;
  text-align: center;
  margin-right: 4px;
  font-size: 16px;
}
.edit-modal-body .form-group input,
.edit-modal-body .form-group select {
  flex: 1;
  padding: 6px 8px;
  font-size: 14px;
}

// 新版个人信息卡片 - 左右布局
.profile-info-card {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr);
  background: white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  overflow: hidden;
}

.profile-info-col {
  padding: $spacing-md $spacing-lg;
  min-width: 0;
}

.profile-info-col + .profile-info-col {
  border-left: 1px dashed $border-color;
}

.profile-info-col--avatar {
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
}

.avatar-wrapper-lg {
  position: relative;
  cursor: pointer;
}

.avatar-lg {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 3px solid rgba(102, 126, 234, 0.3);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 100%; height: 100%; object-fit: cover; }

  &__fallback {
    font-size: 28px;
    font-weight: $font-weight-bold;
    color: white;
    font-family: $font-family-display;
  }
}

.default-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 6px;
  font-size: 10px;
  color: #fff;
  background: #3b82f6;
  border-radius: 3px;
}

.avatar-edit-badge-lg {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow;
  color: $primary;
  svg { width: 11px; height: 11px; }
}

.avatar-label {
  font-size: 15px;
  color: $text-primary;
  font-weight: $font-weight-semibold;
  margin-top: $spacing-sm;
}

.info-group {
  min-width: 0;
}

.info-group-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid $gray-100;
}

.info-group-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.info-group-title {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  color: $text-primary;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.info-item {
  display: grid;
  grid-template-columns: 18px 70px 1fr;
  align-items: center;
  gap: $spacing-sm;
}

.info-item__icon {
  font-size: 18px;
  flex-shrink: 0;
}

.info-item__label {
  font-size: $font-size-xs;
  color: $text-muted;
  min-width: 70px;
}

.info-item__value {
  font-size: 14px;
  color: $text-primary;
  font-weight: $font-weight-medium;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.job-select-wrap {
  display: flex;
  justify-content: flex-start;
  margin-top: $spacing-md;
}

.job-select-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: $primary;
  border: none;
  color: white;
  font-size: $font-size-sm;
  cursor: pointer;
  font-family: $font-family-base;
  padding: $spacing-sm $spacing-md;
  border-radius: $border-radius;
  box-shadow: $shadow-sm;
  transition: opacity $transition-fast;
  &:hover { opacity: 0.9; }
}

// 响应式适配
@media (max-width: 768px) {
  .profile-info-card {
    grid-template-columns: 1fr;
  }

  .profile-info-col + .profile-info-col {
    border-left: none;
    border-top: 1px dashed $border-color;
  }
}

// 信息卡片
.info-card {
  background: white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
}

.info-row {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  border-bottom: 1px solid $gray-100;

  &:last-child { border-bottom: none; }

  &__icon { font-size: 18px; flex-shrink: 0; }
  &__content { flex: 1; display: flex; flex-direction: column; gap: 2px; }
  &__label { font-size: $font-size-xs; color: $text-muted; text-transform: uppercase; letter-spacing: 0.05em; }
  &__value { font-size: $font-size-base; color: $text-primary; font-weight: $font-weight-medium; }
  &__value.muted { color: $text-muted; font-weight: $font-weight-regular; }
}

// 岗位偏好
.job-preference-card {
  background: white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  overflow: hidden;
}

.job-selected {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;

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
  &__info { flex: 1; }
  &__name { font-weight: $font-weight-semibold; font-size: $font-size-base; color: $text-primary; }
  &__stack { font-size: $font-size-xs; color: $text-muted; margin-top: 2px; }
}

.job-change-btn {
  background: $primary-bg;
  border: none;
  border-radius: $border-radius-full;
  padding: 6px $spacing-md;
  color: $primary;
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  font-family: $font-family-base;
}

.job-set-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-base;
  background: none;
  border: none;
  cursor: pointer;
  font-size: $font-size-base;
  color: $text-secondary;
  font-family: $font-family-base;
  transition: background $transition-fast;
  &:hover { background: $gray-50; }
}

// 菜单卡片
.menu-card {
  background: white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
}

// 账号安全：双入口同一行（自适应，移动端不足时自动换行）
.menu-card--security {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: $spacing-md;
  padding: $spacing-md;
  overflow: visible;

  .menu-item {
    border: 1px solid $border-color;
    border-radius: $border-radius-lg;
    background: white;
    border-bottom: none;
    padding: $spacing-md;

    &:last-child { border-bottom: none; }
    &:hover { background: $gray-50; }
    &:active { background: $gray-100; }

    .menu-item__arrow { color: $gray-400; }
  }
}

// 其它板块卡片样式（与账号安全一致）
.menu-card--other {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: $spacing-md;
  padding: $spacing-md;
  overflow: visible;

  .menu-item {
    border: 1px solid $border-color;
    border-radius: $border-radius-lg;
    background: white;
    border-bottom: none;
    padding: $spacing-md;

    &:last-child { border-bottom: none; }
    &:hover { background: $gray-50; }
    &:active { background: $gray-100; }

    .menu-item__arrow { color: $gray-400; }
  }
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  background: none;
  border: none;
  border-bottom: 1px solid $gray-100;
  cursor: pointer;
  text-align: left;
  font-family: $font-family-base;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: $gray-50; }
  &:active { background: $gray-100; }

  &__icon {
    width: 36px;
    height: 36px;
    border-radius: $border-radius-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__content { flex: 1; }
  &__label { font-size: $font-size-base; font-weight: $font-weight-medium; color: $text-primary; }
  &__sub { font-size: $font-size-xs; color: $text-muted; margin-top: 1px; display: block; }

  &__arrow { width: 16px; height: 16px; color: $gray-300; flex-shrink: 0; }
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  padding: 15px;
  background: white;
  border: 1.5px solid $danger;
  border-radius: $border-radius-lg;
  color: $danger;
  font-size: $font-size-md;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  font-family: $font-family-base;
  transition: all $transition-base;
  &:hover { background: $danger-bg; }
  &:active { transform: scale(0.98); }
}

// 弹窗
.modal-overlay {
  position: fixed;
  inset: 0;
  background: $bg-overlay;
  z-index: 200;
  display: flex;
  align-items: flex-end; /* default bottom-aligned */
  justify-content: center;
}

// 居中弹窗（仅在需要时额外加类）
.modal-overlay--center {
  align-items: center;
  padding: $spacing-base;
}

// 居中弹窗（仅在需要时额外加类）
.modal-overlay--center {
  align-items: center;
  padding: $spacing-base;
}

.modal-sheet {
  width: 100%;
  max-width: $max-content-width;
  background: white;
  border-radius: $border-radius-xl;
  max-height: 80vh;
  overflow-y: auto;

  &--sm { max-height: 40vh; }
  &--tall { max-height: 85vh; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-lg $spacing-base $spacing-md;
  border-bottom: 1px solid $border-color;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;

  h3 { font-size: $font-size-lg; font-weight: $font-weight-bold; color: $text-primary; }
}

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: $gray-100;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  color: $text-muted;
  transition: all $transition-fast;
  &:hover { background: $gray-200; }
}

.modal-body {
  padding: $spacing-base;

  .form-group {
    margin-bottom: $spacing-base;
    label {
      display: block;
      font-size: 11px;
      font-weight: $font-weight-semibold;
      color: $text-secondary;
      margin-bottom: $spacing-sm;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
  }
}

.modal-footer {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-base $spacing-xl;
  border-top: 1px solid $border-color;

  .btn { flex: 1; height: 48px; display: flex; align-items: center; justify-content: center; gap: $spacing-sm; }
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
  padding-right: 36px;
}

.global-error {
  background: $danger-bg;
  border: 1px solid rgba(239,68,68,0.2);
  color: $danger;
  padding: $spacing-md;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  margin-bottom: $spacing-base;
}

.success-tip {
  background: $success-bg;
  color: darken($success, 10%);
  padding: $spacing-md;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  text-align: center;
}

// 修改密码弹窗（局部优化，不影响其他弹窗）
.password-sheet {
  overflow: hidden;

  .modal-header {
    align-items: flex-start;
  }

  // 居中弹窗更适合四角圆角
  border-radius: $border-radius-xl;
}

.password-header {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &__title {
    margin: 0;
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }

  &__sub {
    margin: 0;
    font-size: $font-size-sm;
    color: $text-muted;
    line-height: $line-height-normal;
  }
}

.password-card {
  background: $gradient-primary-soft;
  border: 1px solid $border-color;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  position: relative;
}

.form-hint {
  margin-top: 6px;
  font-size: $font-size-xs;
  color: $text-muted;
}

// 绑定手机弹窗（居中卡片）
.phone-sheet {
  overflow: hidden;
  border-radius: $border-radius-xl;

  .modal-header {
    align-items: flex-start;
  }
}

.phone-header {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &__title {
    margin: 0;
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }

  &__sub {
    margin: 0;
    font-size: $font-size-sm;
    color: $text-muted;
    line-height: $line-height-normal;
  }
}

.phone-card {
  background: $gradient-primary-soft;
  border: 1px solid $border-color;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  position: relative;
}

.success-float {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: $spacing-base $spacing-base $spacing-xl;
  z-index: 2;
  pointer-events: none;
}

.success-tip--float {
  width: 100%;
  max-width: 380px;
  margin: 0;
  box-shadow: $shadow-sm;
}

.phone-current {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md;
  margin-bottom: $spacing-base;
  border-radius: $border-radius-lg;
  border: 1px dashed rgba(148, 163, 184, 0.7);
  background: rgba(255,255,255,0.75);

  &__label {
    font-size: $font-size-xs;
    color: $text-muted;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  &__value {
    font-family: $font-family-mono;
    font-size: $font-size-base;
    font-weight: $font-weight-semibold;
    color: $text-primary;
  }
}

// 岗位选择列表
.job-picker-body { padding-top: 0; }

.job-picker-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  cursor: pointer;
  border-bottom: 1px solid $gray-100;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: $gray-50; }

  &.selected { background: $primary-bg; }

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
  &__info { flex: 1; }
  &__name { font-weight: $font-weight-semibold; font-size: $font-size-base; color: $text-primary; }
  &__stack { font-size: $font-size-xs; color: $text-muted; margin-top: 2px; }
  &__check { color: $primary; font-weight: $font-weight-bold; font-size: $font-size-lg; }
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  &--dark { border-color: rgba($danger, 0.3); border-top-color: $danger; }
}

@keyframes spin { to { transform: rotate(360deg); } }

// 弹窗动画
//.modal-enter-active { animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
//.modal-leave-active { animation: modalOut 0.2s ease both; }

//@keyframes modalIn {
  ///from { opacity: 0; .modal-sheet { transform: translateY(100%); } }
  //to { opacity: 1; .modal-sheet { transform: translateY(0); } }
//}

//@keyframes modalOut {
 // from { opacity: 1; }
  //to { opacity: 0; }
//}


// 1. 定义弹窗背景的进入/离开动画
@keyframes modalIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modalOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

// 2. 定义弹窗内容（sheet）的进入/离开动画
@keyframes sheetIn {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes sheetOut {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}

// 3. 分别给弹窗容器和sheet绑定动画
.modal-enter-active { 
  animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both; 
}
.modal-leave-active { 
  animation: modalOut 0.2s ease both; 
}

// sheet的动画（和弹窗同步执行）
.modal-enter-active .modal-sheet {
  animation: sheetIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.modal-leave-active .modal-sheet {
  animation: sheetOut 0.2s ease both;
}

.modal-overlay.version-modal {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.version-card {
  min-width: 220px;
  max-width: 320px;
  min-height: 80px;
  padding: 20px 18px 18px 18px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.version-card__text {
  font-size: 15px;
  color: #333;
  margin-bottom: 6px;
  text-align: center;
}
</style>