<!--
  =============================================
  frontend/src/views/system/Dashboard.vue
  仪表盘首页组件
  ============================================= -->
<template>
  <div class="dashboard-page">
    
    <!-- 顶部渐变Header -->
    <div class="dashboard-header">
      
      <div class="header-content">
        <div class="header-top">
          <div class="greeting">
            <p class="greeting__time">{{ timeGreeting }}</p>
            <!-- 未登录状态 -->
            <template v-if="!isLoggedIn">
              <h1 class="greeting__name">你好，访客 👋</h1>
              <p class="greeting__hint">登录后开始你的面试学习之旅</p>
              <button class="login-btn" @click="$router.push('/login')">
                <span>立即登录</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
            </template>
            <!-- 已登录状态 -->
            <template v-else>
              <h1 class="greeting__name">{{ userName }} 👋</h1>
            </template>
          </div>

          <!-- 已登录：头像 -->
          <div class="header-avatar" v-if="isLoggedIn" @click="$router.push('/profile')">
            <img v-if="userInfo && userInfo.avatar" :src="resolvedAvatarSrc" alt="头像" />
            <span v-else class="avatar-fallback">{{ avatarLetter }}</span>
          </div>
        </div>

        <!-- 最近面试卡片 - 仅登录用户显示 -->
        <div class="recent-score-card" v-if="isLoggedIn && stats.lastInterviewScore">
          <div class="recent-score-card__left">
            <p class="recent-score-card__label">上次面试</p>
            <p class="recent-score-card__job">{{ stats.lastInterviewJob }}</p>
            <p class="recent-score-card__date">{{ formatDate(stats.lastInterviewAt) }}</p>
          </div>
          <div class="recent-score-card__right">
            <div class="score-ring">
              <svg viewBox="0 0 60 60">
                <circle cx="30" cy="30" r="24" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="5"/>
                <circle
                  cx="30" cy="30" r="24"
                  fill="none"
                  stroke="white"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="scoreCircumference"
                  :stroke-dashoffset="scoreOffset"
                  transform="rotate(-90 30 30)"
                  style="transition: stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)"
                />
              </svg>
              <span class="score-ring__value">{{ stats.lastInterviewScore }}</span>
            </div>
            <div
              class="score-trend"
              :class="stats.scoreImprovement >= 0 ? 'up' : 'down'"
              v-if="stats.scoreImprovement !== undefined && stats.scoreImprovement !== 0"
            >
              <span>{{ stats.scoreImprovement >= 0 ? '↑' : '↓' }}</span>
              <span>{{ Math.abs(stats.scoreImprovement) }}分</span>
            </div>
          </div>
        </div>

        <!-- 无面试记录 - 仅登录用户显示 -->
        <div class="no-interview-card" v-else-if="isLoggedIn">
          <span class="no-interview-card__icon">🎯</span>
          <div>
            <p class="no-interview-card__title">开始你的第一次面试</p>
            <p class="no-interview-card__sub">AI面试官已就位，随时开始练习</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="dashboard-body">
      <!-- 数据概览 - 仅登录用户显示 -->
      <div class="stats-row" v-if="isLoggedIn">
        <div class="stats-card" v-for="s in statCards" :key="s.label">
          <span class="stats-card__icon">{{ s.icon }}</span>
          <span class="stats-card__value">{{ s.value }}</span>
          <span class="stats-card__label">{{ s.label }}</span>
        </div>
      </div>

      <!-- 快速开始 - 全新卡片式设计 -->
      <section class="section quick-start-section">
        <div class="quick-start-card">
          <div class="quick-start-card__bg"></div>
          <div class="quick-start-card__content">
            <div class="quick-start-card__header">
              <span class="quick-start-card__icon">🚀</span>
              <h2 class="quick-start-card__title">开始模拟面试</h2>
            </div>
            <p class="quick-start-card__desc">AI面试官已就位，选择岗位立即开始</p>
            
            <!-- 热门岗位标签 -->
            <div class="hot-job-tags">
              <button 
                class="job-tag" 
                v-for="job in topHotJobs" 
                :key="job.id"
                :style="{ '--tag-color': job.color, '--tag-bg': job.colorBg, '--tag-hover-bg': job.colorHoverBg }"
                @click="showJobConfirm(job)"
              >
                <span class="job-tag__icon">{{ job.icon }}</span>
                <span class="job-tag__name">{{ job.name.replace('开发', '').replace('工程师', '') }}</span>
              </button>
              <button class="job-tag job-tag--more" @click="$router.push('/interview/select')">
                <span class="job-tag__icon">📋</span>
                <span class="job-tag__name">更多岗位</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="job-tag__arrow">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>

            <!-- 开始面试按钮 -->
            <button class="start-interview-btn" @click="startInterview">
              <span>开始面试</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </div>
        </div>
      </section>

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

      <!-- 未登录时显示平台特色 -->
      <section class="section feature-section" v-else>
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

      <!-- 热门面试题 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">🔥 技术热榜</h2>
        </div>
        <div class="question-list" v-if="!trendingLoading">
          <div class="question-card" v-for="(q, idx) in displayHotQuestions" :key="idx" @click="goToQuestionDetail(q)">
            <div class="question-card__top">
              <span class="question-card__tag" :style="{ background: q.tagBg, color: q.tagColor }">{{ q.tag }}</span>
              <span class="question-card__source" v-if="q.sourceLabel">{{ q.sourceLabel }}</span>
            </div>
            <p class="question-card__text">{{ q.text || q.title }}</p>
            <div class="question-card__meta">
              <span v-if="q.likes">👍 {{ q.likes }}</span>
              <span v-if="q.comments">💬 {{ q.comments }}</span>
              <span v-if="q.hasContent" class="question-card__readable">可阅读全文</span>
            </div>
          </div>
        </div>
        <div class="question-list question-list--loading" v-else>
          <div class="question-card question-card--skeleton" v-for="i in 3" :key="i">
            <span class="skeleton-tag"></span>
            <p class="skeleton-text"></p>
            <div class="skeleton-meta"></div>
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
import { fetchJobs, fetchPopularJobs, getTrendingTopics } from '@/api/job'
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
      dailyTips: [
        '回答时采用 STAR 法则（情境-任务-行动-结果），让回答更有结构和说服力。',
        '面试前10分钟快速回顾项目亮点，准备2-3个"失败经历+如何改进"的故事。',
        '技术问题不会时，不要沉默，大声思考推理过程同样体现能力。',
        '多使用数字和具体案例，比如"优化后性能提升了40%"比"优化了很多"更有说服力。',
        '复杂问题先说结论，再展开细节，让面试官第一时间抓住重点。'
      ],
      hotQuestions: [
        { tag: 'Java', tagBg: '#FEF3C7', tagColor: '#B45309', text: '请介绍一下JVM的内存模型和垃圾回收机制', difficulty: '中等', views: 2847 },
        { tag: '前端', tagBg: '#DBEAFE', tagColor: '#1D4ED8', text: 'Vue的响应式原理是什么？Vue3相比Vue2有哪些改进？', difficulty: '中等', views: 3156 },
        { tag: '算法', tagBg: '#D1FAE5', tagColor: '#047857', text: '如何实现一个LRU缓存？时间复杂度是多少？', difficulty: '较难', views: 1923 }
      ],
      // 成就徽章 - 根据真实数据动态计算
      badges: [
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
      // 实时热榜数据
      trendingTopics: [],
      trendingLoading: false,

      // 使用帮助指南（首次登录自动弹出一次）
      showHelpGuide: false,
      helpGuideStorageKey: ''
    }
  },
  computed: {
    ...mapGetters('user', ['userInfo', 'userName', 'defaultJob', 'isLoggedIn']),

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

    statCards() {
      return [
        { icon: '🎯', value: this.stats.totalInterviews || 0, label: '练习次数' },
        { icon: '⭐', value: this.stats.avgScore || '--', label: '平均得分' },
        { icon: '🔥', value: this.stats.weeklyPractice || 0, label: '本周练习' }
      ]
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

    // 热门题目（优先显示实时热榜，失败时回退到本地经典题）
    displayHotQuestions() {
      if (this.trendingTopics.length > 0) {
        return this.trendingTopics.slice(0, 9).map(item => ({
          ...item,
          text: item.title || item.text,
          isTrending: true
        }))
      }
      return this.hotQuestions
    }
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
    this.loadJobs() 
    this.loadStats()
    this.loadTrendingTopics()
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

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return `${d.getMonth() + 1}月${d.getDate()}日`
    },

    startInterview() {
      this.$router.push('/interview/select')
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

    // 加载掘金实时热榜
    async loadTrendingTopics() {
      this.trendingLoading = true
      try {
        const jobId = this.defaultJob || 'default'
        const res = await getTrendingTopics(jobId, 6)
        // 响应拦截器已自动解包 res.data，这里 res 直接就是文章数组
        const list = Array.isArray(res) ? res : (res && res.data ? res.data : [])
        if (list.length > 0) {
          this.trendingTopics = list
        }
      } catch (e) {
        console.warn('热榜加载失败，使用本地经典题', e)
      } finally {
        this.trendingLoading = false
      }
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
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// 顶部 Header
.dashboard-header {
  background: $gradient-primary;
  padding: 0;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    top: -80px; right: -60px;
    pointer-events: none;
  }
  &::after {
    content: '';
    position: absolute;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(124,58,237,0.3) 0%, transparent 70%);
    bottom: -40px; left: -40px;
    pointer-events: none;
  }
}

.header-content {
  position: relative;
  z-index: 1;
  padding: 52px $spacing-base $spacing-xl;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-lg;
}

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

// 未登录时的登录按钮
.login-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 20px;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: $border-radius-lg;
  color: white;
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);

  svg {
    width: 16px;
    height: 16px;
  }

  &:hover {
    background: rgba(255,255,255,0.3);
    transform: translateX(2px);
  }

  &:active {
    transform: scale(0.98);
  }
}

