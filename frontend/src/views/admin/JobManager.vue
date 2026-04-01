<template>
  <div class="jm-layout">
    <AdminSideNav />
    <div class="jm-main">
      <div class="jm-content">
        <div class="jm-header">
          <div class="jm-header__left">
            <h1 class="jm-header__title">岗位管理</h1>
            <p class="jm-header__sub">共 <strong>{{ total }}</strong> 个岗位</p>
          </div>
          <button class="btn btn-primary" @click="openCreate">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            新建岗位
          </button>
        </div>

        <div class="jm-filters">
          <input v-model="searchKeyword" class="filter-input" placeholder="按岗位名/描述搜索" @keyup.enter="onSearch" />
          <button class="btn btn-primary" @click="onSearch">搜索</button>
          <button v-if="hasFilters" class="btn btn-text" @click="clearFilters">清空</button>
        </div>

        <div class="table-card">
          <div v-if="loading" class="table-loading"><span class="spinner"></span> 加载中...</div>

          <div v-else-if="jobs.length === 0" class="table-empty">
            <p>暂无岗位数据</p>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th style="width:60px">ID</th>
                <th>岗位名称</th>
                <th>描述</th>
                <th style="width:230px">技术栈</th>
                <th style="width:170px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.id">
                <td>#{{ job.id }}</td>
                <td class="job-name-cell">
                  <template v-if="job.icon_url">
                    <img :src="job.icon_url" class="job-icon" alt="icon" @error="onJobIconError" />
                  </template>
                  <template v-else>
                    <div class="job-icon job-icon--default">💼</div>
                  </template>
                  <span>{{ job.name }}</span>
                </td>
                <td>{{ job.description || '—' }}</td>
                <td>{{ job.tech_stack && job.tech_stack.length ? job.tech_stack.join(', ') : '—' }}</td>
                <td>
                  <div class="row-actions">
                    <button class="act-btn act-btn--edit" @click="openEdit(job)">编辑</button>
                    <button class="act-btn act-btn--del" @click="confirmDelete(job)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

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

    <transition name="modal">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box modal-box--wide">
          <div class="modal-head">
            <h2>{{ modalMode === 'create' ? '新建岗位' : '编辑岗位' }}</h2>
            <button class="modal-close" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group form-group--half">
                <label class="form-label">岗位名 <span class="req">*</span></label>
                <input v-model="form.name" class="form-control" type="text" placeholder="岗位名称" />
              </div>
              <div class="form-group form-group--half">
                <label class="form-label">图标 URL</label>
                <div class="icon-input-container">
                  <input v-model="form.icon_url" class="form-control" type="text" placeholder="可选" />
                  <div class="icon-input-extra">
                    <label v-if="!form.icon_url" class="upload-btn upload-btn--icon compact">
                      <span class="upload-icon">+</span>
                      <input type="file" accept="image/*" @change="onIconFileChange" />
                    </label>
                    <div v-else class="icon-preview-small">
                      <img :src="form.icon_url" alt="图标预览" @error="onJobIconError" />
                    </div>
                  </div>
                </div>
              </div>
              <div class="form-group form-group--full">
                <label class="form-label">岗位描述</label>
                <textarea v-model="form.description" class="form-control form-textarea" rows="3" placeholder="岗位描述"></textarea>
              </div>
              <div class="form-group form-group--full">
                <label class="form-label">技术栈（逗号分隔）</label>
                <textarea v-model="techStackText" class="form-control form-textarea" rows="3" placeholder="Java, SpringBoot, MySQL"></textarea>
              </div>
            </div>
            <p v-if="formError" class="form-error">{{ formError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeModal">取消</button>
            <button class="btn btn-primary" :disabled="modalLoading" @click="submitForm">
              <span v-if="modalLoading" class="spinner spinner--sm"></span>
              {{ modalMode === 'create' ? '创建岗位' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="modal-box modal-box--sm">
          <div class="modal-head">
            <h2>确认删除岗位</h2>
            <button class="modal-close" @click="showDeleteConfirm = false">✕</button>
          </div>
          <div class="modal-body">
            <p>确认删除岗位《{{ deletingJob?.name || '' }}》吗？此操作不可恢复。</p>
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
import AdminSideNav from '@/components/admin/AdminSideNav.vue'
import { listJobs, createJob, updateJob, deleteJob, uploadJobIcon } from '@/api/admin'

function defaultJobForm() {
  return {
    name: '',
    description: '',
    tech_stack: [],
    icon_url: ''
  }
}

export default {
  name: 'JobManager',
  components: { AdminSideNav },
  data() {
    return {
      jobs: [],
      total: 0,
      page: 1,
      size: 15,
      loading: false,
      searchKeyword: '',

      showModal: false,
      modalMode: 'create',
      modalLoading: false,
      formError: '',
      form: defaultJobForm(),
      techStackText: '',
      editingId: null,

      showDeleteConfirm: false,
      deletingJob: null,
      deleteLoading: false,
      deleteError: ''
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.size) || 1
    },
    hasFilters() {
      return !!this.searchKeyword
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
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const params = { page: this.page, size: this.size }
        if (this.searchKeyword) {
          params.q = this.searchKeyword
        }
        const res = await listJobs(params)
        this.jobs = res.list || []
        this.total = res.total || 0
      } catch (err) {
        console.error('加载岗位失败', err)
      } finally {
        this.loading = false
      }
    },

    onSearch() {
      this.page = 1
      this.loadData()
    },

    clearFilters() {
      this.searchKeyword = ''
      this.page = 1
      this.loadData()
    },

    goPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.page = page
      this.loadData()
    },

    openCreate() {
      this.modalMode = 'create'
      this.form = defaultJobForm()
      this.techStackText = ''
      this.formError = ''
      this.editingId = null
      this.showModal = true
    },

    openEdit(job) {
      this.modalMode = 'edit'
      this.editingId = job.id
      this.form = {
        name: job.name || '',
        description: job.description || '',
        tech_stack: Array.isArray(job.tech_stack) ? job.tech_stack : [],
        icon_url: job.icon_url || ''
      }
      this.techStackText = (this.form.tech_stack || []).join(', ')
      this.formError = ''
      this.showModal = true
    },

    closeModal() {
      this.showModal = false
    },

    onJobIconError(event) {
      const parent = event.target.parentNode
      event.target.style.display = 'none'
      if (parent) {
        const defaultIcon = parent.querySelector('.job-icon--default')
        if (defaultIcon) {
          defaultIcon.style.display = 'flex'
        }
      }
    },

    async onIconFileChange(event) {
      const file = event.target.files[0]
      if (!file) {
        return
      }
      this.formError = ''
      this.modalLoading = true
      try {
        const data = await uploadJobIcon(file)
        this.form.icon_url = data.icon_url
      } catch (err) {
        this.formError = err.message || '图标上传失败'
      } finally {
        this.modalLoading = false
      }
    },

    async submitForm() {
      this.formError = ''
      if (!this.form.name.trim()) {
        this.formError = '岗位名称不能为空'
        return
      }
      this.modalLoading = true
      try {
        const payload = {
          name: this.form.name.trim(),
          description: this.form.description.trim() || null,
          tech_stack: this.techStackText
            .split(',')
            .map(s => s.trim())
            .filter(Boolean),
          icon_url: this.form.icon_url.trim() || null
        }
        if (this.modalMode === 'create') {
          await createJob(payload)
        } else {
          await updateJob(this.editingId, payload)
        }
        this.showModal = false
        this.loadData()
      } catch (err) {
        this.formError = err.message || '操作失败'
      } finally {
        this.modalLoading = false
      }
    },

    confirmDelete(job) {
      this.deletingJob = job
      this.deleteError = ''
      this.showDeleteConfirm = true
    },

    async doDelete() {
      if (!this.deletingJob) return
      this.deleteLoading = true
      try {
        await deleteJob(this.deletingJob.id)
        this.showDeleteConfirm = false
        this.deletingJob = null
        this.deleteError = ''
        if (this.jobs.length === 1 && this.page > 1) this.page--
        this.loadData()
      } catch (err) {
        this.deleteError = err.message || '删除失败'
      } finally {
        this.deleteLoading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.jm-layout { display: flex; min-height: 100vh; background: #f5f6fa; }
.jm-main { flex: 1; min-width: 0; display: flex; flex-direction: column; padding: 28px 32px; overflow-y: auto; max-height: 100vh; }
.jm-content { max-width: 1400px; width: 100%; margin: 0 auto; }
.jm-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; gap: 16px; }
.jm-header__title { font-size: 22px; font-weight: 700; margin: 0; }
.jm-header__sub { margin: 0; color: #6b7280; }
.jm-filters { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.filter-input { height: 36px; padding: 0 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: white; }
.table-card { background: white; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 4px rgba(0,0,0,0.04); overflow: hidden; }
.table-loading, .table-empty { padding: 50px 20px; text-align: center; color: #9ca3af; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 12px 16px; border-bottom: 1px solid #f3f4f6; text-align: left; }
.data-table th { background: #f9fafb; color: #6b7280; font-weight: 600; }
.row-actions { display: flex; gap: 6px; }

.job-name-cell { display: flex; align-items: center; gap: 8px; }
.job-icon { width: 24px; height: 24px; border-radius: 4px; object-fit: cover; }
.job-icon--default { width: 24px; height: 24px; border-radius: 4px; background: #e5e7eb; color: #4b5563; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; }

.icon-upload-row { display: flex; align-items: center; gap: 8px; }
.icon-input-row { display: flex; gap: 8px; align-items: center; }
.icon-input-container { display: flex; align-items: center; gap: 6px; }
.icon-input-extra { display: flex; gap: 8px; align-items: center; }
.form-control { flex: 1; }
.upload-btn--icon.compact { width: 26px; height: 26px; padding: 0; border-radius: 4px; font-size: 18px; line-height: 26px; position: relative; border: 1px dashed #c2c8d6; background: #f9fbff; color: #6b7280; display: flex; align-items: center; justify-content: center; }
.upload-btn--icon.compact:hover { background: #eef3ff; border-color: #9eb5e6; }
.upload-btn--icon.compact input[type="file"] { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
.icon-preview-small { width: 26px; height: 26px; border-radius: 4px; overflow: hidden; border: 1px solid #dbeafe; background: #fff; }
.icon-preview-small img { width: 100%; height: 100%; object-fit: cover; }
.icon-upload-row .upload-btn { display: inline-flex; align-items: center; justify-content: center; height: 36px; padding: 0 12px; background: #5c6ac4; color: white; border-radius: 8px; cursor: pointer; position: relative; overflow: hidden; font-size: 12px; }
.icon-upload-row .upload-btn input[type="file"] { position: absolute; inset: 0; opacity: 0; width: 100%; cursor: pointer; }
.icon-preview img { max-width: 48px; max-height: 48px; border-radius: 6px; border: 1px solid #e5e7eb; }

.act-btn { border: 1px solid #d9e2f3; background: #fff; border-radius: 4px; padding: 5px 10px; font-size: 12px; color: #1f4ed8; cursor: pointer; }
.act-btn--edit { background: #eef2ff; color: #1f4ed8; border-color: #c6cdd8; }
.act-btn--del { background: #fff1f2; color: #c7483b; border-color: #f1d7dd; }
.pagination { padding: 12px; display: flex; justify-content: space-between; align-items: center; }
.pagination__info { color: #666; }
.delete-error { margin-top: 8px; color: #e11d48; font-weight: 500; }
.pg-btn { border: 1px solid #d9dfee; background: #fff; line-height: 1.2; border-radius: 4px; padding: 5px 10px; cursor: pointer; }
.pg-btn--active { background: #2f80ed; color: #fff; border-color: #2f80ed; }
.pg-btn--ellipsis { cursor: default; }
.modal-overlay { position: fixed; top:0;left:0;right:0;bottom:0; background: rgba(0,0,0,0.4); display: flex; justify-content: center; align-items: center; z-index: 999; }
.modal-box { background: white; border-radius: 12px; width: 680px; max-width: 96%; overflow: hidden; }
.modal-close { width: 28px; height: 28px; border-radius: 6px; border: none; background: #f3f4f6; color: #6b7280; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: #e5e7eb; color: #111827; }
.modal-head, .modal-foot { padding: 14px 18px; border-bottom: 1px solid #f3f4f6; display: flex; align-items:center; justify-content: space-between; }
.modal-body { padding: 16px 18px; }
.form-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 1px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-control { height: 36px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0 10px; }
.form-textarea { min-height: 80px; resize: vertical; }
.form-error { color: #e11d48; margin-top: 8px; }
</style>
