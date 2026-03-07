<!--
  =============================================
  frontend/src/views/interview/InterviewSession.vue
  面试会话页组件
  ============================================= -->
<template>
  <div class="interview-page">
    <!-- 顶部状态栏 -->
    <header class="interview-header">
      <div class="interview-header__left">
        <button class="header-end-btn" @click="showEndConfirm = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="job-info">
          <span class="job-info__icon" :style="selectedJob ? { background: selectedJob.colorBg } : {}">
            {{ selectedJob ? selectedJob.icon : '🎯' }}
          </span>
          <div>
            <p class="job-info__name">{{ selectedJob ? selectedJob.name : '模拟面试' }}</p>
            <p class="job-info__progress">问题 {{ questionIndex }} / {{ totalQuestions }}</p>
          </div>
        </div>
      </div>

      <div class="interview-header__right">
        <!-- 进度环 -->
        <div class="progress-ring">
          <svg viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="15" fill="none" stroke="#E2E8F0" stroke-width="3"/>
            <circle
              cx="20" cy="20" r="15"
              fill="none"
              :stroke="timerWarning ? '#EF4444' : '#4338CA'"
              stroke-width="3"
              stroke-linecap="round"
              :stroke-dasharray="progressCircle"
              :stroke-dashoffset="progressOffset"
              transform="rotate(-90 20 20)"
              style="transition: stroke-dashoffset 1s linear, stroke 0.3s"
            />
          </svg>
          <span class="progress-ring__time" :class="{ warning: timerWarning }">
            {{ timerDisplay }}
          </span>
        </div>

        <!-- 结束按钮 -->
        <button class="end-btn" @click="showEndConfirm = true">结束</button>
      </div>
    </header>

    <!-- 消息流 -->
    <div class="messages-container" ref="messagesContainer">
      <!-- 面试开始提示 -->
      <div class="session-start-tip">
        <div class="session-start-tip__line" />
        <span>面试正式开始</span>
        <div class="session-start-tip__line" />
      </div>

      <!-- 消息气泡 -->
      <transition-group name="message" tag="div" class="messages-list">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message-item', 'message-item--' + msg.role]"
          v-show="!(msg.role === 'ai' && msg.streaming && !msg.content)"
          >
          <!-- AI 头像 -->
          <div v-if="msg.role === 'ai'" class="message-avatar message-avatar--ai">
            <span>🤖</span>
          </div>

          <div class="message-bubble-wrap">
            <!-- 追问标识 -->
            <div v-if="msg.isFollowUp" class="followup-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              追问
            </div>

            <div :class="['message-bubble', 'message-bubble--' + msg.role]" v-show="msg.content">
              <p class="message-text">
                {{ msg.content }}
                <!-- <span v-if="msg.streaming" class="typing-cursor">▌</span> -->
              </p>
            </div>

            <span class="message-time" v-show="msg.content">{{ formatTime(msg.timestamp) }}</span>
          </div>

          <!-- 用户头像 -->
          <div v-if="msg.role === 'user'" class="message-avatar message-avatar--user">
            <span>{{ userAvatarLetter }}</span>
          </div>
        </div>
      </transition-group>

      <!-- AI 思考中动画 -->
      <transition name="fade">
        <div v-if="isLoading && !hasStreamingMessage" class="message-item message-item--ai thinking-row">
          <div class="message-avatar message-avatar--ai">
            <span>🤖</span>
          </div>
          <div class="thinking-bubble">
            <span class="thinking-dot" />
            <span class="thinking-dot" />
            <span class="thinking-dot" />
          </div>
        </div>
      </transition>

      <!-- 面试结束提示 -->
      <div v-if="isFinished" class="session-end-tip">
        <div class="session-end-tip__icon">🎉</div>
        <p class="session-end-tip__title">面试已完成</p>
        <p class="session-end-tip__sub">正在生成评估报告，请稍候...</p>
        <div class="session-end-tip__spinner" />
      </div>

      <div style="height: 16px;" />
    </div>

    <!-- 底部输入区 -->
    <div class="input-area" :class="{ disabled: isFinished || isLoading }">
      <!-- 语音状态提示条 -->
      <transition name="slide-up">
        <div v-if="isRecording" class="recording-bar">
          <div class="recording-bar__wave">
            <span v-for="n in 5" :key="n" class="wave-bar" :style="{ animationDelay: n * 0.1 + 's' }" />
          </div>
          <span class="recording-bar__text">正在录音... 再次点击麦克风停止</span>
          <span class="recording-bar__time">{{ recordingTime }}s</span>
        </div>
      </transition>
      <div v-if="isTranscribing" class="transcribing-tip">
        🎤 语音转写中...
      </div>
      <div class="input-row">
        <!-- 语音按钮 -->
        <button
          :class="['voice-btn', { active: isRecording }]"
          @click="toggleRecording"
          :disabled="isFinished || isLoading"
          :title="isRecording ? '停止录音' : '语音输入'"
        >
          <svg v-if="!isRecording" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>



        <!-- 文本输入框 -->
        <div class="textarea-wrapper">
          <textarea
            ref="inputRef"
            v-model="inputText"
            :placeholder="isLoading ? 'AI 正在思考中...' : '在此输入你的回答，支持换行...'"
            :disabled="isFinished || isLoading"
            class="input-textarea"
            rows="1"
            @keydown.enter.exact.prevent="handleSend"
            @input="autoResize"
          />
          <span class="input-hint">Enter 发送 · Shift+Enter 换行</span>
        </div>

        <!-- 发送按钮 -->
        <button
          :class="['send-btn', { ready: inputText.trim() && !isLoading && !isFinished }]"
          :disabled="!inputText.trim() || isLoading || isFinished"
          @click="handleSend"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>

        <!-- ↓ 新增：面试结束/报告生成中 遮罩 -->
    <transition name="ending-fade">
      <div v-if="isEnding || isFinished" class="ending-overlay">
        <div class="ending-card">
          <div class="ending-icon-wrap">
            <svg class="ending-spin-ring" viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="26" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="5"/>
              <circle cx="30" cy="30" r="26" fill="none" stroke="white" stroke-width="5"
                stroke-linecap="round" stroke-dasharray="50 114" transform="rotate(-90 30 30)"/>
            </svg>
            <span class="ending-emoji">🎯</span>
          </div>
          <h2 class="ending-title">面试已结束</h2>
          <p class="ending-sub">AI 正在为你生成专属评估报告...</p>
          <div class="ending-progress-track">
            <div class="ending-progress-fill" />
          </div>
          <p class="ending-hint">通常需要 10 ~ 30 秒，请勿关闭页面</p>
        </div>
      </div>
    </transition>

    <!-- 结束确认弹窗 -->
    <transition name="modal">
      <div v-if="showEndConfirm" class="modal-overlay" @click.self="showEndConfirm = false">
        <div class="modal-sheet">
          <div class="modal-body-centered">
            <div class="confirm-icon">⚠️</div>
            <h3 class="confirm-title">确认结束面试？</h3>
            <p class="confirm-desc">
              当前进度 {{ questionIndex }}/{{ totalQuestions }} 题，结束后将立即生成面试报告。
            </p>
            <div class="confirm-actions">
              <button class="btn btn-ghost" @click="showEndConfirm = false">继续面试</button>
              <button class="btn btn-danger" :disabled="endingInterview" @click="handleEnd">
                <span v-if="endingInterview" class="btn-spinner btn-spinner--danger" />
                {{ endingInterview ? '结束中...' : '确认结束' }}
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

