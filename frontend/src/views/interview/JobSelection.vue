.job-grid.job-grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 14px;
}

@media (max-width: 700px) {
  .job-grid.job-grid-2col {
    grid-template-columns: 1fr;
    gap: 14px 0;
  }
}
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
      <div v-if="filteredJobs.length > 0" class="job-grid job-grid-2col">
        <div
          v-for="(job, idx) in filteredJobs"
          :key="job.id"
          class="job-card"
          :class="{
            selected: currentSelected && currentSelected.id === job.id,
            'job-card--default': normalizedDefaultJobId && normalizedDefaultJobId === String(job.id)
          }"
          :style="{
            animationDelay: idx * 0.06 + 's',
            borderColor: cardColors[idx % cardColors.length].main,
            background: cardColors[idx % cardColors.length].bg
          }"
          @click="toggleSelect(job)"
        >
          <!-- 选中勾 -->
          <div v-if="currentSelected && currentSelected.id === job.id" class="job-card__check">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <!-- 热门岗位筛选时显示TOP标记，左下角圆角徽章，金银铜色 -->
          <div v-if="activeFilter === 'popular' && job.popularRank && job.popularRank <= 3"
               :class="['job-card__rank-badge', 'top-badge', 'top-badge-' + job.popularRank]">
            <span>TOP{{ job.popularRank }}</span>
          </div>


          <!-- 精简卡片内容 -->
          <div class="job-card__mainrow">
            <div v-if="job.icon" class="job-card__icon-wrap" :style="{ background: job.colorBg }">
              <span class="job-card__icon">{{ job.icon }}</span>
            </div>
            <div class="job-card__info">
              <h3 v-if="job.name" class="job-card__name">{{ job.name }}</h3>
              <div v-if="typeof job.avg_score === 'number'" class="job-card__avgrow">
                <span class="avg-label">面试均分</span>
                <span class="avg-value" :style="{ color: job.color }">{{ job.avg_score }}</span>
              </div>
            </div>
          </div>
          <p v-if="job.description" class="job-card__desc">{{ job.description }}</p>
          <div v-if="Array.isArray(job.techStack) && job.techStack.length" class="job-card__stack">
            <span v-for="tech in job.techStack" :key="tech" class="stack-tag" :style="getTechStyle(tech)">{{ tech }}</span>
          </div>

          <!-- 默认岗位操作，固定右下角 -->
          <div class="job-card__default fixed-default-btn">
            <button v-if="normalizedDefaultJobId !== String(job.id)" class="btn-set-default" @click.stop="setDefault(job)">设为默认</button>
            <span v-else class="default-badge">默认岗位</span>
          </div>

          <!-- 底部：题型（如有） -->
          <div class="job-card__footer">
            <div v-if="Array.isArray(job.questionTypes) && job.questionTypes.length" class="job-card__types">
              <span v-for="t in job.questionTypes.slice(0, 2)" :key="t" class="type-tag">{{ t }}</span>
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
        <label class="voice-mode-toggle" :class="{ active: voiceMode }" @click="voiceMode = !voiceMode">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px;flex-shrink:0">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          <span>语音面试</span>
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


