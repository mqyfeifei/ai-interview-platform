<!--
  =============================================
  frontend/src/views/interview/VoiceInterviewSession.vue
  语音面试会话页组件
  ============================================= -->
<template>
  <div class="interview-page">
    <!-- 顶部状态栏 -->
    <header class="interview-header">
      <div class="interview-header__left">
        <button class="header-end-btn" @click="isFinished ? handleBack() : showBackConfirm = true">
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
            <p class="job-info__progress">
              <span class="voice-mode-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                </svg>
                语音模式
              </span>
            </p>
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
              :stroke="timerWarning ? '#EF4444' : '#7C6FF7'"
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
        <button class="end-btn" @click="showEndConfirm = true" :disabled="isFinished || isEnding">结束</button>
      </div>
    </header>

    <!-- 主内容区 - 左右分屏 -->
    <div class="interview-body">
      <!-- 左边：语音转文字对话框 -->
      <div class="left-panel">
        <div class="messages-container" ref="messagesContainer">
          <!-- 面试开始提示 -->
          <div class="messages-inner"> 
            <div class="session-start-tip">
              <div class="session-start-tip__line" />
              <span>面试正式开始</span>
              <div class="session-start-tip__line" />
            </div>
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
                <div
                  v-if="msg.role === 'ai'"
                  class="message-text markdown-body"
                  v-html="renderMarkdown(msg.content)"
                />
                <p v-else class="message-text">{{ msg.content }}</p>
                </div>

                <span class="message-time" v-show="msg.content">{{ formatTime(msg.timestamp) }}</span>
              </div>

              <!-- 用户头像 -->
              <div v-if="msg.role === 'user'" class="message-avatar message-avatar--user">
                <img v-if="userAvatarUrl" :src="userAvatarUrl" class="avatar-img" alt="avatar" />
                <span v-else>{{ userAvatarLetter }}</span>
              </div>
            </div>
          </transition-group>

          <!-- AI 思考中动画 -->
          <transition name="fade">
            <div v-if="isLoading && !hasStreamingMessage && !isEnding" class="message-item message-item--ai thinking-row">
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

          <transition name="fade">
            <div v-if="isEnding && !isFinished" class="session-end-progress">
              <div class="session-end-spinner" />
              <p class="session-end-progress-text">面试报告生成中，请耐心等待</p>
            </div>
          </transition>

          <!-- 面试结束提示 -->
          <div v-if="isFinished" class="session-end-tip">
            <div class="session-end-tip__icon">🎉</div>
            <p class="session-end-tip__title">面试已完成</p>
            <p class="session-end-tip__sub">面试报告已生成，且已保存在历史记录中</p>
                <transition name="fade">
                <button class="view-report-btn" @click="goToReport">
                  查看面试报告 →
                </button>
              </transition>
          </div>

          <div style="height: 16px;" />
        </div>
      </div>

      <!-- 右边：语音聊天动画和输入区 -->
      <div class="right-panel">
        <div class="voice-animation-container">
          <!-- 语音动画 -->
          <div class="voice-animation">
            <!-- 面试官动画 -->
            <div class="voice-character voice-character--ai">
              <div class="character-avatar">
                <span>🤖</span>
              </div>
              <div class="character-name">AI 面试官</div>
              <div class="voice-wave" v-if="isAISpeaking">
                <span v-for="n in 5" :key="n" class="wave-bar" :style="{ animationDelay: n * 0.1 + 's' }" />
              </div>
            </div>

            <!-- 连接线 -->
            <div class="voice-connection">
              <div class="connection-line" :class="{ active: isRecording || isAISpeaking }"></div>
            </div>

            <!-- 候选人动画 -->
            <div class="voice-character voice-character--user">
              <div class="character-avatar">
                <img v-if="userAvatarUrl" :src="userAvatarUrl" class="avatar-img" alt="avatar" />
                <span v-else>{{ userAvatarLetter }}</span>
              </div>
              <div class="character-name">{{ userName || '我' }}</div>
              <div class="voice-wave" v-if="isRecording">
                <span v-for="n in 5" :key="n" class="wave-bar" :style="{ animationDelay: n * 0.1 + 's' }" />
              </div>
            </div>
          </div>

          <!-- 语音状态提示 -->
          <div class="voice-status">
            <div v-if="isRecording" class="status-item status-item--recording">
              <span class="status-dot"></span>
              <span>正在录音...</span>
              <span class="status-time">{{ recordingTime }}s</span>
            </div>
            <div v-else-if="isAISpeaking" class="status-item status-item--ai-speaking">
              <span class="status-dot"></span>
              <span>AI 正在说话...</span>
            </div>
            <div v-else class="status-item status-item--waiting">
              <span class="status-dot"></span>
              <span>等待中...</span>
            </div>
          </div>

          <!-- 语音控制按钮 -->
          <div class="voice-controls">
            <button
              :class="['voice-control-btn', { active: isRecording }]"
              @click="toggleRecording"
              :disabled="isFinished || isLoading || isEnding"
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
              {{ isRecording ? '停止录音' : '开始录音' }}
            </button>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-area" :class="{ disabled: isFinished || isLoading || isEnding }">
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
          <div v-if="isSending" class="transcribing-tip">
            📡 语音发送中，请稍候...
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
                :disabled="isFinished || isLoading || isEnding"
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
              :disabled="!inputText.trim() || isLoading || isFinished || isEnding"
              @click="handleSend"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 结束确认弹窗 -->
    <transition name="modal">
      <div v-if="showEndConfirm" class="modal-overlay" @click.self="showEndConfirm = false">
        <div class="modal-sheet">
          <div class="modal-header-bar modal-header-bar--danger">
            <h2 class="modal-header-title">确认结束面试？</h2>
            <p class="modal-header-sub">结束后将立即生成面试报告</p>
          </div>
          <div class="modal-body">
            <ul class="rules-list">
              <li><span class="rule-dot rule-dot--orange" />当前面试进度将被保存</li>
              <li><span class="rule-dot rule-dot--blue" />AI 将根据你的回答生成专属评估报告</li>
              <li><span class="rule-dot rule-dot--purple" />报告生成通常需要 10 ~ 30 秒</li>
            </ul>
            <div class="modal-actions">
              <button class="btn-cancel" @click="showEndConfirm = false">继续面试</button>
              <button class="btn-confirm btn-confirm--danger" :disabled="endingInterview" @click="handleEnd">
                <span v-if="endingInterview" class="btn-spinner" />
                {{ endingInterview ? '结束中...' : '确认结束' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
    <!-- 返回确认弹窗 -->
    <transition name="modal">
      <div v-if="showBackConfirm" class="modal-overlay" @click.self="showBackConfirm = false">
        <div class="modal-sheet">
          <div class="modal-header-bar modal-header-bar--danger">
            <h2 class="modal-header-title">确认离开面试？</h2>
            <p class="modal-header-sub">离开后本次面试进度将丢失</p>
          </div>
          <div class="modal-body">
            <ul class="rules-list">
              <li><span class="rule-dot rule-dot--danger" />本次面试记录不会被保存</li>
              <li><span class="rule-dot rule-dot--orange" />不会生成面试报告</li>
              <li><span class="rule-dot rule-dot--blue" />可随时重新开始新的面试</li>
            </ul>
            <div class="modal-actions">
              <button class="btn-cancel" @click="showBackConfirm = false">继续面试</button>
              <button class="btn-confirm btn-confirm--danger" @click="handleBack">确认离开</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { marked } from 'marked'
import { sendVoiceAnswerStream } from '@/api/interview'  // ✅ 导入语音面试专用接口

export default {
  name: 'VoiceInterviewSession',
  data() {
    return {
      inputText: '',
      isRecording: false,
      recordingTime: 0,
      showEndConfirm: false,
      endingInterview: false,
      // 计时相关
      questionTimer: 180, // 语音模式3分钟
      timerInterval: null,
      recordingInterval: null,
      // 语音识别
      mediaRecorder: null,
      audioChunks: [],
      // 语音转写状态
      isTranscribing: false,
      showBackConfirm: false,
      isSending: false,
      autoRecordTimer: null,
      
      // ==================== WebSocket 实时 ASR ====================
      socket: null,
      voiceId: null,
      sendSeq: 0,
      audioContext: null,
      processor: null,
      inputNode: null,
      globalStream: null,
      lastSendTs: 0,
      MIN_SEND_INTERVAL_MS: 80,  // 两次发送最小间隔
      ENABLE_VAD: true,           // 启用语音活动检测
      VAD_THRESHOLD: 0.01,        // VAD 阈值
      sampleRate: 16000,          // 目标采样率
      cleanupTimer: null,         // 清理资源定时器
      asrPollingTimer: null,       // ASR轮询定时器
      
      // ==================== TTS 音频队列管理 ====================
      ttsAudioQueue: [],           // 音频播放队列
      isPlayingTTS: false,         // 是否正在播放TTS
      currentAudio: null           // 当前播放的 Audio 对象
      // ==========================================================
      // ============================================================
    }
  },
  computed: {
    ...mapGetters('user', ['userName','userInfo']),
    ...mapGetters('interview', [
      'selectedJob', 'messages', 'questionIndex',
      'isEnding',
      'totalQuestions', 'isFinished', 'isLoading', 'isAISpeaking', 'reportId'
    ]),
    questionTimeLimit() {
      return 180 // 语音3分钟
    },
    userAvatarLetter() {
      return (this.userName || '我').charAt(0)
    },
    userAvatarUrl() {
      return this.userInfo?.avatar || this.userInfo?.avatarUrl || null
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
      return this.progressCircle * (1 - this.questionTimer / this.questionTimeLimit)
    },
    hasStreamingMessage() {
      return this.messages.some(m => m.streaming && m.content.length > 0)
    }
  },
  async created() {
    this.$store.commit('interview/SET_VOICE_MODE', true)

    // 如果没有选择岗位，重定向到岗位选择
    if (!this.selectedJob) {
      this.$router.replace('/interview/select')
      return
    }
    // 如果没有进行中的会话，启动
    if (!this.$store.getters['interview/currentSession']) {
      this.questionTimer = this.questionTimeLimit
      await this.startSession()
    }
    this.startQuestionTimer()
    
    // ==================== 初始化 WebSocket 连接 ====================
    this.initWebSocket()
    // ==============================================================
  },
  beforeUnmount() {
    this.clearTimers()
    if (this._progressTimer) clearInterval(this._progressTimer)
    
    // ==================== 清理 WebSocket 和音频资源 ====================
    this.disconnectWebSocket()
    this.cleanupAudioResources()
    this.clearTTSQueue()  // ✅ 清空TTS队列
    // ==================================================================
  },
  watch: {
    // 切换到新问题时重置计时器
    questionIndex(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.questionTimer = this.questionTimeLimit
      }
    },
    // isEnding 一旦为 true 立即停止计时器
    isEnding(val) {
      if (val) {
        this.clearTimers()
      }
    },
    // 消息更新自动滚底
    messages() {
      this.$nextTick(this.scrollToBottom)
    },
    isLoading(val) {
      this.$nextTick(this.scrollToBottom)
      this.tryScheduleAutoRecording()
    },
    isAISpeaking() {
      this.tryScheduleAutoRecording()
    }
  },
  methods: {
    ...mapActions('interview', ['startSession', 'submitAnswer', 'endInterview']),

    /**
     * 将TTS音频加入播放队列
     */
    enqueueTTSAudio(audioB64) {
      this.ttsAudioQueue.push(audioB64)
      console.log('[TTS] 音频入队, 队列长度:', this.ttsAudioQueue.length)
      
      // 如果当前没有播放，开始播放队列
      if (!this.isPlayingTTS) {
        this.playNextTTSAudio()
      }
    },
    
    /**
     * 播放队列中的下一个音频
     */
    playNextTTSAudio() {
      if (this.ttsAudioQueue.length === 0) {
        this.isPlayingTTS = false
        this.$store.commit('interview/SET_AI_SPEAKING', false)
        console.log('[TTS] 队列播放完毕')
        
        // ✅ 关键：TTS 播放完毕后，延迟800ms自动开始下一轮录音
        setTimeout(() => {
          console.log('[TTS] 准备自动开始下一轮录音')
          this.tryScheduleAutoRecording()
        }, 800)
        
        return
      }
      
      this.isPlayingTTS = true
      const audioB64 = this.ttsAudioQueue.shift()
      
      // 停止之前的音频
      if (this.currentAudio) {
        this.currentAudio.pause()
        this.currentAudio = null
      }
      
      // 创建新的 Audio 对象
      const audioSrc = `data:audio/mp3;base64,${audioB64}`
      const audio = new Audio(audioSrc)
      this.currentAudio = audio
      
      audio.play()
        .then(() => {
          console.log('[TTS] 开始播放音频片段')
        })
        .catch((err) => {
          console.error('[TTS] 播放失败:', err)
          // 即使失败也继续播放下一个
          this.playNextTTSAudio()
        })
      
      // 监听播放结束
      audio.onended = () => {
        console.log('[TTS] 音频片段播放完成')
        this.currentAudio = null
        // 播放下一个
        this.playNextTTSAudio()
      }
      
      // 监听错误
      audio.onerror = (err) => {
        console.error('[TTS] 音频错误:', err)
        this.currentAudio = null
        this.playNextTTSAudio()
      }
    },
    
    /**
     * 清空TTS音频队列并停止播放
     */
    clearTTSQueue() {
      this.ttsAudioQueue = []
      this.isPlayingTTS = false
      if (this.currentAudio) {
        this.currentAudio.pause()
        this.currentAudio = null
      }
      this.$store.commit('interview/SET_AI_SPEAKING', false)
      console.log('[TTS] 队列已清空')
    },

    isMeaningfulVoiceText(text) {
      const t = (text || '').trim()
      if (!t) return false
      if (t.length <= 2) return false
      return !/^(好|好的|嗯|嗯嗯|嗯哼|哦|噢|啊|行|可以|是|对|没了|没有了|不知道|ok|okay|yes|no|[，。！？、\s]+)$/i.test(t)
    },

    async handleSend() {
      const text = this.inputText.trim()
      // ✅ 修复：移除 isTranscribing 检查，语音模式下不需要
      if (!text || this.isLoading || this.isFinished) {
        console.log('[语音面试] handleSend 被跳过:', { hasText: !!text, isLoading: this.isLoading, isFinished: this.isFinished })
        return
      }
      
      console.log('[语音面试] ✅ 开始提交答案:', text.substring(0, 50))
      
      // ✅ 使用专用的语音面试接口
      this.isSending = true
      this.inputText = ''
      this.resetTextarea()
      this.questionTimer = this.questionTimeLimit
      
      const sessionId = this.$store.getters['interview/currentSession']?.sessionId
      if (!sessionId) {
        console.error('[语音面试] 未找到会话ID')
        this.isSending = false
        return
      }
      
      // 添加用户消息到聊天记录
      this.$store.commit('interview/ADD_MESSAGE', {
        role: 'user',
        content: text,
        timestamp: new Date().toISOString()
      })
      
      // ✅ 添加AI流式消息占位符（关键！）
      this.$store.commit('interview/ADD_MESSAGE', {
        role: 'ai',
        content: '',
        timestamp: new Date().toISOString(),
        streaming: true  // 标记为流式消息
      })
      
      // 调用语音专用接口
      sendVoiceAnswerStream(sessionId, text, {
        onChunk: (chunk) => {
          this.$store.commit('interview/APPEND_AI_CHUNK', chunk)
        },
        onAudio: (audioB64) => {
          // ✅ 将TTS音频加入播放队列
          console.log('[语音面试] 收到TTS音频片段, 长度:', audioB64.length)
          this.enqueueTTSAudio(audioB64)
        },
        onFinish: () => {
          console.log('[语音面试] AI主动结束面试，开始生成报告')
          this.isSending = false
          // ✅ 标记流式消息完成
          this.$store.commit('interview/MARK_STREAM_DONE')
          this.$store.commit('interview/SET_LOADING', false)
          
          // ✅ 清空TTS队列
          this.clearTTSQueue()
          
          // ✅ 关键：直接调用 endInterview 生成报告（它会设置 isFinished）
          this.endInterview().then(() => {
            console.log('[语音面试] 报告生成成功, reportId:', this.reportId)
          }).catch((err) => {
            console.error('[语音面试] 报告生成失败:', err)
          })
        },
        onStreamEnd: () => {
          console.log('[语音面试] 流式响应结束')
          this.isSending = false
          // ✅ 标记流式消息完成
          this.$store.commit('interview/MARK_STREAM_DONE')
          this.$store.commit('interview/SET_LOADING', false)
          
          // ✅ 关键：不立即开始录音，等待 TTS 音频播放完毕
          // playNextTTSAudio() 会在队列清空时自动触发 tryScheduleAutoRecording()
          console.log('[语音面试] 等待 TTS 音频播放完毕...')
        },
        onError: (error) => {
          console.error('[语音面试] 错误:', error)
          alert('发送失败：' + error.message)
          this.isSending = false
        },
        voice: null  // 使用默认音色
      })
    },
    goToReport() {
      this.$router.push(`/interview/report/${this.reportId}`)
    },
    async handleEnd() {
      console.log('[语音面试] 用户主动结束面试')
      this.endingInterview = true
      this.showEndConfirm = false
      
      // ✅ 关键：不立即清空TTS队列，等待当前音频播放完毕
      // isSending 设为 false，允许 endInterview 调用
      this.isSending = false
      
      try {
        await this.endInterview()
        console.log('[语音面试] 报告生成成功, reportId:', this.reportId)
        
        // ✅ 报告生成成功后，清空TTS队列（让剩余音频继续播放）
        // 注意：不清空队列，让 playNextTTSAudio 自然播放完
      } catch (err) {
        console.error('[语音面试] 报告生成失败:', err)
        alert('报告生成失败：' + err.message)
      } finally {
        this.endingInterview = false
      }
    },

    handleBack() {
      this.showBackConfirm = false
      this.$router.replace('/interview/select')
    },
    renderMarkdown(text) {
      if (!text) return '';
      marked.setOptions({ breaks: false });
      const cleaned = text
        .replace(/\r\n|\r/g, '\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
      let html = marked.parse(cleaned);
      html = html
        .replace(/<p><br\s*\/?><\/p>/gi, '')
        .replace(/<p>\s*<\/p>/gi, '')
        .replace(/<br\s*\/?>\s*(<\/p>)/gi, '$1')
        .replace(/<li>\s*<p>([\s\S]*?)<\/p>\s*<\/li>/gi, '<li>$1</li>');
      return html;
    },
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
          // 超时自动发送
          this.questionTimer = -1
          this.autoSubmitOnTimeout()
        }
      }, 1000)
    },

    autoSubmitOnTimeout() {
      if (this.isLoading || this.isFinished || this.isTranscribing) {
        this.questionTimer = this.questionTimeLimit
        return
      }
      const text = this.inputText.trim() || '（超时，跳过此题）'
      this.inputText = ''
      this.resetTextarea()
      this.questionTimer = this.questionTimeLimit
      this.submitAnswer(text)
    },

    clearTimers() {
      if (this.timerInterval) { clearInterval(this.timerInterval); this.timerInterval = null }
      if (this.recordingInterval) { clearInterval(this.recordingInterval); this.recordingInterval = null }
      if (this.autoRecordTimer) { clearTimeout(this.autoRecordTimer); this.autoRecordTimer = null }
    },

    tryScheduleAutoRecording() {
      if (this.autoRecordTimer) {
        clearTimeout(this.autoRecordTimer)
        this.autoRecordTimer = null
      }

      if (
        !this.isLoading &&
        !this.isAISpeaking &&
        !this.isFinished &&
        !this.isEnding &&
        !this.isRecording &&
        !this.isSending
      ) {
        this.autoRecordTimer = setTimeout(() => {
          this.autoRecordTimer = null
          if (
            !this.isLoading &&
            !this.isAISpeaking &&
            !this.isFinished &&
            !this.isEnding &&
            !this.isRecording &&
            !this.isSending
          ) {
            this.startRecording()
          }
        }, 800)
      }
    },

    async toggleRecording() {
      if (this.isRecording) {
        this.stopRecording()
      } else {
        await this.startRecording()
      }
    },

    async startRecording() {
      if (this.isSending) {
        alert('正在发送上一段语音，请稍等...')
        return
      }
      
      // ==================== 使用 WebSocket 实时流式传输 ====================
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        // 生成唯一的 voiceId
        this.voiceId = String(Date.now())
        this.sendSeq = 0
        
        // 创建 AudioContext
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        this.globalStream = stream
        this.inputNode = this.audioContext.createMediaStreamSource(stream)
        
        // 创建 ScriptProcessor（用于实时捕获音频数据）
        const bufferSize = 2048  // 缓冲区大小（越小延迟越低，但 CPU 占用越高）
        this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1)
        
        this.processor.onaudioprocess = (e) => {
          if (!this.isRecording) return
          
          const floatData = e.inputBuffer.getChannelData(0)
          // 立即发送音频分片（内部有节流控制）
          this.sendChunkImmediate(new Float32Array(floatData))
        }
        
        // 连接音频节点
        this.inputNode.connect(this.processor)
        this.processor.connect(this.audioContext.destination)
        
        // 更新状态
        this.isRecording = true
        this.recordingTime = 0
        this.recordingInterval = setInterval(() => {
          this.recordingTime++
        }, 1000)
        
        console.log('[ASR] 开始实时录音，voiceId:', this.voiceId)
        
      } catch (err) {
        console.error('[ASR] 麦克风权限被拒绝:', err)
        alert('无法访问麦克风，请检查浏览器权限设置。')
      }
      // ===================================================================
    },

    stopRecording() {
      // ==================== 发送最终标记触发后端识别 ====================
      if (this.isRecording) {
        // 发送结束标记
        this.sendFinalMarker()
        
        // 停止录音
        this.isRecording = false
        if (this.recordingInterval) {
          clearInterval(this.recordingInterval)
          this.recordingInterval = null
        }
        
        // ✅ 关键修复：不清理音频资源，保持 WebSocket 连接
        // this.cleanupAudioResources()  ← 注释掉，避免触发连接断开
        
        console.log('[ASR] 停止录音，等待识别结果...')
        
        // ✅ 启动轮询，每500ms检查一次ASR结果
        this.asrPollingTimer = setInterval(() => {
          this.pollAsrResult()
        }, 500)
        
        // ✅ 设置超时，如果10秒内没收到结果，再清理资源
        setTimeout(() => {
          console.log('[ASR] 超时清理音频资源')
          this.cleanupAudioResources()
          this.stopAsrPolling()
        }, 10000)
      }
      // ==================================================================
    },

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
    },
    
    // ==================== WebSocket 实时 ASR 方法 ====================
    
    /**
     * 初始化 WebSocket 连接
     */
    initWebSocket() {
      if (window.io) {
        this.connectSocket()
      } else {
        // 动态加载 Socket.IO 客户端
        this.loadSocketIO()
      }
    },
    
    /**
     * 动态加载 Socket.IO CDN
     */
    loadSocketIO() {
      const script = document.createElement('script')
      script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js'
      script.onload = () => {
        console.log('[ASR] Socket.IO 客户端加载成功')
        this.connectSocket()
      }
      script.onerror = () => {
        console.error('[ASR] Socket.IO 客户端加载失败')
      }
      document.head.appendChild(script)
    },
    
    /**
     * 连接 Socket.IO 服务器
     */
    connectSocket() {
      // 防止多次初始化
      if (this.socket) {
        console.log('[ASR] 断开旧连接')
        this.socket.disconnect();
        this.socket = null;
      }
      
      const SERVER_URL = 'http://localhost:5000'; // 必须和后端一致
      console.log('[ASR] 正在连接 Socket.IO:', SERVER_URL)
      
      this.socket = window.io(SERVER_URL, { 
        transports: ['websocket', 'polling'],  // ✅ 允许降级到 polling
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        timeout: 20000,
        forceNew: true  // ✅ 强制创建新连接
      });

      // 全局监听所有事件，便于调试
      this.socket.onAny((event, ...args) => {
        console.log('[SOCKET.IO] 事件:', event, JSON.stringify(args).substring(0, 200))
      });

      this.socket.on('connect', () => {
        console.log('[ASR] ✅ WebSocket 连接成功, ID:', this.socket.id);
      });

      this.socket.on('disconnect', (reason) => {
        console.log('[ASR] ❌ WebSocket 断开, 原因:', reason);
      });
      
      this.socket.on('connect_error', (error) => {
        console.error('[ASR] ❌ 连接错误:', error);
      });
      
      this.socket.on('reconnect', (attemptNumber) => {
        console.log('[ASR] 🔄 重连成功, 尝试次数:', attemptNumber);
      });
      
      this.socket.on('reconnect_failed', () => {
        console.error('[ASR] ❌ 重连失败');
      });

      // ✅ 关键：接收实时 partial 结果并更新输入框
      this.socket.on('asr_partial', (data) => {
        console.log('[ASR] Partial:', data);
        if (data.text) {
          this.inputText = data.text;
          this.$nextTick(() => this.autoResize());
        }
      });

      // ✅ 关键：接收 final 结果
      this.socket.on('asr_final', (data) => {
        console.log('[ASR] Final:', data);
        
        // ✅ 清理保活定时器
        if (this.asrKeepAliveTimer) {
          clearInterval(this.asrKeepAliveTimer)
          this.asrKeepAliveTimer = null
          console.log('[ASR] 已清理保活定时器')
        }
        
        if (this.cleanupTimer) {
          clearTimeout(this.cleanupTimer);
          this.cleanupTimer = null;
        }
        this.cleanupAudioResources();
        if (data.text) {
          this.inputText = data.text;
          this.$nextTick(() => this.autoResize());
          setTimeout(() => {
            if (this.inputText.trim() && !this.isLoading && !this.isFinished && !this.isSending) {
              this.handleSend();
            }
          }, 500);
        }
      });

      this.socket.on('asr_error', (data) => {
        console.error('[ASR] Error:', data);
        alert('语音识别出错：' + (data.error || '未知错误'));
      });

      // 调试：服务器确认收到 end 包
      this.socket.on('asr_server_ack', (data) => {
        console.log('[ASR] server ack:', data);
      });

      // 回退广播（如果定向emit未到达）
      this.socket.on('asr_final_broadcast', (data) => {
        console.log('[ASR] final_broadcast received:', data);
        if (data && data.text) {
          this.inputText = data.text;
          this.$nextTick(() => this.autoResize());
          // 不自动提交广播结果，等待定向final或用户确认
        }
      });
    },
    
    /**
     * 断开 WebSocket 连接
     */
    disconnectWebSocket() {
      try {
        if (this.socket) {
          this.socket.disconnect()
          this.socket = null
        }
      } catch (e) {
        console.error('[ASR] 断开 WebSocket 失败:', e)
      }
    },
    
    /**
     * 清理音频资源
     */
    cleanupAudioResources() {
      try {
        if (this.processor) {
          this.processor.disconnect()
          this.processor = null
        }
        if (this.inputNode) {
          this.inputNode.disconnect()
          this.inputNode = null
        }
        if (this.globalStream) {
          this.globalStream.getTracks().forEach(track => track.stop())
          this.globalStream = null
        }
        if (this.audioContext && this.audioContext.state !== 'closed') {
          this.audioContext.close()
          this.audioContext = null
        }
      } catch (e) {
        console.error('[ASR] 清理音频资源失败:', e)
      }
    },
    
    /**
     * 下采样音频（降低采样率到 16kHz）
     */
    downsampleBuffer(buffer, inputSampleRate, outSampleRate) {
      if (outSampleRate === inputSampleRate) {
        return buffer
      }
      const sampleRateRatio = inputSampleRate / outSampleRate
      const newLength = Math.round(buffer.length / sampleRateRatio)
      const result = new Float32Array(newLength)
      let offsetResult = 0
      let offsetBuffer = 0
      
      while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
        let accum = 0
        let count = 0
        
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
          accum += buffer[i]
          count++
        }
        
        result[offsetResult] = accum / count
        offsetResult++
        offsetBuffer = nextOffsetBuffer
      }
      
      return result
    },
    
    /**
     * Float32 转 Int16 PCM
     */
    floatTo16BitPCM(input) {
      const output = new DataView(new ArrayBuffer(input.length * 2))
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]))
        output.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
      }
      return output.buffer
    },
    
    /**
     * 发送音频分片（带VAD和节流）
     */
    sendChunkImmediate(float32Chunk) {
      const now = Date.now()
      if (now - this.lastSendTs < this.MIN_SEND_INTERVAL_MS) return
      this.lastSendTs = now
      // 简单VAD
      if (this.ENABLE_VAD) {
        let sum = 0
        for (let i = 0; i < float32Chunk.length; i++) sum += float32Chunk[i] * float32Chunk[i]
        const rms = Math.sqrt(sum / float32Chunk.length)
        if (rms < this.VAD_THRESHOLD) return
      }
      const inputSampleRate = this.audioContext.sampleRate
      const out = this.downsampleBuffer(float32Chunk, inputSampleRate, this.sampleRate)
      const pcm16Buffer = this.floatTo16BitPCM(out)
      const b64 = this.arrayBufferToBase64(pcm16Buffer)
      const payload = { voice_id: this.voiceId, seq: this.sendSeq++, chunk_b64: b64, is_end: 0 }
      try {
        this.socket && this.socket.emit('audio_chunk', payload)
        // console.log('[ASR] sent seq', this.sendSeq - 1)
      } catch (e) {
        console.error('[ASR] socket emit error', e)
      }
    },
    /**
     * 发送最终结束包
     */
    sendFinalMarker() {
      if (!this.socket || !this.voiceId) return
      
      // ✅ 检查连接状态
      console.log('[ASR] 发送结束标记前, 连接状态:', this.socket.connected, 'SID:', this.socket.id)
      
      const payload = { voice_id: this.voiceId, seq: this.sendSeq++, chunk_b64: '', is_end: 1 }
      try {
        this.socket.emit('audio_chunk', payload)
        console.log('[ASR] sent final marker')
        
        // ✅ 发送后立即检查连接
        setTimeout(() => {
          console.log('[ASR] 发送结束标记后 100ms, 连接状态:', this.socket?.connected, 'SID:', this.socket?.id)
        }, 100)
      } catch (e) {
        console.error('[ASR] final emit error', e)
      }
    },
    /**
     * PCM转base64
     */
    arrayBufferToBase64(buffer) {
      let binary = ''
      const bytes = new Uint8Array(buffer)
      const chunkSize = 0x8000
      for (let i = 0; i < bytes.length; i += chunkSize) {
        const chunk = bytes.subarray(i, i + chunkSize)
        binary += String.fromCharCode.apply(null, chunk)
      }
      return btoa(binary)
    },
    
    /**
     * 轮询ASR结果
     */
    async pollAsrResult() {
      if (!this.voiceId) return
      
      try {
        const API_BASE = process.env.VUE_APP_API_BASE_URL || '/api/v1'
        const response = await fetch(`${API_BASE}/interviews/asr-result/${this.voiceId}`)
        
        if (response.ok) {
          const result = await response.json()
          console.log('[ASR] 轮询结果:', result.data)
          
          if (result.data && result.data.text) {
            // ✅ 收到结果，停止轮询
            this.stopAsrPolling()
            
            // 更新输入框
            this.inputText = result.data.text
            this.$nextTick(() => this.autoResize())
            
            // 清理资源
            if (this.cleanupTimer) {
              clearTimeout(this.cleanupTimer)
              this.cleanupTimer = null
            }
            this.cleanupAudioResources()
            
            // 500ms后自动提交
            setTimeout(() => {
              console.log('[ASR] 准备调用 handleSend, 状态:', {
                hasText: !!this.inputText.trim(),
                isLoading: this.isLoading,
                isFinished: this.isFinished,
                isSending: this.isSending,
                isTranscribing: this.isTranscribing,
                inputText: this.inputText
              })
              
              if (this.inputText.trim() && !this.isLoading && !this.isFinished && !this.isSending) {
                console.log('[ASR] ✅ 条件满足，调用 handleSend')
                this.handleSend()
              } else {
                console.log('[ASR] ❌ 条件不满足，跳过')
              }
            }, 500)
          }
        }
      } catch (error) {
        // 忽略错误，继续轮询
        console.log('[ASR] 轮询中...')
      }
    },
    
    /**
     * 停止轮询
     */
    stopAsrPolling() {
      if (this.asrPollingTimer) {
        clearInterval(this.asrPollingTimer)
        this.asrPollingTimer = null
        console.log('[ASR] 已停止轮询')
      }
    },

    // ================================================================
  }
}
</script>

