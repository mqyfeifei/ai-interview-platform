<!--
  frontend/src/views/admin/QuestionManager.vue
  题库管理 — 支持增删改查、按岗位/类型/难度筛选、批量 YAML 导入
-->
<template>
  <div class="qm-layout">

    <!-- ── 主内容区 ── -->
    <div class="qm-main">
    <!-- ── 主体 ── -->
      <div class="qm-content">

        <!-- 页头 -->
        <div class="qm-header">
          <div class="qm-header__left">
            <h1 class="qm-header__title">题库管理</h1>
            <p class="qm-header__sub">共 <strong>{{ total }}</strong> 道题目</p>
          </div>
          <div class="qm-header__actions">
            <button class="btn btn-outline" @click="openImport">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              批量导入
            </button>
            <button class="btn btn-primary" @click="openCreate">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              新建题目
            </button>
          </div>
        </div>

        <!-- 筛选栏 -->
        <div class="qm-filters">
          <select v-model="filterJobId" class="filter-select" @change="onFilterChange">
            <option value="">全部岗位</option>
            <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
          </select>
          <select v-model="filterType" class="filter-select" @change="onFilterChange">
            <option value="">全部类型</option>
            <option v-for="t in questionTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
          <select v-model="filterDifficulty" class="filter-select" @change="onFilterChange">
            <option value="">全部难度</option>
            <option v-for="d in difficulties" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
          <button v-if="hasFilters" class="btn-text" @click="clearFilters">清空筛选</button>
        </div>

        <!-- 表格卡片 -->
        <div class="table-card">
          <div v-if="loading" class="table-loading">
            <span class="spinner"></span> 加载中...
          </div>

          <div v-else-if="items.length === 0" class="table-empty">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="empty-icon">
              <rect x="8" y="16" width="48" height="36" rx="4" stroke="#d1d5db" stroke-width="2"/>
              <line x1="8" y1="26" x2="56" y2="26" stroke="#d1d5db" stroke-width="2"/>
              <line x1="20" y1="34" x2="44" y2="34" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
              <line x1="20" y1="40" x2="38" y2="40" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>暂无题目数据</p>
            <button class="btn btn-primary btn-sm" @click="openCreate">立即新建</button>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th style="width:60px">ID</th>
                <th>题目内容</th>
                <th style="width:90px">类型</th>
                <th style="width:80px">难度</th>
                <th style="width:120px">岗位</th>
                <th style="width:150px">关键词</th>
                <th style="width:110px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" class="data-table__row">
                <td class="td-id">#{{ item.id }}</td>
                <td class="td-content">
                  <span class="content-preview" :title="item.content">{{ truncate(item.content, 60) }}</span>
                </td>
                <td><span class="badge" :class="'badge-type--' + item.type">{{ labelType(item.type) }}</span></td>
                <td><span class="badge" :class="'badge-diff--' + item.difficulty">{{ labelDiff(item.difficulty) }}</span></td>
                <td class="td-job">{{ jobName(item.job_id) }}</td>
                <td>
                  <div class="tag-list">
                    <span v-for="(kw, i) in (item.keywords || []).slice(0, 3)" :key="i" class="mini-tag">{{ kw }}</span>
                    <span v-if="(item.keywords || []).length > 3" class="mini-tag mini-tag--more">+{{ item.keywords.length - 3 }}</span>
                  </div>
                </td>
                <td>
                  <div class="row-actions">
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
                        <path d="M10 11v6"/><path d="M14 11v6"/>
                        <path d="M9 6V4h6v2"/>
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
                v-for="p in pageList"
                :key="p"
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
            <h2>{{ formMode === 'create' ? '新建题目' : '编辑题目' }}</h2>
            <button class="modal-close" @click="closeForm">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <!-- 岗位 -->
              <div class="form-group form-group--half">
                <label class="form-label">关联岗位 <span class="req">*</span></label>
                <select v-model="form.job_id" class="form-control">
                  <option value="">请选择岗位</option>
                  <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
                </select>
              </div>
              <!-- 类型 -->
              <div class="form-group form-group--quarter">
                <label class="form-label">题目类型 <span class="req">*</span></label>
                <select v-model="form.type" class="form-control">
                  <option v-for="t in questionTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                </select>
              </div>
              <!-- 难度 -->
              <div class="form-group form-group--quarter">
                <label class="form-label">难度</label>
                <select v-model="form.difficulty" class="form-control">
                  <option value="">不设置</option>
                  <option v-for="d in difficulties" :key="d.value" :value="d.value">{{ d.label }}</option>
                </select>
              </div>
              <!-- 题目内容 -->
              <div class="form-group form-group--full">
                <label class="form-label">题目内容 <span class="req">*</span></label>
                <textarea v-model="form.content" class="form-control form-textarea" rows="4"
                  placeholder="请输入面试题目…"></textarea>
              </div>
              <!-- 参考答案 -->
              <div class="form-group form-group--full">
                <label class="form-label">参考答案</label>
                <textarea v-model="form.reference_answer" class="form-control form-textarea" rows="5"
                  placeholder="候选人标准回答要点（可选）…"></textarea>
              </div>
              <!-- 关键词 -->
              <div class="form-group form-group--half">
                <label class="form-label">关键词</label>
                <textarea v-model="form.keywordsText" class="form-control form-textarea form-textarea--sm" rows="3"
                  placeholder="每行一个关键词，例如：&#10;Redis&#10;缓存穿透"></textarea>
                <p class="form-hint">每行输入一个关键词</p>
              </div>
              <!-- 知识点 -->
              <div class="form-group form-group--half">
                <label class="form-label">考察知识点</label>
                <textarea v-model="form.knowledgeText" class="form-control form-textarea form-textarea--sm" rows="3"
                  placeholder="每行一个知识点，例如：&#10;线程安全&#10;volatile 关键字"></textarea>
                <p class="form-hint">每行输入一个知识点</p>
              </div>
            </div>

            <p v-if="formError" class="form-error">{{ formError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeForm" :disabled="formLoading">取消</button>
            <button class="btn btn-primary" @click="submitForm" :disabled="formLoading">
              <span v-if="formLoading" class="spinner spinner--sm"></span>
              {{ formMode === 'create' ? '创建题目' : '保存修改' }}
            </button>
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
            <p class="confirm-text">确定要删除这道题目吗？</p>
            <p class="confirm-sub">此操作不可恢复。</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="showDeleteConfirm = false" :disabled="deleteLoading">取消</button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="deleteLoading">
              <span v-if="deleteLoading" class="spinner spinner--sm"></span>
              确认删除
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ══════════ 批量导入 Modal ══════════ -->
    <transition name="modal">
      <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
        <div class="modal-box">
          <div class="modal-head">
            <h2>批量导入题库</h2>
            <button class="modal-close" @click="showImport = false">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="!importResult">
              <p class="import-desc">从服务器 <code>FuChuangTiKu</code> 目录读取 YAML 文件批量导入题目。</p>
              <div class="import-options">
                <label class="switch-label">
                  <span>预览模式（dry run）</span>
                  <input type="checkbox" v-model="importDryRun" class="sr-only"/>
                  <span class="switch" :class="{ 'switch--on': importDryRun }"></span>
                </label>
                <p class="option-hint">开启后只分析不实际写入数据库，用于确认导入内容</p>
              </div>
              <div class="import-options import-options--danger" v-if="!importDryRun">
                <label class="switch-label">
                  <span class="text-danger">清空已有题库</span>
                  <input type="checkbox" v-model="importClearExisting" class="sr-only"/>
                  <span class="switch switch--danger" :class="{ 'switch--on': importClearExisting }"></span>
                </label>
                <p class="option-hint text-danger">⚠️ 危险操作：执行前会删除所有现有题目</p>
              </div>
              <p v-if="importError" class="form-error">{{ importError }}</p>
            </div>

            <!-- 导入结果 -->
            <div v-else class="import-result">
              <div class="import-result__header" :class="importResult.dry_run ? 'dry' : 'real'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ importResult.dry_run ? '预览完成（未写入数据库）' : '导入成功' }}
              </div>
              <div class="import-result__stats">
                <div class="stat-chip">
                  <span class="stat-chip__num">{{ importResult.imported_total }}</span>
                  <span class="stat-chip__label">待导入</span>
                </div>
                <div class="stat-chip stat-chip--warn">
                  <span class="stat-chip__num">{{ importResult.skipped }}</span>
                  <span class="stat-chip__label">跳过</span>
                </div>
              </div>
              <div class="import-files">
                <div v-for="f in importResult.files" :key="f.type" class="import-file">
                  <span class="import-file__name">{{ f.type }}</span>
                  <span class="import-file__job">{{ f.job_name }}</span>
                  <span class="import-file__cnt">{{ f.count }} 题</span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeImport">{{ importResult ? '关闭' : '取消' }}</button>
            <button v-if="!importResult" class="btn btn-primary" @click="runImport" :disabled="importLoading">
              <span v-if="importLoading" class="spinner spinner--sm"></span>
              {{ importDryRun ? '预览导入' : '执行导入' }}
            </button>
            <button v-if="importResult && importResult.dry_run" class="btn btn-primary" @click="runImport(true)">
              确认导入
            </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import {
  listQuestions, createQuestion, updateQuestion, deleteQuestion, importQuestions, listAdminJobs
} from '@/api/admin'

const QUESTION_TYPES = [
  { value: 'technical', label: '技术题' },
  { value: 'basic', label: '基础知识' },
  { value: 'scenario', label: '场景设计' },
  { value: 'followup', label: '追问题' },
  { value: 'behavioral', label: '行为面试' },
]

const DIFFICULTIES = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' },
]

function defaultForm() {
  return {
    job_id: '',
    type: 'technical',
    difficulty: '',
    content: '',
    reference_answer: '',
    keywordsText: '',
    knowledgeText: ''
  }
}

export default {
  name: 'QuestionManager',

  data() {
    return {
      // list
      items: [],
      total: 0,
      page: 1,
      size: 15,
      loading: false,

      // filters
      filterJobId: '',
      filterType: '',
      filterDifficulty: '',

      // options
      jobs: [],
      questionTypes: QUESTION_TYPES,
      difficulties: DIFFICULTIES,

      // form modal
      showForm: false,
      formMode: 'create',
      formLoading: false,
      formError: '',
      form: defaultForm(),
      editingId: null,

      // delete
      showDeleteConfirm: false,
      deletingId: null,
      deleteLoading: false,

      // import
      showImport: false,
      importLoading: false,
      importDryRun: true,
      importClearExisting: false,
      importResult: null,
      importError: ''
    }
  },

  computed: {
    hasFilters() {
      return this.filterJobId || this.filterType || this.filterDifficulty
    },
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
      } catch (e) {
        console.warn('加载岗位失败', e)
      }
    },

    async loadData() {
      this.loading = true
      try {
        const params = { page: this.page, size: this.size }
        if (this.filterJobId) params.job_id = this.filterJobId
        if (this.filterType) params.type = this.filterType
        if (this.filterDifficulty) params.difficulty = this.filterDifficulty
        const res = await listQuestions(params)
        this.items = res.list || []
        this.total = res.total || 0
      } catch (e) {
        console.error('加载题目失败', e)
      } finally {
        this.loading = false
      }
    },

    onFilterChange() {
      this.page = 1
      this.loadData()
    },

    clearFilters() {
      this.filterJobId = ''
      this.filterType = ''
      this.filterDifficulty = ''
      this.page = 1
      this.loadData()
    },

    goPage(p) {
      if (p < 1 || p > this.totalPages) return
      this.page = p
      this.loadData()
    },

    // ── Form helpers ──
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
        job_id: item.job_id || '',
        type: item.type || 'technical',
        difficulty: item.difficulty || '',
        content: item.content || '',
        reference_answer: item.reference_answer || '',
        keywordsText: Array.isArray(item.keywords) ? item.keywords.join('\n') : '',
        knowledgeText: Array.isArray(item.knowledge_points) ? item.knowledge_points.join('\n') : ''
      }
      this.formError = ''
      this.showForm = true
    },

    closeForm() {
      this.showForm = false
    },

    parseLines(text) {
      if (!text || !text.trim()) return null
      const arr = text.split(/\n/).map(s => s.trim()).filter(Boolean)
      return arr.length ? arr : null
    },

    async submitForm() {
      this.formError = ''
      if (!this.form.job_id) { this.formError = '请选择关联岗位'; return }
      if (!this.form.content.trim()) { this.formError = '题目内容不能为空'; return }

      const data = {
        job_id: this.form.job_id,
        type: this.form.type,
        difficulty: this.form.difficulty || null,
        content: this.form.content.trim(),
        reference_answer: this.form.reference_answer.trim() || null,
        keywords: this.parseLines(this.form.keywordsText),
        knowledge_points: this.parseLines(this.form.knowledgeText)
      }

      this.formLoading = true
      try {
        if (this.formMode === 'create') {
          await createQuestion(data)
        } else {
          await updateQuestion(this.editingId, data)
        }
        this.showForm = false
        this.loadData()
      } catch (e) {
        this.formError = e.message || '操作失败，请重试'
      } finally {
        this.formLoading = false
      }
    },

    // ── Delete ──
    askDelete(item) {
      this.deletingId = item.id
      this.showDeleteConfirm = true
    },

    async confirmDelete() {
      this.deleteLoading = true
      try {
        await deleteQuestion(this.deletingId)
        this.showDeleteConfirm = false
        this.deletingId = null
        // if last item on page, go back
        if (this.items.length === 1 && this.page > 1) this.page--
        this.loadData()
      } catch (e) {
        alert(e.message || '删除失败')
      } finally {
        this.deleteLoading = false
      }
    },

    // ── Import ──
    openImport() {
      this.importResult = null
      this.importError = ''
      this.importDryRun = true
      this.importClearExisting = false
      this.showImport = true
    },

    closeImport() {
      this.showImport = false
      if (this.importResult && !this.importResult.dry_run) {
        this.loadData()
      }
    },

    async runImport(confirmReal = false) {
      // confirmReal = true 表示干跑完后用户确认要真正导入
      this.importError = ''
      const dryRun = confirmReal ? false : this.importDryRun
      const clearExisting = !dryRun && this.importClearExisting

      this.importLoading = true
      try {
        const res = await importQuestions({ dry_run: dryRun, clear_existing: clearExisting })
        this.importResult = res
      } catch (e) {
        this.importError = e.message || '导入失败'
      } finally {
        this.importLoading = false
      }
    },

    // ── Display helpers ──
    truncate(str, len) {
      if (!str) return ''
      return str.length > len ? str.slice(0, len) + '…' : str
    },

    jobName(jobId) {
      const j = this.jobs.find(j => j.id === jobId)
      return j ? j.name : (jobId ? `#${jobId}` : '—')
    },

    labelType(type) {
      const t = QUESTION_TYPES.find(t => t.value === type)
      return t ? t.label : (type || '—')
    },

    labelDiff(diff) {
      const d = DIFFICULTIES.find(d => d.value === diff)
      return d ? d.label : (diff || '—')
    }
  }
}
</script>