export default {
  name: 'JobSelection',
  data() {
    return {
      searchQuery: '',
      activeFilter: 'all',
      currentSelected: null,
      rememberChoice: false,
      voiceMode: false,
      filterTabs: [
        { key: 'all', label: '全部岗位' },
        { key: 'popular', label: '热门岗位' }
      ],
      jobDbIdMap: {},
      jobs: [], // 后端岗位数据
      popularIds: [] // 热门岗位 id 顺序，前端用于排序与标记
      ,cardColors: [
        { main: '#3b82f6', bg: 'linear-gradient(135deg, #e0eaff 0%, #f5faff 100%)' },
        { main: '#f59e42', bg: 'linear-gradient(135deg, #fff3e0 0%, #fffaf5 100%)' },
        { main: '#10b981', bg: 'linear-gradient(135deg, #e0fff3 0%, #f5fffa 100%)' },
        { main: '#6366f1', bg: 'linear-gradient(135deg, #e0e7ff 0%, #f5f7ff 100%)' },
        { main: '#f43f5e', bg: 'linear-gradient(135deg, #ffe0e7 0%, #fff5f7 100%)' },
        { main: '#fbbf24', bg: 'linear-gradient(135deg, #fffbe0 0%, #fffdf5 100%)' },
        { main: '#06b6d4', bg: 'linear-gradient(135deg, #e0faff 0%, #f5fdff 100%)' },
        { main: '#8b5cf6', bg: 'linear-gradient(135deg, #ede9fe 0%, #fafaff 100%)' }
      ]
    }
  },
  computed: {
    filteredJobs() {
      let jobs = this.jobs
      if (this.activeFilter === 'popular') {
        // 保持热门顺序
        jobs = this.popularIds.map(id => jobs.find(j => j.id === id)).filter(Boolean)
      }
      if (this.searchQuery.trim()) {
        const q = this.searchQuery.toLowerCase()
        jobs = jobs.filter(j =>
          (j.name && j.name.toLowerCase().includes(q)) ||
          (Array.isArray(j.techStack) && j.techStack.some(t => t.toLowerCase().includes(q))) ||
          (j.description && j.description.toLowerCase().includes(q))
        )
      }
      return jobs
    },
    // ensure comparison is done with strings to avoid type mismatch
    normalizedDefaultJobId() {
      const id = this.$store.getters['user/defaultJob']
      return id != null ? String(id) : null
    }
  },

  watch: {
    activeFilter(newVal) {
      if (newVal === 'popular') {
        this.refreshPopular()
      }
    }
  },
  async created() {
    try {
      const { fetchJobs, fetchJobAvgScores, fetchPopularJobs } = await import('@/api/job')
      let jobs = await fetchJobs()
      // 先获取均分数据
      let avgList = []
      try {
        avgList = await fetchJobAvgScores()
      } catch (_) {
        avgList = []
      }
      const avgMap = {}
      avgList.forEach(a => { if (a.id != null) avgMap[a.id] = a.avg_score })

      // 同步加载热门岗位
      let popular = []
      try {
        popular = await fetchPopularJobs()
      } catch (_) {
        popular = []
      }
      this.popularIds = (popular || []).map(p => p.id)

      // 字段适配：后端 tech_stack → techStack, icon_url → icon
      jobs = (jobs || []).map(j => ({
        ...j,
        techStack: j.tech_stack || [],
        icon: j.icon_url || '💼',
        // 兼容 level/questionTypes，后端可补充
        level: j.level || '',
        avg_score: avgMap[j.id] != null ? avgMap[j.id] : (j.avg_score || 0),
        questionTypes: j.question_types || [],
        color: j.color || '#888',
        colorBg: j.color_bg || '#f3f3f3'
      }))
      // 为前端添加排名字段
      jobs.forEach(j => {
        const idx = this.popularIds.indexOf(j.id)
        j.popularRank = idx >= 0 ? idx + 1 : null
      })
      this.jobs = jobs
    } catch (e) {
      this.jobs = []
      console.warn('加载岗位列表失败', e)
    }
    // 回显 store 中已选岗位 或 用户默认岗位
    const storeJob = this.$store.getters['interview/selectedJob']
    if (storeJob) {
      this.currentSelected = storeJob
    } else {
      const defaultJobId = this.normalizedDefaultJobId
      if (defaultJobId) {
        this.currentSelected = this.jobs.find(j => String(j.id) === defaultJobId) || null
      }
    }
  },
  methods: {
    toggleSelect(job) {
      this.currentSelected = this.currentSelected?.id === job.id ? null : job
    },
    async setDefault(job) {
      try {
        await this.$store.dispatch('user/updateDefaultJob', job.id)
        this.currentSelected = job
        // no notification as requested
      } catch (err) {
        console.error('设置默认岗位失败', err)
        // quietly fail, could show toast later if needed
      }
    },

    async refreshPopular() {
      try {
        const { fetchPopularJobs } = await import('@/api/job')
        const popular = await fetchPopularJobs()
        this.popularIds = (popular || []).map(p => p.id)
        this.jobs.forEach(j => {
          const idx = this.popularIds.indexOf(j.id)
          j.popularRank = idx >= 0 ? idx + 1 : null
        })
      } catch (e) {
        console.warn('刷新热门岗位失败', e)
      }
    },

    getTechStyle(tech) {
      // simple deterministic pastel color based on tech name
      const colors = ['#e0f7fa', '#e8f5e9', '#fff3e0', '#f3e5f5', '#e1f5fe', '#fbe9e7']
      let hash = 0
      for (let i = 0; i < tech.length; i++) {
        hash = (hash * 31 + tech.charCodeAt(i)) & 0xffffffff
      }
      const idx = Math.abs(hash) % colors.length
      return {
        background: colors[idx],
        color: '#333'
      }
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
      if (this.$message && typeof this.$message.error === 'function') {
        this.$message.error('请先选择一个面试岗位！');
      } else {
        alert('请先选择一个面试岗位！');
      }
      return;
    }
  try {
    // 关键2：正确获取岗位数据库ID（优先后端映射的jobDbIdMap，兜底用constants里的dbId）
    const jobDbId = this.jobDbIdMap[this.currentSelected.id] || this.currentSelected.dbId|| this.currentSelected.id;
    console.log('传递给 Vuex 的岗位数据库 ID:', jobDbId);
    
    // 关键3：先重置面试状态，再存储数据
    await this.$store.dispatch('interview/resetInterview');
    this.$store.commit('interview/SET_JOB_DB_ID', jobDbId); // 传给后端的数字 ID
    this.$store.commit('interview/SET_VOICE_MODE', this.voiceMode);
    await this.$store.dispatch('interview/selectJob', this.currentSelected); // 传递完整岗位对象
    
    // 跳转到面试会话页
    this.$router.push('/interview/session');
  } catch (err) {
      console.error('启动面试失败：', err);
      if (this.$message && typeof this.$message.error === 'function') {
        this.$message.error('启动面试失败，请重试！');
      } else {
        alert('启动面试失败，请重试！');
      }
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

.job-card {
  position: relative;
}
.job-card__default {
  /* inline placement just above footer divider */
  position: static;
  margin: 0 0 8px; /* add bottom gap before divider */
  text-align: right; /* move horizontally to right */
}
.job-card__default .default-badge {
  display: inline-block;
  padding: 2px 6px;
  font-size: 10px;
  color: #fff;
  background: #3b82f6;
  border-radius: 3px;
}

.job-grid.job-grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 14px;
}
.job-card {
  position: relative;
  min-height: 80px;
  padding: 10px 8px 32px 8px;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(0,0,0,0.04);
  border: 2px solid #e5e7eb;
  transition: box-shadow 0.2s, border-color 0.2s;
  background: #fff;
}
.job-card__default.fixed-default-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  margin: 0;
  text-align: right;
  z-index: 3;
}
.btn-set-default {
  font-size: 11px;
  color: #3b82f6;
  background: transparent;
  border: 1px solid #3b82f6;
  border-radius: 3px;
  padding: 2px 6px;
  cursor: pointer;
}
.btn-set-default:hover {
  background: #3b82f6;
  color: #fff;
}
.job-card__rank-badge.top-badge {
  position: absolute;
  bottom: 10px;
  left: 10px;
  font-size: 11px;
  font-weight: bold;
  min-width: 36px;
  height: 22px;
  /* badge sits in the lower-left corner with rounded right side */
  border-radius: 12px 12px 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  box-shadow: 0 2px 6px 0 rgba(0,0,0,0.08);
}
.top-badge-1 {
  background: linear-gradient(135deg, #ffd700 60%, #ffecb3 100%);
  color: #222;
}
.top-badge-2 {
  background: linear-gradient(135deg, #c0c0c0 60%, #f5f5f5 100%);
  color: #222;
}
.top-badge-3 {
  background: linear-gradient(135deg, #cd7f32 60%, #ffe0b2 100%);
  color: #222;
}
@media (max-width: 700px) {
  .job-card__default.fixed-default-btn {
    right: 6px;
    bottom: 6px;
  }
  .job-card {
    padding-bottom: 36px;
  }
}
.job-card__mainrow {
  display: flex;
  align-items: center;
  gap: 8px;
}
.job-card__icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: #f3f3f3;
}
.job-card__footer-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 4px;
}
.job-card__default {
  position: static;
  margin: 0;
  text-align: right;
}
.btn-set-default {
  font-size: 11px;
  color: #3b82f6;
  background: transparent;
  border: 1px solid #3b82f6;
  border-radius: 3px;
  padding: 2px 6px;
  cursor: pointer;
}
.btn-set-default:hover {
  background: #3b82f6;
  color: #fff;
}/* duplicate badge styles removed; colors handled by .top-badge-1/2/3 above */
.job-card.selected {
  box-shadow: 0 4px 16px 0 rgba(59,130,246,0.10);
  border-color: #3b82f6;
}
.job-card--default {
  border-color: #3b82f6;
}
.job-card__mainrow {
  display: flex;
  align-items: center;
  gap: 10px;
}
.job-card__icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #f3f3f3;
}
.job-card__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.job-card__name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 2px;
}
.job-card__avgrow {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  margin-top: 2px;
}
.job-card__desc {
  font-size: 12px;
  color: #666;
  margin: 4px 0 0 0;
  line-height: 1.5;
  min-height: 0;
}
.job-card__stack {
  margin-top: 2px;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.stack-tag {
  background: #f1f5f9;
  color: #64748b;
  font-size: 10px;
  border-radius: 3px;
  padding: 1px 6px;
}

.job-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}
/* legacy badge definition no longer needed */
.job-card__default .btn-set-default {
  font-size: 11px;
  color: #3b82f6;
  background: transparent;
  border: 1px solid #3b82f6;
  border-radius: 3px;
  padding: 2px 6px;
  cursor: pointer;
}
.job-card__default .btn-set-default:hover {
  background: #3b82f6;
  color: #fff;
}

