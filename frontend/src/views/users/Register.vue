<!--
  =============================================
  frontend/src/views/users/Register.vue
  注册页组件 — 毛玻璃极简风格（两步注册）
  ============================================= -->
<template>
  <div class="auth-scene">
    <!-- 背景装饰 -->
    <div class="scene-orb scene-orb--1" />
    <div class="scene-orb scene-orb--2" />
    <div class="scene-orb scene-orb--3" />
    <div class="scene-grid" />

    <div class="auth-wrap">
      <!-- 左侧品牌区 -->
      <div class="brand-panel">
        <div class="brand-inner">
          <div class="brand-mark">
            <span class="brand-mark__name">AI面试助手</span>
          </div>
          <p class="brand-tagline">开启你的<br>AI面试训练之旅</p>

          <div class="steps-list">
            <div class="step-item" v-for="(s, i) in onboardingSteps" :key="i">
              <div class="step-item__num">{{ i + 1 }}</div>
              <div class="step-item__body">
                <p class="step-item__title">{{ s.title }}</p>
                
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧玻璃卡片 -->
      <div class="glass-card">
        <div class="mobile-logo">
          <span>🎯</span>
          <span>AI面试助手</span>
        </div>

        <!-- 步骤指示器 -->
        <div class="step-indicator">
          <div
            v-for="n in totalSteps"
            :key="n"
            class="step-node"
            :class="{ active: currentStep === n, done: currentStep > n }"
          >
            <span v-if="currentStep > n">✓</span>
            <span v-else>{{ n }}</span>
          </div>
          <div
            class="step-track"
            :style="{ width: ((currentStep - 1) / (totalSteps - 1) * 100) + '%' }"
          />
        </div>

        <div class="card-header">
          <h2>{{ stepTitles[currentStep - 1].title }}</h2>
          <p>{{ stepTitles[currentStep - 1].sub }}</p>
        </div>

        <form @submit.prevent="handleSubmit" novalidate>

          <!-- Step 1: 账号信息 -->
          <transition name="step" mode="out-in">
            <div v-if="currentStep === 1" key="s1">

              <div class="field">
                <label>邮箱地址 *</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="2" y="4" width="20" height="16" rx="2"/>
                      <path d="M2 7l10 7 10-7"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.email"
                    type="email"
                    placeholder="your@email.com"
                    class="form-control with-icon"
                    :class="{ error: errors.email }"
                    autocomplete="email"
                  />
                </div>
                <span v-if="errors.email" class="field-err">{{ errors.email }}</span>
              </div>

              <div class="field">
                <label>手机号码（可选）</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                      <line x1="12" y1="18" x2="12.01" y2="18"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.phone"
                    type="tel"
                    placeholder="13800138000"
                    class="form-control with-icon"
                    :class="{ error: errors.phone }"
                  />
                </div>
                <span v-if="errors.phone" class="field-err">{{ errors.phone }}</span>
              </div>

              <div class="field">
                <label>设置密码 *</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="至少6位，建议字母+数字"
                    class="form-control with-icon with-icon-right"
                    :class="{ error: errors.password }"
                    autocomplete="new-password"
                  />
                  <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                    <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
                      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  </button>
                </div>
                <div class="pwd-strength" v-if="form.password">
                  <div class="pwd-bar">
                    <div class="pwd-bar__fill" :class="passwordStrength.level" :style="{ width: passwordStrength.percent + '%' }" />
                  </div>
                  <span class="pwd-label" :class="passwordStrength.level">{{ passwordStrength.text }}</span>
                </div>
                <span v-if="errors.password" class="field-err">{{ errors.password }}</span>
              </div>

              <div class="field">
                <label>确认密码 *</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.confirmPassword"
                    type="password"
                    placeholder="再次输入密码"
                    class="form-control with-icon"
                    :class="{ error: errors.confirmPassword }"
                    autocomplete="new-password"
                  />
                </div>
                <span v-if="errors.confirmPassword" class="field-err">{{ errors.confirmPassword }}</span>
              </div>

            </div>
          </transition>

          <!-- Step 2: 个人信息 -->
          <transition name="step" mode="out-in">
            <div v-if="currentStep === 2" key="s2">

              <div class="field">
                <label>你的姓名 *</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.username"
                    type="text"
                    placeholder="请输入姓名"
                    class="form-control with-icon"
                    :class="{ error: errors.username }"
                    autocomplete="nickname"
                  />
                </div>
                <span v-if="errors.username" class="field-err">{{ errors.username }}</span>
              </div>

              <div class="field">
                <label>就读学校 *</label>
                <div class="input-wrap">
                  <span class="input-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                      <path d="M6 12v5c3 3 9 3 12 0v-5"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.school"
                    type="text"
                    placeholder="如：北京大学"
                    class="form-control with-icon"
                    :class="{ error: errors.school }"
                  />
                </div>
                <span v-if="errors.school" class="field-err">{{ errors.school }}</span>
              </div>

              <div class="field-row">
                <div class="field">
                  <label>专业方向 *</label>
                  <input
                    v-model="form.major"
                    type="text"
                    placeholder="如：计算机科学"
                    class="form-control"
                    :class="{ error: errors.major }"
                  />
                  <span v-if="errors.major" class="field-err">{{ errors.major }}</span>
                </div>
                <div class="field">
                  <label>年级 *</label>
                  <select v-model="form.grade" class="form-control form-select" :class="{ error: errors.grade }">
                    <option value="">选择年级</option>
                    <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
                  </select>
                  <span v-if="errors.grade" class="field-err">{{ errors.grade }}</span>
                </div>
              </div>

            </div>
          </transition>

          <div v-if="globalError" class="global-err">
            <span>⚠️</span> {{ globalError }}
          </div>

          <div class="form-actions">
            <button v-if="currentStep > 1" type="button" class="btn-back" @click="currentStep--">
              ← 上一步
            </button>

            <button v-if="currentStep < totalSteps" type="button" class="btn-next" @click="nextStep">
              下一步 →
            </button>

            <button v-if="currentStep === totalSteps" type="submit" class="btn-submit" :disabled="loading">
              <span v-if="loading" class="spinner" />
              <span>{{ loading ? '注册中...' : '完成注册' }}</span>
            </button>
          </div>
        </form>

        <div class="card-footer">
          <span>已有账号？</span>
          <router-link to="/login" class="link-accent">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import { GRADE_OPTIONS } from '@/utils/constants'

