<!--
  =============================================
  frontend/src/views/interview/JobSelection.vue
  岗位选择页组件
  ============================================= -->
<template>
  <div class="job-selection-page">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="header-inner">
        <button class="back-btn" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="header-text">
          <h1>选择岗位</h1>
          <p>选择目标岗位，开始 AI 模拟面试</p>
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <span class="search-box__icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索岗位或技术栈..."
          class="search-box__input"
        />
        <button v-if="searchQuery" class="search-box__clear" @click="searchQuery = ''">✕</button>
      </div>
    </div>

    <!-- 主体 -->
    <div class="page-body">
      <!-- 过滤标签 -->
      <div class="filter-tabs">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          :class="['filter-tab', { active: activeFilter === tab.key }]"
          @click="activeFilter = tab.key"
        >{{ tab.label }}</button>
      </div>

      <!-- 岗位列表 -->
      <div v-if="filteredJobs.length > 0" class="job-grid">
        <div
          v-for="(job, idx) in filteredJobs"
          :key="job.id"
          class="job-card"
          :class="{ selected: currentSelected && currentSelected.id === job.id }"
          :style="{ animationDelay: idx * 0.06 + 's' }"
          @click="toggleSelect(job)"
        >
          <!-- 选中勾 -->
          <div v-if="currentSelected && currentSelected.id === job.id" class="job-card__check">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>

          <!-- 图标 -->
          <div class="job-card__icon-wrap" :style="{ background: job.colorBg }">
            <span class="job-card__icon">{{ job.icon }}</span>
          </div>

          <!-- 信息 -->
          <div class="job-card__header">
            <h3 class="job-card__name">{{ job.name }}</h3>
            <span :class="['level-badge', 'level-' + job.level]">{{ job.level }}</span>
          </div>

          <p class="job-card__desc">{{ job.description }}</p>

          <!-- 技术栈 -->
          <div class="job-card__stack">
            <span v-for="tech in job.techStack.slice(0, 4)" :key="tech" class="stack-tag">
              {{ tech }}
            </span>
          </div>

          <!-- 底部：题型 + 均分 -->
          <div class="job-card__footer">
            <div class="job-card__types">
              <span v-for="t in job.questionTypes.slice(0, 2)" :key="t" class="type-tag">{{ t }}</span>
            </div>
            <div class="job-card__avg">
              <span class="avg-label">均分</span>
              <span class="avg-value" :style="{ color: job.color }">{{ job.avgScore }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索空态 -->
      <div v-else class="empty-state-wrap">
        <span style="font-size:48px">🔍</span>
        <p>没有找到匹配的岗位</p>
        <button class="btn btn-ghost btn-sm" @click="searchQuery = ''; activeFilter = 'all'">清空筛选</button>
      </div>

      <div style="height: 120px;" />
    </div>

    <!-- 底部操作栏 -->
    <transition name="action-bar">
      <div v-if="currentSelected" class="bottom-action-bar">
        <label class="remember-check">
          <input type="checkbox" v-model="rememberChoice" />
          <span class="remember-check__box">
            <svg v-if="rememberChoice" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </span>
          <span>记住选择</span>
        </label>

        <button class="start-btn" @click="handleStart">
          <span class="start-btn__main">开始面试</span>
          <span class="start-btn__sub">{{ currentSelected.name }}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
import { JOB_TYPES } from '@/utils/constants'

export default {
  name: 'JobSelection',
  data() {
    return {
      searchQuery: '',
      activeFilter: 'all',
      currentSelected: null,
      rememberChoice: false,
      filterTabs: [
        { key: 'all', label: '全部岗位' },
        { key: '中级', label: '中级' },
        { key: '高级', label: '高级' }
      ],
      jobDbIdMap: {}
    }
  },
  computed: {
    filteredJobs() {
      let jobs = JOB_TYPES
      if (this.activeFilter !== 'all') {
        jobs = jobs.filter(j => j.level === this.activeFilter)
      }
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.toLowerCase()
        jobs = jobs.filter(j =>
          j.name.toLowerCase().includes(q) ||
          j.techStack.some(t => t.toLowerCase().includes(q)) ||
          j.description.toLowerCase().includes(q)
        )
      }
      return jobs
    }
  },
created() {
  // 核心修改1：将异步逻辑封装到 async 函数中并立即执行
  const initJobs = async () => {
    try {
      const { fetchJobs } = await import('@/api/job')
      const jobs = await fetchJobs()
      console.log('后端岗位列表:', jobs)
      if (jobs && jobs.length) {
        // 用后端返回的name匹配前端的JOB_TYPES，建立 frontKey→dbId 映射
        const nameToKey = {
          'Java后端开发': 'java-backend',
          '前端开发': 'web-frontend',
          'Python算法工程师': 'python-algorithm',
          '全栈开发工程师': 'fullstack',
          'Android开发': 'android',
          'DevOps工程师': 'devops'
        }
        jobs.forEach(j => {
          const key = nameToKey[j.name]
          if (key) this.jobDbIdMap[key] = j.id
        })
        
        console.log('岗位列表加载成功，jobDbIdMap:', this.jobDbIdMap)
      }
    } catch (e) {
      console.warn('加载岗位列表失败，使用本地 dbId 兜底', e)
    }

    // 回显 store 中已选岗位 或 用户默认岗位
    const storeJob = this.$store.getters['interview/selectedJob']
    if (storeJob) {
      this.currentSelected = storeJob
    } else {
      const defaultJobId = this.$store.getters['user/defaultJob']
      if (defaultJobId) {
        this.currentSelected = JOB_TYPES.find(j => j.id === defaultJobId) || null
      }
    }
  }

  // 核心修改2：立即执行异步初始化函数
  initJobs()
},
  methods: {
    toggleSelect(job) {
      this.currentSelected = this.currentSelected?.id === job.id ? null : job
    },

// async handleStart() {
//   const job = this.selectedJob
//   console.log('开始面试，选择的岗位:', job)
//   const dbId = this.jobDbIdMap[job.id] || job.dbId  // 优先用后端返回的，兜底用constants里的
//   await this.$store.dispatch('interview/selectJob', job)
//   await this.$store.dispatch('interview/resetInterview')
//   // 把 dbId 也存到 store，后续 startSession 用
//   this.$store.commit('interview/SET_JOB_DB_ID', dbId)
//   this.$router.push('/interview/session')
// },

// JobSelection.vue 的 handleStart 方法完整修复版
async handleStart() {
  //  关键1：校验选中的岗位是否存在
  console.log('准备开始面试，当前选中岗位:', this.currentSelected)
  if (!this.currentSelected) {
    this.$message.error('请先选择一个面试岗位！');
    return;
  }
  
  try {
    // 关键2：正确获取岗位数据库ID（优先后端映射的jobDbIdMap，兜底用constants里的dbId）
    const jobDbId = this.jobDbIdMap[this.currentSelected.id] || this.currentSelected.dbId|| this.currentSelected.id;
    console.log('传递给 Vuex 的岗位数据库 ID:', jobDbId);
    
    // 关键3：先重置面试状态，再存储数据
    await this.$store.dispatch('interview/resetInterview');
    this.$store.commit('interview/SET_JOB_DB_ID', jobDbId); // 传给后端的数字 ID
    await this.$store.dispatch('interview/selectJob', this.currentSelected); // 传递完整岗位对象
    
    // 跳转到面试会话页
    this.$router.push('/interview/session');
  } catch (err) {
    console.error('启动面试失败：', err);
    this.$message.error('启动面试失败，请重试！');
  }
}
  }
}
</script>

