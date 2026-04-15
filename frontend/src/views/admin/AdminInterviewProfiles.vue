<template>
  <div class="pm-layout">
    <div class="pm-main">
      <div class="pm-content">
        <div class="pm-header">
          <div class="pm-header__left">
            <h1 class="pm-header__title">面试配置预设</h1>
            <p class="pm-header__sub">共 <strong>{{ total }}</strong> 条预设，支持按岗位与风格快速筛选</p>
          </div>
          <button class="btn btn-primary btn-image" @click="openCreate">
            新增预设
          </button>
        </div>

        <div class="pm-toolbar">
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-box__icon">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input v-model="searchKeyword" type="text" placeholder="按风格 / 语音 / 岗位搜索" class="search-box__input" @input="onSearchDebounce" />
            <button v-if="searchKeyword" class="search-box__clear" @click="clearSearch">✕</button>
          </div>
          <div class="filter-group">
            <select v-model="filterJobId" class="form-control" @change="onFilterChange">
              <option :value="0">全部岗位</option>
              <option v-for="job in jobs" :key="job.id" :value="job.id">{{ job.name }}</option>
            </select>
          </div>
          <div class="filter-group">
            <select v-model.number="filterRound" class="form-control" @change="onFilterChange">
              <option :value="0">全部轮次</option>
              <option :value="1">一面</option>
              <option :value="2">二面</option>
              <option :value="3">三面</option>
            </select>
          </div>
        </div>

        <div class="table-card">
          <div v-if="loading" class="table-loading"><span class="spinner"></span> 加载中...</div>

          <div v-else-if="displayProfiles.length === 0" class="table-empty">
            <svg viewBox="0 0 64 64" class="empty-icon" xmlns="http://www.w3.org/2000/svg">
              <rect x="12" y="12" width="40" height="40" rx="6" stroke="#d1d5db" stroke-width="2"/>
              <path d="M20 32h24" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
              <path d="M32 20v24" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>暂无面试预设</p>
            <button class="btn btn-primary btn-sm" @click="openCreate">新增一个预设</button>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th class="col-id">ID</th>
                <th class="col-job">岗位</th>
                <th class="col-round">轮次</th>
                <th>风格</th>
                <th class="col-dynamic">是否微调</th>
                <th>题型占比</th>
                <th>语音音色</th>
                <th>启用维度</th>
                <th class="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="profile in displayProfiles" :key="profile.id" class="data-table__row">
                <td class="td-id">#{{ profile.id }}</td>
                <td class="col-job">
                  <div class="profile-title">{{ profile.job_name || '未知岗位' }}</div>
                </td>
                <td class="col-round"><span class="tag tag--round">第 {{ profile.round || 1 }} 轮</span></td>
                <td><span class="tag tag--style">{{ profile.interviewer_style || '—' }}</span></td>
                <td class="col-dynamic"><span class="tag" :class="profile.is_dynamic_adjust ? 'tag--style' : 'tag--difficulty'">{{ profile.is_dynamic_adjust ? '是' : '否' }}</span></td>
                <td>
                  技术 {{ profile.technique_percentage }}% / 项目 {{ profile.project_deep_dive_percentage }}% / 场景 {{ profile.scenario_percentage }}% / 行为 {{ profile.behavioral_percentage }}%
                  <div class="profile-note">难度：低{{ profile.difficulty_low_percentage }}% 中{{ profile.difficulty_medium_percentage }}% 高{{ profile.difficulty_high_percentage }}%</div>
                </td>
                <td>
                  <div class="profile-cell">
                    <span class="profile-label">{{ profile.voice_id || '默认' }}</span>
                    <div class="profile-note">语速 {{ profile.speech_speed || 1.0 }}x · {{ profile.tone_descriptor || '默认语调' }}</div>
                  </div>
                </td>
                <td>
                  <div class="profile-cell">
                    <span class="profile-label">{{ (profile.enabled_dimensions || []).join(', ') || '默认' }}</span>
                  </div>
                </td>
                <td>
                  <div class="row-actions">
                    <button class="act-btn act-btn--edit" @click="openEdit(profile)">编辑</button>
                    <button class="act-btn act-btn--del" @click="confirmDelete(profile)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="total > 0" class="pagination">
            <span class="pagination__info">共 {{ total }} 条，第 {{ page }}/{{ totalPages }} 页</span>
            <div class="pagination__btns">
              <button class="pg-btn" :disabled="page <= 1" @click="goToPage(page - 1)">‹ 上一页</button>
              <button
                v-for="p in pageList"
                :key="p"
                class="pg-btn"
                :class="{ 'pg-btn--active': p === page, 'pg-btn--ellipsis': p === '...' }"
                :disabled="p === '...'"
                @click="p !== '...' && goToPage(p)"
              >{{ p }}</button>
              <button class="pg-btn" :disabled="page >= totalPages" @click="goToPage(page + 1)">下一页 ›</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="modal">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box modal-box--wide">
          <div class="modal-head">
            <h2>{{ modalMode === 'create' ? '新增预设' : '编辑预设' }}</h2>
            <button class="modal-close" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-section">
              <div class="section-title">轮次与题型配置</div>
              <div class="slider-panel">
                <div class="form-grid">
                  <div class="form-group form-group--half">
                    <label class="form-label">所属岗位 <span class="req">*</span></label>
                    <select v-model.number="form.job_id" class="form-control">
                      <option value="0" disabled>请选择岗位</option>
                      <option v-for="job in jobs" :key="job.id" :value="job.id">{{ job.name }}</option>
                    </select>
                  </div>
                  <div class="form-group form-group--half">
                    <label class="form-label">轮次 <span class="req">*</span></label>
                    <select v-model.number="form.round" class="form-control">
                      <option :value="1">一面</option>
                      <option :value="2">二面</option>
                      <option :value="3">三面</option>
                    </select>
                  </div>
                  <div class="form-group form-group--full slider-summary">
                  <span>类型占比(总和为100%) <span class="req">*</span></span>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">技术题占比 <span class="form-label-hint slider-value">{{ form.technique_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.technique_percentage"
                      @input="onTopicChange('technique_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">项目深挖题目占比 <span class="form-label-hint slider-value">{{ form.project_deep_dive_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.project_deep_dive_percentage"
                      @input="onTopicChange('project_deep_dive_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">场景题占比 <span class="form-label-hint slider-value">{{ form.scenario_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.scenario_percentage"
                      @input="onTopicChange('scenario_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">行为题占比 <span class="form-label-hint slider-value">{{ form.behavioral_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.behavioral_percentage"
                      @input="onTopicChange('behavioral_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--full slider-summary">
                  <span>难度占比(总和为100%) <span class="req">*</span></span>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">基础题占比 <span class="form-label-hint">{{ form.difficulty_low_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.difficulty_low_percentage"
                      @input="onDifficultyChange('difficulty_low_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">中等题占比 <span class="form-label-hint">{{ form.difficulty_medium_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.difficulty_medium_percentage"
                      @input="onDifficultyChange('difficulty_medium_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">高难度题占比 <span class="form-label-hint">{{ form.difficulty_high_percentage }}%</span></label>
                  <div class="slider-box">
                    <input
                      type="range"
                      min="0"
                      step="10"
                      max="100"
                      v-model.number="form.difficulty_high_percentage"
                      @input="onDifficultyChange('difficulty_high_percentage', $event.target.value)"
                      class="slider" />
                    <div class="slider-meta">范围：0 - 100%</div>
                  </div>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">是否动态微调</label>
                  <label class="switch">
                    <input type="checkbox" v-model="form.is_dynamic_adjust" />
                    <span class="switch-slider"></span>
                  </label>
                </div>
              </div>
              </div>
            </div>
            <div class="form-section">
              <div class="section-title">风格与语音配置</div>
              <div class="voice-panel">
                <div class="form-grid">
                  <div class="form-group form-group--half">
                    <label class="form-label">风格 <span class="req">*</span></label>
                    <select v-model="form.interviewer_style" class="form-control">
                      <option value="pressure">压力面</option>
                      <option value="confident">自信面</option>
                      <option value="teaching">教学面</option>
                    </select>
                  </div>
                  <div class="form-group form-group--half">
                    <label class="form-label">语速倍率 <span class="req">*</span></label>
                    <select v-model.number="form.speech_speed" class="form-control">
                      <option :value="0.5">0.5x</option>
                      <option :value="0.7">0.7x</option>
                      <option :value="1.0">1.0x</option>
                      <option :value="1.5">1.5x</option>
                      <option :value="2.0">2.0x</option>
                    </select>
                  </div>
                  <div class="form-group form-group--half">
                    <label class="form-label">语音 ID <span class="req">*</span></label>
                    <select v-model="form.voice_id" class="form-control">
                      <option v-for="voice in voiceOptions" :key="voice.id" :value="voice.id">{{ voice.label }}</option>
                    </select>
                  </div>
                  <div class="form-group form-group--half">
                    <label class="form-label">语调描述 <span class="req">*</span></label>
                    <input v-model="form.tone_descriptor" type="text" class="form-control" placeholder="例如 温柔耐心" />
                  </div>
                  <div class="form-group form-group--full">
                    <label class="form-label">启用维度 <span class="req">*</span></label>
                    <input v-model="form.enabled_dimensions_text" type="text" class="form-control" placeholder="例如 technical, project_deep_dive,用逗号分割多个维度" />
                    
                  </div>
                </div>
              </div>
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeModal">取消</button>
            <button class="btn btn-primary" :disabled="modalLoading" @click="submitForm">
              <span v-if="modalLoading" class="spinner spinner--sm"></span>
              {{ modalMode === 'create' ? '创建预设' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="modal-box modal-box--sm">
          <div class="modal-head">
            <h2>确认删除预设</h2>
            <button class="modal-close" @click="showDeleteConfirm = false">✕</button>
          </div>
          <div class="modal-body">
            <p>确认删除预设《{{ deletingProfile?.interviewer_style || '' }}》吗？</p>
            <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="showDeleteConfirm = false">取消</button>
            <button class="btn btn-danger" :disabled="deleteLoading" @click="doDelete">
              <span v-if="deleteLoading" class="spinner spinner--sm"></span> 删除
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { listInterviewProfiles, createInterviewProfile, updateInterviewProfile, deleteInterviewProfile, listAdminJobs } from '@/api/admin'
import { VOICE_ID_OPTIONS } from '@/constants/ttsVoices'

function defaultProfileForm() {
  return {
    id: null,
    job_id: 0,
    round: 1,
    technique_percentage: 40,
    scenario_percentage: 20,
    project_deep_dive_percentage: 20,
    behavioral_percentage: 20,
    difficulty_low_percentage: 30,
    difficulty_medium_percentage: 50,
    difficulty_high_percentage: 20,
    is_dynamic_adjust: true,
    interviewer_style: 'confident',
    custom_personality_json_text: '{"tone":"平稳","feedback_level":"balanced"}',
    voice_id: '',
    speech_speed: 1.0,
    tone_descriptor: '',
    enabled_dimensions_text: 'technical, project_deep_dive, scenario_design, behavioral',
    difficulty_level: 2
  }
}

export default {
  name: 'AdminInterviewProfiles',
  data() {
    return {
      profiles: [],
      jobs: [],
      total: 0,
      loading: false,
      searchKeyword: '',
      filterJobId: 0,
      filterRound: 0,
      page: 1,
      pageSize: 10,
      showModal: false,
      modalMode: 'create',
      modalLoading: false,
      formError: '',
      form: defaultProfileForm(),
      showDeleteConfirm: false,
      deletingProfile: null,
      deleteLoading: false,
      deleteError: '',
      searchTimer: null,
      voiceOptions: VOICE_ID_OPTIONS
    }
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil((this.total || 0) / this.pageSize))
    },
    pageList() {
      const total = this.totalPages
      const cur = this.page
      if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
      const pages = []
      if (cur <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i)
        pages.push('...', total)
      } else if (cur >= total - 3) {
        pages.push(1, '...')
        for (let i = total - 4; i <= total; i++) pages.push(i)
      } else {
        pages.push(1, '...', cur - 1, cur, cur + 1, '...', total)
      }
      return pages
    },
    displayProfiles() {
      const keyword = (this.searchKeyword || '').trim().toLowerCase()
      return this.profiles.filter(profile => {
        if (this.filterJobId && profile.job_id !== this.filterJobId) {
          return false
        }
        if (this.filterRound && profile.round !== this.filterRound) {
          return false
        }
        if (!keyword) {
          return true
        }
        return [
          profile.interviewer_style,
          profile.voice_id,
          profile.tone_descriptor,
          profile.job_name
        ].some(value => (value || '').toString().toLowerCase().includes(keyword))
      })
    },
    topicTotal() {
      return (Number(this.form.technique_percentage) || 0)
        + (Number(this.form.project_deep_dive_percentage) || 0)
        + (Number(this.form.scenario_percentage) || 0)
        + (Number(this.form.behavioral_percentage) || 0)
    },
    topicRemaining() {
      return 100 - this.topicTotal
    },
    difficultyTotal() {
      return (Number(this.form.difficulty_low_percentage) || 0)
        + (Number(this.form.difficulty_medium_percentage) || 0)
        + (Number(this.form.difficulty_high_percentage) || 0)
    },
    difficultyRemaining() {
      return 100 - this.difficultyTotal
    }
  },
  created() {
    this.loadJobs()
    this.loadData()
  },
  methods: {
    async loadJobs() {
      try {
        const res = await listAdminJobs()
        this.jobs = res.list || []
      } catch (err) {
        console.error('加载岗位失败', err)
      }
    },
    async loadData() {
      this.loading = true
      try {
        const params = {
          page: this.page,
          size: this.pageSize
        }
        if (this.filterJobId) {
          params.job_id = this.filterJobId
        }
        if (this.filterRound) {
          params.round = this.filterRound
        }
        const res = await listInterviewProfiles(params)
        this.profiles = res.list || []
        this.total = res.total || this.profiles.length
      } catch (err) {
        console.error('加载面试预设失败', err)
      } finally {
        this.loading = false
      }
    },
    onFilterChange() {
      this.page = 1
      this.loadData()
    },
    onPageSizeChange() {
      this.page = 1
      this.loadData()
    },
    goToPage(page) {
      if (page < 1 || page > this.totalPages || page === this.page) return
      this.page = page
      this.loadData()
    },
    onSearchDebounce() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        this.searchTimer = null
      }, 300)
    },
    onTopicChange(field, value) {
      this.form[field] = Math.max(0, Math.min(100, Number(value)))
    },
    onDifficultyChange(field, value) {
      this.form[field] = Math.max(0, Math.min(100, Number(value)))
    },
    clearSearch() {
      this.searchKeyword = ''
    },
    openCreate() {
      this.modalMode = 'create'
      this.form = defaultProfileForm()
      this.showModal = true
      this.formError = ''
    },
    openEdit(profile) {
      this.modalMode = 'edit'
      this.form = {
        id: profile.id,
        job_id: profile.job_id || 0,
        round: profile.round || 1,
        technique_percentage: profile.technique_percentage || 60,
        scenario_percentage: profile.scenario_percentage || 40,
        project_deep_dive_percentage: profile.project_deep_dive_percentage || 15,
        behavioral_percentage: profile.behavioral_percentage || 15,
        difficulty_low_percentage: profile.difficulty_low_percentage || 30,
        difficulty_medium_percentage: profile.difficulty_medium_percentage || 50,
        difficulty_high_percentage: profile.difficulty_high_percentage || 20,
        is_dynamic_adjust: profile.is_dynamic_adjust !== false,
        interviewer_style: profile.interviewer_style || 'confident',
        custom_personality_json_text: JSON.stringify(profile.custom_personality_json || {}, null, 2),
        voice_id: profile.voice_id || '',
        speech_speed: profile.speech_speed || 1.0,
        tone_descriptor: profile.tone_descriptor || '',
        enabled_dimensions_text: Array.isArray(profile.enabled_dimensions) ? profile.enabled_dimensions.join(', ') : (profile.enabled_dimensions || []).toString(),
        difficulty_level: profile.difficulty_level || 2
      }
      this.formError = ''
      this.showModal = true
    },
    closeModal() {
      this.showModal = false
    },
    async submitForm() {
      this.formError = ''
      if (!this.form.job_id) {
        this.formError = '请选择所属岗位'
        return
      }
      if (!this.form.interviewer_style) {
        this.formError = '请选择面试风格'
        return
      }
      let customPersonality
      try {
        customPersonality = JSON.parse(this.form.custom_personality_json_text || '{}')
      } catch (err) {
        this.formError = '自定义人格参数必须是合法 JSON'
        return
      }
      const topicTotal = (Number(this.form.technique_percentage) || 0)
        + (Number(this.form.project_deep_dive_percentage) || 0)
        + (Number(this.form.scenario_percentage) || 0)
        + (Number(this.form.behavioral_percentage) || 0)
      if (Math.abs(topicTotal - 100) > 0.1) {
        this.formError = '技术/项目/场景/行为占比总和必须为 100%'
        return
      }
      const totalRatio = (Number(this.form.difficulty_low_percentage) || 0)
        + (Number(this.form.difficulty_medium_percentage) || 0)
        + (Number(this.form.difficulty_high_percentage) || 0)
      if (Math.abs(totalRatio - 100) > 0.1) {
        this.formError = '低/中/高级占比总和必须为 100%'
        return
      }
      const payload = {
        job_id: this.form.job_id,
        round: this.form.round,
        technique_percentage: this.form.technique_percentage,
        scenario_percentage: this.form.scenario_percentage,
        project_deep_dive_percentage: this.form.project_deep_dive_percentage,
        behavioral_percentage: this.form.behavioral_percentage,
        difficulty_low_percentage: this.form.difficulty_low_percentage,
        difficulty_medium_percentage: this.form.difficulty_medium_percentage,
        difficulty_high_percentage: this.form.difficulty_high_percentage,
        is_dynamic_adjust: this.form.is_dynamic_adjust,
        interviewer_style: this.form.interviewer_style,
        custom_personality_json: customPersonality,
        voice_id: this.form.voice_id,
        speech_speed: this.form.speech_speed,
        tone_descriptor: this.form.tone_descriptor,
        enabled_dimensions: this.form.enabled_dimensions_text && this.form.enabled_dimensions_text.trim()
          ? this.form.enabled_dimensions_text.split(',').map(s => s.trim()).filter(Boolean)
          : ['technical', 'project_deep_dive', 'scenario_design', 'behavioral'],
        difficulty_level: this.form.difficulty_level
      }
      try {
        this.modalLoading = true
        if (this.modalMode === 'create') {
          await createInterviewProfile(payload)
        } else {
          await updateInterviewProfile(this.form.id, payload)
        }
        this.showModal = false
        this.loadData()
      } catch (err) {
        console.error('保存失败', err)
        this.formError = err?.message || '保存失败，请稍后重试'
      } finally {
        this.modalLoading = false
      }
    },
    confirmDelete(profile) {
      this.deletingProfile = profile
      this.deleteError = ''
      this.showDeleteConfirm = true
    },
    async doDelete() {
      if (!this.deletingProfile) return
      this.deleteLoading = true
      try {
        await deleteInterviewProfile(this.deletingProfile.id)
        this.showDeleteConfirm = false
        this.loadData()
      } catch (err) {
        console.error('删除失败', err)
        this.deleteError = err?.message || '删除失败，请稍后重试'
      } finally {
        this.deleteLoading = false
      }
    }
  }
}
</script>

<style scoped>
.pm-layout {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}
.pm-main {
  flex: 1;
}
.pm-content {
  padding: 24px;
  background: #f5f7fb;
}
.pm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}
.pm-header__title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}
.pm-header__sub {
  margin: 6px 0 0;
  color: #586069;
  line-height: 1.6;
}
.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.btn-image {
  padding-left: 44px;
  position: relative;
}
.btn-image::before {
  content: '';
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fff' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='5' x2='12' y2='19'/%3E%3Cline x1='5' y1='12' x2='19' y2='12'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: contain;
}
.pm-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
}
.search-box {
  flex: 1;
  min-width: 260px;
  max-width: 520px;
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #dfe2ec;
  border-radius: 10px;
  padding: 8px 12px;
}
.search-box__icon {
  width: 18px;
  height: 18px;
  color: #8b96a6;
}
.search-box__input {
  flex: 1;
  border: none;
  outline: none;
  padding: 8px 10px;
  font-size: 14px;
  color: #111827;
  background: transparent;
}
.search-box__clear {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #6b7280;
  font-size: 14px;
}
.filter-group {
  display: flex;
  flex-direction: column;
  min-width: 220px;
}
.form-section {
  margin-bottom: 24px;
}
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
}
.filter-group {
  display: flex;
  flex-direction: column;
  min-width: 220px;
}
.filter-label {
  margin-bottom: 6px;
  font-size: 13px;
  color: #4b5563;
}
.table-card {
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}
.table-loading,
.table-empty {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  color: #475569;
  padding: 32px;
}
.empty-icon {
  width: 72px;
  height: 72px;
  color: #cbd5e1;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table thead {
  background: #f8fafc;
}
.data-table th,
.data-table td {
  padding: 18px 16px;
  text-align: left;
  border-bottom: 1px solid #eef2f7;
  font-size: 14px;
  color: #1f2937;
}
.data-table th.col-actions,
.data-table td.col-actions {
  width: 180px;
}
.data-table th.col-job,
.data-table td.col-job {
  width: 130px;
}
.data-table th.col-round,
.data-table td.col-round {
  width: 100px;
}
.data-table th.col-dynamic,
.data-table td.col-dynamic {
  width: 90px;
}
.data-table__row:hover {
  background: #f8fbff;
}
.td-id,
.col-id {
  width: 78px;
}
.profile-title {
  font-weight: 600;
  color: #111827;
}
.profile-sub {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}
.tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 12px;
}
.tag--style {
  background: #eef2ff;
  color: #3730a3;
}
.tag--difficulty {
  background: #fef2f2;
  color: #b91c1c;
}
.profile-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.profile-label {
  font-size: 14px;
  color: #111827;
}
.profile-note {
  font-size: 12px;
  color: #64748b;
}
.row-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}
.pagination {
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}
.pagination__info {
  color: #475569;
  font-size: 14px;
}
.pagination__btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.pg-btn {
  border: 1px solid #d9dfee;
  background: #fff;
  line-height: 1.2;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  color: #334155;
}
.pg-btn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
.pg-btn--active {
  background: #2f80ed;
  color: #fff;
  border-color: #2f80ed;
}
.pg-btn--ellipsis {
  cursor: default;
  background: transparent;
  border-color: transparent;
}
.pagination-size {
  display: flex;
  flex-direction: column;
  min-width: 110px;
}
.pagination-size .filter-label {
  margin-bottom: 6px;
  font-size: 12px;
  color: #475569;
}
.act-btn {
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.act-btn--edit {
  color: #2563eb;
  background: #eff6ff;
}
.act-btn--edit:hover {
  background: #dbeafe;
}
.act-btn--del {
  color: #b91c1c;
  background: #fef2f2;
}
.act-btn--del:hover {
  background: #fee2e2;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group--full {
  grid-column: span 2;
}
.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.form-label-hint {
  font-weight: 400;
  color: #9ca3af;
  font-size: 11px;
}
.req {
  color: #ef4444;
  margin-left: 2px;
}
.form-control {
  width: 100%;
  border: 1px solid #dfe2ec;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 14px;
  color: #111827;
  background: #ffffff;
}
.form-control:focus {
  border-color: #4338ca;
  box-shadow: 0 0 0 3px rgba(67,56,202,0.1);
}
.slider-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.slider {
  width: 100%;
  height: 6px;
  appearance: none;
  background: #e2e8f0;
  border-radius: 999px;
  outline: none;
}
.slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4338ca;
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(67,56,202,0.15);
}
.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4338ca;
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(67,56,202,0.15);
}
.slider-meta {
  font-size: 12px;
  color: #6b7280;
}
.slider-summary {
  font-size: 13px;
  color: #111827;
  font-weight: 600;
  text-align: center;
}
.slider-panel {
  background: #f8fafc;
  padding: 18px 18px 16px;
  border-radius: 16px;
}
.voice-panel {
  background: #f8fafc;
  padding: 18px 18px 16px;
  border-radius: 16px;
}
.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 28px;
  border: 1px solid #ced4da;
  border-radius: 999px;
  background: #f1f3f5;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.switch-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ced4da;
  transition: 0.2s;
  border-radius: 999px;
  box-sizing: border-box;
}
.switch-slider:before {
  position: absolute;
  content: "";
  height: 24px;
  width: 24px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.2s;
  border-radius: 50%;
}
.switch input:checked + .switch-slider {
  background-color: #27ae60;
}
.switch input:checked + .switch-slider:before {
  transform: translateX(20px);
}
.slider-value {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}
.form-textarea {
  min-height: 120px;
}
.form-error,
.delete-error {
  color: #b91c1c;
  margin-top: 12px;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 10, 40, 0.55);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}
.modal-box--wide {
  max-width: 780px;
}
.modal-box--sm {
  max-width: 420px;
}
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
}
.modal-head h2 {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 2px;
}
.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}
.modal-close:hover {
  background: #e5e7eb;
  color: #111827;
}
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
}
.btn-sm {
  height: 36px;
  padding: 0 14px;
}
</style>