export default {
  name: 'RegisterPage',
  data() {
    return {
      currentStep: 1,
      totalSteps: 2,
      form: {
        email: '',
        phone: '',
        password: '',
        confirmPassword: '',
        username: '',
        school: '',
        major: '',
        grade: '',
        realName: ''
      },
      errors: {},
      globalError: '',
      showPassword: false,
      loading: false,
      gradeOptions: GRADE_OPTIONS.map(o => o.value),
      stepTitles: [
        { title: '注册', sub: '创建账号，填写登录信息' },
        { title: '注册', sub: '完善资料，帮助 AI 更精准地了解你' }
      ],
      onboardingSteps: [
        { title: '创建账号：填写邮箱和密码' },
        { title: '完善资料：学校、专业、年级 ' },
        { title: '选择岗位：指定目标岗位' },
        { title: '开始面试：与AI面试官对话' }
      ]
    }
  },
  computed: {
    passwordStrength() {
      const p = this.form.password
      if (!p) return { level: '', percent: 0, text: '' }
      let score = 0
      if (p.length >= 8) score++
      if (/[A-Z]/.test(p)) score++
      if (/[0-9]/.test(p)) score++
      if (/[^A-Za-z0-9]/.test(p)) score++
      if (score <= 1) return { level: 'weak', percent: 25, text: '弱' }
      if (score === 2) return { level: 'fair', percent: 50, text: '一般' }
      if (score === 3) return { level: 'good', percent: 75, text: '强' }
      return { level: 'strong', percent: 100, text: '非常强' }
    }
  },
  methods: {
    ...mapActions('user', ['register']),
    validateStep1() {
      this.errors = {}
      const { email, phone, password, confirmPassword } = this.form
      if (!email) {
        this.errors.email = '请输入邮箱地址'
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        this.errors.email = '请输入有效的邮箱地址'
      }
      if (phone && !/^1\d{10}$/.test(phone)) {
        this.errors.phone = '请输入有效的手机号码'
      }
      if (!password) {
        this.errors.password = '请设置密码'
      } else if (password.length < 6) {
        this.errors.password = '密码不能少于6位'
      }
      if (!confirmPassword) {
        this.errors.confirmPassword = '请确认密码'
      } else if (password !== confirmPassword) {
        this.errors.confirmPassword = '两次输入的密码不一致'
      }
      return Object.keys(this.errors).length === 0
    },
    validateStep2() {
      this.errors = {}
      if (!this.form.username.trim()) this.errors.username = '请输入姓名'
      if (!this.form.school.trim()) this.errors.school = '请输入学校'
      if (!this.form.major.trim()) this.errors.major = '请输入专业'
      if (!this.form.grade) this.errors.grade = '请选择年级'
      return Object.keys(this.errors).length === 0
    },
    nextStep() {
      if (this.currentStep === 1 && !this.validateStep1()) return
      this.currentStep++
    },
    async handleSubmit() {
      if (!this.validateStep2()) return
      this.globalError = ''
      this.loading = true
      try {
        const { confirmPassword, ...submitData } = this.form
        submitData.real_name = submitData.realName
        delete submitData.realName
        await this.register(submitData)
        this.$router.push('/interview/select')
      } catch (err) {
        this.globalError = err.message || '注册失败，请稍后重试'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

// ── 场景背景（与 Login 相同） ─────────────────
.auth-scene {
  font-family: 'Outfit', sans-serif;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: url('@/assets/backgroundA.jpg') center/cover no-repeat fixed;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.scene-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.scene-orb--1 {
  width: 560px; height: 560px;
  background: radial-gradient(circle, rgba(124,58,237,0.22) 0%, transparent 70%);
  top: -160px; right: -80px;
  animation: orbDrift 11s ease-in-out infinite;
}
.scene-orb--2 {
  width: 480px; height: 480px;
  background: radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%);
  bottom: -120px; left: -100px;
  animation: orbDrift 14s ease-in-out infinite reverse;
}
.scene-orb--3 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(167,139,250,0.13) 0%, transparent 70%);
  top: 40%; left: 45%;
  animation: orbDrift 8s ease-in-out infinite 1.5s;
}
.scene-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}

.auth-scene::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(92, 77, 165, 0.7); // 调透明度控制图片能透出多少
  backdrop-filter: blur(2px);          // 轻微模糊图片本身
  z-index: 0;
}