/* highlight default job card */
.job-card--default {
  border: 1px solid #3b82f6;
}

// ---- Header ----
.page-header {
  background: $gradient-primary;
  padding: 52px $spacing-base $spacing-lg;
  position: sticky;
  top: 0;
  z-index: 30;
  /* expose header height for other elements */
  --header-height: 200px; /* adjust if actual height differs */
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
  /* header height plus spacer and tab height so content sits below fixed tabs */
  padding-top: calc(var(--header-height) + $spacing-base + var(--filter-height, 48px));
}


.filter-tabs {
  --filter-height: 48px;
  display: flex;
  /*gap: $spacing-sm;*/
  margin-top: 0;
  overflow-x: auto;
  padding-bottom: 2px;
  /* 固定浮动在头部与内容之间 */
  position: fixed;
  top: calc(var(--header-height) + $spacing-base); /* 在留白区显示 */
  left: $spacing-base; /* 靠左显示 */
  z-index: 40;
  background: transparent; /* 浮层透明 */
  &::-webkit-scrollbar { display: none; }
}

.filter-tab {
  padding: 4px 12px;
  border-radius: $border-radius-full;
  border: 1px solid $border-color;
  background: transparent; /* 改为透明 */
  font-size: $font-size-xs;
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
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: $spacing-md;
  margin-top: $spacing-lg; /* 顶部留白 */

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
    padding-top: $spacing-md; /* border-top removed to eliminate divider line */
    border-top: none;
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

.voice-mode-toggle {
  display: flex; align-items: center; gap: 5px;
  flex-shrink: 0; cursor: pointer; user-select: none;
  font-size: $font-size-sm; color: $text-secondary;
  padding: 6px 12px; border-radius: $border-radius-full;
  border: 1.5px solid $border-color; background: white;
  transition: all $transition-fast;

  &.active {
    background: $primary-bg;
    border-color: $primary;
    color: $primary;
    font-weight: $font-weight-semibold;
  }
}
</style>