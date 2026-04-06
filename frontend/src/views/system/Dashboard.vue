<!--
  =============================================
  frontend/src/views/system/Dashboard.vue
  仪表盘首页组件
  ============================================= -->
<template>
  <div class="dashboard-page">

    <!-- 主内容区 -->
    <div class="dashboard-body page-container">

      <div class="homepage-hero-container">
        <div class="homepage-hero">
          <div class="homepage-hero__bg"></div>
          <transition name="hero-fade" mode="out-in">
            <div :key="heroTab" class="homepage-hero__content floating">
              <div class="hero-tabs">
                <button :class="{ active: heroTab === 'interview' }" @click="heroTab = 'interview'">AI 面试教练</button>
                <button :class="{ active: heroTab === 'learning' }" @click="heroTab = 'learning'">个性化学习</button>
              </div>
              <h1 class="hero-title">
                <template v-if="heroTab === 'interview'">
                  你的 <span class="hero-word-highlight">专属AI</span> 面试教练
                </template>
                <template v-else>
                  打造你的 <span class="hero-word-highlight">个性化</span> 学习资源
                </template>
              </h1>
              <p class="hero-desc">{{ heroDesc }}</p>
              <p v-if="heroTab === 'interview'" class="hero-current-job">当前岗位：{{ currentJobName }}</p>
              <button class="hero-action-btn" @click="startHeroAction">{{ heroActionText }}</button>
              <div class="learning-extra" :class="{ 'learning-extra--learning': heroTab === 'learning', 'learning-extra--interview': heroTab === 'interview' }">
                <div class="learning-extra__card" v-if="heroTab === 'learning'">
                  <h4>能力成长曲线</h4>
                  <p>实时展示你在不同维度的进步趋势，目标可视化。</p>
                </div>
                <div class="learning-extra__card" v-if="heroTab === 'learning'">
                  <h4>短板可视化</h4>
                  <p>一目了然识别弱项，智能补强，降低盲区。</p>
                </div>
                <div class="learning-extra__card" v-if="heroTab === 'learning'">
                  <h4>学习资源智能推荐</h4>
                  <p>基于你的弱项自动推荐课程、题库与训练路径。</p>
                </div>

                <div class="learning-extra__card" v-if="heroTab === 'interview'">
                  <h4>模拟真实场景</h4>
                  <p>高度还原面试现场，压力和过程同步训练。</p>
                </div>
                <div class="learning-extra__card" v-if="heroTab === 'interview'">
                  <h4>智能报告生成</h4>
                  <p>自动分析表现，生成重点改进建议与复盘报告。</p>
                </div>
                <div class="learning-extra__card" v-if="heroTab === 'interview'">
                  <h4>全面综合考察</h4>
                  <p>覆盖技能、逻辑、表达与抗压全方位评估。</p>
                </div>
              </div>
            </div>
          </transition>
        </div>

        <section class="homepage-stats">
        <div class="stat-card">
          <div class="stat-number">{{ formatNumber(platformStats.users) }}</div>
          <div class="stat-label">使用用户数目</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ formatNumber(platformStats.interviews) }}</div>
          <div class="stat-label">平台面试次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ formatNumber(platformStats.jobs) }}</div>
          <div class="stat-label">针对性岗位数目</div>
        </div>
      </section>
    </div>



      <!-- 未登录时显示平台特色 -->
      <section class="section feature-section" v-if="!isLoggedIn">
        <h2 class="feature-section__title">✨ 为什么选择 AI面试助手？</h2>
        <div class="feature-grid">
          <div class="feature-box">
            <div class="feature-box__icon">🤖</div>
            <h3 class="feature-box__title">AI智能面试官</h3>
            <p class="feature-box__desc">基于大语言模型，真实模拟面试场景，智能追问深入考察</p>
          </div>
          <div class="feature-box">
            <div class="feature-box__icon">📊</div>
            <h3 class="feature-box__title">多维能力评估</h3>
            <p class="feature-box__desc">从专业知识、逻辑思维、表达能力等多个维度全面分析</p>
          </div>
          <div class="feature-box">
            <div class="feature-box__icon">📈</div>
            <h3 class="feature-box__title">个性化学习路径</h3>
            <p class="feature-box__desc">AI分析薄弱点，智能推荐学习内容，高效提升</p>
          </div>
          <div class="feature-box">
            <div class="feature-box__icon">🎯</div>
            <h3 class="feature-box__title">精准题库覆盖</h3>
            <p class="feature-box__desc">覆盖Java、前端、Python等热门方向，紧跟面试趋势</p>
          </div>
        </div>
      </section>

      <!-- 每日提示 -->
      <section class="section">
        <div class="daily-tip-card">
          <div class="daily-tip-card__header">
            <span>💡</span>
            <span>今日面试小贴士</span>
          </div>
          <p class="daily-tip-card__content">{{ dailyTip }}</p>
        </div>
      </section>

    </div>

    <!-- 使用帮助指南（首次登录自动弹出一次） -->
    <HelpGuideModal v-model="showHelpGuide" @dismiss="markHelpGuideShown" />
    <!-- 岗位确认弹窗 -->
    <transition name="modal-fade">
      <div class="modal-overlay" v-if="showConfirmModal" @click.self="closeConfirmModal">
        <div class="modal-sheet">

          <!-- 顶部渐变头 -->
          <div class="modal-header-bar">
            <h2 class="modal-header-title">准备好了吗？</h2>
            <p class="modal-header-sub">热门岗位 · {{ selectedJob?.name }} · {{ voiceMode ? '语音面试' : '文字面试' }}</p>
          </div>

          <div class="modal-body">
            <!-- 面试模式标签 -->
            <div class="interview-mode-tag" :class="voiceMode ? 'mode-voice' : 'mode-text'">
              <svg v-if="voiceMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              {{ voiceMode ? '语音模式 · 每题 3 分钟' : '文字模式 · 每题 5 分钟' }}
            </div>

            <!-- 语音/文字切换 -->
            <div class="mode-switch-row">
              <button
                :class="['mode-switch-btn', { active: !voiceMode }]"
                @click="voiceMode = false"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                文字面试
              </button>
              <button
                :class="['mode-switch-btn', { active: voiceMode }]"
                @click="voiceMode = true"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
                语音面试
              </button>
            </div>

            <!-- 注意事项 -->
            <ul class="rules-list">
              <li>
                <span class="rule-dot rule-dot--blue" />
                AI 将逐题提问，请认真作答，回答后 AI 可能追问
              </li>
              <li>
                <span class="rule-dot rule-dot--purple" />
                每题均有时间限制，超时将自动跳题
              </li>
              <li v-if="voiceMode">
                <span class="rule-dot rule-dot--green" />
                语音模式下 AI 回答完毕后将自动开始录音
              </li>
              <li v-else>
                <span class="rule-dot rule-dot--green" />
                使用 Enter 发送回答，Shift+Enter 换行
              </li>
              <li>
                <span class="rule-dot rule-dot--orange" />
                面试结束后将生成专属评估报告，可在历史记录中查看
              </li>
            </ul>

            <div class="modal-actions">
              <button class="btn-cancel" @click="closeConfirmModal">再想想</button>
              <button class="btn-confirm" @click="confirmStartInterview">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                开始面试
              </button>
            </div>
          </div>

        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { getDashboardStats } from '@/api/user'
