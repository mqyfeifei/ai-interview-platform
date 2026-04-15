// =============================================
// frontend/src/store/modules/interview.js
// Vuex 面试模块
// =============================================

import { startInterview, sendAnswer, finishInterview } from '@/api/interview'

const DEFAULT_TTS_VOICE = 'zh_female_shuangkuaisisi_uranus_bigtts'

// 清理文本中的冗余换行，保持对话紧凑
function cleanContent(text) {
  if (!text) return ''
  // normalize line endings to \n then collapse
  let t = text.replace(/\r\n|\r/g, '\n')
    .replace(/\n{2,}/g, ' ')   // collapse consecutive newlines to space
    .replace(/\n/g, ' ')       // finally remove any leftover newline
    .trim()
  // also collapse multiple spaces
  t = t.replace(/ {2,}/g, ' ')
  return t
}

function base64ToUint8Array(base64) {
  const binary = atob(base64 || '')
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

let currentPlayback = null
let playbackCancelled = false

function getSharedAudioContext() {
  if (typeof window === 'undefined') return null
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null

  if (!window.__aiInterviewAudioContext) {
    window.__aiInterviewAudioContext = new AudioCtx()
  }
  return window.__aiInterviewAudioContext
}

function isAutoplayError(err) {
  const name = err?.name || ''
  const msg = String(err || '').toLowerCase()
  return (
    name === 'NotAllowedError' ||
    msg.includes('notallowederror') ||
    msg.includes('play() failed') ||
    msg.includes('user gesture')
  )
}

function base64ToObjectUrl(base64, mimeType = 'audio/mpeg') {
  const bytes = base64ToUint8Array(base64)
  const blob = new Blob([bytes], { type: mimeType })
  const objectUrl = URL.createObjectURL(blob)
  return {
    objectUrl,
    audio: new Audio(objectUrl)
  }
}

function base64ToDataUriAudio(base64, mimeType = 'audio/mp3') {
  return {
    objectUrl: null,
    audio: new Audio(`data:${mimeType};base64,${base64 || ''}`)
  }
}

function cleanupCurrentPlayback() {
  if (!currentPlayback) return

  try {
    if (currentPlayback.type === 'html') {
      const { audio, objectUrl } = currentPlayback
      audio.onended = null
      audio.onerror = null
      audio.pause()
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
    if (currentPlayback.type === 'web') {
      currentPlayback.source?.stop?.()
      currentPlayback.source = null
    }
  } catch (err) {
    console.warn('[TTS] cleanupCurrentPlayback failed', err)
  }

  currentPlayback.resolve?.()
  currentPlayback = null
}

function stopCurrentPlayback() {
  playbackCancelled = true
  cleanupCurrentPlayback()
}

function bindAudioUnlockOnce(callback) {
  if (typeof window === 'undefined') return

  const events = ['pointerdown', 'keydown', 'touchstart']
  const handler = () => {
    events.forEach((eventName) => {
      window.removeEventListener(eventName, handler, true)
    })
    callback && callback()
  }

  events.forEach((eventName) => {
    window.addEventListener(eventName, handler, true)
  })
}

function waitForUserGesture(timeoutMs = 12000) {
  return new Promise((resolve) => {
    let settled = false
    const timer = setTimeout(() => {
      if (settled) return
      settled = true
      resolve(false)
    }, timeoutMs)

    bindAudioUnlockOnce(() => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      resolve(true)
    })
  })
}

async function playWithWebAudio(base64) {
  const audioContext = getSharedAudioContext()
  if (!audioContext) {
    throw new Error('WebAudio 不可用')
  }

  if (audioContext.state === 'suspended') {
    await audioContext.resume()
    if (audioContext.state === 'suspended') {
      const err = new Error('NotAllowedError: WebAudio context is suspended and cannot be resumed without user interaction.')
      err.name = 'NotAllowedError'
      throw err
    }
  }

  const bytes = base64ToUint8Array(base64)
  const arrayBuffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)
  const decodedBuffer = await audioContext.decodeAudioData(arrayBuffer)

  await new Promise((resolve) => {
    const source = audioContext.createBufferSource()
    source.buffer = decodedBuffer
    source.connect(audioContext.destination)
    source.onended = () => resolve()

    currentPlayback = {
      type: 'web',
      source,
      resolve,
      reject: null
    }

    source.start(0)
  })
}