<style lang="scss" scoped>
/* ── 全局容器 ── */
.qm-layout {
  display: flex;
  min-height: 100vh;
  background: #f5f6fa;
  font-family: $font-family-base;
}

.qm-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 28px 32px;
  overflow-y: auto;
  max-height: 100vh;
}



/* ── 主体内容 ── */
.qm-content {
  max-width: 1500px;
  width: 100%;
  margin: 0 auto;
}

/* ── 页头 ── */
.qm-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;

  &__title {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    margin: 0 0 4px;
    letter-spacing: -0.3px;
  }
  &__sub {
    font-size: 13px;
    color: #9ca3af;
    margin: 0;
    strong { color: #4338ca; font-weight: 600; }
  }
  &__actions {
    display: flex;
    gap: 10px;
    flex-shrink: 0;
    align-items: center;
  }
}

/* ── 按钮 ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 18px;
  height: 38px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  font-family: $font-family-base;
  border: none;

  &-primary {
    background: #4338ca;
    color: white;
    &:hover { background: #3730a3; }
    &:active { transform: scale(0.98); }
  }
  &-outline {
    background: white;
    color: #4338ca;
    border: 1.5px solid #c7d2fe;
    &:hover { background: #eef2ff; }
  }
  &-ghost {
    background: #f3f4f6;
    color: #6b7280;
    &:hover { background: #e5e7eb; color: #374151; }
  }
  &-danger {
    background: #ef4444;
    color: white;
    &:hover { background: #dc2626; }
  }
  &-sm { height: 32px; padding: 0 14px; font-size: 12px; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}
.btn-icon { width: 14px; height: 14px; flex-shrink: 0; }
.btn-text {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: $font-family-base;
  &:hover { background: #f3f4f6; color: #374151; }
}

/* ── 筛选栏 ── */
.qm-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-select {
  height: 36px;
  padding: 0 30px 0 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat right 10px center;
  appearance: none;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  font-family: $font-family-base;
  transition: border-color 0.15s;
  &:focus { outline: none; border-color: #4338ca; }
}

/* ── 表格卡片 ── */
.table-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  overflow: hidden;
}