import { fetchJobs, fetchPopularJobs, fetchJobAvgScores } from '@/api/job'
import { getAdminDashboardStats } from '@/api/admin'
import { JOB_TYPES } from '@/utils/constants'
import HelpGuideModal from '@/components/common/HelpGuideModal.vue'

export default {
  name: 'DashboardPage',
  components: {
    HelpGuideModal
  },
  data() {
    return {
      jobs: [],
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
        // 能力维度分数 - 从后端获取真实数据
        abilities: {
          knowledge: 0,
          logic: 0,
          expression: 0,
          problemSolving: 0,
          coding: 0,
          learning: 0
        }

      },
      platformStats: {
        users: 0,
        interviews: 0,
        jobs: 0
      },
      platformFeatures: [
  { icon: '🤖', title: 'AI智能面试官', desc: '基于大语言模型，真实模拟面试场景' },
  { icon: '📊', title: '多维能力评估', desc: '从专业知识、逻辑、表达等多维度分析' },
  { icon: '📈', title: '个性化学习路径', desc: 'AI分析薄弱点，智能推荐学习内容' },
  { icon: '🎯', title: '精准题库覆盖', desc: '覆盖Java、前端、Python等热门方向' },
],
      heroTab: 'interview',
      dailyTips: [
        '回答时采用 STAR 法则（情境-任务-行动-结果），让回答更有结构和说服力。',
        '面试前10分钟快速回顾项目亮点，准备2-3个"失败经历+如何改进"的故事。',
        '技术问题不会时，不要沉默，大声思考推理过程同样体现能力。',
        '多使用数字和具体案例，比如"优化后性能提升了40%"比"优化了很多"更有说服力。',
        '复杂问题先说结论，再展开细节，让面试官第一时间抓住重点。'
      ],
      // 成就徽章 - 根据真实数据动态计算
      badges:[
        { id: 1, icon: '🌟', name: '初次面试', condition: 'firstInterview' },
        { id: 2, icon: '🔥', name: '连续3天', condition: 'streak3' },
        { id: 3, icon: '💪', name: '突破80分', condition: 'score80' },
        { id: 4, icon: '🏅', name: '面试达人', condition: 'interviews10' },
        { id: 5, icon: '👑', name: '全能王者', condition: 'score90' }
      ],
      // 弹窗状态
      showConfirmModal: false,
      selectedJob: null,
      voiceMode: false, 
      // 使用帮助指南（首次登录自动弹出一次）
      showHelpGuide: false,
      helpGuideStorageKey: ''
    }
  },
  computed: {
    heroDate() {
  const d = new Date()
  const days = ['周日','周一','周二','周三','周四','周五','周六']
  return `${d.getMonth()+1}月${d.getDate()}日 ${days[d.getDay()]}`
},
    ...mapGetters('user', ['userInfo', 'userName', 'defaultJob', 'defaultJobName', 'isLoggedIn']),

    currentJobName() {
      // 从数据库返回的用户默认岗位优先显示
      const dbJobName = this.userInfo?.defaultJobName || this.userInfo?.default_job_name || this.userInfo?.default_job || this.userInfo?.job_name
      if (dbJobName) return dbJobName

      // 然后使用 Vuex 里升级后的 defaultJobName
      if (this.defaultJobName) return this.defaultJobName

      // 其次尝试 jobs 列表 id -> name 匹配
      if (this.defaultJob && this.jobs && this.jobs.length > 0) {
        const job = this.jobs.find(j => String(j.id) === String(this.defaultJob) || (j.name && j.name === this.defaultJob))
        if (job) return job.name
      }
      return "未设置"
    },

    heroTitle() {
      if (this.heroTab === 'learning') {
        return '打造你的个性化学习资源'
      }
      return '你的专属AI面试教练'
    },

    heroDesc() {
      if (this.heroTab === 'learning') {
        return '展示多维度能力曲线，针对薄弱点进行学习与练习，持续提升面试表现'
      }
      return '面试过程中实时提供专业建议，帮助构建清晰有逻辑的回答框架，面试成功率提升3倍'
    },

    heroActionText() {
      return this.heroTab === 'learning' ? '开始学习' : '开始面试'
    },

    timeGreeting() {
      const hour = new Date().getHours()
      if (hour < 6) return '夜深了，注意休息'
      if (hour < 12) return '早上好'
      if (hour < 14) return '中午好'
      if (hour < 18) return '下午好'
      return '晚上好'
    },

    avatarLetter() {
      if (!this.isLoggedIn) return '客'
      const name = this.userName || '用'
      return name.charAt(0)
    },

    resolvedAvatarSrc() {
      const raw = this.userInfo && this.userInfo.avatar
      if (!raw) return ''
      const asString = String(raw)
      const stamp = Date.now()

      const withStamp = (url) => url.includes('?') ? `${url}&t=${stamp}` : `${url}?t=${stamp}`
      if (/^https?:\/\//i.test(asString)) return withStamp(asString)

      const origin = (process.env.VUE_APP_BACKEND_ORIGIN || '').replace(/\/$/, '')
      if (origin) {
        return withStamp(`${origin}${asString.startsWith('/') ? '' : '/'}${asString}`)
      }
      return withStamp(asString)
    },

    defaultJobName() {
      if (!this.defaultJob) return ''
      const job = this.jobs.find(j => String(j.id) === String(this.defaultJob))
      return job ? job.name : ''
    },

    topHotJobs() {
      return this.jobs.slice(0, 3)
    },

    scoreCircumference() {
      return 2 * Math.PI * 24
    },

    scoreOffset() {
      const score = this.stats.lastInterviewScore || 0
      const pct = score / 100
      return this.scoreCircumference * (1 - pct)
    },

    dailyTip() {
      const idx = new Date().getDate() % this.dailyTips.length
      return this.dailyTips[idx]
    },

    // 连续学习天数
    streakDays() {
      return this.stats.streakDays || this.stats.weeklyPractice || 0
    },

    // 雷达图数据点
    radarPoints() {
      const a = this.stats.abilities || { knowledge: 0, logic: 0, expression: 0, problemSolving: 0, coding: 0, learning: 0 }
      const center = 100
      const maxRadius = 80
      // 六边形顶点角度（从顶部开始，顺时针）
      const angles = [-90, -30, 30, 90, 150, 210].map(d => d * Math.PI / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]
      
      // 如果所有值都为0，显示一个小的默认形状（10%）
      const hasData = values.some(v => v > 0)
      const defaultValue = hasData ? 0 : 10
      
      return values.map((v, i) => {
        const actualValue = v > 0 ? v : defaultValue
        const r = (actualValue / 100) * maxRadius
        const x = center + r * Math.cos(angles[i])
        const y = center + r * Math.sin(angles[i])
        return `${x},${y}`
      }).join(' ')
    },

    // 雷达图上的点
    radarDots() {
      const a = this.stats.abilities || { knowledge: 0, logic: 0, expression: 0, problemSolving: 0, coding: 0, learning: 0 }
      const center = 100
      const maxRadius = 80
      const angles = [-90, -30, 30, 90, 150, 210].map(d => d * Math.PI / 180)
      const values = [a.knowledge, a.logic, a.expression, a.problemSolving, a.coding, a.learning]
      
      // 如果所有值都为0，显示一个小的默认形状
      const hasData = values.some(v => v > 0)
      const defaultValue = hasData ? 0 : 10
      
      return values.map((v, i) => {
        const actualValue = v > 0 ? v : defaultValue
        const r = (actualValue / 100) * maxRadius
        return {
          x: center + r * Math.cos(angles[i]),
          y: center + r * Math.sin(angles[i])
        }
      })
    },

    // 是否有能力数据
    hasAbilityData() {
      const a = this.stats.abilities
      if (!a) return false
      return Object.values(a).some(v => v > 0)
    },

    // 能力评语
    abilityComment() {
      if (!this.hasAbilityData) return '完成面试后解锁能力分析'
      const avg = this.stats.avgScore || 0
      if (avg >= 85) return '表现优秀，继续保持！'
      if (avg >= 70) return '整体良好，部分能力可加强'
      if (avg >= 60) return '有提升空间，建议多练习'
      return '建议从基础开始系统学习'
    },

    // 显示的徽章（根据真实数据计算解锁状态）
    displayBadges() {
      return this.badges.map(badge => {
        let unlocked = false
        switch (badge.condition) {
          case 'firstInterview':
            unlocked = this.stats.totalInterviews >= 1
            break
          case 'streak3':
            unlocked = this.stats.streakDays >= 3
            break
          case 'score80':
            unlocked = this.stats.maxScore >= 80 || this.stats.avgScore >= 80
            break
          case 'interviews10':
            unlocked = this.stats.totalInterviews >= 10
            break
          case 'score90':
            unlocked = this.stats.maxScore >= 90 || this.stats.avgScore >= 90
            break
        }
        return { ...badge, unlocked }
      })
    },

    // 最近活动
    recentActivities() {
      const activities = []
      if (this.stats.lastInterviewAt) {
        activities.push({
          icon: '🎯',
          text: `完成了 ${this.stats.lastInterviewJob || '面试'} 面试`,
          time: this.formatDate(this.stats.lastInterviewAt)
        })
      }
      if (this.stats.totalInterviews > 0) {
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
      // 如果没有活动，显示提示
      if (activities.length === 0) {
        activities.push({
          icon: '💡',
          text: '开始你的第一次面试练习吧',
          time: '待解锁'
        })
      }
      return activities.slice(0, 3)
    },

  },
  watch: {
    isLoggedIn: {
      immediate: true,
      handler(val) {
        if (val) this.maybeAutoShowHelpGuide()
      }
    }
  },
  async created() {
    if (this.isLoggedIn) {
      await this.fetchUserInfo()
    }
    this.loadJobs()
    this.loadPlatformStats()
    this.loadStats()
    this.maybeAutoShowHelpGuide()
  },
  methods: {
    ...mapActions('user', ['fetchUserInfo']),
    ...mapActions('interview', ['selectJob']),

    getHelpGuideUserKey() {
      const u = this.userInfo || {}
      return u.id ?? u.user_id ?? u.userId ?? u.uid ?? u.email ?? null
    },
    async loadJobs() {
  try {
    // 优先用热门岗位填充快捷标签，失败则回退到全量列表前3个
    const popular = await fetchPopularJobs()
    if (popular && popular.length > 0) {
      this.jobs = popular.map(j => ({
        ...j,
        icon: j.icon_url || '💼',
        techStack: j.tech_stack || [],
        color: j.color || '#888',
        colorBg: j.color_bg || 'rgba(139, 92, 246, 0.1)',
        colorHoverBg: j.color_hover_bg || 'rgba(139, 92, 246, 0.2)',
      }))
    } else {
      const all = await fetchJobs()
      this.jobs = (all || []).slice(0, 3).map(j => ({
        ...j,
        icon: j.icon_url || '💼',
        techStack: j.tech_stack || [],
        color: j.color || '#888',
        colorBg: j.color_bg || 'rgba(139, 92, 246, 0.1)',
        colorHoverBg: j.color_hover_bg || 'rgba(139, 92, 246, 0.2)',
      }))
    }
  } catch (e) {
    console.warn('加载岗位失败', e)
    this.jobs = []
  }
},

    computeHelpGuideStorageKey() {
      const userKey = this.getHelpGuideUserKey()
      if (!userKey) return ''
      return `ai-interview-platform:helpGuideShown:${userKey}`
    },

    maybeAutoShowHelpGuide() {
      if (!this.isLoggedIn) return

      const storageKey = this.computeHelpGuideStorageKey()
      if (!storageKey) return
      this.helpGuideStorageKey = storageKey

      try {
        const shown = window.localStorage.getItem(storageKey)
        if (shown === '1') return
      } catch (e) {
        // localStorage 不可用时不阻断功能；仍允许弹出
      }

      this.showHelpGuide = true
    },

    markHelpGuideShown() {
      const storageKey = this.helpGuideStorageKey || this.computeHelpGuideStorageKey()
      if (!storageKey) return
      try {
        window.localStorage.setItem(storageKey, '1')
      } catch (e) {
        // ignore
      }
    },

    async loadPlatformStats() {
      try {
        const data = await getAdminDashboardStats()
        this.platformStats = {
          users: data.total_users ?? 0,
          interviews: data.total_interviews ?? 0,
          jobs: data.total_jobs ?? 0
        }
      } catch (e) {
        console.warn('加载管理员平台统计数据失败，回退到可访问的岗位汇总统计', e)
        try {
          const jobStats = await fetchJobAvgScores()
          const interviews = jobStats.reduce((sum, job) => sum + (job.interview_count || 0), 0)
          const users = Math.max(0, ...jobStats.map(job => job.user_count || 0))
          const jobs = jobStats.length
          this.platformStats = {
            users,
            interviews,
            jobs
          }
        } catch (innerErr) {
          console.warn('加载岗位统计数据失败，首页统计继续显示为0', innerErr)
          this.platformStats = {
            users: 0,
            interviews: 0,
            jobs: 0
          }
        }
      }
    },

    async loadStats() {
      // 未登录时不加载数据
      if (!this.isLoggedIn) return
      try {
        const data = await getDashboardStats()
        // 合并后端返回的数据，包括 abilities
        this.stats = {
          ...this.stats,
          ...data,
          // 确保 abilities 正确合并
          abilities: {
            ...this.stats.abilities,
            ...(data.abilities || {})
          }
        }
      } catch (e) {
        console.warn('加载统计数据失败', e)
      }
    },

    formatNumber(value) {
      if (value === null || value === undefined) return '0'
      return Number(value).toLocaleString()
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    startHeroAction() {
      if (this.heroTab === 'learning') {
        this.$router.push('/learning')
      } else {
        this.$router.push('/interview/select')
      }
    },

    // 显示岗位确认弹窗
    showJobConfirm(job) {
      this.selectedJob = job
      this.showConfirmModal = true
    },

    // 关闭弹窗
    closeConfirmModal() {
      this.showConfirmModal = false
      this.selectedJob = null
    },

    // 确认开始面试
    async confirmStartInterview() {
      if (!this.selectedJob) return
      
      const job = this.selectedJob  // 先保存引用
      this.closeConfirmModal()       // 关闭弹窗（会把 selectedJob 置 null）
      
      await this.$store.dispatch('interview/resetInterview')
      this.$store.commit('interview/SET_JOB_DB_ID', job.id)  // 用保存的引用
      this.$store.commit('interview/SET_VOICE_MODE', this.voiceMode)
      await this.$store.dispatch('interview/selectJob', job)
      this.$router.push('/interview/session')
    },

    selectJobAndStart(job) {
      this.selectJob(job)
      this.$router.push('/interview/select')
    },

    // 跳转题目详情页
    goToQuestionDetail(item) {
      const data = encodeURIComponent(JSON.stringify(item))
      const type = item.isTrending ? 'trending' : 'classic'
      this.$router.push({ path: '/question/detail', query: { data, type } })
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: #f8f8fb;
  padding-bottom: $bottom-nav-height;
  position: relative;
  overflow: hidden;
}

.dashboard-page::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url('@/assets/backgroundA.jpg') center/cover no-repeat;
  opacity: 0.12;
  filter: blur(4px);
  pointer-events: none;
  z-index: 0;
}

.homepage-hero-container {
  position: relative;
  background: url('@/assets/backgroundA.jpg') center/cover no-repeat;
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 18px;
  box-shadow: 0 10px 26px rgba(76, 66, 143, 0.14);
  overflow: hidden;
}

.homepage-hero-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(250, 250, 255, 0.62);
  backdrop-filter: blur(5px);
  z-index: 1;
}

.homepage-hero,
.homepage-stats,
.page-container {
  position: relative;
  z-index: 1;
}

.homepage-hero {
  position: relative;
  background: transparent;
  border-radius: 18px;
  min-height: 420px;
  margin-bottom: 18px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.homepage-hero__bg {
  display: none;
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(232, 221, 255, 0.3), rgba(218, 240, 232, 0.24)), url('@/assets/backgroundA.jpg') center/cover no-repeat;
  opacity: 0.18;
  z-index: 1;
}

.homepage-hero__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
  max-width: 760px;
}

.homepage-hero__content.floating {
  background: transparent;
  border-radius: 0;
  padding: 0;
  backdrop-filter: none;
  box-shadow: none;
}


.hero-tabs {
  display: inline-flex;
  gap: 8px;
  background: rgba(226, 214, 255, 0.5);
  border-radius: 999px;
  padding: 4px;
}

.hero-tabs button {
  border: none;
  outline: none;
  background: transparent;
  color: #6940f7;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 999px;
  cursor: pointer;
}

.hero-tabs button.active {
  color: #fff;
  background: #6a59f8;
}

.hero-title {
  font-family: 'Microsoft YaHei', PingFangSC, sans-serif;
  font-size: 44px;
  font-weight: 900;
  color: #2a2553;
  margin: 0;
  letter-spacing: -0.02em;
}

.hero-desc {
  font-size: 16px;
  line-height: 1.5;
  color: #4b4a60;
  max-width: 720px;
}

.hero-current-job {
  font-size: 14px;
  font-weight: 700;
  color: #6a59f8;
  background: rgba(226, 214, 255, 0.5);
  border-radius: 999px;
  padding: 8px 14px;
  margin: 0;
}

.hero-word-highlight {
  color: #7c56ff;
}

.learning-extra {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.learning-extra__card {
  min-width: 160px;
  max-width: 220px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #e9e5ff;
  border-radius: 14px;
  box-shadow: 0 6px 14px rgba(77, 64, 170, 0.12);
  padding: 12px 14px;
  text-align: left;
}

.learning-extra__card h4 {
  margin: 0 0 6px 0;
  color: #5a3ee4;
}

.learning-extra__card p {
  margin: 0;
  color: #524d6e;
  font-size: 13px;
}

.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: all 0.35s ease;
}
.hero-fade-enter-from,
.hero-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.hero-fade-enter-to,
.hero-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.hero-action-btn {
  width: 160px;
  height: 45px;
  font-size: 15px;
  font-weight: 700;
  border-radius: 999px;
  border: none;
  color: #fff;
  background: linear-gradient(90deg, #7365f0 0%, #543ed4 100%);
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(94, 64, 170, 0.25);
}

.homepage-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e9e5ff;
  padding: 14px;
  box-shadow: 0 6px 18px rgba(80, 54, 158, 0.1);
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: 800;
  color: #4233a2;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 13px;
  color: #68628e;
}

@media (max-width: 1024px) {
  .hero-title {
    font-size: 34px;
  }

  .homepage-stats {
    grid-template-columns: 1fr;
  }
}


// =============================================
// Hero 标题+数据合并区
// =============================================


.greeting {
  &__time {
    font-size: $font-size-sm;
    color: rgba(255,255,255,0.65);
    margin-bottom: 4px;
  }
  &__name {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    color: white;
    letter-spacing: -0.01em;
  }
  &__hint {
    font-size: $font-size-sm;
    color: rgba(255,255,255,0.7);
    margin-top: 4px;
  }
}

// 主体
.dashboard-body {
  padding: 0;
  animation: fadeSlideUp 0.4s ease both;
}


// =============================================
// Hero 左右布局
// =============================================
.hero-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;

  @media (max-width: 767px) {
    grid-template-columns: 1fr;
  }
}