function playWithHtmlAudio(base64, mode = 'blob') {
  return new Promise((resolve, reject) => {
    const source = mode === 'blob'
      ? base64ToObjectUrl(base64)
      : base64ToDataUriAudio(base64)

    const { audio, objectUrl } = source
    let settled = false

    const cleanup = () => {
      audio.onended = null
      audio.onerror = null
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }

    const finishResolve = () => {
      if (settled) return
      settled = true
      cleanup()
      resolve()
    }

    const finishReject = (err) => {
      if (settled) return
      settled = true
      cleanup()
      reject(err)
    }

    audio.onended = () => finishResolve()
    audio.onerror = (err) => finishReject(err || new Error('HTMLAudio onerror'))

    currentPlayback = {
      type: 'html',
      audio,
      objectUrl,
      resolve: finishResolve,
      reject: finishReject
    }

    const playPromise = audio.play()
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch((err) => finishReject(err))
    }
  })
}

async function playBase64AudioReliable(base64, tag = 'stream', waitTimeoutMs = 12000) {
  if (!base64) return
  if (playbackCancelled) return

  const tryWebAudio = async () => {
    if (playbackCancelled) return
    await playWithWebAudio(base64)
    return 'webaudio'
  }

  try {
    return await tryWebAudio()
  } catch (err) {
    if (isAutoplayError(err)) {
      console.warn(`[TTS][${tag}] WebAudio 被拦截，等待用户交互后重试`, err)
      const unlocked = await waitForUserGesture(waitTimeoutMs)
      if (!unlocked) {
        throw new Error('等待用户交互超时（WebAudio）')
      }
      return await tryWebAudio()
    }
    console.warn(`[TTS][${tag}] WebAudio 播放失败，回退 HTMLAudio`, err)
  }

  try {
    await playWithHtmlAudio(base64, 'blob')
    return 'html-blob'
  } catch (err) {
    if (isAutoplayError(err)) {
      console.warn(`[TTS][${tag}] HTMLAudio 被拦截，等待用户交互后重试`, err)
      const unlocked = await waitForUserGesture(waitTimeoutMs)
      if (!unlocked) {
        throw new Error('等待用户交互超时（HTMLAudio）')
      }
      await playWithHtmlAudio(base64, 'blob')
      return 'html-blob'
    }
    console.warn(`[TTS][${tag}] HTMLAudio(blob) 失败，回退 data URI`, err)
  }

  await playWithHtmlAudio(base64, 'data-uri')
  return 'html-data'
}

const state = () => ({
  currentSession: null,    // { sessionId, totalQuestions }
  selectedJob: null,       // 选中的岗位对象（来自 constants.js JOB_TYPES）
  messages: [],            // { id, role:'ai'|'user', content, timestamp, isFollowUp? }
  questionIndex: 1,        // 当前是第几题（0-based）
  isFinished: false,
  isEnding: false,
  reportId: null,
  isLoading: false,        // AI 正在"思考"中
  isAISpeaking: false,     // AI 音频仍在播放中
  elapsedSeconds: 0,        // 已用时（秒）
  jobDbId: null,  // 后端数据库真实岗位id
  resumeId: null,  // 选中的简历ID
  selectedProfileId: null,
  selectedProfileConfig: null,
  voiceMode: false,
  interviewStyle: 'confident',
  interviewSource: '通用',
  voiceRole: 'role_calm',
  ttsVoice: DEFAULT_TTS_VOICE
})

const mutations = {
  SET_JOB_DB_ID(state, id) { state.jobDbId = id },
  SET_RESUME_ID(state, id) { state.resumeId = id },
  SET_SESSION(state, session) { state.currentSession = session },
  SET_SELECTED_JOB(state, job) { state.selectedJob = job },
  SET_SELECTED_PROFILE_ID(state, id) { state.selectedProfileId = id },
  SET_SELECTED_PROFILE_CONFIG(state, config) { state.selectedProfileConfig = config },
  ADD_MESSAGE(state, msg) {
    const m = { ...msg, content: cleanContent(msg.content) }
    state.messages.push(m)
  },
  SET_MESSAGES(state, msgs) { state.messages = msgs },
  SET_QUESTION_INDEX(state, idx) { state.questionIndex = idx },
  SET_VOICE_MODE(state, v) { state.voiceMode = v },
  SET_INTERVIEW_STYLE(state, v) { state.interviewStyle = v || 'confident' },
  SET_INTERVIEW_SOURCE(state, v) { state.interviewSource = v || '通用' },
  SET_VOICE_ROLE(state, v) { state.voiceRole = v || 'role_calm' },
  SET_TTS_VOICE(state, v) { state.ttsVoice = (v || DEFAULT_TTS_VOICE) },
  SET_AI_SPEAKING(state, v) { state.isAISpeaking = v },
  SET_FINISHED(state, reportId) {
    state.isFinished = true
    state.isEnding = false
    state.reportId = reportId
  },
  SET_ENDING(state, v) { state.isEnding = v },

  APPEND_AI_CHUNK(state, chunk) {
    const last = state.messages[state.messages.length - 1]
    if (last && last.role === 'ai') {
      last.content = (last.content + chunk).replace(/\[INTERVIEW_OVER\]/g, '')
    }
  },
  MARK_STREAM_DONE(state) {
    const last = state.messages[state.messages.length - 1]
    if (last) {
      last.streaming = false
      last.content = cleanContent(last.content)

    }
  },

  SET_LOADING(state, v) { state.isLoading = v },
  SET_ELAPSED(state, v) { state.elapsedSeconds = v },
  RESET_INTERVIEW(state) {
    state.currentSession = null
    state.messages = []
    state.questionIndex = 0
    state.isFinished = false
    state.isEnding = false
    state.reportId = null
    state.isLoading = false
    state.isAISpeaking = false
    state.elapsedSeconds = 0
    state.selectedProfileId = null
    state.selectedProfileConfig = null
    state.voiceMode = false
    state.interviewStyle = 'confident'
    state.interviewSource = '通用'
    state.voiceRole = 'role_calm'
    state.ttsVoice = DEFAULT_TTS_VOICE
    state.resumeId = null
  }
}