<style lang="scss" scoped>
.job-selection-page {
  min-height: 100vh;
  background: $bg-page;
}

// ---- Header ----
.page-header {
  background: $gradient-primary;
  padding: 52px $spacing-base $spacing-lg;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 280px; height: 280px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 70%);
    top: -80px; right: -60px;
    pointer-events: none;
  }
}

.header-inner {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-base;
  position: relative;
  z-index: 1;
}

.back-btn {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0;
  transition: background $transition-fast;
  color: white;
  svg { width: 18px; height: 18px; }
  &:hover { background: rgba(255,255,255,0.25); }
}

.header-text {
  position: relative; z-index: 1;
  h1 {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-extrabold;
    color: white;
    margin-bottom: 3px;
  }
  p { font-size: $font-size-sm; color: rgba(255,255,255,0.65); }
}

.search-box {
  position: relative; z-index: 1;

  &__icon {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    color: $text-muted; display: flex; align-items: center; pointer-events: none;
    svg { width: 16px; height: 16px; }
  }

  &__input {
    width: 100%; height: 44px;
    padding: 0 38px 0 42px;
    background: white; border: none;
    border-radius: $border-radius-full;
    font-size: $font-size-base; color: $text-primary;
    outline: none; font-family: $font-family-base;
    box-shadow: $shadow-md;
    &::placeholder { color: $text-muted; }
  }

  &__clear {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    background: $gray-200; border: none;
    width: 20px; height: 20px; border-radius: 50%;
    cursor: pointer; font-size: $font-size-xs; color: $text-muted;
    display: flex; align-items: center; justify-content: center;
    transition: background $transition-fast;
    &:hover { background: $gray-300; }
  }
}

