<!--
  frontend/src/views/admin/PromptManager.vue
  AI Prompt 管理 — 增删改查，支持关联岗位、温度/Token 参数调整、启用/禁用切换
-->
<template>
   <div class="pm-layout">

    <div class="pm-main">
      <div class="pm-content">

        <!-- 页头 -->
        <div class="pm-header">
          <div class="pm-header__left">
            <h1 class="pm-header__title">AI Prompt 管理</h1>
            <p class="pm-header__sub">共 <strong>{{ total }}</strong> 个提示词配置</p>
          </div>
          <button class="btn btn-primary" @click="openCreate">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            新建 Prompt
          </button>
        </div>

        <!-- 搜索栏 -->
        <div class="pm-search">
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" class="search-box__icon">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input v-model="keyword" type="text" placeholder="搜索名称、提问风格、角色描述…"
              class="search-box__input" @keyup.enter="onSearch" @input="onSearchDebounce"/>
            <button v-if="keyword" class="search-box__clear" @click="clearSearch">✕</button>
          </div>
        </div>

        <!-- 表格卡片 -->
        <div class="table-card">
          <div v-if="loading" class="table-loading">
            <span class="spinner"></span> 加载中...
          </div>

          <div v-else-if="items.length === 0" class="table-empty">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="empty-icon">
              <rect x="12" y="8" width="40" height="48" rx="4" stroke="#d1d5db" stroke-width="2"/>
              <line x1="20" y1="20" x2="44" y2="20" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
              <line x1="20" y1="28" x2="44" y2="28" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
              <line x1="20" y1="36" x2="36" y2="36" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>暂无 Prompt 配置</p>
            <button class="btn btn-primary btn-sm" @click="openCreate">立即创建</button>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th class="col-id">ID</th>
                <th class="col-name">名称</th>
                <th class="col-job">关联岗位</th>
                <th class="col-style">提问风格</th>
                <th class="col-temp">温度</th>
                <th class="col-tokens">Max Tokens</th>
                <th class="col-status">状态</th>
                <th class="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" class="data-table__row">
                <td class="td-id">#{{ item.id }}</td>
                <td>
                  <div class="prompt-name">{{ item.name }}</div>
                  <div v-if="item.role_description" class="prompt-desc">{{ truncate(item.role_description, 40) }}</div>
                </td>
                <td class="td-center"><span class="job-chip">{{ getJobName(item.job_id) }}</span></td>
                <td class="td-style">{{ item.questioning_style || '—' }}</td>
                <td class="td-center">
                  <span class="temp-val" :class="tempClass(item.temperature)">{{ item.temperature }}</span>
                </td>
                <td class="td-center td-muted">{{ item.max_tokens || '—' }}</td>
                <td class="td-center">
                  <button
                    class="toggle-btn"
                    :class="item.is_active ? 'toggle-btn--on' : 'toggle-btn--off'"
                    @click="toggleActive(item)"
                    :disabled="togglingId === item.id"
                    :title="item.is_active ? '点击禁用' : '点击启用'"
                  >
                    <span class="toggle-dot"></span>
                    {{ item.is_active ? '启用中' : '已禁用' }}
                  </button>
                </td>
                <td>
                  <div class="row-actions">
                    <button class="act-btn act-btn--preview" @click="openPreview(item)" title="预览">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                    </button>
                    <button class="act-btn act-btn--edit" @click="openEdit(item)" title="编辑">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4z"/>
                      </svg>
                    </button>
                    <button class="act-btn act-btn--del" @click="askDelete(item)" title="删除">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
                        <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 分页 -->
          <div v-if="total > 0" class="pagination">
            <span class="pagination__info">共 {{ total }} 条，第 {{ page }}/{{ totalPages }} 页</span>
            <div class="pagination__btns">
              <button class="pg-btn" :disabled="page <= 1" @click="goPage(page - 1)">‹ 上一页</button>
              <button
                v-for="p in pageList" :key="p"
                class="pg-btn"
                :class="{ 'pg-btn--active': p === page, 'pg-btn--ellipsis': p === '...' }"
                :disabled="p === '...'"
                @click="p !== '...' && goPage(p)"
              >{{ p }}</button>
              <button class="pg-btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页 ›</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- ══════════ 新建 / 编辑 Modal ══════════ -->
    <transition name="modal">
      <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
        <div class="modal-box modal-box--wide">
          <div class="modal-head">
            <h2>{{ formMode === 'create' ? '新建 Prompt' : '编辑 Prompt' }}</h2>
            <button class="modal-close" @click="closeForm">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <!-- 名称 -->
              <div class="form-group form-group--half">
                <label class="form-label">Prompt 名称 <span class="req">*</span></label>
                <input v-model="form.name" type="text" class="form-control" placeholder="例如：Java后端默认面试官"/>
              </div>
              <!-- 关联岗位 -->
              <div class="form-group form-group--half">
                <label class="form-label">关联岗位</label>
                <select v-model="form.job_id" class="form-control">
                  <option value="">不绑定岗位（通用）</option>
                  <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
                </select>
              </div>
              <!-- 角色描述 -->
              <div class="form-group form-group--full">
                <label class="form-label">角色描述</label>
                <input v-model="form.role_description" type="text" class="form-control"
                  placeholder="例如：专注 Java 后端的资深面试官"/>
              </div>
              <!-- 开场白 -->
              <div class="form-group form-group--full">
                <label class="form-label">开场白（greeting message）</label>
                <textarea v-model="form.greeting_message" class="form-control form-textarea" rows="2"
                  placeholder="面试开始时 AI 说的第一句话…"></textarea>
              </div>
              <!-- System Prompt (核心字段) -->
              <div class="form-group form-group--full">
                <label class="form-label">
                  System Prompt <span class="req">*</span>
                  <span class="form-label-hint">控制 AI 面试官行为的核心指令</span>
                </label>
                <textarea v-model="form.system_prompt" class="form-control form-textarea form-textarea--lg" rows="10"
                  placeholder="你是一位专业的 XX 面试官。请围绕该岗位核心能力进行提问…&#10;&#10;【核心指令】：题量请结合知识库规模动态控制（建议 8-16 题）；评估充分后再结束。结束时最后一句请感谢候选人，并在该句末尾加上 [INTERVIEW_OVER]。"></textarea>
                <p class="form-hint">⚠️ 请在结束面试指令末尾包含 <code>[INTERVIEW_OVER]</code> 标记，否则面试将无法自动结束</p>
              </div>
              <!-- 提问风格 / 参数行 -->
              <div class="form-group form-group--third">
                <label class="form-label">提问风格</label>
                <input v-model="form.questioning_style" type="text" class="form-control"
                  placeholder="例如：专业、结构化追问"/>
              </div>
              <div class="form-group form-group--sixth">
                <label class="form-label">
                  温度（temperature）
                  <span class="form-label-hint">0 保守 · 1 创意</span>
                </label>
                <div class="range-group">
                  <input v-model.number="form.temperature" type="range" min="0" max="1" step="0.1"
                    class="range-slider"/>
                  <span class="range-val">{{ form.temperature }}</span>
                </div>
              </div>
              <div class="form-group form-group--sixth">
                <label class="form-label">最大 Token 数</label>
                <input v-model.number="form.max_tokens" type="number" min="100" max="4000" class="form-control"
                  placeholder="500"/>
              </div>
              <!-- 状态 -->
              <div class="form-group form-group--full">
                <label class="form-label">启用状态</label>
                <div class="active-toggle" @click="form.is_active = !form.is_active">
                  <div class="switch" :class="{ 'switch--on': form.is_active }"></div>
                  <span>{{ form.is_active ? '启用（面试时将使用此配置）' : '禁用（不会被新面试使用）' }}</span>
                </div>
              </div>
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeForm" :disabled="formLoading">取消</button>
            <button class="btn btn-primary" @click="submitForm" :disabled="formLoading">
              <span v-if="formLoading" class="spinner spinner--sm spinner--light"></span>
              {{ formMode === 'create' ? '创建 Prompt' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ══════════ 预览 Modal ══════════ -->
    <transition name="modal">
      <div v-if="showPreview" class="modal-overlay" @click.self="showPreview = false">
        <div class="modal-box modal-box--wide">
          <div class="modal-head">
            <div>
              <h2>{{ previewItem && previewItem.name }}</h2>
              <p class="modal-sub">{{ previewItem && previewItem.job_name ? previewItem.job_name + ' · ' : '' }}Prompt 预览</p>
            </div>
            <button class="modal-close" @click="showPreview = false">✕</button>
          </div>
          <div v-if="previewItem" class="modal-body">
            <div class="preview-meta">
              <div class="meta-chip">
                <span class="meta-chip__label">温度</span>
                <span class="meta-chip__val" :class="tempClass(previewItem.temperature)">{{ previewItem.temperature }}</span>
              </div>
              <div class="meta-chip">
                <span class="meta-chip__label">Max Tokens</span>
                <span class="meta-chip__val">{{ previewItem.max_tokens }}</span>
              </div>
              <div class="meta-chip">
                <span class="meta-chip__label">提问风格</span>
                <span class="meta-chip__val">{{ previewItem.questioning_style || '—' }}</span>
              </div>
              <div class="meta-chip">
                <span class="meta-chip__label">状态</span>
                <span class="meta-chip__val" :class="previewItem.is_active ? 'text-green' : 'text-muted'">
                  {{ previewItem.is_active ? '启用' : '禁用' }}
                </span>
              </div>
            </div>
            <div v-if="previewItem.greeting_message" class="prompt-block prompt-block--greeting">
              <div class="prompt-block__label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                开场白
              </div>
              <p>{{ previewItem.greeting_message }}</p>
            </div>
            <div class="prompt-block">
              <div class="prompt-block__label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
                </svg>
                System Prompt
              </div>
              <pre class="prompt-pre">{{ previewItem.system_prompt }}</pre>
            </div>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="showPreview = false">关闭</button>
            <button class="btn btn-primary" @click="showPreview = false; openEdit(previewItem)">编辑</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ══════════ 删除确认 Modal ══════════ -->
    <transition name="modal">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="modal-box modal-box--sm">
          <div class="modal-head">
            <h2>确认删除</h2>
            <button class="modal-close" @click="showDeleteConfirm = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="confirm-icon confirm-icon--danger">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
                <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
              </svg>
            </div>
            <p class="confirm-text">确定要删除这个 Prompt 配置吗？</p>
            <p class="confirm-sub">删除后，该岗位面试将回退到默认系统提示词。</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="showDeleteConfirm = false" :disabled="deleteLoading">取消</button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="deleteLoading">
              <span v-if="deleteLoading" class="spinner spinner--sm spinner--light"></span>
              确认删除
            </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import {
  listPrompts, createPrompt, updatePrompt, deletePrompt, listAdminJobs
} from '@/api/admin'

function defaultForm() {
  return {
    name: '',
    job_id: '',
    role_description: '',
    system_prompt: '',
    greeting_message: '',
    questioning_style: '',
    temperature: 0.7,
    max_tokens: 500,
    is_active: true
  }
}

export default {
  name: 'PromptManager',

  data() {
    return {
      items: [],
      total: 0,
      page: 1,
      size: 15,
      loading: false,
      jobs: [],
      keyword: '',
      searchTimer: null,
      togglingId: null,

      // form
      showForm: false,
      formMode: 'create',
      formLoading: false,
      formError: '',
      form: defaultForm(),
      editingId: null,

      // preview
      showPreview: false,
      previewItem: null,

      // delete
      showDeleteConfirm: false,
      deletingId: null,
      deleteLoading: false
    }
  },

  computed: {
    totalPages() {
      return Math.ceil(this.total / this.size) || 1
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
        this.jobs = (res && res.list) ? res.list : (Array.isArray(res) ? res : [])
      } catch (e) { /* silent */ }
    },

    async loadData() {
      this.loading = true
      try {
        const params = { page: this.page, size: this.size }
        if (this.keyword.trim()) params.keyword = this.keyword.trim()
        const res = await listPrompts(params)
        this.items = res.list || []
        this.total = res.total || 0
      } catch (e) {
        console.error('加载 Prompt 失败', e)
      } finally {
        this.loading = false
      }
    },

    onSearch() {
      this.page = 1
      this.loadData()
    },

    onSearchDebounce() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => { this.page = 1; this.loadData() }, 400)
    },

    clearSearch() {
      this.keyword = ''
      this.page = 1
      this.loadData()
    },

    goPage(p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.loadData()
    },

    // ── Toggle active ──
    async toggleActive(item) {
      this.togglingId = item.id
      try {
        await updatePrompt(item.id, { is_active: !item.is_active })
        item.is_active = !item.is_active
      } catch (e) {
        alert(e.message || '操作失败')
      } finally {
        this.togglingId = null
      }
    },

    // ── Form ──
    openCreate() {
      this.formMode = 'create'
      this.form = defaultForm()
      this.formError = ''
      this.editingId = null
      this.showForm = true
    },

    openEdit(item) {
      this.formMode = 'edit'
      this.editingId = item.id
      this.form = {
        name: item.name || '',
        job_id: item.job_id || '',
        role_description: item.role_description || '',
        system_prompt: item.system_prompt || '',
        greeting_message: item.greeting_message || '',
        questioning_style: item.questioning_style || '',
        temperature: item.temperature != null ? Number(item.temperature) : 0.7,
        max_tokens: item.max_tokens || 500,
        is_active: item.is_active !== false
      }
      this.formError = ''
      this.showForm = true
    },

    closeForm() {
      this.showForm = false
    },

    async submitForm() {
      this.formError = ''
      if (!this.form.name.trim()) { this.formError = 'Prompt 名称不能为空'; return }
      if (!this.form.system_prompt.trim()) { this.formError = 'System Prompt 不能为空'; return }

      const data = {
        name: this.form.name.trim(),
        job_id: this.form.job_id || null,
        role_description: this.form.role_description.trim() || null,
        system_prompt: this.form.system_prompt.trim(),
        greeting_message: this.form.greeting_message.trim() || null,
        questioning_style: this.form.questioning_style.trim() || null,
        temperature: this.form.temperature,
        max_tokens: this.form.max_tokens || 500,
        is_active: this.form.is_active
      }

      this.formLoading = true
      try {
        if (this.formMode === 'create') {
          await createPrompt(data)
        } else {
          await updatePrompt(this.editingId, data)
        }
        this.showForm = false
        this.loadData()
      } catch (e) {
        this.formError = e.message || '操作失败，请重试'
      } finally {
        this.formLoading = false
      }
    },

    getJobName(jobId) {
      if (!jobId) return '通用'
      const job = this.jobs.find(j => j.id === jobId)
      return job ? job.name : '通用'
    },

    // ── Preview ──
    openPreview(item) {
      this.previewItem = item
      this.showPreview = true
    },

    // ── Delete ──
    askDelete(item) {
      this.deletingId = item.id
      this.showDeleteConfirm = true
    },

    async confirmDelete() {
      this.deleteLoading = true
      try {
        await deletePrompt(this.deletingId)
        this.showDeleteConfirm = false
        this.deletingId = null
        if (this.items.length === 1 && this.page > 1) this.page--
        this.loadData()
      } catch (e) {
        alert(e.message || '删除失败')
      } finally {
        this.deleteLoading = false
      }
    },

    // ── Helpers ──
    truncate(str, len) {
      if (!str) return ''
      return str.length > len ? str.slice(0, len) + '…' : str
    },

    tempClass(t) {
      const v = Number(t)
      if (v >= 0.8) return 'temp--hot'
      if (v >= 0.4) return 'temp--warm'
      return 'temp--cool'
    }
  }
}
</script>

