<!--
  =============================================
  frontend/src/views/users/Register.vue
  注册页组件
  ============================================= --> 
<template>
  <div class="auth-page register-page">
    <div class="auth-page__brand">
      <div class="brand-content">
        <div class="brand-logo">
          <span>🎯</span>
          <span>AI面试助手</span>
        </div>
        <h1 class="brand-slogan">开启你的<br>AI面试训练之旅</h1>
        <div class="steps-preview">
          <div class="step-preview-item" v-for="(s, i) in onboardingSteps" :key="i">
            <div class="step-preview-item__num">{{ i + 1 }}</div>
            <div>
              <p class="step-preview-item__title">{{ s.title }}</p>
              <p class="step-preview-item__desc">{{ s.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="auth-page__form">
      <div class="form-container">
        <div class="mobile-logo">
          <span>🎯</span>
          <span>AI面试助手</span>
        </div>

        <!-- 步骤进度条 -->
        <div class="step-progress">
          <div
            v-for="n in totalSteps"
            :key="n"
            class="step-dot"
            :class="{ active: currentStep === n, done: currentStep > n }"
          >
            <span v-if="currentStep > n">✓</span>
            <span v-else>{{ n }}</span>
          </div>
          <div
            class="step-line"
            :style="{ width: ((currentStep - 1) / (totalSteps - 1) * 100) + '%' }"
          />
        </div>

        <div class="form-header">
          <h2>{{ stepTitles[currentStep - 1].title }}</h2>
          <p>{{ stepTitles[currentStep - 1].sub }}</p>
        </div>

        <form @submit.prevent="handleSubmit" novalidate>
          <!-- Step 1: 账号信息 -->
          <transition name="step" mode="out-in">
            <div v-if="currentStep === 1" key="step1" class="step-fields">

              <div class="form-group">
                <label>邮箱地址 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
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
                <span v-if="errors.email" class="form-error">{{ errors.email }}</span>
              </div>

              <div class="form-group">
                <label>手机号码（可选）</label>
                <div class="input-wrapper">
                  <span class="input-icon">
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
                <span v-if="errors.phone" class="form-error">{{ errors.phone }}</span>
              </div>

              <div class="form-group">
                <label>设置密码 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
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
                  <button type="button" class="toggle-password" @click="showPassword = !showPassword">
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
                <div class="password-strength" v-if="form.password">
                  <div class="strength-bar">
                    <div
                      class="strength-bar__fill"
                      :class="passwordStrength.level"
                      :style="{ width: passwordStrength.percent + '%' }"
                    />
                  </div>
                  <span class="strength-label" :class="passwordStrength.level">{{ passwordStrength.text }}</span>
                </div>
                <span v-if="errors.password" class="form-error">{{ errors.password }}</span>
              </div>

              <div class="form-group">
                <label>确认密码 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
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
                <span v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</span>
              </div>
            </div>
          </transition>

          <!-- Step 2: 个人信息 -->
          <transition name="step" mode="out-in">
            <div v-if="currentStep === 2" key="step2" class="step-fields">
              <div class="form-group">
                <label>真实姓名 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.realName"
                    type="text"
                    placeholder="请输入真实姓名"
                    class="form-control with-icon"
                    :class="{ error: errors.realName }"
                  />
                </div>
                <span v-if="errors.realName" class="form-error">{{ errors.realName }}</span>
              </div>


              <div class="form-group">
                <label>你的昵称 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </span>
                  <input
                    v-model="form.username"
                    type="text"
                    placeholder="请输入昵称"
                    class="form-control with-icon"
                    :class="{ error: errors.username }"
                    autocomplete="nickname"
                  />
                </div>
                <span v-if="errors.username" class="form-error">{{ errors.username }}</span>
              </div>

              <div class="form-group">
                <label>就读学校 *</label>
                <div class="input-wrapper">
                  <span class="input-icon">
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
                <span v-if="errors.school" class="form-error">{{ errors.school }}</span>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>专业方向 *</label>
                  <input
                    v-model="form.major"
                    type="text"
                    placeholder="如：计算机科学"
                    class="form-control"
                    :class="{ error: errors.major }"
                  />
                  <span v-if="errors.major" class="form-error">{{ errors.major }}</span>
                </div>
                <div class="form-group">
                  <label>年级 *</label>
                  <select v-model="form.grade" class="form-control form-select">
                    <option value="">选择年级</option>
                    <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
                  </select>
                  <span v-if="errors.grade" class="form-error">{{ errors.grade }}</span>
                </div>
              </div>
            </div>
          </transition>

          <!-- 全局错误 -->
          <div v-if="globalError" class="global-error">
            <span>⚠️</span> {{ globalError }}
          </div>

          <!-- 按钮区 -->
          <div class="form-actions">
            <button
              v-if="currentStep > 1"
              type="button"
              class="btn btn-outline"
              @click="currentStep--"
            >上一步</button>

            <button
              v-if="currentStep < totalSteps"
              type="button"
              class="btn btn-primary flex-1"
              @click="nextStep"
            >下一步</button>

            <button
              v-if="currentStep === totalSteps"
              type="submit"
              class="btn btn-primary flex-1 submit-btn"
              :disabled="loading"
            >
              <span v-if="loading" class="btn-spinner"></span>
              <span>{{ loading ? '注册中...' : '完成注册' }}</span>
            </button>
          </div>
        </form>

        <div class="form-footer">
          <span>已有账号？</span>
          <router-link to="/login" class="link-primary">立即登录</router-link>
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
        realName: '',
        confirmPassword: '',
        username: '',
        school: '',
        major: '',
        grade: ''
      },
      errors: {},
      globalError: '',
      showPassword: false,
      loading: false,
      gradeOptions: GRADE_OPTIONS.map(o => o.value),
      stepTitles: [
        { title: '创建账号', sub: '填写登录信息，保障账号安全' },
        { title: '完善资料', sub: '帮助AI更精准地了解你' }
      ],
      onboardingSteps: [
        { title: '创建账号', desc: '填写邮箱和密码，快速注册' },
        { title: '完善资料', desc: '告诉我们你的学校和专业' },
        { title: '选择岗位', desc: '指定目标岗位，开始练习' },
        { title: '开始面试', desc: '与AI面试官展开对话' }
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

if (phone && !/^1\d{10}$/.test(phone)) { // 原规则：/^1[3-9]\d{9}$/
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

// 修改 validateStep2 方法
    validateStep2() {
      this.errors = {}
      if (!this.form.realName.trim()) {
        this.errors.realName = '请输入真实姓名'
      }
      if (!this.form.username.trim()) {
        this.errors.username = '请输入昵称'
      }
      if (!this.form.school.trim()) {
        this.errors.school = '请输入就读学校'
      }
      if (!this.form.major.trim()) {
        this.errors.major = '请输入专业方向'
      }
      if (!this.form.grade.trim()) {
        this.errors.grade = '请选择年级'
      }
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
        // const { ...submitData } = this.form
        const { confirmPassword, ...submitData } = this.form
        submitData.real_name = submitData.realName
        delete submitData.realName // 移除驼峰命名的字段
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
.auth-page {
  min-height: 100vh;
  display: flex;

  &__brand {
    flex: 1;
    background: $gradient-primary;
    position: relative;
    overflow: hidden;
    display: none;

    @media (min-width: 768px) {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    &::before {
      content: '';
      position: absolute;
      width: 500px; height: 500px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
      top: -100px; right: -100px;
    }
  }

  &__form {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl $spacing-base;
    background: $bg-page;

    @media (min-width: 768px) {
      width: 500px;
      flex-shrink: 0;
      background: white;
      padding: $spacing-3xl $spacing-4xl;
    }
  }
}

.brand-content {
  position: relative;
  z-index: 1;
  padding: $spacing-3xl $spacing-4xl;
  color: white;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-2xl;
  font-family: $font-family-display;
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  span:first-child { font-size: 36px; }
}

.brand-slogan {
  font-family: $font-family-display;
  font-size: 30px;
  font-weight: $font-weight-extrabold;
  line-height: 1.25;
  letter-spacing: -0.02em;
  margin-bottom: $spacing-3xl;
  color: white;
}

.steps-preview {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

.step-preview-item {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;

  &__num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: $font-size-sm;
    font-weight: $font-weight-bold;
    color: white;
    flex-shrink: 0;
  }

  &__title {
    font-weight: $font-weight-semibold;
    color: white;
    font-size: $font-size-base;
    margin-bottom: 2px;
  }

  &__desc {
    font-size: $font-size-sm;
    color: rgba(255,255,255,0.65);
  }
}

.form-container {
  width: 100%;
  max-width: 420px;
}

.mobile-logo {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $primary;
  margin-bottom: $spacing-lg;
  font-family: $font-family-display;
  span:first-child { font-size: 28px; }
  @media (min-width: 768px) { display: none; }
}

.step-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-3xl;
  margin-bottom: $spacing-xl;
  position: relative;
  padding: $spacing-sm 0;
}

.step-line {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translateX(-50%) translateY(-50%);
  height: 2px;
  background: $primary;
  transition: width $transition-slow;
  z-index: 0;
}

.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  border: 2px solid $border-color;
  background: white;
  color: $text-muted;
  transition: all $transition-base;
  position: relative;
  z-index: 1;

  &.active {
    border-color: $primary;
    background: $primary;
    color: white;
    box-shadow: 0 0 0 4px $primary-bg;
  }
  &.done {
    border-color: $primary;
    background: $primary-bg;
    color: $primary;
  }
}

.form-header {
  margin-bottom: $spacing-xl;
  h2 {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-extrabold;
    color: $text-primary;
    margin-bottom: 4px;
  }
  p { font-size: $font-size-sm; color: $text-muted; }
}

.step-fields .form-group {
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

.input-wrapper { position: relative; }
.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: $text-muted;
  display: flex;
  align-items: center;
  pointer-events: none;
  svg { width: 16px; height: 16px; }
}

.form-control {
  &.with-icon { padding-left: 42px; }
  &.with-icon-right { padding-right: 44px; }
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

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: $text-muted;
  display: flex;
  align-items: center;
  padding: 4px;
  svg { width: 16px; height: 16px; }
  &:hover { color: $text-primary; }
}

.password-strength {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-top: $spacing-xs;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: $gray-200;
  border-radius: 2px;
  overflow: hidden;

  &__fill {
    height: 100%;
    border-radius: 2px;
    transition: width $transition-base;
    &.weak { background: $danger; }
    &.fair { background: $warning; }
    &.good { background: $info; }
    &.strong { background: $success; }
  }
}

.strength-label {
  font-size: $font-size-xs;
  font-weight: $font-weight-medium;
  &.weak { color: $danger; }
  &.fair { color: $warning; }
  &.good { color: $info; }
  &.strong { color: $success; }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-md;
}

.global-error {
  background: $danger-bg;
  border: 1px solid rgba(239,68,68,0.2);
  color: $danger;
  padding: $spacing-md $spacing-base;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  margin-bottom: $spacing-base;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.form-actions {
  display: flex;
  gap: $spacing-md;
  margin-top: $spacing-lg;

  .flex-1 { flex: 1; }
}

.submit-btn {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.form-footer {
  text-align: center;
  font-size: $font-size-sm;
  color: $text-muted;
  margin-top: $spacing-lg;
  .link-primary {
    color: $primary;
    font-weight: $font-weight-semibold;
    margin-left: 4px;
  }
}

// 步骤切换动画
.step-enter-active { animation: stepIn 0.3s ease both; }
.step-leave-active { animation: stepOut 0.2s ease both; }

@keyframes stepIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes stepOut {
  from { opacity: 1; transform: translateX(0); }
  to { opacity: 0; transform: translateX(-20px); }
}
</style>