<template>
  <div class="auth-page">
    <!-- 左侧品牌区 -->
    <div class="auth-page__brand">
      <div class="brand-content">
        <div class="brand-logo">
          <span class="brand-logo__icon">🎯</span>
          <span class="brand-logo__text">AI面试助手</span>
        </div>
        <h1 class="brand-slogan">用AI驱动的模拟面试<br>让你从容应对每一次挑战</h1>
        <div class="brand-features">
          <div
            class="feature-item"
            v-for="(f, i) in features"
            :key="i"
            :style="{ animationDelay: i * 0.12 + 's' }"
          >
            <span class="feature-item__icon">{{ f.icon }}</span>
            <span>{{ f.text }}</span>
          </div>
        </div>
        <div class="brand-stats">
          <div class="stat-item" v-for="s in stats" :key="s.label">
            <span class="stat-item__value">{{ s.value }}</span>
            <span class="stat-item__label">{{ s.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="auth-page__form">
      <div class="form-container">
        <div class="mobile-logo">
          <span>🎯</span>
          <span>AI面试助手</span>
        </div>

        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>登录账号，继续你的面试之旅</p>
        </div>

        <div class="login-tabs">
          <button
            v-for="tab in loginTabs"
            :key="tab.key"
            :class="['tab-btn', { active: loginType === tab.key }]"
            @click="loginType = tab.key"
          >{{ tab.label }}</button>
        </div>

        <form class="login-form" @submit.prevent="handleLogin" novalidate>
          <div class="form-group">
            <label>{{ loginType === 'email' ? '邮箱地址' : '手机号码' }}</label>
            <div class="input-wrapper">
              <span class="input-icon">
                <svg v-if="loginType === 'email'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/>
                  <path d="M2 7l10 7 10-7"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                  <line x1="12" y1="18" x2="12.01" y2="18"/>
                </svg>
              </span>
              <input
                v-model="form.loginId"
                :type="loginType === 'email' ? 'email' : 'tel'"
                :placeholder="loginType === 'email' ? 'test@example.com' : '请输入手机号码'"
                class="form-control with-icon"
                :class="{ error: errors.loginId }"
                autocomplete="username"
              />
            </div>
            <span v-if="errors.loginId" class="form-error">{{ errors.loginId }}</span>
          </div>

          <div class="form-group">
            <label>
              <span>密码</span>
              <a href="#" class="forgot-link" @click.prevent>忘记密码？</a>
            </label>
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
                placeholder="请输入密码（演示：123456）"
                class="form-control with-icon with-icon-right"
                :class="{ error: errors.password }"
                autocomplete="current-password"
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
            <span v-if="errors.password" class="form-error">{{ errors.password }}</span>
          </div>

          <div v-if="globalError" class="global-error">
            <span>⚠️</span> {{ globalError }}
          </div>

          <button
            type="submit"
            class="btn btn-primary btn-block submit-btn"
            :disabled="loading"
          >
            <span v-if="loading" class="btn-spinner"></span>
            <span>{{ loading ? '登录中...' : '立即登录' }}</span>
          </button>
        </form>

        <div class="divider">或</div>

        <div class="form-footer">
          <span>还没有账号？</span>
          <router-link to="/register" class="link-primary">免费注册</router-link>
        </div>

        <div class="demo-hint">
          <span>🔑</span>
          <span>演示账号：test@example.com / 123456</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'LoginPage',
  data() {
    return {
      loginType: 'email',
      loginTabs: [
        { key: 'email', label: '邮箱登录' },
        { key: 'phone', label: '手机登录' }
      ],
      form: {
        loginId: '',
        password: ''
      },
      errors: {},
      globalError: '',
      showPassword: false,
      loading: false,
      features: [
        { icon: '🤖', text: 'AI智能面试官，真实模拟企业场景' },
        { icon: '📊', text: '多维度能力评估，精准定位短板' },
        { icon: '📚', text: '个性化学习推荐，高效补强弱项' },
        { icon: '🚀', text: '持续练习，显著提升面试通过率' }
      ],
      stats: [
        { value: '10,000+', label: '练习用户' },
        { value: '50+', label: '岗位类型' },
        { value: '98%', label: '好评率' }
      ]
    }
  },
  methods: {
    ...mapActions('user', ['login']),

    validate() {
      this.errors = {}
      const { loginId, password } = this.form

      if (!loginId) {
        this.errors.loginId = `请输入${this.loginType === 'email' ? '邮箱地址' : '手机号码'}`
      } else if (this.loginType === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(loginId)) {
        this.errors.loginId = '请输入有效的邮箱地址'
      } else if (this.loginType === 'phone' && !/^1[3-9]\d{9}$/.test(loginId)) {
        this.errors.loginId = '请输入有效的手机号码'
      }

      if (!password) {
        this.errors.password = '请输入密码'
      } else if (password.length < 6) {
        this.errors.password = '密码不能少于6位'
      }

      return Object.keys(this.errors).length === 0
    },

    async handleLogin() {
      if (!this.validate()) return
      this.globalError = ''
      this.loading = true
      try {
        await this.login({
          loginId: this.form.loginId,
          password: this.form.password,
          loginType: this.loginType
        })
        const redirect = this.$route.query.redirect || '/dashboard'
        this.$router.push(redirect)
      } catch (err) {
        this.globalError = err.message || '登录失败，请检查账号密码'
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
    background: $gradient-dark;
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
      width: 600px; height: 600px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(67,56,202,0.35) 0%, transparent 70%);
      top: -150px; right: -150px;
    }
    &::after {
      content: '';
      position: absolute;
      width: 400px; height: 400px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(124,58,237,0.25) 0%, transparent 70%);
      bottom: 0; left: -80px;
    }
  }

  &__form {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-2xl $spacing-base;
    background: $bg-page;

    @media (min-width: 768px) {
      width: 460px;
      flex-shrink: 0;
      background: white;
      padding: $spacing-4xl;
    }
  }
}