.table-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px;
  color: #9ca3af;
  font-size: 14px;
}

.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 70px 20px;
  gap: 12px;
  color: #9ca3af;
  font-size: 14px;
}
.empty-icon { width: 64px; height: 64px; opacity: 0.5; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;

  th {
    background: #f9fafb;
    color: #6b7280;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 11px 16px;
    text-align: left;
    border-bottom: 1px solid #f3f4f6;
    white-space: nowrap;
  }

  td {
    padding: 13px 16px;
    color: #374151;
    border-bottom: 1px solid #f9fafb;
    vertical-align: middle;
  }

  &__row {
    transition: background 0.1s;
    &:hover { background: #fafbff; }
    &:last-child td { border-bottom: none; }
  }
}

.td-id { color: #9ca3af; font-size: 12px; font-weight: 500; }
.td-content { max-width: 320px; }
.content-preview {
  display: block;
  color: #111827;
  font-weight: 500;
  line-height: 1.45;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.td-job { color: #6b7280; }

/* ── 徽章 ── */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.badge-type {
  &--technical { background: #dbeafe; color: #1e40af; }
  &--basic     { background: #d1fae5; color: #065f46; }
  &--scenario  { background: #ede9fe; color: #5b21b6; }
  &--followup  { background: #fef3c7; color: #92400e; }
  &--behavioral{ background: #fce7f3; color: #9d174d; }
}

.badge-diff {
  &--easy   { background: #d1fae5; color: #065f46; }
  &--medium { background: #fef3c7; color: #78350f; }
  &--hard   { background: #fee2e2; color: #991b1b; }
}

/* ── 关键词标签 ── */
.tag-list { display: flex; flex-wrap: wrap; gap: 4px; }
.mini-tag {
  background: #f3f4f6;
  color: #6b7280;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  &--more { background: #e5e7eb; }
}

/* ── 行操作按钮 ── */
.row-actions { display: flex; gap: 6px; align-items: center; }
.act-btn {
  width: 30px; height: 30px;
  border-radius: 6px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  svg { width: 14px; height: 14px; }

  &--edit {
    background: #eef2ff; color: #4338ca;
    &:hover { background: #e0e7ff; }
  }
  &--del {
    background: #fff1f2; color: #e11d48;
    &:hover { background: #ffe4e6; }
  }
}

/* ── 分页 ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #f3f4f6;
  gap: 16px;
  flex-wrap: wrap;

  &__info { font-size: 13px; color: #9ca3af; }
  &__btns { display: flex; gap: 4px; flex-wrap: wrap; }
}

.pg-btn {
  min-width: 34px; height: 34px;
  border: 1.5px solid #e5e7eb;
  border-radius: 7px;
  background: white;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  padding: 0 10px;
  font-family: $font-family-base;
  transition: all 0.15s;
  &:hover:not(:disabled) { border-color: #4338ca; color: #4338ca; }
  &--active { background: #4338ca; border-color: #4338ca; color: white; font-weight: 600; }
  &--ellipsis { cursor: default; border-color: transparent; background: none; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
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
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  overflow: hidden;

  &--wide { max-width: 760px; }
  &--sm { max-width: 420px; }
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;

  h2 { font-size: 16px; font-weight: 700; color: #111827; margin: 0; }
}

.modal-close {
  width: 28px; height: 28px;
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
  &:hover { background: #e5e7eb; color: #111827; }
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid #f3f4f6;
  flex-shrink: 0;
  background: #fafafa;
}

/* ── Form ── */
.form-grid { display: flex; flex-wrap: wrap; gap: 16px; }
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  &--full { width: 100%; }
  &--half { flex: 1; min-width: 200px; }
  &--quarter { width: calc(25% - 12px); min-width: 120px; }
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.req { color: #ef4444; margin-left: 2px; }

.form-control {
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: #111827;
  background: white;
  font-family: $font-family-base;
  transition: border-color 0.15s;
  outline: none;
  width: 100%;
  box-sizing: border-box;

  &:focus { border-color: #4338ca; box-shadow: 0 0 0 3px rgba(67,56,202,0.1); }
}

.form-textarea {
  resize: vertical;
  line-height: 1.6;
  &--sm { resize: vertical; }
}

.form-hint { font-size: 11px; color: #9ca3af; margin: 0; }
.form-error { color: #ef4444; font-size: 13px; margin: 10px 0 0; }

/* ── Confirm dialog ── */
.confirm-icon {
  width: 56px; height: 56px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
  svg { width: 24px; height: 24px; }
  &--danger { background: #fff1f2; color: #e11d48; }
}
.confirm-text { text-align: center; font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 6px; }
.confirm-sub { text-align: center; font-size: 13px; color: #9ca3af; margin: 0; }

/* ── Import ── */
.import-desc {
  font-size: 13px; color: #6b7280; margin: 0 0 20px; line-height: 1.6;
  code { background: #f3f4f6; padding: 1px 6px; border-radius: 4px; font-size: 12px; color: #374151; }
}

.import-options {
  padding: 14px 16px;
  background: #f9fafb;
  border-radius: 10px;
  margin-bottom: 12px;
  &--danger { background: #fff5f5; }
}

.switch-label {
  display: flex; align-items: center; justify-content: space-between; cursor: pointer;
  font-size: 13px; font-weight: 600; color: #374151;
  .sr-only { display: none; }
}
.text-danger { color: #dc2626; }

.switch {
  width: 36px; height: 20px;
  border-radius: 10px;
  background: #e5e7eb;
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
  &::after {
    content: '';
    position: absolute;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: white;
    top: 2px; left: 2px;
    transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  &--on { background: #4338ca; &::after { transform: translateX(16px); } }
  &--danger.switch--on { background: #dc2626; }
}

.option-hint { font-size: 11px; color: #9ca3af; margin: 6px 0 0; }

.import-result {
  &__header {
    display: flex; align-items: center; gap: 8px;
    padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 600;
    margin-bottom: 16px;
    &.real { background: #d1fae5; color: #065f46; }
    &.dry { background: #dbeafe; color: #1e40af; }
  }
  &__stats { display: flex; gap: 12px; margin-bottom: 16px; }
}

.stat-chip {
  flex: 1; background: #f9fafb; border-radius: 10px; padding: 12px 16px; text-align: center;
  border: 1px solid #e5e7eb;
  &--warn { border-color: #fcd34d; background: #fffbeb; }
  &__num { display: block; font-size: 24px; font-weight: 800; color: #111827; line-height: 1; margin-bottom: 4px; }
  &__label { font-size: 12px; color: #9ca3af; }
}

.import-files {
  display: flex; flex-direction: column; gap: 6px;
  max-height: 200px; overflow-y: auto;
}
.import-file {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: #f9fafb; border-radius: 7px;
  font-size: 12px;
  &__name { flex: 1; color: #374151; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  &__job { color: #9ca3af; }
  &__cnt { color: #4338ca; font-weight: 600; }
}

/* ── Spinner ── */
.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
  &--sm { width: 14px; height: 14px; border-width: 2px; }
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 深色 spinner 变体（用于 loading 状态）── */
.table-loading .spinner {
  border-color: rgba(67,56,202,0.2);
  border-top-color: #4338ca;
}

/* ── Modal 动画 ── */
.modal-enter-active { animation: modal-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
.modal-leave-active { animation: modal-in 0.18s ease reverse both; }
@keyframes modal-in {
  from { opacity: 0; transform: scale(0.94) translateY(12px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
</style>