// 左：问候卡片
.hero-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);

  &__greet {
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.hero-greet {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.hero-date {
  font-size: 13px;
  color: #9ca3af;
}

.hero-stats {
  display: flex;
  align-items: center;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px;
  gap: 4px;

  // 第一个不要左边距
  &:first-child { padding-left: 0; }

  &__val {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    line-height: 1;
    font-family: $font-family-display;

    &--accent { color: #6366f1; }
  }

  &__lbl {
    font-size: 11px;
    color: #9ca3af;
    white-space: nowrap;
  }

  &__sep {
    width: 1px;
    height: 28px;
    background: #e5e7eb;
    flex-shrink: 0;
  }
}

// 右：开始面试卡片
.start-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);

  &__header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
    margin: 0 0 4px;
  }

  &__desc {
    font-size: 13px;
    color: #6b7280;
    margin: 0;
  }

  &__jobs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.job-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  font-family: $font-family-base;
  transition: all 0.15s;

  &:hover {
    border-color: #6366f1;
    color: #6366f1;
    background: #eef2ff;
  }

  &--more {
    border-style: dashed;
    color: #6b7280;
    &:hover { border-color: #6366f1; color: #6366f1; background: #eef2ff; }
  }
}

.start-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: $font-family-base;
  transition: all 0.2s;
  align-self: flex-start; // 不要撑满宽度

  &:hover {
    background: #4f46e5;
    transform: translateY(-1px);
  }
}



