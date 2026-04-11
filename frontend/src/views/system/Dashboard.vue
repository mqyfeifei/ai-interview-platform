<!--
  =============================================
  frontend/src/views/system/Dashboard.vue
  仪表盘首页组件
  ============================================= -->
<template>
  <div class="dashboard-page">

    <!-- 主内容区 -->
    <div class="dashboard-body">

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
        <!-- 每日提示 -->
        <div class="daily-tip-card">
          <div class="daily-tip-card__header">
            <span>💡</span>
            <span>今日面试小贴士</span>
          </div>
          <p class="daily-tip-card__content">{{ dailyTip }}</p>
        </div>
    </div>

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
      heroTab: 'interview',
      dailyTips: [
        '回答时采用 STAR 法则（情境-任务-行动-结果），让回答更有结构和说服力。',
        '面试前10分钟快速回顾项目亮点，准备2-3个"失败经历+如何改进"的故事。',
        '技术问题不会时，不要沉默，大声思考推理过程同样体现能力。',
        '多使用数字和具体案例，比如"优化后性能提升了40%"比"优化了很多"更有说服力。',
        '复杂问题先说结论，再展开细节，让面试官第一时间抓住重点。'
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

    heroDesc() {
      if (this.heroTab === 'learning') {
        return '展示多维度能力曲线，针对薄弱点进行学习与练习，持续提升面试表现'
      }
      return '面试过程中实时提供专业建议，帮助构建清晰有逻辑的回答框架，面试成功率提升3倍'
    },

    heroActionText() {
      return this.heroTab === 'learning' ? '开始学习' : '开始面试'
    },

    defaultJobName() {
      if (!this.defaultJob) return ''
      const job = this.jobs.find(j => String(j.id) === String(this.defaultJob))
      return job ? job.name : ''
    },

    dailyTip() {
      const idx = new Date().getDate() % this.dailyTips.length
      return this.dailyTips[idx]
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
    this.loadPlatformStats()
    this.loadStats()
    this.maybeAutoShowHelpGuide()
  },
  methods: {
    ...mapActions('user', ['fetchUserInfo']),
    ...mapActions('interview', ['selectJob']),

    async primeAudioPlayback() {
      if (!this.voiceMode || typeof window === 'undefined') return
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext
        if (!AudioCtx) return

        if (!window.__aiInterviewAudioContext) {
          window.__aiInterviewAudioContext = new AudioCtx()
        }

        const ctx = window.__aiInterviewAudioContext
        if (ctx.state === 'suspended') {
          await ctx.resume()
        }

        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        gain.gain.value = 0.00001
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start()
        osc.stop(ctx.currentTime + 0.01)
      } catch (err) {
        console.warn('语音播放预解锁失败', err)
      }
    },

    getHelpGuideUserKey() {
      const u = this.userInfo || {}
      return u.id ?? u.user_id ?? u.userId ?? u.uid ?? u.email ?? null
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

      await this.primeAudioPlayback()
      
      await this.$store.dispatch('interview/resetInterview')
      this.$store.commit('interview/SET_JOB_DB_ID', job.id)  // 用保存的引用
      this.$store.commit('interview/SET_VOICE_MODE', this.voiceMode)
      await this.$store.dispatch('interview/selectJob', job)
      if (this.voiceMode) {
        this.$router.push('/interview/voice-session')
      } else {
        this.$router.push('/interview/session')
      }
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
  height: 100vh;
  min-height: 100vh;
  background: #f8f8fb;
  padding-bottom: $bottom-nav-height;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  border-radius: 0;
  padding: 40px 20px;
  margin-bottom: 0;
  box-shadow: 0 10px 26px rgba(76, 66, 143, 0.14);
  overflow: hidden;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
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
  border-radius: 0;
  min-height: 420px;
  margin-bottom: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  flex: 1;
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
  margin-bottom: 0;
  width: 100%;
  padding: 20px;
  background: rgba(255, 255, 255, 0);
  flex-shrink: 0;
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
  width: 100%;
  max-width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-top: 0;
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
  padding: 0 20px;
  flex-shrink: 0;
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
  margin-top:$spacing-lg;
  z-index: 1;

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

}

// 平板适配 (768px - 1024px)
@media (min-width: 768px) and (max-width: 1024px) {
  .two-column-section {
    gap: $spacing-sm;
  }

  .radar-preview {
    max-width: 150px;
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