@keyframes orbDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(18px, -22px) scale(1.04); }
  66%  { transform: translate(-12px, 12px) scale(0.97); }
}

// ── 布局 ──────────────────────────────────────
.auth-wrap {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  max-width: 940px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06);
}

// ── 左侧品牌区 ────────────────────────────────
.brand-panel {
  display: none;
  flex: 1;
  background: rgba(238, 235, 255, 0.35);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,0.07);
  padding: 56px 44px;
  align-items: center;
  justify-content: center;

  @media (min-width: 768px) { display: flex; }
}

.brand-inner { max-width: 300px; }

.brand-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;

  &__icon { font-size: 34px; filter: drop-shadow(0 0 12px rgba(167,139,250,0.7)); }
  &__name { font-size: 29px; font-weight: 750; color: #1e1b4b;  letter-spacing: -0.02em; }
}

.brand-tagline {
  font-size: 23px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.02em;
  color: #1e1b4b; 
  margin-bottom: 32px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 5px 15px;       
  background: rgba(255,255,255,0.07);
  border: 0.5px solid rgba(255,255,255,0.1);
  border-radius: 100px;      // 原来是 14px，改成全圆角胶囊形
  backdrop-filter: blur(8px);
  transition: background 0.2s;
  &:hover { background: rgba(255,255,255,0.12); }
  &__num {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: rgba(99,102,241,0.3);
    border: 1px solid rgba(99,102,241,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    color: #c4b5fd;
    flex-shrink: 0;
  }
  &__title { font-weight: 500; color: rgba(255,255,255,0.7); font-size: 12px; margin-bottom: 1px; }

}

// ── 右侧玻璃卡片 ──────────────────────────────
.glass-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.55); 
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-left: 1px solid rgba(255, 255, 255, 0.6);
  padding: 36px 40px;
  display: flex;
  flex-direction: column;

  @media (min-width: 768px) {
    width: 460px;
    flex-shrink: 0;
  }
}

.mobile-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 800;
  color: white;
  margin-bottom: 20px;
  span:first-child { font-size: 24px; }
  @media (min-width: 768px) { display: none; }
}

// ── 步骤指示器 ────────────────────────────────
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 60px;
  margin-bottom: 20px;
  position: relative;
  padding: 4px 0;
}