// Section
.section {
  margin-bottom: $spacing-xl;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}




// 双栏布局
.two-column-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-md;
  margin-bottom: $spacing-xl;
}

// 能力雷达图卡片
.ability-card {
  background: white;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  box-shadow: $shadow;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-sm;
  }

  &__title {
    font-size: $font-size-sm;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }

  &__more {
    font-size: $font-size-xs;
    color: $primary;
    background: none;
    border: none;
    cursor: pointer;
    font-weight: $font-weight-medium;
  }

  &__summary {
    font-size: $font-size-xs;
    color: $text-secondary;
    text-align: center;
    margin-top: $spacing-sm;

    strong {
      color: $primary;
      font-weight: $font-weight-bold;
    }
  }
}

.radar-preview {
  position: relative;
  width: 100%;
  max-width: 180px;
  margin: 0 auto;
  aspect-ratio: 1;
}

// 未登录 - 平台特色区域
.feature-section {
  margin-bottom: $spacing-xl;

  &__title {
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    color: $text-primary;
    text-align: center;
    margin-bottom: $spacing-lg;
  }
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
}

.feature-box {
  background: white;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  text-align: center;
  box-shadow: $shadow;
  border: 1px solid $border-color;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
    border-color: $primary;
  }

  &__icon {
    font-size: 36px;
    margin-bottom: $spacing-sm;
  }

  &__title {
    font-size: $font-size-sm;
    font-weight: $font-weight-bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  &__desc {
    font-size: $font-size-xs;
    color: $text-secondary;
    line-height: 1.5;
  }
}

