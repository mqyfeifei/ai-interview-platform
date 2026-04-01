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
            <h1 class="qm-header__title">题库与学习资源管理</h1>
            <p class="qm-header__sub">共 <strong>{{ total }}</strong> 条记录</p>
            <div class="entity-tabs">
              <button :class="['tab-btn', { active: entity === 'question' }]" @click="switchEntity('question')">题目</button>
              <button :class="['tab-btn', { active: entity === 'resource' }]" @click="switchEntity('resource')">学习资源</button>
            </div>
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
            <button class="btn btn-primary btn-image" @click="openCreate">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" class="btn-icon">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              {{ entity === 'question' ? '新建题目' : '新建学习资源' }}
            </button>
          </div>
        </div>

        <!-- 筛选栏 -->
        <div class="qm-filters">
          <select v-if="entity === 'question'" v-model="filterJobId" class="filter-select" @change="onFilterChange">
            <option value="">全部岗位</option>
            <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
          </select>
          <select v-model="filterType" class="filter-select" @change="onFilterChange">
            <option value="">全部类型</option>
            <option v-for="t in (entity === 'resource' ? resourceTypes : questionTypes)" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
          <select v-model="filterDifficulty" class="filter-select" @change="onFilterChange">
            <option value="">全部难度</option>
            <option v-for="d in difficulties" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
          <select v-if="entity === 'question'" v-model="filterStatus" class="filter-select" @change="onFilterChange">
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="published">已发布</option>
          </select>
          <div class="qm-search" style="flex: 1; min-width: 220px; max-width: 360px;">
            <div class="qm-search-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="qm-search-box__icon">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input v-model="filterKeyword" type="text" placeholder="按内容/标题搜索" class="qm-search-box__input" @input="onSearchDebounce" />
              <button v-if="filterKeyword" class="qm-search-box__clear" @click="clearSearch">✕</button>
            </div>
          </div>
          <button v-if="hasFilters" class="btn-clear" @click="clearFilters">清空筛选</button>
          <button v-if="entity === 'question' && filterStatus === 'draft' && items.length > 0" 
                  class="btn btn-primary btn-sm" 
                  @click="bulkPublish" 
                  style="margin-left:auto;">
            批量发布全部
          </button>
        </div>

        <!-- 表格卡片（支持横向滚动） -->
        <div class="table-card table-card--scrollable">
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
            <p>暂无{{ entity === 'question' ? '题目' : '学习资源' }}数据</p>
            <button class="btn btn-primary btn-sm" @click="openCreate">立即新建</button>
          </div>

                    <table v-else class="data-table">
            <thead>
              <tr v-if="entity === 'question'">
                <th style="width:60px">ID</th>
                <th style="width:120px">岗位</th>
                <th>内容</th>
                <th style="width:90px">类型</th>
                <th style="width:90px">难度</th>
                <th style="width:160px">关键点</th>
                <th style="width:160px">参考答案</th>
                <th style="width:110px">来源</th>
                <th style="width:90px">状态</th>
                <th style="width:110px">操作</th>
              </tr>
              <tr v-else>
                <th style="width:50px">ID</th>
                <th style="width:170px">标题</th>
                <th style="width:55px">类型</th>
                <th style="width:120px">学习链接</th>
                <th style="width:140px">内容简介</th>
                <th style="width:80px">来源</th>
                <th style="width:70px">难度</th>
                <th style="width:120px">知识标签</th>
                <th style="width:80px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" class="data-table__row" @click="viewDetail(item)" style="cursor:pointer;">
                <template v-if="entity === 'question'">
                  <td class="td-id">#{{ item.id }}</td>
                  <td class="td-job">{{ jobName(item.job_id) }}</td>
                  <td class="td-content"><span class="content-preview" :title="item.content">{{ truncate(item.content, 80) }}</span></td>
                  <td><span class="badge" :class="'badge-type--' + item.type">{{ labelType(item.type) }}</span></td>
                  <td><span class="badge" :class="'badge-diff--' + item.difficulty">{{ labelDiff(item.difficulty) }}</span></td>
                  <td>
                    <div class="tag-list">
                      <span v-for="(kw, i) in (item.keywords || []).slice(0, 3)" :key="i" class="mini-tag">{{ kw }}</span>
                      <span v-if="(item.keywords || []).length > 3" class="mini-tag mini-tag--more">+{{ item.keywords.length - 3 }}</span>
                    </div>
                  </td>
                  <td><span class="content-preview" :title="Array.isArray(item.reference_answer) ? item.reference_answer.join('\n') : item.reference_answer">{{ truncate(Array.isArray(item.reference_answer) ? item.reference_answer.join(', ') : item.reference_answer, 50) }}</span></td>
                  <td class="td-source">{{ item.source || '—' }}</td>
                  <td>
                    <div class="status-toggle" @click.stop="toggleStatus(item)">
                      <div class="toggle-track" :class="{ 'toggle-track--on': item.status === 'published' }">
                        <div class="toggle-thumb"></div>
                      </div>
                      <span class="status-label">{{ item.status === 'published' ? '发布' : '草稿' }}</span>
                    </div>
                  </td>
                </template>
                <template v-else>
                  <td class="td-id">#{{ item.id }}</td>
                  <td class="td-content"><span class="content-preview" :title="item.title">{{ truncate(item.title, 80) }}</span></td>
                  <td><span class="badge" :class="'badge-type--' + item.type">{{ labelType(item.type) }}</span></td>
                  <td><a :href="item.url" target="_blank" rel="noopener noreferrer">{{ item.url || '—' }}</a></td>
                  <td><span class="content-preview" :title="item.content">{{ truncate(item.content, 80) }}</span></td>
                  <td class="td-source">{{ item.source || '—' }}</td>
                  <td><span class="badge" :class="'badge-diff--' + item.difficulty">{{ labelDiff(item.difficulty) }}</span></td>
                  <td>
                    <div class="tag-list">
                      <span v-for="(tag, i) in ((item.tags || item.knowledge_tags) || []).slice(0, 3)" :key="i" class="mini-tag">{{ tag }}</span>
                      <span v-if="((item.tags || item.knowledge_tags) || []).length > 3" class="mini-tag mini-tag--more">+{{ ((item.tags || item.knowledge_tags) || []).length - 3 }}</span>
                    </div>
                  </td>
                </template>
                <td>
                  <div class="row-actions">
                    <button class="act-btn act-btn--edit" @click.stop="openEdit(item)" title="编辑">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4z"/>
                      </svg>
                    </button>
                    <button class="act-btn act-btn--del" @click.stop="askDelete(item)" title="删除">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
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
            <h2>{{ formMode === 'create' ? (entity === 'question' ? '新建题目' : '新建学习资源') : (entity === 'question' ? '编辑题目' : '编辑学习资源') }}</h2>
            <button class="modal-close" @click="closeForm">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <!-- 岗位 -->
              <div v-if="entity === 'question'" class="form-group form-group--half">
                <label class="form-label">关联岗位 <span class="req">*</span></label>
                <select v-model="form.job_id" class="form-control">
                  <option value="">请选择岗位</option>
                  <option v-for="j in jobs" :key="j.id" :value="j.id">{{ j.name }}</option>
                </select>
              </div>
              <template v-if="entity === 'question'">
                <!-- 类型 -->
                <div class="form-group form-group--quarter">
                  <label class="form-label">题目类型 <span class="req">*</span></label>
                  <select v-model="form.type" class="form-control">
                    <option value="">请选择</option>
                    <option v-for="t in questionTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                </div>
                <!-- 难度 -->
                <div class="form-group form-group--quarter">
                  <label class="form-label">难度</label>
                  <select v-model="form.difficulty" class="form-control">
                    <option value="">请选择</option>
                    <option v-for="d in difficulties" :key="d.value" :value="d.value">{{ d.label }}</option>
                  </select>
                </div>
              </template>
              <template v-if="entity === 'question'">
                <div class="form-group form-group--full">
                  <label class="form-label">题目内容 <span class="req">*</span></label>
                  <textarea v-model="form.content" class="form-control form-textarea" rows="4" placeholder="请输入面试题目…"></textarea>
                </div>
                <div class="form-group form-group--full">
                  <label class="form-label">关键词（逗号分隔）</label>
                  <input v-model="form.keywordsText" type="text" class="form-control" placeholder="例如：Redis, 缓存穿透" />
                </div>
                <div class="form-group form-group--full">
                  <label class="form-label">参考答案</label>
                  <textarea v-model="form.reference_answer" class="form-control form-textarea" rows="4" placeholder="候选人标准回答要点（可选）…"></textarea>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">来源</label>
                  <input v-model="form.source" type="text" class="form-control" placeholder="例如：内部题库" />
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">状态</label>
                  <select v-model="form.status" class="form-control">
                    <option value="draft">草稿</option>
                    <option value="published">已发布</option>
                  </select>
                </div>
              </template>
              <template v-else>
                <div class="form-group form-group--full">
                  <label class="form-label">资源标题 <span class="req">*</span></label>
                  <input v-model="form.title" class="form-control" type="text" placeholder="请输入资源标题" />
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">资源类型 <span class="req">*</span></label>
                  <select v-model="form.type" class="form-control">
                    <option value="">请选择</option>
                    <option v-for="t in resourceTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">学习链接</label>
                  <input v-model="form.url" type="text" class="form-control" placeholder="例如：https://..." />
                </div>
                <div class="form-group form-group--full">
                  <label class="form-label">内容简介 <span class="req">*</span></label>
                  <textarea v-model="form.content" class="form-control form-textarea" rows="4" placeholder="请输入资源简介…"></textarea>
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">来源</label>
                  <input v-model="form.source" type="text" class="form-control" placeholder="例如：官方文档、社区" />
                </div>
                <div class="form-group form-group--half">
                  <label class="form-label">难度</label>
                  <select v-model="form.difficulty" class="form-control">
                    <option value="">请选择</option>
                    <option v-for="d in difficulties" :key="d.value" :value="d.value">{{ d.label }}</option>
                  </select>
                </div>
                <div class="form-group form-group--full">
                  <label class="form-label">知识标签</label>
                  <textarea v-model="form.tagsText" class="form-control form-textarea form-textarea--sm" rows="3" placeholder="每行一个标签，例如：\nJava\nJVM"></textarea>
                  <p class="form-hint">每行输入一个标签</p>
                </div>
              </template>
            </div>

            <p v-if="formError" class="form-error">{{ formError }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="closeForm" :disabled="formLoading">取消</button>
            <button class="btn btn-primary" @click="submitForm" :disabled="formLoading">
              <span v-if="formLoading" class="spinner spinner--sm"></span>
              {{ formMode === 'create' ? (entity === 'question' ? '创建题目' : '创建学习资源') : '保存修改' }}
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
            <p class="confirm-text">确定要删除{{ entity === 'question' ? '这道题目' : '该知识项' }}吗？</p>
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
            <h2>{{ entity === 'resource' ? '批量导入学习资源' : '批量导入题目' }}</h2>
            <button class="modal-close" @click="showImport = false">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="!importResult">
              <p class="import-desc">
                {{ entity === 'question' ? '支持上传本地 YAML 文件或服务器 FuChuangTiKu 目录。' : '支持上传本地 YAML 文件或服务器 resourcesKu 目录。' }}
              </p>
              <div class="form-group">
                <label class="form-label">上传 YAML 文件（优先），若不上传YAML文件则默认上传服务器文件目录下的资源</label>
                <input type="file" accept=".yaml,.yml" @change="onImportFileChange" />
                <p class="option-hint">{{ entity === 'resource' ? '上传后自动写入数据库并发布' : '预览模式上传则为草稿状态，否则直接为发布状态' }}</p>
              </div>
              <div v-if="entity === 'question'" class="import-options">
                <label class="switch-label">
                  <span>预览导入（存为草稿）</span>
                  <input type="checkbox" v-model="importIsDraft" class="sr-only"/>
                  <span class="switch" :class="{ 'switch--on': importIsDraft }"></span>
                </label>
                <p class="option-hint">开启后，题目将作为草稿导入，不会清空现有题目。</p>
              </div>
              <div class="import-options import-options--danger" v-if="!importIsDraft || entity === 'resource'">
                <label class="switch-label">
                  <span class="text-danger">清空已有{{ entity === 'question' ? '题库' : '学习资源' }}</span>
                  <input type="checkbox" v-model="importClearExisting" class="sr-only"/>
                  <span class="switch switch--danger" :class="{ 'switch--on': importClearExisting }"></span>
                </label>
                <p class="option-hint text-danger">⚠️ 危险操作：执行前会删除所有现有记录</p>
              </div>
              <p v-if="importError" class="form-error">{{ importError }}</p>
            </div>

            <!-- 导入结果 -->
            <div v-else class="import-result">
              <div class="import-result__header real">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                导入成功
              </div>
              <div class="import-result__stats">
                <div class="stat-chip">
                  <span class="stat-chip__num">{{ importResult.imported_total }}</span>
                  <span class="stat-chip__label">已导入</span>
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
              {{ entity === 'resource' ? '执行导入' : (importIsDraft ? '预览导入' : '执行导入') }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
        <div class="modal-box modal-box--wide">
          <div class="modal-head">
            <h2>{{ entity === 'question' ? '题目详情' : '学习资源详情' }}</h2>
            <button class="modal-close" @click="showDetailModal = false">✕</button>
          </div>
                    <div class="modal-body">
            <div v-if="detailItem">
              <p><strong>ID：</strong>#{{ detailItem.id }}</p>
              <p><strong>岗位：</strong>{{ jobName(detailItem.job_id) }}</p>
              <p><strong>类型：</strong>{{ labelType(detailItem.type) }}</p>
              <p><strong>难度：</strong>{{ labelDiff(detailItem.difficulty) }}</p>
              <template v-if="entity === 'question'">
                <p><strong>状态：</strong>{{ detailItem.status || 'draft' }}</p>
                <p><strong>来源：</strong>{{ detailItem.source || '—' }}</p>
                <p><strong>内容：</strong></p>
                <div class="detail-box">{{ detailItem.content }}</div>
                <p><strong>关键点：</strong> {{ (detailItem.keywords || []).join(', ') || '—' }}</p>
                <p><strong>参考答案：</strong></p>
                <div class="detail-box">{{ Array.isArray(detailItem.reference_answer) ? detailItem.reference_answer.join('\n') : detailItem.reference_answer || '—' }}</div>
              </template>
              <template v-else>
                <p><strong>学习链接：</strong><a :href="detailItem.url" target="_blank">{{ detailItem.url || '—' }}</a></p>
                <p><strong>来源：</strong>{{ detailItem.source || '—' }}</p>
                <p><strong>内容简介：</strong></p>
                <div class="detail-box">{{ detailItem.content || '—' }}</div>
                <p><strong>知识标签：</strong> {{ (detailItem.tags || detailItem.knowledge_tags || []).join(', ') || '—' }}</p>
              </template>
            </div>
          </div>
<div class="modal-foot">
            <button class="btn btn-primary" @click="showDetailModal = false">关闭</button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import {
  listQuestions, createQuestion, updateQuestion, deleteQuestion, importQuestions, listAdminJobs, bulkUpdateQuestionStatus
} from '@/api/admin'

const QUESTION_TYPES = [
  { value: 'technical', label: '技术题' },
  { value: 'basic', label: '基础知识' },
  { value: 'scenario', label: '场景设计' },
  { value: 'followup', label: '追问题' },
  { value: 'behavioral', label: '行为面试' },
]

const RESOURCE_TYPES = [
  { value: 'article', label: '文章' },
  { value: 'video', label: '视频' },
  { value: 'course', label: '课程' },
  { value: 'example', label: '示例' },
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
    url: '',
    content: '',
    reference_answer: '',
    keywordsText: '',
    source: '',
    status: 'draft',
    title: '',
    tagsText: ''
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
      entity: 'question',
      filterJobId: '',
      filterType: '',
      filterDifficulty: '',
      filterStatus: '',
      filterKeyword: '',

      // options
      jobs: [],
      questionTypes: QUESTION_TYPES,
      resourceTypes: RESOURCE_TYPES,
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
      showDetailModal: false,
      detailItem: null,

      // import
      showImport: false,
      importLoading: false,
      importIsDraft: true,
      importClearExisting: false,
      importFile: null,
      importResult: null,
      importError: '',

      // search debounce
      searchTimer: null
    }
  },

  computed: {
    hasFilters() {
      return this.filterJobId || this.filterType || this.filterDifficulty || this.filterStatus || this.filterKeyword
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
        const params = {
          entity: this.entity,
          page: this.page,
          size: this.size
        }
        if (this.entity === 'question' && this.filterJobId) params.job_id = this.filterJobId
        if (this.filterType) params.type = this.filterType
        if (this.filterDifficulty) params.difficulty = this.filterDifficulty
        if (this.filterStatus) params.status = this.filterStatus
        if (this.filterKeyword) params.q = this.filterKeyword.trim()

        const res = await listQuestions(params)
        this.items = (res.list || []).slice().sort((a, b) => Number(a.id || 0) - Number(b.id || 0))
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

    onSearchDebounce() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        this.page = 1
        this.loadData()
      }, 400)
    },

    clearSearch() {
      this.filterKeyword = ''
      this.page = 1
      this.loadData()
    },

    switchEntity(entity) {
      if (this.entity === entity) return
      this.entity = entity
      this.page = 1
      this.filterType = ''
      this.filterDifficulty = ''
      this.filterKeyword = ''
      this.loadData()
    },

    clearFilters() {
      this.filterJobId = ''
      this.filterType = ''
      this.filterDifficulty = ''
      this.filterStatus = ''
      this.filterKeyword = ''
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
      if (this.entity === 'resource') {
        this.form.type = 'article'
      }
      this.formError = ''
      this.editingId = null
      this.showForm = true
    },

    openEdit(item) {
      this.formMode = 'edit'
      this.editingId = item.id
      if (this.entity === 'question') {
        this.form = {
          job_id: item.job_id || '',
          type: item.type || 'technical',
          difficulty: item.difficulty || '',
          content: item.content || '',
          reference_answer: Array.isArray(item.reference_answer) ? item.reference_answer.join('\n') : (item.reference_answer || ''),
          keywordsText: Array.isArray(item.keywords) ? item.keywords.join(', ') : '',
          source: item.source || '',
          status: item.status || 'draft',
          title: item.title || '',
          url: item.url || '',
          tagsText: Array.isArray(item.tags) ? item.tags.join('\n') : ''
        }
      } else {
        this.form = {
          type: item.type || 'article',
          title: item.title || '',
          url: item.url || '',
          content: item.content || '',
          source: item.source || '',
          difficulty: item.difficulty || '',
          tagsText: Array.isArray(item.tags) ? item.tags.join('\n') : (Array.isArray(item.knowledge_tags) ? item.knowledge_tags.join('\n') : '')
        }
      }
      this.formError = ''
      this.showForm = true
    },

    closeForm() {
      this.showForm = false
    },

    parseLines(text) {
      if (!text || !text.trim()) return null
      const arr = text.split(/\s*,\s*/).map(s => s.trim()).filter(Boolean)
      return arr.length ? arr : null
    },

    async submitForm() {
      this.formError = ''
      if (this.entity === 'question' && !this.form.job_id) { this.formError = '请选择关联岗位'; return }
      if (this.entity === 'question' && !this.form.content.trim()) { this.formError = '题目内容不能为空'; return }
      if (this.entity === 'resource' && !this.form.title.trim()) { this.formError = '资源标题不能为空'; return }
      if (this.entity === 'resource' && !this.form.type) { this.formError = '请选择资源类型'; return }
      if (this.entity === 'resource' && !this.form.content.trim()) { this.formError = '内容简介不能为空'; return }

      let data
      if (this.entity === 'question') {
        data = {
          job_id: this.form.job_id,
          type: this.form.type,
          difficulty: this.form.difficulty || null,
          content: this.form.content.trim(),
          reference_answer: this.form.reference_answer.trim() || null,
          source: this.form.source.trim() || null,
          status: this.form.status || 'draft',
          keywords: this.parseLines(this.form.keywordsText),
          knowledge_points: this.parseLines(this.form.knowledgeText)
        }
        if (!data.job_id) { this.formError = '请选择关联岗位'; this.formLoading = false; return }
        if (!data.content) { this.formError = '题目内容不能为空'; this.formLoading = false; return }
      } else {
        const parsedTags = this.parseLines(this.form.tagsText)
        data = {
          type: this.form.type || 'article',
          title: this.form.title.trim(),
          url: this.form.url.trim() || null,
          content: this.form.content.trim(),
          source: this.form.source.trim() || null,
          difficulty: this.form.difficulty || null,
          tags: parsedTags,
          knowledge_tags: parsedTags
        }
        if (!data.title) { this.formError = '资源标题不能为空'; this.formLoading = false; return }
        if (!data.content) { this.formError = '内容简介不能为空'; this.formLoading = false; return }
      }

      this.formLoading = true
      try {
        if (this.formMode === 'create') {
          await createQuestion(data, this.entity)
        } else {
          await updateQuestion(this.editingId, data, this.entity)
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

    viewDetail(item) {
      this.detailItem = item
      this.showDetailModal = true
    },

    async confirmDelete() {
      this.deleteLoading = true
      try {
        await deleteQuestion(this.deletingId, this.entity)
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
      this.importIsDraft = true
      this.importClearExisting = false
      this.showImport = true
    },

    closeImport() {
      this.showImport = false
      if (this.importResult && !this.importResult.dry_run) {
        this.loadData()
      }
    },

    onImportFileChange(e) {
      const files = e.target.files || []
      this.importFile = files.length ? files[0] : null
    },

    async runImport() {
      this.importError = ''
      const isDraft = this.entity === 'question' ? this.importIsDraft : false
      const clearExisting = !isDraft && this.importClearExisting

      this.importLoading = true
      try {
        let res
        if (this.importFile) {
          const formData = new FormData()
          formData.append('file', this.importFile)
          formData.append('entity', this.entity)
          formData.append('status', isDraft ? 'draft' : 'published')
          formData.append('clear_existing', String(clearExisting))
          res = await importQuestions(formData)
        } else {
          res = await importQuestions({ 
            entity: this.entity, 
            status: isDraft ? 'draft' : 'published', 
            clear_existing: clearExisting 
          })
        }
        this.importResult = res.data || res
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
      const types = this.entity === 'resource' ? RESOURCE_TYPES : QUESTION_TYPES
      const t = types.find(t => t.value === type)
      return t ? t.label : (type || '—')
    },

    labelDiff(diff) {
      const d = DIFFICULTIES.find(d => d.value === diff)
      return d ? d.label : (diff || '—')
    },

    async toggleStatus(item) {
      const newStatus = item.status === 'published' ? 'draft' : 'published'
      try {
        await updateQuestion(item.id, { status: newStatus }, this.entity)
        item.status = newStatus
      } catch (e) {
        alert('修改状态失败: ' + (e.message || '未知错误'))
      }
    },

    async bulkPublish() {
      if (!confirm(`确定要将当前筛选出的所有草稿状态题目发布吗？`)) return
      
      const ids = this.items.filter(i => i.status === 'draft').map(i => i.id)
      if (ids.length === 0) return

      try {
        await bulkUpdateQuestionStatus({ ids, status: 'published' })
        alert('批量发布成功')
        this.loadData()
      } catch (e) {
        alert('批量发布失败: ' + (e.message || '未知错误'))
      }
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

  .qm-search-box {
    position: relative;
    max-width: 100%;
  }
  .qm-search-box__icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #9ca3af;
    width: 16px;
    height: 16px;
    pointer-events: none;
  }
  .qm-search-box__input {
    width: 100%;
    height: 38px;
    padding: 0 36px 0 38px;
    border: 1.5px solid #e5e7eb;
    border-radius: 8px;
    font-size: 13px;
    color: #374151;
    background: white;
    outline: none;
  }
  .qm-search-box__input:focus {
    border-color: #4338ca;
    box-shadow: 0 0 0 3px rgba(67,56,202,0.1);
  }
  .qm-search-box__clear {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    border: none;
    border-radius: 50%;
    background: #e5e7eb;
    color: #6b7280;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    padding: 0;
  }
  .qm-search-box__clear:hover {
    background: #d1d5db;
  }


.qm-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
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

.entity-tabs {
  display: flex;
  gap: 8px;
  margin-top: 5px;
}

.tab-btn {
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #334155;
  border-radius: 8px;
  font-size: 13px;
  padding: 6px 12px;
  cursor: pointer;
}

.tab-btn.active {
  border-color: #4338ca;
  background: #4338ca;
  color: #fff;
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
.btn-icon { width: 14px; height: 14px; flex-shrink: 0; }
.btn-clear {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1.5px solid #fecaca;
  color: #ef4444;
  font-size: 12.5px;
  cursor: pointer;
  padding: 5px 12px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
}
.btn-clear:hover {
  background: #fef2f2;
}
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
.table-card--scrollable {
  overflow-x: hidden;
}
.data-table {
  min-width: 0;
  width: 100%;
  table-layout: fixed;
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
    padding: 10px 12px;
    color: #374151;
    border-bottom: 1px solid #f9fafb;
    vertical-align: middle;
    word-break: break-word;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__row {
    transition: background 0.1s;
    &:hover { background: #fafbff; }
    &:last-child td { border-bottom: none; }
  }
}

.td-id { color: #9ca3af; font-size: 12px; font-weight: 500; }
.td-content { max-width: 320px; }
.td-source { max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
.detail-box { white-space: pre-wrap; background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; margin-bottom: 10px; }

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
/* ── 状态切换按钮 ── */
.status-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.toggle-track {
  width: 36px;
  height: 18px;
  background: #d1d5db;
  border-radius: 9px;
  position: relative;
  transition: background 0.2s;
}
.toggle-track--on {
  background: #10b981;
}
.toggle-thumb {
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}
.toggle-track--on .toggle-thumb {
  transform: translateX(18px);
}
.status-label {
  font-size: 12px;
  color: #4b5563;
  user-select: none;
}

</style>