
<!--
  =============================================
  frontend/src/views/users/PersonalCenter.vue
  个人中心页组件
  ============================================= --> 
<template>
  <div class="profile-page">
    <!-- 头部 -->
    <div class="profile-header">
      <div class="profile-header__content">
        <!-- 头像 -->
        <div class="avatar-wrapper" @click="triggerAvatarUpload">
          <div class="avatar">
            <img v-if="userInfo && userInfo.avatar" :src="userInfo.avatar" alt="头像" />
            <span v-else class="avatar__fallback">{{ avatarLetter }}</span>
          </div>
          <div class="avatar-edit-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
          </div>
          <input ref="avatarInput" type="file" accept="image/*" class="hidden-input" @change="handleAvatarChange" />
        </div>

        <h1 class="profile-header__name">{{ userInfo && userInfo.username || '用户' }}</h1>
        <p class="profile-header__school">
          <span v-if="userInfo && userInfo.school">{{ userInfo.school }}</span>
          <span v-if="userInfo && userInfo.major"> · {{ userInfo.major }}</span>
          <span v-if="userInfo && userInfo.grade"> · {{ userInfo.grade }}</span>
          <span v-if="!userInfo || !userInfo.school" class="text-muted-inline">未填写学校信息</span>
        </p>

        <!-- 面试统计 -->
        <div class="profile-stats">
          <div class="profile-stat">
            <span class="profile-stat__value">{{ userInfo && userInfo.totalInterviews || 0 }}</span>
            <span class="profile-stat__label">练习次数</span>
          </div>
          <div class="profile-stat-divider" />
          <div class="profile-stat">
            <span class="profile-stat__value">{{ userInfo && userInfo.avgScore || '--' }}</span>
            <span class="profile-stat__label">平均分</span>
          </div>
          <div class="profile-stat-divider" />
          <div class="profile-stat">
            <span class="profile-stat__value">{{ memberDays }}</span>
            <span class="profile-stat__label">加入天数</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="profile-body">
      <!-- 个人信息 - 新版左右布局 -->
      <section class="profile-section">
        <div class="section-header">
          <h2 class="section-title">个人信息</h2>
          <button class="edit-btn" @click="openEditModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            编辑
          </button>
        </div>

        <div class="profile-info-card">
          <!-- 左侧：头像和岗位 -->
          <div class="profile-info-left">
            <!-- 头像区域 -->
            <div class="avatar-section">
              <div class="avatar-wrapper-lg" @click="triggerAvatarUpload">
                <div class="avatar-lg">
                  <img v-if="userInfo && userInfo.avatar" :src="userInfo.avatar" alt="头像" />
                  <span v-else class="avatar-lg__fallback">{{ avatarLetter }}</span>
                </div>
                <div class="avatar-edit-badge-lg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                  </svg>
                </div>
                <input ref="avatarInput" type="file" accept="image/*" class="hidden-input" @change="handleAvatarChange" />
              </div>
              <span class="avatar-label">{{ userInfo && userInfo.username || '用户' }}</span>
            </div>

            <div class="divider-line"></div>

            <!-- 默认岗位区域 -->
            <div class="job-section">
              <span class="job-section-label">默认岗位:</span>
              <div v-if="currentDefaultJob" class="job-display">
                <span class="job-icon">{{ currentDefaultJob.icon }}</span>
                <span class="job-name">{{ currentDefaultJob.name }}</span>
              </div>
              <div v-else class="job-display job-display--empty">
                <span>🎯</span>
                <span>未设置</span>
              </div>
              <button class="job-select-btn" @click="showJobPicker = true">
                选择岗位
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;margin-left:4px">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 分割线 -->
          <div class="profile-info-divider"></div>

          <!-- 右侧：基本信息和教育信息（横向排列） -->
          <div class="profile-info-right">
            <!-- 基本信息 -->
            <div class="info-group">
              <div class="info-group-header">
                <span class="info-group-icon">📋</span>
                <span class="info-group-title">基本信息</span>
              </div>
              <div class="info-list">
                <div class="info-item">
                  <span class="info-item__icon">👤</span>
                  <span class="info-item__label">用户昵称</span>
                  <span class="info-item__value">{{ userInfo && userInfo.username || '未填写' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__icon">📧</span>
                  <span class="info-item__label">邮箱</span>
                  <span class="info-item__value">{{ userInfo && userInfo.email || '未填写' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__icon">📱</span>
                  <span class="info-item__label">手机</span>
                  <span class="info-item__value">{{ userInfo && userInfo.phone ? maskPhone(userInfo.phone) : '未填写' }}</span>
                </div>
              </div>
            </div>

            <!-- 分割线 -->
            <div class="info-vertical-divider"></div>

            <!-- 教育信息 -->
            <div class="info-group">
              <div class="info-group-header">
                <span class="info-group-icon">🎓</span>
                <span class="info-group-title">教育信息</span>
              </div>
              <div class="info-list">
                <div class="info-item">
                  <span class="info-item__icon">🏫</span>
                  <span class="info-item__label">学校</span>
                  <span class="info-item__value">{{ userInfo && userInfo.school || '未填写' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__icon">📖</span>
                  <span class="info-item__label">专业</span>
                  <span class="info-item__value">{{ userInfo && userInfo.major || '未填写' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__icon">📅</span>
                  <span class="info-item__label">年级</span>
                  <span class="info-item__value">{{ userInfo && userInfo.grade || '未填写' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 账号安全 -->
      <section class="profile-section">
        <h2 class="section-title" style="margin-bottom: 12px">账号安全</h2>
        <div class="menu-card">
          <button
            class="menu-item"
            v-for="item in securityMenu"
            :key="item.label"
            @click="item.action"
          >
            <span class="menu-item__icon" :style="{ background: item.iconBg }">{{ item.icon }}</span>
            <div class="menu-item__content">
              <span class="menu-item__label">{{ item.label }}</span>
              <span class="menu-item__sub">{{ item.sub }}</span>
            </div>
            <svg class="menu-item__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </section>

      <!-- 关于 -->
      <section class="profile-section">
        <div class="menu-card">
          <button class="menu-item" v-for="item in aboutMenu" :key="item.label" @click="item.action && item.action()">
            <span class="menu-item__icon" :style="{ background: item.iconBg }">{{ item.icon }}</span>
            <div class="menu-item__content">
              <span class="menu-item__label">{{ item.label }}</span>
              <span class="menu-item__sub" v-if="item.sub">{{ item.sub }}</span>
            </div>
            <svg class="menu-item__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </section>

      <!-- 退出登录 -->
      <section class="profile-section">
        <button class="logout-btn" @click="confirmLogout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出登录
        </button>
      </section>

    </div>

    <!-- 编辑信息弹窗 -->
    <transition name="modal">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-sheet">
          <div class="modal-header">
            <h3>编辑个人信息</h3>
            <button class="modal-close" @click="showEditModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label>昵称</label>
              <input v-model="editForm.username" type="text" class="form-control" placeholder="请输入昵称" />
            </div>
            <div class="form-group">
              <label>学校</label>
              <input v-model="editForm.school" type="text" class="form-control" placeholder="请输入学校名称" />
            </div>
            <div class="form-group">
              <label>专业</label>
              <input v-model="editForm.major" type="text" class="form-control" placeholder="请输入专业名称" />
            </div>
            <div class="form-group">
              <label>年级</label>
              <select v-model="editForm.grade" class="form-control form-select">
                <option value="">选择年级</option>
                <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showEditModal = false">取消</button>
            <button class="btn btn-primary" :disabled="savingInfo" @click="saveUserInfo">
              <span v-if="savingInfo" class="btn-spinner"></span>
              {{ savingInfo ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 修改密码弹窗 -->
    <transition name="modal">
      <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
        <div class="modal-sheet">
          <div class="modal-header">
            <h3>修改密码</h3>
            <button class="modal-close" @click="showPasswordModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label>当前密码</label>
              <input v-model="pwdForm.oldPassword" type="password" class="form-control" placeholder="请输入当前密码" />
              <span v-if="pwdErrors.oldPassword" class="form-error">{{ pwdErrors.oldPassword }}</span>
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input v-model="pwdForm.newPassword" type="password" class="form-control" placeholder="至少6位" />
              <span v-if="pwdErrors.newPassword" class="form-error">{{ pwdErrors.newPassword }}</span>
            </div>
            <div class="form-group">
              <label>确认新密码</label>
              <input v-model="pwdForm.confirmPassword" type="password" class="form-control" placeholder="再次输入新密码" />
              <span v-if="pwdErrors.confirmPassword" class="form-error">{{ pwdErrors.confirmPassword }}</span>
            </div>
            <div v-if="pwdError" class="global-error">{{ pwdError }}</div>
            <div v-if="pwdSuccess" class="success-tip">✅ 密码修改成功！</div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showPasswordModal = false">取消</button>
            <button class="btn btn-primary" :disabled="savingPwd" @click="savePassword">
              <span v-if="savingPwd" class="btn-spinner"></span>
              {{ savingPwd ? '保存中...' : '确认修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 岗位选择弹窗 -->
    <transition name="modal">
      <div v-if="showJobPicker" class="modal-overlay" @click.self="showJobPicker = false">
        <div class="modal-sheet modal-sheet--tall">
          <div class="modal-header">
            <h3>选择默认岗位</h3>
            <button class="modal-close" @click="showJobPicker = false">✕</button>
          </div>
          <div class="modal-body job-picker-body">
            <div
              class="job-picker-item"
              v-for="job in allJobs"
              :key="job.id"
              :class="{ selected: selectedJobId === job.id }"
              @click="pickJob(job)"
            >
              <div class="job-picker-item__icon" :style="{ background: job.colorBg }">{{ job.icon }}</div>
              <div class="job-picker-item__info">
                <p class="job-picker-item__name">{{ job.name }}</p>
                <p class="job-picker-item__stack">{{ job.techStack.slice(0, 3).join(' · ') }}</p>
              </div>
              <div v-if="selectedJobId === job.id" class="job-picker-item__check">✓</div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 退出确认弹窗 -->
    <transition name="modal">
      <div v-if="showLogoutConfirm" class="modal-overlay" @click.self="showLogoutConfirm = false">
        <div class="modal-sheet modal-sheet--sm">
          <div class="modal-header">
            <h3>退出登录</h3>
          </div>
          <div class="modal-body">
            <p style="color: #64748B; font-size: 14px; line-height: 1.6">确定要退出当前账号吗？你的练习数据不会丢失。</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showLogoutConfirm = false">取消</button>
            <button class="btn btn-danger" :disabled="loggingOut" @click="handleLogout">
              <span v-if="loggingOut" class="btn-spinner btn-spinner--dark"></span>
              {{ loggingOut ? '退出中...' : '确认退出' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import { JOB_TYPES, GRADE_OPTIONS } from '@/utils/constants'

export default {
  name: 'PersonalCenter',
  data() {
    return {
      showEditModal: false,
      showPasswordModal: false,
      showJobPicker: false,
      showLogoutConfirm: false,
      savingInfo: false,
      savingPwd: false,
      loggingOut: false,
      editForm: { username: '', school: '', major: '', grade: '' },
      pwdForm: { oldPassword: '', newPassword: '', confirmPassword: '' },
      pwdErrors: {},
      pwdError: '',
      pwdSuccess: false,
      selectedJobId: null,
      gradeOptions: GRADE_OPTIONS.map(o => o.value),
      allJobs: JOB_TYPES
    }
  },
  computed: {
    ...mapGetters('user', ['userInfo', 'userName', 'defaultJob']),

    avatarLetter() {
      return (this.userName || '用').charAt(0)
    },

    infoRows() {
      const u = this.userInfo || {}
      return [
        { key: 'username', icon: '👤', label: '昵称', value: u.username },
        { key: 'email', icon: '📧', label: '邮箱', value: u.email },
        { key: 'phone', icon: '📱', label: '手机', value: u.phone ? u.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : null },
        { key: 'school', icon: '🎓', label: '学校', value: u.school },
        { key: 'major', icon: '📖', label: '专业', value: u.major },
        { key: 'grade', icon: '📅', label: '年级', value: u.grade }
      ]
    },

    currentDefaultJob() {
      const jobId = this.defaultJob
      if (!jobId) return null
      return JOB_TYPES.find(j => j.id === jobId) || null
    },

    memberDays() {
      const u = this.userInfo
      if (!u || !u.createdAt) return 0
      const days = Math.floor((Date.now() - new Date(u.createdAt)) / (1000 * 60 * 60 * 24))
      return Math.max(1, days)
    },

    securityMenu() {
      return [
        {
          label: '修改密码',
          sub: '定期修改密码，保护账号安全',
          icon: '🔒',
          iconBg: '#EEF2FF',
          action: () => { this.openPasswordModal() }
        },
        {
          label: '绑定手机',
          sub: this.userInfo && this.userInfo.phone ? '已绑定 ' + this.maskPhone(this.userInfo.phone) : '未绑定，绑定后可用手机登录',
          icon: '📱',
          iconBg: '#D1FAE5',
          action: () => {}
        }
      ]
    },

    aboutMenu() {
      return [
        { label: '使用帮助', sub: '查看操作指南', icon: '❓', iconBg: '#FEF3C7', action: () => {} },
        { label: '意见反馈', sub: '告诉我们你的想法', icon: '💬', iconBg: '#F5F3FF', action: () => {} },
        { label: '当前版本', sub: 'v1.0.0', icon: 'ℹ️', iconBg: '#F1F5F9', action: null }
      ]
    }
  },
  created() {
    this.selectedJobId = this.defaultJob
  },
  mounted() {
    // 页面加载时从数据库同步最新用户信息
    this.syncUserInfo()
  },
  methods: {
    ...mapActions('user', ['updateUserInfo', 'changePassword', 'updateDefaultJob', 'logout', 'fetchUserInfo']),

    // 从数据库同步用户信息
    async syncUserInfo() {
      try {
        await this.fetchUserInfo()
        this.selectedJobId = this.defaultJob
      } catch (err) {
        console.error('同步用户信息失败', err)
      }
    },

    maskPhone(phone) {
      return phone ? phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : ''
    },

    triggerAvatarUpload() {
      this.$refs.avatarInput.click()
    },

    handleAvatarChange(e) {
      const file = e.target.files[0]
      if (!file) return
      if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB')
        return
      }
      // TODO: 调用上传接口
      console.log('上传头像:', file)
    },

    openEditModal() {
      const u = this.userInfo || {}
      this.editForm = {
        username: u.username || '',
        school: u.school || '',
        major: u.major || '',
        grade: u.grade || ''
      }
      this.showEditModal = true
    },

    async saveUserInfo() {
      if (!this.editForm.username.trim()) return
      this.savingInfo = true
      try {
        await this.updateUserInfo(this.editForm)
        // 保存成功后从数据库同步最新数据
        await this.syncUserInfo()
        this.showEditModal = false
      } catch (e) {
        alert(e.message || '保存失败')
      } finally {
        this.savingInfo = false
      }
    },

    openPasswordModal() {
      this.pwdForm = { oldPassword: '', newPassword: '', confirmPassword: '' }
      this.pwdErrors = {}
      this.pwdError = ''
      this.pwdSuccess = false
      this.showPasswordModal = true
    },

    async savePassword() {
      this.pwdErrors = {}
      this.pwdError = ''
      this.pwdSuccess = false

      if (!this.pwdForm.oldPassword) { this.pwdErrors.oldPassword = '请输入当前密码'; return }
      if (!this.pwdForm.newPassword || this.pwdForm.newPassword.length < 6) { this.pwdErrors.newPassword = '新密码不能少于6位'; return }
      if (this.pwdForm.newPassword !== this.pwdForm.confirmPassword) { this.pwdErrors.confirmPassword = '两次密码不一致'; return }

      this.savingPwd = true
      try {
        await this.changePassword({
          oldPassword: this.pwdForm.oldPassword,
          newPassword: this.pwdForm.newPassword
        })
        this.pwdSuccess = true
        setTimeout(() => { this.showPasswordModal = false }, 1500)
      } catch (e) {
        this.pwdError = e.message || '修改失败'
      } finally {
        this.savingPwd = false
      }
    },

    async pickJob(job) {
      this.selectedJobId = job.id
      try {
        await this.updateDefaultJob(job.id)
        // 保存成功后同步用户信息，确保默认岗位显示正确
        await this.syncUserInfo()
      } catch (e) {
        console.warn('更新默认岗位失败', e)
        alert('更新默认岗位失败，请重试')
      }
      setTimeout(() => { this.showJobPicker = false }, 300)
    },

    confirmLogout() {
      this.showLogoutConfirm = true
    },

    async handleLogout() {
      this.loggingOut = true
      try {
        await this.logout()
        this.$router.push('/login')
      } finally {
        this.loggingOut = false
        this.showLogoutConfirm = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: $bg-page;
  padding-bottom: $bottom-nav-height;
}

// 头部
.profile-header {
  background: $gradient-primary;
  position: relative;
  overflow: hidden;
  padding-bottom: $spacing-lg;

  &::before {
    content: '';
    position: absolute;
    width: 350px; height: 350px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    top: -100px; right: -80px;
  }
}

.profile-header__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 52px $spacing-base $spacing-base;
  text-align: center;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: $spacing-md;
  cursor: pointer;
}

.avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  border: 3px solid rgba(255,255,255,0.4);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 100%; height: 100%; object-fit: cover; }

  &__fallback {
    font-size: 36px;
    font-weight: $font-weight-bold;
    color: white;
    font-family: $font-family-display;
  }
}

.avatar-edit-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 26px;
  height: 26px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow;
  color: $primary;
  svg { width: 13px; height: 13px; }
}

.hidden-input { display: none; }

.profile-header__name {
  font-family: $font-family-display;
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: white;
  margin-bottom: 6px;
}

.profile-header__school {
  font-size: $font-size-sm;
  color: rgba(255,255,255,0.65);
  margin-bottom: $spacing-lg;
}

.text-muted-inline { color: rgba(255,255,255,0.45); }

.profile-stats {
  display: flex;
  align-items: center;
  gap: $spacing-xl;
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: $border-radius-xl;
  padding: $spacing-md $spacing-xl;
}

.profile-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;

  &__value {
    font-family: $font-family-display;
    font-size: $font-size-xl;
    font-weight: $font-weight-extrabold;
    color: white;
    line-height: 1;
  }
  &__label { font-size: $font-size-xs; color: rgba(255,255,255,0.55); }
}

.profile-stat-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.2);
}

// 内容区
.profile-body {
  padding: $spacing-base;
  animation: fadeSlideUp 0.4s ease both;
}

.profile-section {
  margin-bottom: $spacing-lg;
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

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: $primary-bg;
  border: none;
  border-radius: $border-radius-full;
  padding: 6px $spacing-md;
  font-size: $font-size-sm;
  color: $primary;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  font-family: $font-family-base;
  transition: background $transition-fast;
  &:hover { background: darken(#EEF2FF, 4%); }
}

// 新版个人信息卡片 - 左右布局
.profile-info-card {
  display: flex;
  background: white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  overflow: hidden;
}

.profile-info-left {
  flex: 0 0 180px;
  padding: $spacing-lg $spacing-base;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1px dashed $border-color;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
}

.avatar-wrapper-lg {
  position: relative;
  cursor: pointer;
}

.avatar-lg {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 3px solid rgba(102, 126, 234, 0.3);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 100%; height: 100%; object-fit: cover; }

  &__fallback {
    font-size: 28px;
    font-weight: $font-weight-bold;
    color: white;
    font-family: $font-family-display;
  }
}

.avatar-edit-badge-lg {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow;
  color: $primary;
  svg { width: 11px; height: 11px; }
}

.avatar-label {
  font-size: 15px;
  color: $text-primary;
  font-weight: $font-weight-semibold;
  margin-top: $spacing-sm;
}

.divider-line {
  width: 80%;
  height: 1px;
  background: $border-color;
  margin: $spacing-md 0;
}

.job-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  width: 100%;
}

.job-section-label {
  font-size: $font-size-xs;
  color: $text-muted;
  font-weight: $font-weight-medium;
}

.job-display {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: $border-radius;

  .job-icon {
    font-size: 16px;
  }

  .job-name {
    font-size: $font-size-sm;
    font-weight: $font-weight-semibold;
    color: #92400e;
  }

  &--empty {
    background: $gray-100;
    .job-name {
      color: $text-muted;
    }
  }
}

.job-select-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: $primary;
  font-size: $font-size-sm;
  cursor: pointer;
  font-family: $font-family-base;
  padding: $spacing-sm $spacing-md;
  transition: opacity $transition-fast;
  &:hover { opacity: 0.8; }
}

.profile-info-divider {
  width: 1px;
  background: transparent;
}

.profile-info-right {
  flex: 1;
  padding: $spacing-lg $spacing-xl;
  display: flex;
  flex-direction: row;
  gap: $spacing-xl;
}

.info-vertical-divider {
  width: 1px;
  background: $border-color;
  align-self: stretch;
}

.info-group {
  flex: 1;
  min-width: 200px;

  &-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 1px solid $gray-100;
  }

  &-icon {
    font-size: 18px;
  }

  &-title {
    font-size: 15px;
    font-weight: $font-weight-semibold;
    color: $text-primary;
  }
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.info-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;

  &__icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  &__label {
    font-size: 14px;
    color: $text-muted;
    min-width: 70px;
  }

  &__value {
    font-size: 14px;
    color: $text-primary;
    font-weight: $font-weight-medium;
  }
}

// 响应式适配
@media (max-width: 768px) {
  .profile-info-right {
    flex-direction: column;
    gap: $spacing-lg;
  }

  .info-vertical-divider {
    width: 100%;
    height: 1px;
  }
}

@media (max-width: 480px) {
  .profile-info-card {
    flex-direction: column;
  }

  .profile-info-left {
    flex: none;
    border-right: none;
    border-bottom: 1px dashed $border-color;
    padding: $spacing-md;
  }

  .profile-info-right {
    padding: $spacing-md;
  }
}

// 信息卡片
.info-card {
  background: white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
}

.info-row {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  border-bottom: 1px solid $gray-100;

  &:last-child { border-bottom: none; }

  &__icon { font-size: 18px; flex-shrink: 0; }
  &__content { flex: 1; display: flex; flex-direction: column; gap: 2px; }
  &__label { font-size: $font-size-xs; color: $text-muted; text-transform: uppercase; letter-spacing: 0.05em; }
  &__value { font-size: $font-size-base; color: $text-primary; font-weight: $font-weight-medium; }
  &__value.muted { color: $text-muted; font-weight: $font-weight-regular; }
}

// 岗位偏好
.job-preference-card {
  background: white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
  overflow: hidden;
}

.job-selected {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;

  &__icon {
    width: 44px;
    height: 44px;
    border-radius: $border-radius;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
  }
  &__info { flex: 1; }
  &__name { font-weight: $font-weight-semibold; font-size: $font-size-base; color: $text-primary; }
  &__stack { font-size: $font-size-xs; color: $text-muted; margin-top: 2px; }
}

.job-change-btn {
  background: $primary-bg;
  border: none;
  border-radius: $border-radius-full;
  padding: 6px $spacing-md;
  color: $primary;
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  font-family: $font-family-base;
}

.job-set-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-base;
  background: none;
  border: none;
  cursor: pointer;
  font-size: $font-size-base;
  color: $text-secondary;
  font-family: $font-family-base;
  transition: background $transition-fast;
  &:hover { background: $gray-50; }
}

// 菜单卡片
.menu-card {
  background: white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $shadow-sm;
  border: 1px solid $border-color;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  background: none;
  border: none;
  border-bottom: 1px solid $gray-100;
  cursor: pointer;
  text-align: left;
  font-family: $font-family-base;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: $gray-50; }
  &:active { background: $gray-100; }

  &__icon {
    width: 36px;
    height: 36px;
    border-radius: $border-radius-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__content { flex: 1; }
  &__label { font-size: $font-size-base; font-weight: $font-weight-medium; color: $text-primary; }
  &__sub { font-size: $font-size-xs; color: $text-muted; margin-top: 1px; display: block; }

  &__arrow { width: 16px; height: 16px; color: $gray-300; flex-shrink: 0; }
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  padding: 15px;
  background: white;
  border: 1.5px solid $danger;
  border-radius: $border-radius-lg;
  color: $danger;
  font-size: $font-size-md;
  font-weight: $font-weight-semibold;
  cursor: pointer;
  font-family: $font-family-base;
  transition: all $transition-base;
  &:hover { background: $danger-bg; }
  &:active { transform: scale(0.98); }
}

// 弹窗
.modal-overlay {
  position: fixed;
  inset: 0;
  background: $bg-overlay;
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-sheet {
  width: 100%;
  max-width: $max-content-width;
  background: white;
  border-radius: $border-radius-xl $border-radius-xl 0 0;
  max-height: 80vh;
  overflow-y: auto;

  &--sm { max-height: 40vh; }
  &--tall { max-height: 85vh; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-lg $spacing-base $spacing-md;
  border-bottom: 1px solid $border-color;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;

  h3 { font-size: $font-size-lg; font-weight: $font-weight-bold; color: $text-primary; }
}

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: $gray-100;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  color: $text-muted;
  transition: all $transition-fast;
  &:hover { background: $gray-200; }
}

.modal-body {
  padding: $spacing-base;

  .form-group {
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
}

.modal-footer {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-base $spacing-xl;
  border-top: 1px solid $border-color;

  .btn { flex: 1; height: 48px; display: flex; align-items: center; justify-content: center; gap: $spacing-sm; }
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

.global-error {
  background: $danger-bg;
  border: 1px solid rgba(239,68,68,0.2);
  color: $danger;
  padding: $spacing-md;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  margin-bottom: $spacing-base;
}

.success-tip {
  background: $success-bg;
  color: darken($success, 10%);
  padding: $spacing-md;
  border-radius: $border-radius;
  font-size: $font-size-sm;
  text-align: center;
}

// 岗位选择列表
.job-picker-body { padding-top: 0; }

.job-picker-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-base;
  cursor: pointer;
  border-bottom: 1px solid $gray-100;
  transition: background $transition-fast;

  &:last-child { border-bottom: none; }
  &:hover { background: $gray-50; }

  &.selected { background: $primary-bg; }

  &__icon {
    width: 44px;
    height: 44px;
    border-radius: $border-radius;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
  }
  &__info { flex: 1; }
  &__name { font-weight: $font-weight-semibold; font-size: $font-size-base; color: $text-primary; }
  &__stack { font-size: $font-size-xs; color: $text-muted; margin-top: 2px; }
  &__check { color: $primary; font-weight: $font-weight-bold; font-size: $font-size-lg; }
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  &--dark { border-color: rgba($danger, 0.3); border-top-color: $danger; }
}

@keyframes spin { to { transform: rotate(360deg); } }

// 弹窗动画
//.modal-enter-active { animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
//.modal-leave-active { animation: modalOut 0.2s ease both; }

//@keyframes modalIn {
  ///from { opacity: 0; .modal-sheet { transform: translateY(100%); } }
  //to { opacity: 1; .modal-sheet { transform: translateY(0); } }
//}

//@keyframes modalOut {
 // from { opacity: 1; }
  //to { opacity: 0; }
//}


// 1. 定义弹窗背景的进入/离开动画
@keyframes modalIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modalOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

// 2. 定义弹窗内容（sheet）的进入/离开动画
@keyframes sheetIn {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes sheetOut {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}

// 3. 分别给弹窗容器和sheet绑定动画
.modal-enter-active { 
  animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both; 
}
.modal-leave-active { 
  animation: modalOut 0.2s ease both; 
}

// sheet的动画（和弹窗同步执行）
.modal-enter-active .modal-sheet {
  animation: sheetIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
.modal-leave-active .modal-sheet {
  animation: sheetOut 0.2s ease both;
}
</style>