.header-avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: 2px solid rgba(255,255,255,0.3);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img { width: 100%; height: 100%; object-fit: cover; }
}

.avatar-fallback {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: white;
}

// 最近面试卡片
.recent-score-card {
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &__left { flex: 1; }
  &__label {
    font-size: $font-size-xs;
    color: rgba(255,255,255,0.55);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }
  &__job {
    font-weight: $font-weight-semibold;
    color: white;
    font-size: $font-size-base;
    margin-bottom: 3px;
  }
  &__date { font-size: $font-size-xs; color: rgba(255,255,255,0.5); }

  &__right {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
}

.score-ring {
  position: relative;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;

  svg { position: absolute; inset: 0; width: 100%; height: 100%; }

  &__value {
    font-family: $font-family-display;
    font-size: $font-size-xl;
    font-weight: $font-weight-extrabold;
    color: white;
    position: relative;
    z-index: 1;
  }
}

.score-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  padding: 2px 8px;
  border-radius: $border-radius-full;

  &.up { background: rgba(16,185,129,0.25); color: #6ee7b7; }
  &.down { background: rgba(239,68,68,0.25); color: #fca5a5; }
}

.no-interview-card {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  display: flex;
  align-items: center;
  gap: $spacing-md;

  &__icon { font-size: 32px; }
  &__title { font-weight: $font-weight-semibold; color: white; font-size: $font-size-base; }
  &__sub { font-size: $font-size-xs; color: rgba(255,255,255,0.6); margin-top: 3px; }
}

// 未登录用户 - 功能亮点
.guest-features {
  display: flex;
  justify-content: space-around;
  margin-top: $spacing-lg;
  padding: $spacing-md 0;

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }

  &__icon {
    font-size: 24px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.15);
    border-radius: 50%;
  }

  &__text {
    font-size: $font-size-xs;
    color: rgba(255,255,255,0.85);
    font-weight: $font-weight-medium;
  }
}