<style lang="scss" scoped>
.interview-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #e9ecff;
  overflow: hidden;
}

// ---- Header ----
.interview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-base;
  height: 60px;
  background: #b9caff;
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
    &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    pointer-events: none;
  }
}

// ---- 主内容区 - 左右分屏 ----
.interview-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

// 左边面板：语音转文字对话框
.left-panel {
  flex: 1;
  overflow: hidden;
  border-right: 1px solid #DDE1F9;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 $spacing-base;
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
  align-items: flex-start; 
  animation: msgIn 0.3s ease both;

  &--user {
      flex-direction: row;
      justify-content: flex-end;
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
  .message-item--ai &   { align-items: flex-start; }
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
  background: #F5F6FF;
  border: 1px solid #DDE1F9;
  border-bottom-left-radius: $border-radius-sm;
  box-shadow: $shadow-sm;
  padding: $spacing-base $spacing-lg;
}

  &--user {
    background: linear-gradient(135deg, #7C6FF7 0%, #A78BFA 100%);
    box-shadow: 0 2px 12px rgba(124, 111, 247, 0.25);
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
  padding: 2px 4px 0 4px; 
  font-size: $font-size-xs; color: $text-muted;
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
}

.session-end-progress {
  display: flex; flex-direction: column; align-items: center;
  gap: 10px;
  margin-top: $spacing-sm;
  padding: 0;
}

.session-end-spinner {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 4px solid rgba(124, 111, 247, 0.18);
  border-top-color: #7C6FF7;
  border-right-color: transparent;
  border-bottom-color: transparent;
  border-left-color: transparent;
  animation: session-end-spin 0.9s linear infinite;
}

.session-end-progress-text {
  font-size: $font-size-sm;
  color: $text-primary;
  text-align: center;
}

@keyframes session-end-spin { to { transform: rotate(360deg); } }

@keyframes progress-spin { to { transform: rotate(360deg); } }

// 右边面板：语音聊天动画
.right-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f8f9ff;
  border-left: 1px solid #DDE1F9;
}

.voice-animation-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: $spacing-2xl;
  overflow-y: auto;
}

