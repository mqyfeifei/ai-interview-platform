<!--
  =============================================
  frontend/src/views/users/Login.vue
  登录页组件 — 毛玻璃极简风格
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
            <span class="brand-mark__name">码上offer</span>
          </div>
          <p class="brand-tagline">用 AI 驱动模拟面试<br>让你从容应对每一次挑战</p>
          <div class="brand-pills">
            <span class="pill">🤖 AI智能面试官</span>
            <span class="pill">📊 多维能力评估</span>
            <span class="pill">🚀 提升通过率</span>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="glass-card">
        <div class="mobile-logo">
          <span>🎯</span>
          <span>码上offer</span>
        </div>

        <div class="card-header">
          <h2>登录</h2>
          <p>欢迎回来，继续你的面试之旅</p>
        </div>

        <div class="login-tabs">
          <button
            v-for="tab in loginTabs"
            :key="tab.key"
            :class="['tab-btn', { active: loginType === tab.key }]"
            @click="loginType = tab.key"
          >{{ tab.label }}</button>
        </div>

        <form @submit.prevent="handleLogin" novalidate>
          <div class="field">
            <label>{{ loginType === 'email' ? '邮箱地址' : '手机号码' }}</label>
            <div class="input-wrap">
              <span class="input-ico">
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
            <span v-if="errors.loginId" class="field-err">{{ errors.loginId }}</span>
          </div>

          <div class="field">
            <label>
              <span>密码</span>
              <a href="#" class="forgot-link" @click.prevent>忘记密码？</a>
            </label>
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
                placeholder="请输入密码"
                class="form-control with-icon with-icon-right"
                :class="{ error: errors.password }"
                autocomplete="current-password"
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
            <span v-if="errors.password" class="field-err">{{ errors.password }}</span>
          </div>

          <div v-if="globalError" class="global-err">
            <span>⚠️</span> {{ globalError }}
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="loading" class="spinner" />
            <span>{{ loading ? '登录中...' : '立即登录' }}</span>
          </button>
        </form>

        <div class="divider">或</div>

        <div class="card-footer">
          <span>还没有账号？</span>
          <router-link to="/register" class="link-accent">免费注册</router-link>
        </div>

        <div class="demo-hint">
          <span>🔑</span>
          <span>演示：test@example.com / 123456</span>
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
      form: { loginId: '', password: '' },
      errors: {},
      globalError: '',
      showPassword: false,
      loading: false
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
        await this.login({ loginId: this.form.loginId, password: this.form.password })
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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

// ── 场景背景 ──────────────────────────────────
.auth-scene {
  font-family: 'Outfit', sans-serif;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: url('@/assets/backgroundA.jpg') center/cover no-repeat fixed;
  // background: radial-gradient(ellipse at 20% 50%, #21158b 0%, #200c70 40%, #0d0d1a 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.auth-scene::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(92, 77, 165, 0.7); // 调透明度控制图片能透出多少
  backdrop-filter: blur(2px);          // 轻微模糊图片本身
  z-index: 0;
}

.scene-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.scene-orb--1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%);
  top: -200px; left: -100px;
  animation: orbDrift 12s ease-in-out infinite;
}
.scene-orb--2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%);
  bottom: -150px; right: -80px;
  animation: orbDrift 15s ease-in-out infinite reverse;
}
.scene-orb--3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(167,139,250,0.15) 0%, transparent 70%);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: orbDrift 9s ease-in-out infinite 2s;
}
.scene-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}

@keyframes orbDrift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(20px, -25px) scale(1.04); }
  66%  { transform: translate(-15px, 15px) scale(0.97); }
}

// ── 布局 ──────────────────────────────────────
.auth-wrap {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  max-width: 900px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06);
}

// ── 左侧品牌区 ────────────────────────────────
.brand-panel {
  display: none;
  flex: 1;
  background: rgba(238, 235, 255, 0.35);
  // background: linear-gradient(145deg, rgba(99,102,241,0.18) 0%, rgba(139,92,246,0.12) 100%);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,0.07);
  padding: 56px 44px;
  align-items: center;
  justify-content: center;

  @media (min-width: 768px) {
    display: flex;
  }
}

.brand-inner {
  max-width: 300px;
}

.brand-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;

  &__icon { font-size: 34px; filter: drop-shadow(0 0 12px rgba(167,139,250,0.7)); }
  &__name {
    font-size: 29px;
    font-weight: 750;
    // color: white;
    color: #1e1b4b;
    letter-spacing: -0.02em;
  }
}