.brand-content {
  position: relative;
  z-index: 1;
  padding: $spacing-3xl $spacing-4xl;
  color: white;
  max-width: 480px;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-2xl;

  &__icon { font-size: 36px; }
  &__text {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
  }
}

.brand-slogan {
  font-family: $font-family-display;
  font-size: 28px;
  font-weight: $font-weight-extrabold;
  line-height: 1.3;
  letter-spacing: -0.02em;
  margin-bottom: $spacing-2xl;
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.65) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
  margin-bottom: $spacing-3xl;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  font-size: $font-size-base;
  color: rgba(255,255,255,0.78);
  animation: fadeSlideUp 0.5s ease both;

  &__icon { font-size: 20px; flex-shrink: 0; }
}

.brand-stats {
  display: flex;
  gap: $spacing-2xl;
  padding-top: $spacing-xl;
  border-top: 1px solid rgba(255,255,255,0.15);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 3px;

  &__value {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    color: white;
  }
  &__label {
    font-size: $font-size-xs;
    color: rgba(255,255,255,0.5);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
}

.form-container {
  width: 100%;
  max-width: 400px;
}

.mobile-logo {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $primary;
  margin-bottom: $spacing-2xl;
  font-family: $font-family-display;

  span:first-child { font-size: 30px; }

  @media (min-width: 768px) { display: none; }
}

.form-header {
  margin-bottom: $spacing-xl;
  h2 {
    font-family: $font-family-display;
    font-size: $font-size-3xl;
    font-weight: $font-weight-extrabold;
    letter-spacing: -0.03em;
    color: $text-primary;
    margin-bottom: 6px;
  }
  p { font-size: $font-size-base; color: $text-muted; }
}

.login-tabs {
  display: flex;
  background: $gray-100;
  border-radius: $border-radius;
  padding: 3px;
  margin-bottom: $spacing-xl;
}

.tab-btn {
  flex: 1;
  padding: 9px;
  border: none;
  background: transparent;
  border-radius: calc($border-radius - 3px);
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $text-muted;
  cursor: pointer;
  transition: all $transition-base;
  font-family: $font-family-base;

  &.active {
    background: white;
    color: $primary;
    font-weight: $font-weight-semibold;
    box-shadow: $shadow-sm;
  }
}

.login-form {
  .form-group {
    margin-bottom: $spacing-lg;
    label {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      font-weight: $font-weight-semibold;
      color: $text-secondary;
      margin-bottom: $spacing-sm;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
  }
}

.forgot-link {
  font-size: $font-size-sm;
  color: $primary;
  text-transform: none;
  letter-spacing: 0;
  font-weight: $font-weight-medium;
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
  svg { width: 17px; height: 17px; }
}

.form-control {
  &.with-icon { padding-left: 44px; }
  &.with-icon-right { padding-right: 48px; }
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
  border-radius: 6px;
  transition: color $transition-fast;
  svg { width: 17px; height: 17px; }
  &:hover { color: $text-primary; }
}

.global-error {
  background: $danger-bg;
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: $danger;
  padding: $spacing-md $spacing-base;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  margin-bottom: $spacing-base;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.submit-btn {
  height: 52px;
  font-size: $font-size-md;
  letter-spacing: 0.02em;
  margin-top: $spacing-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.divider {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  color: $text-muted;
  font-size: $font-size-sm;
  margin: $spacing-xl 0;
  &::before, &::after { content: ''; flex: 1; height: 1px; background: $border-color; }
}

.form-footer {
  text-align: center;
  font-size: $font-size-sm;
  color: $text-muted;
  .link-primary {
    color: $primary;
    font-weight: $font-weight-semibold;
    margin-left: 4px;
  }
}

.demo-hint {
  margin-top: $spacing-lg;
  padding: $spacing-md $spacing-base;
  background: $primary-bg;
  border-radius: $border-radius;
  font-size: $font-size-xs;
  color: $primary;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  text-align: center;
  justify-content: center;
}
</style>