// 热门面试题
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  color: $text-primary;
}


.question-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.question-card {
  background: white;
  border-radius: $border-radius;
  padding: $spacing-md;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: $shadow;
    border-color: $primary;
    transform: translateX(4px);
  }

  &__top {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: $spacing-xs;
  }

  &__tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: $font-weight-semibold;
  }

  &__source {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 3px;
    background: #f1f5f9;
    color: #64748b;
    font-weight: 500;
  }

  &__text {
    font-size: $font-size-sm;
    color: $text-primary;
    line-height: 1.5;
    margin-bottom: $spacing-xs;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: $font-size-xs;
    color: $text-muted;
  }

  &__readable {
    color: #6366f1;
    font-weight: 500;
    font-size: 10px;
    background: #eef2ff;
    padding: 1px 6px;
    border-radius: 3px;
  }
}

// 每日贴士
.daily-tip-card {
  background: linear-gradient(135deg, #FEF3C7 0%, #FEF9C3 100%);
  border: 1px solid #FDE68A;
  border-radius: $border-radius-lg;
  padding: $spacing-base;

  &__header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-weight: $font-weight-semibold;
    color: #92400E;
    font-size: $font-size-sm;
    margin-bottom: $spacing-sm;
  }

  &__content {
    font-size: $font-size-base;
    color: #78350F;
    line-height: $line-height-relaxed;
  }
}