// 未登录用户引导区
.guest-intro {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-xl;

  @media (min-width: 480px) {
    grid-template-columns: repeat(3, 1fr);
  }
}

.intro-card {
  background: white;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  text-align: center;
  box-shadow: $shadow;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  &__icon {
    font-size: 36px;
    margin-bottom: $spacing-sm;
  }

  &__title {
    font-family: $font-family-display;
    font-size: $font-size-base;
    font-weight: $font-weight-bold;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  &__desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.5;
  }
}

// 主体
.dashboard-body {
  padding: $spacing-base;
  animation: fadeSlideUp 0.4s ease both;
}

// 统计行
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-sm;
  margin-bottom: $spacing-xl;
  margin-top: -($spacing-base);
}

.stats-card {
  background: white;
  border-radius: $border-radius;
  padding: $spacing-md $spacing-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  box-shadow: $shadow;

  &__icon { font-size: 22px; }
  &__value {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-extrabold;
    color: $text-primary;
    line-height: 1;
  }
  &__label { font-size: $font-size-xs; color: $text-muted; }
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

.section-more {
  font-size: $font-size-sm;
  color: $primary;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: $font-weight-medium;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 2px;
  font-family: $font-family-base;
}

// 快速开始卡片 - 全新设计
.quick-start-section {
  margin-bottom: $spacing-xl;
}

.quick-start-card {
  position: relative;
  background: white;
  border-radius: $border-radius-xl;
  padding: $spacing-lg;
  box-shadow: $shadow-lg;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.1);

  &__bg {
    position: absolute;
    top: -50px;
    right: -50px;
    width: 200px;
    height: 200px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%);
    border-radius: 50%;
    pointer-events: none;
  }

  &__content {
    position: relative;
    z-index: 1;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-xs;
  }

  &__icon {
    font-size: 28px;
  }

  &__title {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $text-primary;
    font-family: $font-family-display;
  }

  &__desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-lg;
    padding-left: 2px;
  }
}