.brand-tagline {
  font-size: 23px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.02em;
  color: #1e1b4b; 
  margin-bottom: 32px;

}

.brand-pills {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 100px;
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  backdrop-filter: blur(8px);
  transition: all 0.2s;
  &:hover { background: rgba(255,255,255,0.12); color: white; }
}

// ── 右侧玻璃卡片 ──────────────────────────────
.glass-card {
  width: 100%;
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-left: 1px solid rgba(255,255,255,0.08);
  padding: 44px 40px;
  display: flex;
  flex-direction: column;

  @media (min-width: 768px) {
    width: 420px;
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
  margin-bottom: 28px;
  span:first-child { font-size: 26px; }
  @media (min-width: 768px) { display: none; }
}

.card-header {
  margin-bottom: 24px;
  text-align: center; 
  h2 {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #1e1b4b;
    // color: white;
    margin-bottom: 5px;
  }
  p {
    font-size: 14px;
     color: #6b7280; 
  }
}

// ── 标签切换 ──────────────────────────────────
.login-tabs {
  display: flex;
  background: rgba(238, 235, 255, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  padding: 3px;
  margin-bottom: 24px;
}

.tab-btn {
  flex: 1;
  padding: 9px;
  border: none;
  background: transparent;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280; 
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;

  &.active {
    background: white;
    color: #4338ca;
    box-shadow: 0 2px 10px rgba(99,102,241,0.2);
  }
  &:hover:not(.active) { color: rgba(255,255,255,0.7); }
}

// ── 表单字段 ──────────────────────────────────
.field {
  margin-bottom: 16px;
  label {
  display: flex;             // 保持不变
  justify-content: space-between; // 保持不变
  font-size: 13px;          // 原来是 11px
  font-weight: 700;          // 保持不变
  color: #3730a3;            // 原来是 rgba(255,255,255,0.4)，换成深蓝紫
  text-transform: none;      // 去掉全大写，中文不需要
  letter-spacing: 0.02em;   // 原来是 0.09em，适当收紧
}

  // label {
  //   display: flex;
  //   justify-content: space-between;
  //   align-items: center;
  //   font-size: 11px;
  //   font-weight: 700;
  //   color: rgba(255,255,255,0.4);
  //   text-transform: uppercase;
  //   letter-spacing: 0.09em;
  //   margin-bottom: 7px;
  // }
}

.forgot-link {
  font-size: 12px;
  color: rgba(167,139,250,0.8);
  text-transform: none;
  letter-spacing: 0;
  font-weight: 600;
  &:hover { color: #a78bfa; }
}

.input-wrap { position: relative; }

.input-ico {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(167,139,250,0.5);
  display: flex;
  align-items: center;
  pointer-events: none;
  svg { width: 15px; height: 15px; }
}

.form-control {
  background: rgba(255, 255, 255, 0.7); 
  border-radius: 12px;
  border: 1.5px solid rgba(99, 102, 241, 0.25);
  color: #1e1b4b; 
  font-size: 14px;
  padding: 12px 14px;
  transition: all 0.2s;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color:  #6366f1;
    background:  rgba(255, 255, 255, 0.9);
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
  }
  &.error {
    border-color: rgba(248,113,113,0.6);
    background: rgba(248,113,113,0.06);
  }
  &.with-icon { padding-left: 40px; }
  &.with-icon-right { padding-right: 44px; }
  &::placeholder { color: #a5b4c8; }
}

.eye-btn {
  position: absolute;
  right: 11px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(167,139,250,0.5);
  display: flex;
  align-items: center;
  padding: 4px;
  svg { width: 15px; height: 15px; }
  &:hover { color: #a78bfa; }
}

.field-err {
  display: block;
  margin-top: 5px;
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
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 7px;
}

// ── 提交按钮 ──────────────────────────────────
.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border: none;
  border-radius: 14px;
  color: white;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 4px 20px rgba(79,70,229,0.45);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(79,70,229,0.55);
  }
  &:active:not(:disabled) { transform: translateY(0); }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}

.spinner {
  width: 17px; height: 17px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

// ── 底部 ──────────────────────────────────────
.divider {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  margin: 20px 0;
  &::before, &::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.08); }
}

.card-footer {
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.52);
  .link-accent {
    color: #977aed;
    font-weight: 700;
    margin-left: 4px;
    &:hover { color: #6c58bf; }
  }
}

.demo-hint {
  margin-top: 14px;
  padding: 10px 14px;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 10px;
  font-size: 12px;
  color: rgba(167,139,250,0.8);
  display: flex;
  align-items: center;
  gap: 7px;
  justify-content: center;
}
</style>