<style lang="scss" scoped>
.pm-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f6fa;
  font-family: $font-family-base;
}

.pm-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 28px 32px;
  overflow-y: auto;
  max-height: 100vh;
}

.pm-content {
  max-width: 1500px;
  width: 100%;
  margin: 0 auto;
}



/* ── Layout ── */

.pm-header {
  display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px;
  &__title { font-size: 22px; font-weight: 700; color: #111827; margin: 0 0 4px; letter-spacing: -0.3px; }
  &__sub { font-size: 13px; color: #9ca3af; margin: 0; strong { color: #4338ca; font-weight: 600; } }
  &__left {}
}

/* ── Search ── */
.pm-search { margin-bottom: 16px; }
.search-box {
  position: relative; max-width: 420px;
  &__icon {
    position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
    color: #9ca3af; display: flex; align-items: center; pointer-events: none;
    width: 16px; height: 16px;
  }
  &__input {
    width: 100%; height: 38px; padding: 0 36px 0 38px;
    border: 1.5px solid #e5e7eb; border-radius: 8px;
    font-size: 13px; color: #374151; background: white;
    font-family: $font-family-base; outline: none;
    &:focus { border-color: #4338ca; box-shadow: 0 0 0 3px rgba(67,56,202,0.1); }
  }
  &__clear {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: #e5e7eb; border: none; width: 18px; height: 18px; border-radius: 50%;
    cursor: pointer; font-size: 10px; color: #6b7280;
    display: flex; align-items: center; justify-content: center;
    &:hover { background: #d1d5db; }
  }
}

/* ── Button ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 0 18px; height: 38px;
  border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: all 0.15s; font-family: $font-family-base; border: none;
  &-primary { background: #4338ca; color: white; &:hover { background: #3730a3; } &:active { transform: scale(0.98); } }
  &-ghost { background: #f3f4f6; color: #6b7280; &:hover { background: #e5e7eb; color: #374151; } }
  &-danger { background: #ef4444; color: white; &:hover { background: #dc2626; } }
  &-sm { height: 32px; padding: 0 14px; font-size: 12px; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}
.btn-icon { width: 14px; height: 14px; flex-shrink: 0; }

/* ── Table ── */
.table-card {
  background: white; 
  border-radius: 12px; 
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04); 
  overflow-x: auto;  // 添加横向滚动
  overflow-y: hidden; // 可选，隐藏纵向溢出
  -webkit-overflow-scrolling: touch; // 移动端平滑滚动
}
.table-loading {
  display: flex; 
  align-items: center; 
  justify-content: center;
  gap: 10px; 
  padding: 60px; 
  color: #9ca3af; 
  font-size: 14px;
  // 移除或注释掉 min-width: 900px; 让它在小屏幕也能正常居中
  // min-width: 900px;  
}
.table-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 70px 20px; gap: 12px; color: #9ca3af; font-size: 14px;
}
.empty-icon { width: 64px; height: 64px; opacity: 0.5; }

.data-table {
  width: 100%; border-collapse: collapse; font-size: 13px;min-width: 900px;
  th {
    background: #f9fafb; color: #6b7280; font-weight: 600; font-size: 12px;
    text-transform: uppercase; letter-spacing: 0.04em;
    padding: 11px 16px; text-align: center; border-bottom: 1px solid #f3f4f6; white-space: nowrap;
  }
  td { padding: 13px 16px; color: #374151; border-bottom: 1px solid #f9fafb; vertical-align: middle; }
  &__row {
    transition: background 0.1s;
    &:hover { background: #fafbff; }
    &:last-child td { border-bottom: none; }
  }
}

.data-table {
  table-layout: fixed; // 固定表格布局
  
  .col-id { width: 30px; }
  .col-name { width: 26%; }
  .col-job { width: 8%; }
  .col-style { width: 24%; }
  .col-temp { width: 6%; }
  .col-tokens { width: 10%; }
  .col-status { width: 8%; }
  .col-actions { width: 12%; }
  
  td {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    
    // 让名称列的 description 可以换行
    &.col-name {
      white-space: normal;
      word-break: break-word;
    }
  }
}
.td-id { color: #9ca3af; font-size: 12px; font-weight: 500; text-align: center; }
.td-center { text-align: center; }
.td-muted { color: #9ca3af; }
.td-style { color: #6b7280; font-size: 12px; }

.prompt-name { font-size: 13px; font-weight: 600; color: #111827; margin-bottom: 2px; }
.prompt-desc { font-size: 11px; color: #9ca3af; }

.job-chip {
  display: inline-block; padding: 2px 8px; 
  color: #5b21b6; font-size: 11px; font-weight: 600;
}

/* ── Temperature indicator ── */
.temp-val {
  font-size: 13px; font-weight: 700;
  &.temp--hot { color: #dc2626; }
  &.temp--warm { color: #d97706; }
  &.temp--cool { color: #2563eb; }
}

/* ── Toggle button ── */
.toggle-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px; border-radius: 6px; border: none;
  font-size: 11px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; font-family: $font-family-base;
  &--on { background: #ecfcf3; color: #1b8060; &:hover { background: #a7f3d0; } }
  &--off { background: #f3f4f6; color: #9ca3af; &:hover { background: #e5e7eb; } }
  &:disabled { opacity: 0.6; cursor: wait; }
}
.toggle-dot {
  width: 7px; height: 7px; border-radius: 50%;
  .toggle-btn--on & { background: #3a987b; }
  .toggle-btn--off & { background: #d1d5db; }
}

/* ── Row actions ── */
.row-actions { display: flex; gap: 6px; align-items: center;  }
.act-btn {
  width: 32px; height: 32px; border-radius: 8px; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.15s;
  svg { width: 16px; height: 16px; }
  &--preview { background: #f5f7f5; color: #059669; &:hover { background: #e2f9ea; } }
  &--edit { background: #f3f5fa; color: #4338ca; &:hover { background: #e4eafc; } }
  &--del { background: #fef7f7; color: #e11d48; &:hover { background: #f7e3e4; } }
}

/* ── Pagination ── */
.pagination {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-top: 1px solid #f3f4f6; gap: 16px; flex-wrap: wrap;
  &__info { font-size: 13px; color: #9ca3af; }
  &__btns { display: flex; gap: 4px; flex-wrap: wrap; }
}
.pg-btn {
  min-width: 34px; height: 34px; border: 1.5px solid #e5e7eb; border-radius: 7px;
  background: white; color: #374151; font-size: 13px; cursor: pointer; padding: 0 10px;
  font-family: $font-family-base; transition: all 0.15s;
  &:hover:not(:disabled) { border-color: #4338ca; color: #4338ca; }
  &--active { background: #4338ca; border-color: #4338ca; color: white; font-weight: 600; }
  &--ellipsis { cursor: default; border-color: transparent; background: none; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15,10,40,0.55); backdrop-filter: blur(4px);
  z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal-box {
  background: white; border-radius: 16px; width: 100%; max-width: 520px;
  max-height: 92vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2); overflow: hidden;
  &--wide { max-width: 780px; }
  &--sm { max-width: 420px; }
}
.modal-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 20px 24px 16px; border-bottom: 1px solid #f3f4f6; flex-shrink: 0;
  h2 { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 2px; }
}
.modal-sub { font-size: 12px; color: #9ca3af; margin: 0; }
.modal-close {
  width: 28px; height: 28px; border-radius: 6px; border: none;
  background: #f3f4f6; color: #6b7280; font-size: 13px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0;
  &:hover { background: #e5e7eb; color: #111827; }
}
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-foot {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; border-top: 1px solid #f3f4f6; flex-shrink: 0; background: #fafafa;
}

/* ── Form ── */
.form-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.form-group {
  display: flex; flex-direction: column; gap: 6px;
  &--full { width: 100%; }
  &--half { flex: 1; min-width: 200px; }
  &--third { flex: 1; min-width: 160px; }
  &--sixth { flex: 0 0 calc(33% - 12px); min-width: 140px; }
}
.form-label {
  font-size: 13px; font-weight: 600; color: #374151;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.form-label-hint { font-weight: 400; color: #9ca3af; font-size: 11px; }
.req { color: #ef4444; margin-left: 2px; }
.form-control {
  border: 1.5px solid #e5e7eb; border-radius: 8px; padding: 8px 12px;
  font-size: 13px; color: #111827; background: white; font-family: $font-family-base;
  transition: border-color 0.15s; outline: none; width: 100%; box-sizing: border-box;
  &:focus { border-color: #4338ca; box-shadow: 0 0 0 3px rgba(67,56,202,0.1); }
}
.form-textarea { resize: vertical; line-height: 1.6; &--lg { font-size: 12px; font-family: 'Menlo', 'Monaco', monospace; } }
.form-hint { font-size: 11px; color: #9ca3af; margin: 2px 0 0; line-height: 1.5; code { background: #f3f4f6; padding: 0 4px; border-radius: 3px; } }
.form-error { color: #ef4444; font-size: 13px; margin: 10px 0 0; }

/* Range slider */
.range-group { display: flex; align-items: center; gap: 10px; }
.range-slider {
  flex: 1; height: 4px; border-radius: 2px; cursor: pointer;
  accent-color: #4338ca;
}
.range-val { font-size: 14px; font-weight: 700; color: #4338ca; min-width: 28px; text-align: right; }

/* Active toggle */
.active-toggle {
  display: flex; align-items: center; gap: 12px; cursor: pointer;
  font-size: 13px; color: #374151; user-select: none;
}
.switch {
  width: 40px; height: 22px; border-radius: 11px; background: #e5e7eb; position: relative;
  transition: background 0.2s; flex-shrink: 0;
  &::after {
    content: ''; position: absolute; width: 18px; height: 18px; border-radius: 50%;
    background: white; top: 2px; left: 2px; transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  &--on { background: #4338ca; &::after { transform: translateX(18px); } }
}

/* ── Confirm ── */
.confirm-icon {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
  svg { width: 24px; height: 24px; }
  &--danger { background: #fff1f2; color: #e11d48; }
}
.confirm-text { text-align: center; font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 6px; }
.confirm-sub { text-align: center; font-size: 13px; color: #9ca3af; margin: 0; }

/* ── Preview ── */
.preview-meta {
  display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;
}
.meta-chip {
  display: flex; align-items: center; gap: 6px;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 5px 10px;
  &__label { font-size: 11px; color: #9ca3af; }
  &__val { font-size: 12px; font-weight: 600; color: #374151; }
}
.text-green { color: #059669 !important; }
.text-muted { color: #9ca3af !important; }

.prompt-block {
  background: #f9fafb; border-radius: 10px; padding: 16px; margin-bottom: 12px;
  border: 1px solid #f3f4f6;
  &--greeting { background: #eff6ff; border-color: #bfdbfe; }
  &__label {
    display: flex; align-items: center; gap: 5px;
    font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;
    letter-spacing: 0.06em; margin-bottom: 10px;
    .prompt-block--greeting & { color: #2563eb; }
  }
  p { font-size: 13px; color: #374151; line-height: 1.7; margin: 0; }
}
.prompt-pre {
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 12px; color: #374151; line-height: 1.7; margin: 0;
  white-space: pre-wrap; word-break: break-word;
}

/* ── Spinner ── */
.spinner {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid rgba(67,56,202,0.2); border-top-color: #4338ca;
  animation: spin 0.7s linear infinite; display: inline-block;
  &--sm { width: 14px; height: 14px; }
  &--light { border-color: rgba(255,255,255,0.3); border-top-color: white; }
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Modal 动画 ── */
.modal-enter-active { animation: modal-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
.modal-leave-active { animation: modal-in 0.18s ease reverse both; }
@keyframes modal-in {
  from { opacity: 0; transform: scale(0.94) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