const actions = {
  // 选择岗位（从岗位选择页调用）
  selectJob({ commit }, job) {
    commit('SET_SELECTED_JOB', job)
  },

  selectInterviewProfile({ commit }, profileId) {
    commit('SET_SELECTED_PROFILE_ID', profileId)
  },

  // 开始面试（从面试主界面初始化时调用）
  async startSession({ commit, state, rootGetters }, options = {}) {
    commit('SET_LOADING', true)
    try {
      // 在进入异步耗时任务之前，立刻尝试初始化 AudioContext，利用现有的用户交互手势！
      const ctx = getSharedAudioContext();
      if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(e => console.warn('唤醒由于没有活跃手势被拒绝', e));
      }

      // 从 user 模块拿数字 id
      const userInfo = rootGetters['user/userInfo']
      const userId = userInfo?.id  // 数字，如 1
      console.log('当前用户ID:', userId)
      console.log('当前岗位ID:', state.jobDbId)
      console.log('[InterviewDebug][store] startSession payload =', {
        selectedProfileId: state.selectedProfileId,
        selectedRound: state.selectedProfileConfig?.interview_round,
        selectedInterviewStyle: state.interviewStyle,
        selectedInterviewSource: state.interviewSource,
        selectedProfileConfig: state.selectedProfileConfig,
      })
      const res = await startInterview({
        userId,                    // 传给后端的 user_id
        jobDbId: state.jobDbId,     // 传给后端的 job_id（数字）
        resumeId: state.resumeId,   // 传给后端的 resume_id
        profileId: state.selectedProfileId,
        interviewRound: state.selectedProfileConfig?.interview_round,
        interviewSource: state.interviewSource || state.selectedProfileConfig?.target_source || '通用',
        sessionConfig: state.selectedProfileConfig,
        voiceMode: state.voiceMode,
        interviewStyle: state.interviewStyle,
        voiceRole: state.voiceRole,
        voice: state.ttsVoice
      })
      commit('SET_SESSION', { sessionId: res.sessionId, totalQuestions: 10 })
      commit('ADD_MESSAGE', {
        id: Date.now(),
        role: 'ai',
        content: res.firstQuestion,
        timestamp: new Date()
      })
      if (state.voiceMode && res.firstQuestionAudio) {
        console.log('[TTS][opening] 收到开场白音频，base64长度=', res.firstQuestionAudio.length)
        commit('SET_AI_SPEAKING', true)
        // ✅ 修复：确保开场白音频完整播放后才解除 isAISpeaking，防止与录音冲突
        playBase64AudioReliable(res.firstQuestionAudio, 'opening', 30000)
          .then(() => {
            console.log('[TTS][opening] 开场白播放完毕')
          })
          .catch((err) => {
            console.error('[TTS][opening] 播放失败，尝试最终兜底重播：', err)
            return playWithHtmlAudio(res.firstQuestionAudio, 'data-uri')
              .catch((fallbackErr) => {
                console.error('[TTS][opening] data-uri 兜底仍失败：', fallbackErr)
              })
          })
          .finally(() => {
            commit('SET_AI_SPEAKING', false)
            console.log('[TTS][opening] 已解除 isAISpeaking 标志，用户可以开始操作')
          })
      }
      commit('SET_QUESTION_INDEX', 1)
      return res
    } finally {
      commit('SET_LOADING', false)
    }
  },
  // 用户提交回答
  async submitAnswer({ commit, state, dispatch }, answerText) {
    if (state.isLoading) return
    commit('ADD_MESSAGE', { id: Date.now(), role: 'user', content: answerText, timestamp: Date.now() })
    commit('SET_LOADING', true)
    commit('ADD_MESSAGE', { id: Date.now() + 1, role: 'ai', content: '', timestamp: Date.now(), streaming: true })

    // 在长耗时异步开始前激活音频上下文
    const ctx = getSharedAudioContext();
    if (ctx && ctx.state === 'suspended') {
      ctx.resume().catch(e => console.warn('音频激活失败', e));
    }

    const { sendAnswerStream } = await import('@/api/interview')

    // ✅ 创建音频播放器（仅当流结束且音频播放完毕，才进入下一轮）
    let streamDone = false
    let shouldFinishInterview = false
    let pendingAudioCount = 0
    let playbackChain = Promise.resolve()

    const tryCompleteTurn = () => {
      if (!streamDone || pendingAudioCount > 0) return

      commit('SET_AI_SPEAKING', false)
      commit('SET_LOADING', false)
      commit('MARK_STREAM_DONE')

      if (shouldFinishInterview) {
        dispatch('endInterview')
      } else {
        commit('SET_QUESTION_INDEX', state.questionIndex + 1)
      }
    }

    const playBase64Audio = (base64Str) => {
      if (playbackCancelled) return
      pendingAudioCount += 1
      commit('SET_AI_SPEAKING', true)

      playbackChain = playbackChain
        .then(() => {
          if (playbackCancelled) return
          return playBase64AudioReliable(base64Str, 'stream', 12000)
        })
        .catch(async (err) => {
          console.error('[TTS][stream] 音频播放失败，尝试 data-uri 兜底：', err)
          try {
            await playWithHtmlAudio(base64Str, 'data-uri')
          } catch (retryErr) {
            console.error('[TTS][stream] 兜底重播失败，跳过该片段：', retryErr)
          }
        })
        .finally(() => {
          pendingAudioCount = Math.max(0, pendingAudioCount - 1)
          if (pendingAudioCount === 0) {
            commit('SET_AI_SPEAKING', false)
            tryCompleteTurn()
          }
        })
    }

    sendAnswerStream(state.currentSession.sessionId, answerText, {
      voiceMode: state.voiceMode,
      voice: state.ttsVoice,
      onChunk(chunk) {
        commit('APPEND_AI_CHUNK', chunk)
      },

      // ✅ 新增：处理音频数据
      onAudio(base64Audio) {
        if (!playbackCancelled) {
          playBase64Audio(base64Audio)
        }
      },

      onStreamEnd() {
        streamDone = true
        tryCompleteTurn()
      },
      onFinish() {
        shouldFinishInterview = true
        streamDone = true
        tryCompleteTurn()
      },
      onError(err) {
        pendingAudioCount = 0
        commit('SET_AI_SPEAKING', false)
        commit('SET_LOADING', false)
        commit('MARK_STREAM_DONE')
        console.error('SSE error', err)
      }
    })
  },
  // 手动结束面试
  async endInterview({ commit, state }) {
    if (!state.currentSession) return
    if (state.isEnding || state.isFinished) return
    commit('SET_ENDING', true) // 立即标记：面试结束流程开始，计时器将停止
    stopCurrentPlayback()
    commit('SET_AI_SPEAKING', false)
    commit('SET_LOADING', true)
    try {
      const res = await finishInterview(state.currentSession.sessionId)
      // commit('ADD_MESSAGE', {
      //   id: Date.now(),
      //   role: 'ai',
      //   content: '好的，面试提前结束。感谢你的参与，正在为你生成评估报告...',
      //   timestamp: new Date()
      // })
      commit('SET_FINISHED', res.reportId)
      return res
    } catch (e) {
      commit('SET_ENDING', false)  // ← 失败时恢复，允许重试
      throw e
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 重置（回到岗位选择重新开始时调用）
  resetInterview({ commit }) {
    playbackCancelled = false
    cleanupCurrentPlayback()
    commit('RESET_INTERVIEW')
  },

  updateElapsed({ commit }, seconds) {
    commit('SET_ELAPSED', seconds)
  }
}

const getters = {
  selectedJob: s => s.selectedJob,
  currentSession: s => s.currentSession,
  messages: s => s.messages,
  questionIndex: s => s.questionIndex,
  totalQuestions: s => s.currentSession?.totalQuestions,
  progressText: s => `${s.questionIndex} / ${s.currentSession?.totalQuestions}`,
  isFinished: s => s.isFinished,
  isEnding: s => s.isEnding,
  reportId: s => s.reportId,
  isLoading: s => s.isLoading,
  isAISpeaking: s => s.isAISpeaking,
  voiceMode: s => s.voiceMode,
  ttsVoice: s => s.ttsVoice,
  elapsedSeconds: s => s.elapsedSeconds
}

export default { namespaced: true, state, mutations, actions, getters }