.step-track {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translateX(-50%) translateY(-50%);
  height: 2px;
  background: linear-gradient(90deg, #6366f1, #a78bfa);
  border-radius: 2px;
  transition: width 0.4s ease;
  z-index: 0;
}

.step-node {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  border: 2px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.3);
  transition: all 0.3s;
  position: relative;
  z-index: 1;
  font-family: inherit;

  &.active {
    border-color: #6366f1;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    box-shadow: 0 0 0 5px rgba(99,102,241,0.15), 0 4px 16px rgba(99,102,241,0.4);
  }
  &.done {
    border-color: rgba(99,102,241,0.5);
    background: rgba(99,102,241,0.15);
    color: #a78bfa;
  }
}

// ── 头部 ──────────────────────────────────────
.card-header {
  margin-bottom: 18px;
  text-align: center; 
  h2 {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: #1e1b4b; 
    margin-bottom: 4px;
    
  }
  p { font-size: 13px; color: #6b7280; }
}

// ── 表单字段 ──────────────────────────────────
.field {
  margin-bottom: 14px;

  label {
    display: block;
    font-size: 13px;
    font-weight: 700;
    color: #3730a3;
    text-transform: none;
    letter-spacing: 0.02em;
    margin-bottom: 6px;
  }
}

.input-wrap { position: relative; }

.input-ico {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(167,139,250,0.45);
  display: flex;
  align-items: center;
  pointer-events: none;
  svg { width: 15px; height: 15px; }
}

.form-control {
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7); 
  border: 1.5px solid rgba(99, 102, 241, 0.25);
  color:  #1e1b4b;  
  font-size: 14px;
  padding: 11px 13px;
  transition: all 0.2s;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;

  &:focus {
    outline: none;
    background: rgba(255, 255, 255, 0.9);
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
  }
  &.error {
    border-color: rgba(248,113,113,0.5);
    background: rgba(248,113,113,0.05);
  }
  &.with-icon { padding-left: 40px; }
  &.with-icon-right { padding-right: 44px; }
  &::placeholder { color: #a5b4c8; }
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='rgba(167,139,250,0.5)' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 14px;
  padding-right: 34px;

  option { background: #1a1040; color: white; }
}

.eye-btn {
  position: absolute;
  right: 11px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(167,139,250,0.45);
  display: flex;
  align-items: center;
  padding: 4px;
  svg { width: 15px; height: 15px; }
  &:hover { color: #a78bfa; }
}

.pwd-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.pwd-bar {
  flex: 1;
  height: 3px;
  background: rgba(255,255,255,0.08);
  border-radius: 2px;
  overflow: hidden;

  &__fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s;
    &.weak  { background: #f87171; }
    &.fair  { background: #fb923c; }
    &.good  { background: #34d399; }
    &.strong { background: linear-gradient(90deg, #34d399, #6366f1); }
  }
}

.pwd-label {
  font-size: 11px;
  font-weight: 600;
  &.weak   { color: #f87171; }
  &.fair   { color: #fb923c; }
  &.good   { color: #34d399; }
  &.strong { color: #a78bfa; }
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.field-err {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #f87171;
}

.global-err {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.25);
  color: #fca5a5;
  padding: 10px 13px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 7px;
}

// ── 操作按钮 ──────────────────────────────────
.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.btn-back {
  padding: 0 18px;
  height: 48px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  background: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.6);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  white-space: nowrap;
  &:hover { border-color: rgba(99,102,241,0.4); color: white; background: rgba(99,102,241,0.1); }
}

.btn-next,
.btn-submit {
  flex: 1;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 4px 18px rgba(79,70,229,0.4);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 26px rgba(79,70,229,0.5);
  }
  &:active:not(:disabled) { transform: translateY(0); }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}

.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

// ── 底部 ──────────────────────────────────────
.card-footer {
  text-align: center;
  font-size: 13px;
  color: rgba(255,255,255,0.52);
  margin-top: 16px;

  .link-accent {
    color: #977aed;
    font-weight: 700;
    margin-left: 4px;
    &:hover { color: #6c58bf; }
  }
}

// ── 步骤切换动画 ──────────────────────────────
.step-enter-active { animation: stepIn 0.28s ease both; }
.step-leave-active { animation: stepOut 0.18s ease both; }

@keyframes stepIn {
  from { opacity: 0; transform: translateX(16px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes stepOut {
  from { opacity: 1; transform: translateX(0); }
  to   { opacity: 0; transform: translateX(-16px); }
}
</style>