// ---- Body ----
.page-body {
  padding: $spacing-base;
}

.filter-tabs {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-base;
  overflow-x: auto;
  padding-bottom: 2px;
  &::-webkit-scrollbar { display: none; }
}

.filter-tab {
  padding: 7px $spacing-base;
  border-radius: $border-radius-full;
  border: 1.5px solid $border-color;
  background: white;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: $text-secondary;
  cursor: pointer;
  font-family: $font-family-base;
  transition: all $transition-fast;
  white-space: nowrap;

  &.active { background: $primary; border-color: $primary; color: white; box-shadow: 0 4px 12px rgba(67,56,202,0.3); }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

// ---- 岗位网格 ----
.job-grid {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.job-card {
  background: white;
  border-radius: $border-radius-lg;
  padding: $spacing-base;
  border: 2px solid $border-color;
  cursor: pointer;
  transition: all $transition-base;
  position: relative;
  animation: fadeSlideUp 0.45s ease both;
  box-shadow: $shadow-sm;
  overflow: hidden;

  &:hover {
    border-color: rgba(67,56,202,0.4);
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }

  &.selected {
    border-color: $primary;
    background: $primary-bg;
    box-shadow: 0 0 0 1px $primary, $shadow-md;
  }

  &__check {
    position: absolute; top: $spacing-md; right: $spacing-md;
    width: 26px; height: 26px; border-radius: 50%;
    background: $primary; display: flex; align-items: center; justify-content: center;
    color: white; animation: scaleIn 0.25s $transition-spring both;
    box-shadow: 0 2px 8px rgba(67,56,202,0.4);
    svg { width: 13px; height: 13px; }
  }

  &__icon-wrap {
    width: 52px; height: 52px; border-radius: $border-radius;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: $spacing-md;
  }
  &__icon { font-size: 26px; }

  &__header {
    display: flex; align-items: center; gap: $spacing-sm;
    margin-bottom: 6px;
  }
  &__name {
    font-size: $font-size-lg; font-weight: $font-weight-bold;
    color: $text-primary; flex: 1;
  }

  &__desc {
    font-size: $font-size-sm; color: $text-secondary;
    line-height: $line-height-normal; margin-bottom: $spacing-md;
  }

  &__stack {
    display: flex; flex-wrap: wrap; gap: $spacing-xs;
    margin-bottom: $spacing-md;
  }

  &__footer {
    display: flex; align-items: center; justify-content: space-between;
    padding-top: $spacing-md; border-top: 1px solid $gray-100;
  }
  &__types { display: flex; gap: $spacing-xs; }
  &__avg { display: flex; align-items: center; gap: 4px; }
}

.level-badge {
  font-size: $font-size-xs; font-weight: $font-weight-semibold;
  padding: 3px 10px; border-radius: $border-radius-full;
  flex-shrink: 0;
  &.level-中级 { background: $info-bg; color: $info; }
  &.level-高级 { background: $warning-bg; color: darken($warning, 20%); }
  &.level-初级 { background: $success-bg; color: darken($success, 10%); }
}

.stack-tag {
  font-size: $font-size-xs; font-weight: $font-weight-medium;
  background: $gray-100; color: $text-secondary;
  padding: 3px 8px; border-radius: $border-radius-full;
  border: 1px solid $gray-200;
  transition: all $transition-fast;

  .selected & { background: rgba(67,56,202,0.08); border-color: rgba(67,56,202,0.2); color: $primary; }
}

.type-tag {
  font-size: $font-size-xs; color: $text-muted;
  background: $gray-50; padding: 2px 8px;
  border-radius: $border-radius-full; border: 1px solid $gray-200;
}

.avg-label { font-size: $font-size-xs; color: $text-muted; }
.avg-value {
  font-family: $font-family-display;
  font-size: $font-size-md; font-weight: $font-weight-bold;
}

// ---- 搜索空态 ----
.empty-state-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-4xl $spacing-xl;
  gap: $spacing-md;
  p { color: $text-muted; font-size: $font-size-base; }
}

// ---- 底部操作栏 ----
.bottom-action-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: $max-content-width;
  background: rgba(255,255,255,0.97);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid $border-color;
  padding: $spacing-md $spacing-base calc(#{$spacing-md} + env(safe-area-inset-bottom));
  box-shadow: 0 -8px 32px rgba(0,0,0,0.1);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: $spacing-md;
}

.action-bar-enter-active { animation: actionBarIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
.action-bar-leave-active { animation: actionBarOut 0.2s ease both; }
@keyframes actionBarIn { from { transform: translateX(-50%) translateY(100%); } to { transform: translateX(-50%) translateY(0); } }
@keyframes actionBarOut { from { transform: translateX(-50%) translateY(0); } to { transform: translateX(-50%) translateY(100%); } }

.remember-check {
  display: flex; align-items: center; gap: $spacing-sm;
  cursor: pointer; flex-shrink: 0;
  font-size: $font-size-sm; color: $text-secondary;
  user-select: none;
  input[type="checkbox"] { display: none; }

  &__box {
    width: 20px; height: 20px; border-radius: 6px;
    border: 2px solid $border-color; background: white;
    display: flex; align-items: center; justify-content: center;
    transition: all $transition-fast; color: white; flex-shrink: 0;
  }
  input:checked + .remember-check__box { background: $primary; border-color: $primary; }
}

.start-btn {
  flex: 1; height: 50px;
  background: $gradient-primary;
  border: none; border-radius: $border-radius-full;
  display: flex; align-items: center; justify-content: center;
  gap: $spacing-sm; cursor: pointer;
  box-shadow: $shadow-primary;
  transition: all $transition-base;
  color: white; font-family: $font-family-base;

  &:hover { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(67,56,202,0.4); }
  &:active { transform: scale(0.98); }

  &__main { font-size: $font-size-md; font-weight: $font-weight-bold; }
  &__sub {
    font-size: $font-size-xs; opacity: 0.75;
    background: rgba(255,255,255,0.18);
    padding: 2px 8px; border-radius: $border-radius-full;
  }
  svg { width: 16px; height: 16px; flex-shrink: 0; }
}
</style>