// 热门岗位标签
.hot-job-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
}

.job-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--tag-bg, #c8cad2);
  border: 1px solid transparent;
  border-radius: $border-radius-lg;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: $font-family-base;

  &:hover {
    border-color: var(--tag-color, $primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  &:active {
    transform: scale(0.98);
  }

  &__icon {
    font-size: 18px;
  }

  &__name {
    font-size: $font-size-sm;
    font-weight: $font-weight-medium;
    color: $text-primary;
  }

  &__arrow {
    width: 12px;
    height: 12px;
    color: $text-muted;
    margin-left: 2px;
  }

  // 更多岗位样式
  &--more {
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
    border: 1px dashed rgba(99, 102, 241, 0.3);

    .job-tag__name {
      color: $primary;
    }

    &:hover {
      border-color: $primary;
      border-style: solid;
      background: linear-gradient(135deg, #E0E7FF 0%, #EDE9FE 100%);
    }
  }
}

// 开始面试按钮
.start-interview-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  width: 100%;
  padding: 14px $spacing-lg;
  background: $gradient-primary;
  border: none;
  border-radius: $border-radius-lg;
  color: white;
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
  font-family: $font-family-base;

  svg {
    width: 18px;
    height: 18px;
    transition: transform 0.2s ease;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.45);

    svg {
      transform: translateX(3px);
    }
  }

  &:active {
    transform: translateY(0);
  }
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
  stroke: $primary;
  stroke-width: 2;
}

.radar-dot {
  fill: $primary;
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
  font-size: 9px;
  color: $text-muted;
  white-space: nowrap;
}

// 成就卡片
.achievement-card {
  background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  border: 1px solid #DDD6FE;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;
  }

  &__title {
    font-size: $font-size-sm;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }
}

.streak-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid #F59E0B;

  &__fire {
    font-size: 14px;
  }

  &__text {
    font-size: 11px;
    font-weight: $font-weight-semibold;
    color: #B45309;
  }
}

.badges-row {
  display: flex;
  gap: $spacing-xs;
  margin-bottom: $spacing-md;
  overflow-x: auto;
  padding-bottom: 4px;

  &::-webkit-scrollbar {
    display: none;
  }
}

.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 52px;
  padding: 8px 6px;
  background: white;
  border-radius: $border-radius;
  border: 1px solid #E5E7EB;
  transition: all 0.2s ease;

  &__icon {
    font-size: 20px;
  }

  &__name {
    font-size: 9px;
    color: $text-secondary;
    white-space: nowrap;
  }

  &.locked {
    opacity: 0.4;
    filter: grayscale(1);
  }

  &:not(.locked):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    border-color: $primary;
  }
}

.recent-activity {
  &__title {
    font-size: $font-size-xs;
    font-weight: $font-weight-semibold;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: white;
  border-radius: $border-radius-sm;
  font-size: $font-size-xs;

  &__icon {
    font-size: 14px;
  }

  &__text {
    flex: 1;
    color: $text-primary;
  }

  &__time {
    color: $text-muted;
    font-size: 10px;
  }
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

.section-more {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: $font-size-sm;
  color: $primary;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: $font-weight-medium;
  font-family: $font-family-base;
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
  &--blue   { background: #3b82f6; }
  &--purple { background: #7c3aed; }
  &--green  { background: #10b981; }
  &--orange { background: #f59e0b; }
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

  // 统计行
  .stats-row {
    gap: $spacing-xs;
  }

  .stats-card {
    padding: $spacing-sm;
    
    &__value {
      font-size: $font-size-xl;
    }
    
    &__icon {
      font-size: 18px;
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
</style>