// ---- 弹窗（与 JobSelection 统一） ----
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 10, 40, 0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
}

.modal-sheet {
  width: 100%; max-width: 480px;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(67, 56, 202, 0.25);
  animation: sheetIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes sheetIn {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header-bar {
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  padding: 28px 24px 20px;
  text-align: center;
}
.modal-header-title { font-size: 20px; font-weight: 700; color: white; margin: 0 0 4px; }
.modal-header-sub   { font-size: 13px; color: rgba(255,255,255,0.7); margin: 0; }

.modal-body { padding: 20px 24px 28px; }

.interview-mode-tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 20px;
  font-size: 12px; font-weight: 600; margin-bottom: 14px;

  &.mode-voice { background: rgba(67,56,202,0.08); color: #4338ca; border: 1px solid rgba(67,56,202,0.2); }
  &.mode-text  { background: rgba(124,58,237,0.08); color: #7c3aed; border: 1px solid rgba(124,58,237,0.2); }
}

.mode-switch-row {
  display: flex; gap: 10px; margin-bottom: 18px;
}

.mode-switch-btn {
  flex: 1; height: 40px;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  border-radius: 20px;
  border: 1.5px solid #e5e7eb;
  background: white; color: #6b7280;
  font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
  font-family: $font-family-base;

  &.active {
    border-color: #4338ca;
    background: rgba(67,56,202,0.07);
    color: #4338ca;
    font-weight: 600;
  }
  &:not(.active):hover { border-color: #c4b5fd; color: #4338ca; }
}

.rules-list {
  list-style: none; padding: 0; margin: 0 0 22px;
  display: flex; flex-direction: column; gap: 11px;

  li {
    display: flex; align-items: flex-start; gap: 10px;
    font-size: 13px; color: #374151; line-height: 1.5;
  }
}

.rule-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0; margin-top: 4px;
  &--blue   { background: #5495ff; }
  &--purple { background: #9d65fe; }
  &--green  { background: #61fdc9; }
  &--orange { background: #f7b84c; }

}

.modal-actions {
  display: flex; gap: 12px;
}

.btn-cancel {
  flex: 0 0 80px; height: 48px;
  border-radius: 24px;
  border: 1.5px solid #e5e7eb;
  background: white; color: #6b7280;
  font-size: 14px; font-weight: 500;
  cursor: pointer; font-family: $font-family-base;
  transition: all 0.2s;
  &:hover { border-color: #d1d5db; background: #f9fafb; }
}

.btn-confirm {
  flex: 1; height: 48px;
  border-radius: 24px; border: none;
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  color: white; font-size: 15px; font-weight: 700;
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; gap: 8px;
  font-family: $font-family-base;
  box-shadow: 0 4px 16px rgba(67,56,202,0.4);
  transition: all 0.2s;
  &:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(67,56,202,0.5); }
  &:active { transform: scale(0.98); }
}

.modal-fade-enter-active { animation: sheetIn 0.3s ease both; }
.modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-leave-to    { opacity: 0; }

// ==================== 响应式适配 ====================
// 移动端适配 (小于 768px)
@media (max-width: 767px) {
  // 双栏变单栏
  .two-column-section {
    grid-template-columns: 1fr;
  }

  // 未登录特色区域也改为单栏
  .feature-grid {
    grid-template-columns: 1fr;
  }

  // 雷达图卡片调整
  .ability-card {
    padding: $spacing-md;
  }

  .radar-preview {
    max-width: 160px;
  }

  .radar-label {
    font-size: 8px;
  }

  // 成就卡片调整
  .achievement-card {
    padding: $spacing-md;
  }

  .badges-row {
    justify-content: flex-start;
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x mandatory;
    
    &::-webkit-scrollbar {
      height: 0;
    }
  }

  .badge-item {
    min-width: 56px;
    scroll-snap-align: start;
  }

  // 热门岗位标签换行
  .hot-job-tags {
    flex-wrap: wrap;
  }

  .job-tag {
    padding: 8px 12px;
    
    &__icon {
      font-size: 16px;
    }
    
    &__name {
      font-size: $font-size-xs;
    }
  }

  // 热门面试题
  .question-card {
    padding: $spacing-sm $spacing-md;
    
    &__text {
      font-size: $font-size-xs;
    }
  }
}

// 超小屏幕适配 (小于 375px)
@media (max-width: 374px) {
  .dashboard-body {
    padding: $spacing-sm;
  }

  .quick-start-card {
    padding: $spacing-md;
    
    &__title {
      font-size: $font-size-base;
    }
    
    &__icon {
      font-size: 22px;
    }
  }

  .radar-preview {
    max-width: 140px;
  }

  .badge-item {
    min-width: 48px;
    padding: 6px 4px;
    
    &__icon {
      font-size: 16px;
    }
    
    &__name {
      font-size: 8px;
    }
  }

  .streak-badge {
    padding: 3px 8px;
    
    &__text {
      font-size: 10px;
    }
  }

  .activity-item {
    padding: 4px 6px;
    gap: 6px;
    
    &__icon {
      font-size: 12px;
    }
    
    &__text {
      font-size: 11px;
    }
  }

  .feature-box {
    padding: $spacing-sm;
    
    &__icon {
      font-size: 28px;
    }
    
    &__title {
      font-size: $font-size-xs;
    }
    
    &__desc {
      font-size: 10px;
    }
  }
}

// 平板适配 (768px - 1024px)
@media (min-width: 768px) and (max-width: 1024px) {
  .two-column-section {
    gap: $spacing-sm;
  }

  .radar-preview {
    max-width: 150px;
  }

  .badge-item {
    min-width: 50px;
  }
}


// 弹窗移动端适配
@media (max-width: 768px) {

}

/* spinner for trending loading */
.trending-spinner-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #eee;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

</style>