const QUESTION_TIME_LIMIT = 120 // 每题时限（秒）

export default {
  name: 'InterviewSession',
  data() {
    return {
      inputText: '',
      isRecording: false,
      recordingTime: 0,
      showEndConfirm: false,
      endingInterview: false,
      // 计时相关
      questionTimer: QUESTION_TIME_LIMIT,
      timerInterval: null,
      recordingInterval: null,
      // 语音识别
      mediaRecorder: null,
      audioChunks: [],
      // ✅ 新增：语音转写状态（用于显示加载中）
      isTranscribing: false
    }
  },
  computed: {
    ...mapGetters('user', ['userName']),
    ...mapGetters('interview', [
      'selectedJob', 'messages', 'questionIndex',
      'isEnding', 
      'totalQuestions', 'isFinished', 'isLoading', 'reportId'
    ]),

    userAvatarLetter() {
      return (this.userName || '我').charAt(0)
    },

    timerDisplay() {
      const m = Math.floor(this.questionTimer / 60)
      const s = this.questionTimer % 60
      return m > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${s}s`
    },

    timerWarning() {
      return this.questionTimer <= 30
    },

    progressCircle() {
      return 2 * Math.PI * 15
    },

    progressOffset() {
      return this.progressCircle * (1 - this.questionTimer / QUESTION_TIME_LIMIT)
    },
    hasStreamingMessage() {
  return this.messages.some(m => m.streaming  && m.content.length > 0)
}
  },
  async created() {
    // 如果没有选择岗位，重定向到岗位选择
    if (!this.selectedJob) {
      this.$router.replace('/interview/select')
      return
    }
    // 如果没有进行中的会话，启动
    if (!this.$store.getters['interview/currentSession']) {
      await this.startSession()
    }
    this.startQuestionTimer()
  },
  beforeUnmount() {
    this.clearTimers()
  },
  watch: {
    // 切换到新问题时重置计时器
    questionIndex(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.questionTimer = QUESTION_TIME_LIMIT
      }
    },
    // isEnding 一旦为 true 立即停止计时器（不等 reportId）
      isEnding(val) {
    if (val) this.clearTimers()
  },
    // 面试结束时跳转报告页
  isFinished(val) {
    if (val) {
      this.clearTimers()
      if (this.reportId) {
        setTimeout(() => this.$router.push(`/interview/report/${this.reportId}`), 2500)
      } else {
        // reportId 还未到，等它就位再跳转
        const unwatch = this.$watch('reportId', (id) => {
          if (id) {
            unwatch()
            setTimeout(() => this.$router.push(`/interview/report/${id}`), 2500)
          }
        })
      }
    }
  },
    // 消息更新自动滚底
    messages() {
      this.$nextTick(this.scrollToBottom)
    },
    isLoading() {
      this.$nextTick(this.scrollToBottom)
    }
  },
  methods: {
    ...mapActions('interview', ['startSession', 'submitAnswer', 'endInterview']),

    // ---- 发送回答 ----
    async handleSend() {
      const text = this.inputText.trim()
      if (!text || this.isLoading || this.isFinished || this.isTranscribing) return // ✅ 新增：转写中禁止发送
      this.inputText = ''
      this.resetTextarea()
      // 重置题目计时
      this.questionTimer = QUESTION_TIME_LIMIT
      await this.submitAnswer(text)
    },

    // ---- 结束面试 ----
    async handleEnd() {
      this.endingInterview = true
      this.showEndConfirm = false
      try {
        await this.endInterview()
      } finally {
        this.endingInterview = false
      }
    },

    // ---- 计时器 ----
    startQuestionTimer() {
      this.clearTimers()
      this.timerInterval = setInterval(() => {
            if (this.isFinished || this.isEnding) {
              this.clearTimers()
              return
            }
        if (this.questionTimer > 0) {
          this.questionTimer--
        } else if (this.questionTimer === 0) {
          // 超时自动发送（发送空回答，AI会继续下一题）
          this.questionTimer = -1 // 防止重复触发
          this.autoSubmitOnTimeout()
        }
      }, 1000)
    },

    autoSubmitOnTimeout() {
      // isLoading 或 isTranscribing 时跳过，等流结束后计时器已被 watch(questionIndex) 重置
      if (this.isLoading || this.isFinished || this.isTranscribing) {
        // 还原为0，等 loading 结束后下次 tick 不会再触发（因为 watch questionIndex 会重置为120）
        this.questionTimer = 0
        return
      }
      const text = this.inputText.trim() || '（超时，跳过此题）'
      this.inputText = ''
      this.resetTextarea()
      // 提交前先重置计时器，submitAnswer 完成后 watch(questionIndex) 也会重置
      this.questionTimer = QUESTION_TIME_LIMIT
      this.submitAnswer(text)
    },

    clearTimers() {
      if (this.timerInterval) { clearInterval(this.timerInterval); this.timerInterval = null }
      if (this.recordingInterval) { clearInterval(this.recordingInterval); this.recordingInterval = null }
    },

    // ---- 语音输入 ----
    async toggleRecording() {
      if (this.isRecording) {
        this.stopRecording()
      } else {
        await this.startRecording()
      }
    },

    async startRecording() {
      // ✅ 新增：转写中禁止开始录音
      if (this.isTranscribing) {
        alert('正在处理语音，请稍等...')
        return
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        this.audioChunks = []
        this.mediaRecorder = new MediaRecorder(stream)
        this.mediaRecorder.ondataavailable = e => this.audioChunks.push(e.data)
        
        // ✅ 核心修改：替换原有 onstop 逻辑，整合语音转文字
        this.mediaRecorder.onstop = async () => {
          // 先停止音轨
          stream.getTracks().forEach(t => t.stop())
          // 构建音频 Blob
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' })
          this.isTranscribing = true
          try {
            // 动态导入上传音频API
            const { uploadAudio } = await import('@/api/interview')
            // 上传音频并获取转文字结果
            const { text } = await uploadAudio(audioBlob)
            // ✅ 适配现有变量：把转写结果赋值给 inputText（原有代码用 inputText 而非 userInput）
            this.inputText = text || '（语音识别失败，请手动输入）'
          } catch (err) {
            console.error('语音转文字失败：', err)
            this.inputText = '（语音识别失败，请手动输入）'
          } finally {
            this.isTranscribing = false
            // 转写完成后聚焦输入框
            this.$nextTick(() => {
              if (this.$refs.inputRef) this.$refs.inputRef.focus()
            })
          }
        }

        this.mediaRecorder.start()
        this.isRecording = true
        this.recordingTime = 0
        this.recordingInterval = setInterval(() => { this.recordingTime++ }, 1000)
      } catch (err) {
        // 麦克风权限被拒绝时，降级为文字提示
        console.warn('麦克风权限被拒绝，请使用文字输入', err)
        alert('无法访问麦克风，请使用文字输入或检查浏览器权限设置。')
      }
    },

    stopRecording() {
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop()
      }
      this.isRecording = false
      if (this.recordingInterval) { clearInterval(this.recordingInterval); this.recordingInterval = null }
    },

    // ✅ 移除原有空的 handleRecordingStop 方法（已整合到 onstop 中）

    // ---- 工具方法 ----
    scrollToBottom() {
      const el = this.$refs.messagesContainer
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
    },

    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    },

    autoResize() {
      const el = this.$refs.inputRef
      if (!el) return
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    },

    resetTextarea() {
      const el = this.$refs.inputRef
      if (el) { el.style.height = 'auto' }
    }
  }
}
</script>

<style lang="scss" scoped>
.interview-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
  overflow: hidden;
}

// ---- Header ----
.interview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-base;
  height: 60px;
  background: white;
  border-bottom: 1px solid $border-color;
  box-shadow: $shadow-sm;
  flex-shrink: 0;
  padding-top: env(safe-area-inset-top);

  &__left {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    flex: 1;
    min-width: 0;
  }
  &__right {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    flex-shrink: 0;
  }
}

.header-end-btn {
  width: 34px; height: 34px; border-radius: 50%;
  background: $gray-100; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0; color: $text-secondary;
  svg { width: 17px; height: 17px; }
  &:hover { background: $gray-200; }
}

.job-info {
  display: flex; align-items: center; gap: $spacing-sm; min-width: 0;

  &__icon {
    width: 34px; height: 34px; border-radius: $border-radius-sm;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
    background: $primary-bg;
  }
  &__name {
    font-weight: $font-weight-semibold; font-size: $font-size-base;
    color: $text-primary; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  &__progress { font-size: $font-size-xs; color: $text-muted; }
}

// 进度环
.progress-ring {
  position: relative; width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;

  svg { position: absolute; inset: 0; width: 100%; height: 100%; }

  &__time {
    font-family: $font-family-mono;
    font-size: 10px; font-weight: $font-weight-bold;
    color: $text-secondary; position: relative; z-index: 1;
    &.warning { color: $danger; animation: pulse 1s ease-in-out infinite; }
  }
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.end-btn {
  padding: 7px $spacing-md;
  border-radius: $border-radius-full;
  border: 1.5px solid $danger;
  background: transparent;
  color: $danger; font-size: $font-size-sm; font-weight: $font-weight-semibold;
  cursor: pointer; font-family: $font-family-base;
  transition: all $transition-fast;
  &:hover { background: $danger-bg; }
}

// ---- 消息流 ----
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-base;
  scroll-behavior: smooth;

  &::-webkit-scrollbar { width: 3px; }
  &::-webkit-scrollbar-thumb { background: $gray-300; border-radius: 2px; }
}

.session-start-tip {
  display: flex; align-items: center; gap: $spacing-md;
  margin: $spacing-base 0;
  font-size: $font-size-xs; color: $text-muted;

  &__line { flex: 1; height: 1px; background: $border-color; }
}

.messages-list { display: flex; flex-direction: column; gap: $spacing-base; }

.message-item {
  display: flex;
  gap: $spacing-sm;
  align-items: flex-end;
  animation: msgIn 0.3s ease both;

  &--user {
    flex-direction: row-reverse;
  }
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 16px;

  &--ai { background: $primary-bg; border: 1.5px solid rgba(67,56,202,0.15); }
  &--user {
    background: $gradient-primary;
    color: white; font-size: $font-size-base; font-weight: $font-weight-bold;
  }
}

.message-bubble-wrap {
  display: flex; flex-direction: column; gap: 4px;
  max-width: calc(100% - 80px);

  .message-item--user & { align-items: flex-end; }
  .message-item--ai & { align-items: flex-start; }
}

.followup-badge {
  display: inline-flex; align-items: center; gap: 4px;
  background: $warning-bg; color: darken($warning, 20%);
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 2px 8px; border-radius: $border-radius-full;
  border: 1px solid rgba($warning, 0.3);
}

.message-bubble {
  padding: $spacing-md $spacing-base;
  border-radius: $border-radius-lg;
  max-width: 100%;

  &--ai {
    background: white;
    border: 1px solid $border-color;
    border-bottom-left-radius: $border-radius-sm;
    box-shadow: $shadow-sm;
  }

  &--user {
    background: $gradient-primary;
    color: white;
    border-bottom-right-radius: $border-radius-sm;
    box-shadow: $shadow-primary;
  }
}

.message-text {
  font-size: $font-size-base;
  line-height: $line-height-relaxed;
  word-break: break-word;
  white-space: pre-wrap;

  .message-bubble--ai & { color: $text-primary; }
  .message-bubble--user & { color: white; }
}

.message-time {
  font-size: $font-size-xs; color: $text-muted;
  padding: 0 4px;
}

// AI 思考动画
.thinking-row { padding-bottom: $spacing-sm; }

.thinking-bubble {
  background: white;
  border: 1px solid $border-color;
  border-radius: $border-radius-lg;
  border-bottom-left-radius: $border-radius-sm;
  padding: $spacing-md $spacing-base;
  display: flex; gap: 5px; align-items: center;
  box-shadow: $shadow-sm;
}

.thinking-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: $primary-light;
  animation: thinking 1.2s ease-in-out infinite;
  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes thinking {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

// 面试结束
.session-end-tip {
  display: flex; flex-direction: column; align-items: center;
  padding: $spacing-2xl;
  margin-top: $spacing-lg;
  background: white; border-radius: $border-radius-lg;
  border: 1px solid $border-color;
  box-shadow: $shadow;
  text-align: center;
  gap: $spacing-sm;

  &__icon { font-size: 36px; }
  &__title { font-size: $font-size-lg; font-weight: $font-weight-bold; color: $text-primary; }
  &__sub { font-size: $font-size-sm; color: $text-muted; }
  &__spinner {
    width: 24px; height: 24px; border-radius: 50%;
    border: 3px solid $primary-bg;
    border-top-color: $primary;
    animation: spin 0.8s linear infinite;
    margin-top: $spacing-sm;
  }
}

@keyframes spin { to { transform: rotate(360deg); } }

// ---- 输入区域 ----
.input-area {
  background: white;
  border-top: 1px solid $border-color;
  padding: $spacing-sm $spacing-base;
  padding-bottom: calc(#{$spacing-sm} + env(safe-area-inset-bottom));
  box-shadow: 0 -4px 16px rgba(0,0,0,0.06);
  flex-shrink: 0;

  &.disabled { opacity: 0.6; pointer-events: none; }
}

// 录音状态条
.recording-bar {
  display: flex; align-items: center; gap: $spacing-sm;
  background: linear-gradient(135deg, #FEE2E2, #FFF5F5);
  border: 1px solid rgba($danger, 0.2);
  border-radius: $border-radius;
  padding: $spacing-sm $spacing-md;
  margin-bottom: $spacing-sm;

  &__wave { display: flex; align-items: center; gap: 3px; }
  &__text { flex: 1; font-size: $font-size-xs; color: $danger; }
  &__time { font-family: $font-family-mono; font-size: $font-size-sm; color: $danger; font-weight: $font-weight-bold; }
}

.wave-bar {
  width: 3px; border-radius: 2px;
  background: $danger;
  animation: wave 0.8s ease-in-out infinite alternate;

  @for $i from 1 through 5 {
    &:nth-child(#{$i}) {
      height: #{6 + $i * 3}px;
      animation-delay: #{$i * 0.1}s;
    }
  }
}

@keyframes wave { from { transform: scaleY(0.3); } to { transform: scaleY(1); } }

.slide-up-enter-active { animation: slideUp 0.2s ease both; }
.slide-up-leave-active { animation: slideUp 0.15s ease reverse both; }
@keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.input-row {
  display: flex;
  align-items: flex-end;
  gap: $spacing-sm;
}

.voice-btn {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid $border-color; background: white;
  cursor: pointer; flex-shrink: 0;
  transition: all $transition-base;
  color: $text-secondary;
  svg { width: 20px; height: 20px; }

  &:hover { border-color: $primary; color: $primary; background: $primary-bg; }
  &.active {
    background: $danger; border-color: $danger; color: white;
    animation: recordPulse 1.5s ease-in-out infinite;
  }
}

@keyframes recordPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba($danger, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba($danger, 0); }
}

.textarea-wrapper {
  flex: 1;
  position: relative;
}

.input-textarea {
  width: 100%;
  min-height: 44px;
  max-height: 120px;
  padding: 11px $spacing-md;
  padding-right: $spacing-md;
  border: 1.5px solid $border-color;
  border-radius: $border-radius;
  font-family: $font-family-base;
  font-size: $font-size-base;
  line-height: $line-height-normal;
  color: $text-primary;
  resize: none;
  outline: none;
  background: $gray-50;
  transition: all $transition-base;
  display: block;

  &::placeholder { color: $text-muted; }
  &:focus { border-color: $primary; background: white; box-shadow: 0 0 0 3px rgba(67,56,202,0.1); }
}

.input-hint {
  display: block;
  font-size: $font-size-xs;
  color: $text-muted;
  margin-top: 4px;
  text-align: right;
  padding-right: 2px;
}

.send-btn {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: none; background: $gray-200; cursor: pointer;
  flex-shrink: 0; color: $text-muted;
  transition: all $transition-base;
  svg { width: 18px; height: 18px; }

  &.ready {
    background: $gradient-primary;
    color: white;
    box-shadow: $shadow-primary;
    &:hover { transform: scale(1.05); }
    &:active { transform: scale(0.96); }
  }
  &:disabled:not(.ready) { cursor: not-allowed; }
}

// ---- 弹窗 ----
.modal-overlay {
  position: fixed; inset: 0;
  background: $bg-overlay;
  z-index: 200;
  display: flex; align-items: center; justify-content: center;
  padding: $spacing-xl;
}

.modal-sheet {
  background: white;
  border-radius: $border-radius-xl;
  width: 100%; max-width: 320px;
  overflow: hidden;
  box-shadow: $shadow-lg;
}

.modal-body-centered {
  padding: $spacing-2xl $spacing-xl;
  text-align: center;
}

.confirm-icon { font-size: 40px; margin-bottom: $spacing-md; }
.confirm-title {
  font-family: $font-family-display;
  font-size: $font-size-xl; font-weight: $font-weight-bold;
  color: $text-primary; margin-bottom: $spacing-sm;
}
.confirm-desc { font-size: $font-size-sm; color: $text-secondary; line-height: $line-height-relaxed; margin-bottom: $spacing-xl; }

.confirm-actions {
  display: flex; gap: $spacing-md;
  .btn { flex: 1; height: 46px; display: flex; align-items: center; justify-content: center; gap: $spacing-sm; }
}

.btn-spinner {
  width: 15px; height: 15px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  &--danger { border-color: rgba($danger, 0.3); border-top-color: $danger; }
}



/* ---- 面试结束遮罩 ---- */
.ending-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.ending-card {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 24px;
  padding: 40px 32px;
  width: 300px;
  text-align: center;
  box-shadow: 0 24px 60px rgba(0,0,0,0.4);
}
.ending-icon-wrap {
  position: relative;
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
}
.ending-spin-ring {
  position: absolute;
  inset: 0;
  animation: spin 2s linear infinite;
}
.ending-emoji {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}
.ending-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
}
.ending-sub {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  margin: 0 0 20px;
}
.ending-progress-track {
  height: 4px;
  background: rgba(255,255,255,0.15);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}
.ending-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #818cf8, #c4b5fd);
  border-radius: 2px;
  animation: progress-slide 25s linear forwards;
}
.ending-hint {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  margin: 0;
}

/* 遮罩出现动画 */
.ending-fade-enter-active { transition: opacity 0.4s ease; }
.ending-fade-leave-active { transition: opacity 0.3s ease; }
.ending-fade-enter-from, .ending-fade-leave-to { opacity: 0; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes progress-slide { from { width: 0 } to { width: 95% } }

.modal-enter-active { animation: modalIn 0.3s ease both; }
.modal-leave-active { animation: modalOut 0.2s ease both; }
@keyframes modalIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
@keyframes modalOut { from { opacity: 1; } to { opacity: 0; } }

.fade-enter-active { animation: fadeIn 0.3s ease both; }
.fade-leave-active { animation: fadeIn 0.2s ease reverse both; }

.message-enter-active { animation: msgIn 0.3s ease both; }
</style>