.voice-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-2xl;
  width: 100%;
  max-width: 300px;
}

.voice-character {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;

  &--ai {
    order: 1;
  }
  
  &--user {
    order: 3;
  }
}

.character-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  
  .voice-character--ai & {
    background: $primary-bg;
    border: 2px solid rgba(67,56,202,0.2);
  }
  
  .voice-character--user & {
    background: $gradient-primary;
    color: white;
  }
}

.character-name {
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  color: $text-primary;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: $spacing-sm;
}

.voice-connection {
  order: 2;
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.connection-line {
  width: 2px;
  height: 100%;
  background: #DDE1F9;
  position: relative;
  transition: all 0.3s ease;
  
  &::before, &::after {
    content: '';
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #DDE1F9;
  }
  
  &::before {
    top: -5px;
  }
  
  &::after {
    bottom: -5px;
  }
  
  &.active {
    background: #7C6FF7;
    
    &::before, &::after {
      background: #7C6FF7;
      animation: pulse 1.5s ease-in-out infinite;
    }
    
    &::before {
      animation-delay: 0s;
    }
    
    &::after {
      animation-delay: 0.75s;
    }
  }
}

.voice-status {
  margin-top: $spacing-2xl;
  padding: $spacing-md;
  background: white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;
  width: 100%;
  max-width: 300px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-size-sm;
  
  &--recording {
    color: $danger;
  }
  
  &--ai-speaking {
    color: $primary;
  }
  
  &--waiting {
    color: $text-muted;
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 1.5s ease-in-out infinite;
}

.status-time {
  margin-left: auto;
  font-family: $font-family-mono;
  font-weight: $font-weight-bold;
}

.voice-controls {
  margin-top: $spacing-lg;
  width: 100%;
  max-width: 300px;
  display: flex;
  justify-content: center;
}

.voice-control-btn {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-xl;
  border-radius: $border-radius-full;
  border: 2px solid #b6bce8;
  background: white;
  color: $text-secondary;
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  transition: all $transition-base;
  
  svg {
    width: 20px;
    height: 20px;
  }
  
  &:hover {
    border-color: $primary;
    color: $primary;
    background: $primary-bg;
  }
  
  &.active {
    background: $danger;
    border-color: $danger;
    color: white;
    animation: recordPulse 1.5s ease-in-out infinite;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// ---- 输入区域 ----
.input-area {
  background: #ccd4ff;
  border-top: 1px solid #DDE1F9;
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
  background: currentColor;
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
  width: 100%;
}

.voice-btn {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid #b6bce8;
  cursor: pointer; flex-shrink: 0;
  transition: all $transition-base;
  color: $text-secondary;
  svg { width: 20px; height: 20px; }

  &:hover { border-color: $primary; color: $primary; background: $primary-bg; }
  &.active {
    background: $danger; border-color: $danger; color: white;
    animation: recordPulse 1.5s ease-in-out infinite;
  }
    &:disabled:not(.active) {
    opacity: 0.35;
    cursor: not-allowed;
  }
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
  border: 1.5px solid #CDD2F5;
  border-radius: $border-radius;
  font-family: $font-family-base;
  font-size: $font-size-base;
  line-height: $line-height-normal;
  color: $text-primary;
  resize: none;
  outline: none;
  background: #F3F4FF;
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
  border-radius: 24px;
  width: 100%; max-width: 360px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(67, 56, 202, 0.2);
  animation: sheetIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes sheetIn {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header-bar {
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  padding: 24px 24px 18px;
  text-align: center;
}
.modal-header-title { font-size: 18px; font-weight: 700; color: white; margin: 0 0 4px; }
.modal-header-sub   { font-size: 12px; color: rgba(255,255,255,0.7); margin: 0; }

.modal-body { padding: 18px 20px 24px; }

.rules-list {
  list-style: none; padding: 0; margin: 0 0 20px;
  display: flex; flex-direction: column; gap: 10px;

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
  &--danger { background: #fb7474; }
}

.modal-actions {
  display: flex; gap: 10px;
}

.btn-cancel {
  flex: 0 0 80px; height: 46px;
  border-radius: 23px;
  border: 1.5px solid #e5e7eb;
  background: white; color: #6b7280;
  font-size: 14px; font-weight: 500;
  cursor: pointer; font-family: $font-family-base;
  transition: all 0.2s;
  &:hover { border-color: #d1d5db; background: #f9fafb; }
}

.btn-confirm {
  flex: 1; height: 46px;
  border-radius: 23px; border: none;
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  color: white; font-size: 14px; font-weight: 700;
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; gap: 8px;
  font-family: $font-family-base;
  box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
  transition: all 0.2s;

  &--danger {
    background: linear-gradient(135deg, #ef6e6e 0%, #f963a9 100%);
    box-shadow: 0 4px 14px rgba(220, 38, 38, 0.655);
    &:hover { box-shadow: 0 6px 20px rgba(220, 38, 38, 0.45); }
  }

  &:hover { transform: translateY(-1px); }
  &:active { transform: scale(0.98); }
  &:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
}

.btn-spinner {
  width: 15px; height: 15px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  &--danger { border-color: rgba($danger, 0.3); border-top-color: $danger; }
}


@keyframes spin { to { transform: rotate(360deg); } }
@keyframes recordPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba($danger, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba($danger, 0); }
}

.modal-enter-active { animation: modalIn 0.3s ease both; }
.modal-leave-active { animation: modalOut 0.2s ease both; }
@keyframes modalIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
@keyframes modalOut { from { opacity: 1; } to { opacity: 0; } }

.fade-enter-active { animation: fadeIn 0.3s ease both; }
.fade-leave-active { animation: fadeIn 0.2s ease reverse both; }

.message-enter-active { animation: msgIn 0.3s ease both; }
.voice-mode-badge {
  display: inline-flex; align-items: center; gap: 3px;
  background: rgba(67,56,202,0.1); color: $primary;
  font-size: 10px; font-weight: $font-weight-semibold;
  padding: 2px 7px; border-radius: $border-radius-full;
  margin-top: 2px;
}
.avatar-img {
  width: 100%; height: 100%;
  border-radius: 50%; object-fit: cover;
}

.view-report-btn {
  margin-top: 16px;
  padding: 10px 24px;
  border-radius: $border-radius-full;
  background: white;
  color: #312e81;
  font-weight: $font-weight-bold;
  font-size: $font-size-sm;
  border: none;
  cursor: pointer;
  transition: all $transition-base;
  &:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
}
.messages-inner {
  max-width: 100%;
  margin: 0 auto;
  width: 100%;
}

// 响应式适配
@media (max-width: 768px) {
  .interview-body {
    flex-direction: column;
  }
  
  .left-panel {
    border-right: none;
    border-bottom: 1px solid #DDE1F9;
    flex: 1;
  }
  
  .right-panel {
    flex: 0 0 auto;
    border-left: none;
    border-top: 1px solid #DDE1F9;
  }
  
  .voice-animation-container {
    padding: $spacing-lg;
  }
  
  .voice-animation {
    gap: $spacing-lg;
  }
  
  .voice-connection {
    height: 80px;
  }
}
</style>