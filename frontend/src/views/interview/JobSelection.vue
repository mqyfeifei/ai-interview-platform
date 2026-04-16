﻿﻿<!--
  =============================================
  frontend/src/views/interview/JobSelection.vue
  岗位选择页 — 双栏重构版
  左栏：岗位列表（全部/热门筛选）
  右栏：面试配置（简历选择 + 面试模式）
  ============================================= -->
<template>
  <div class="job-selection-page">

    <!-- ===== 顶部 Header（保持原有样式不改动）===== -->
    <div class="page-header">
      <div class="header-inner">
        <button class="back-btn" @click="$router.push('/dashboard')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
            stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="header-text">
          <h1>选择面试岗位</h1>
          <p>选好目标，开始 AI 模拟面试</p>
        </div>
      </div>

      <!-- 简历未完善警告横幅 -->
      <div v-if="resumeChecked && !hasResume" class="resume-warning-bar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" class="resume-warning-bar__icon">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{{ resumeWarning }}</span>
        <button class="resume-warning-bar__btn" @click="$router.push('/resume')">去完善 →</button>
      </div>

      <div class="search-row">
        <div class="search-box">
          <span class="search-box__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round">
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
    </div>
    <!-- /page-header -->

    <!-- ===== 双栏主体 ===== -->
    <div class="dual-layout">

      <!-- ── 左栏：岗位列表 ── -->
      <div class="left-pane">
        <div class="pane-header">
          <span class="pane-title">选择岗位</span>
          <div class="filter-tabs">
            <button
              v-for="tab in filterTabs"
              :key="tab.key"
              :class="['filter-tab', { active: activeFilter === tab.key }]"
              @click="activeFilter = tab.key"
            >{{ tab.label }}</button>
          </div>
        </div>

        <!-- 岗位列表 -->
        <div v-if="filteredJobs.length > 0" class="job-list">
          <div
            v-for="(job, idx) in filteredJobs"
            :key="job.id"
            class="job-row-wrapper"
            :style="{ animationDelay: idx * 0.04 + 's' }"
          >
            <div
              class="job-row"
              :class="{
                selected: currentSelected && currentSelected.id === job.id,
                'job-row--default': normalizedDefaultJobId &&
                  (normalizedDefaultJobId === String(job.id) || normalizedDefaultJobId === String(job.dbId))
              }"
              @click="toggleSelect(job)"
            >
              <!-- 选中勾 -->
              <div v-if="currentSelected && currentSelected.id === job.id" class="job-row__check">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>

              <!-- TOP 徽章 -->
              <div v-if="activeFilter === 'popular' && job.popularRank && job.popularRank <= 3"
                   :class="['job-row__rank', 'top-badge', 'top-badge-' + job.popularRank]">
                TOP{{ job.popularRank }}
              </div>

              <!-- 左侧图标 -->
              <div class="job-row__icon">
                <img
                  v-if="isImageUrl(job.iconUrl || job.icon)"
                  :src="job.iconUrl || job.icon"
                  alt="岗位图标"
                  class="job-row__icon-img"
                  :title="job.iconUrl" 
                />
                <span v-else>{{ job.icon }}</span>
              </div>

              <!-- 中间信息区 -->
              <div class="job-row__body">
                <div class="job-row__title-line">
                  <span class="job-row__name">{{ job.name }}</span>
                  <span v-if="typeof job.avg_score === 'number' && job.avg_score > 0" class="job-row__score">
                    均分 {{ job.avg_score }}
                  </span>
                </div>
                <p v-if="job.description" class="job-row__desc">{{ job.description }}</p>
                <div v-if="Array.isArray(job.techStack) && job.techStack.length" class="job-row__stack">
                  <span v-for="tech in job.techStack.slice(0, 5)" :key="tech" class="stack-tag">{{ tech }}</span>
                </div>
              </div>

              <!-- 右侧操作区 -->
              <div class="job-row__actions" @click.stop>
                <button
                  v-if="normalizedDefaultJobId !== String(job.id) && normalizedDefaultJobId !== String(job.dbId)"
                  class="btn-set-default"
                  @click.stop="setDefault(job)"
                >设为默认</button>
                <span v-else class="default-badge">默认</span>
              </div>
            </div>

            <transition name="fade-slide-down">
              <div v-if="currentSelected && currentSelected.id === job.id" class="job-row__details" @click.stop>
                <div v-if="availableProfiles.length > 0" class="job-row__detail-row">
                  <div class="job-row__detail-block">
                    <div class="job-row__detail-label">轮次</div>
                    <div class="resume-selector" :class="{ open: roundDropdownOpen }">
                      <button class="resume-selector__trigger" @click.stop="toggleRoundDropdown">
                        <span class="resume-selector__value">{{ currentRoundLabel }}</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                          class="resume-selector__arrow">
                          <polyline points="6 9 12 15 18 9"/>
                        </svg>
                      </button>
                      <transition name="dropdown">
                        <div v-if="roundDropdownOpen" class="resume-selector__dropdown">
                          <div
                            v-for="option in roundOptions"
                            :key="option.value"
                            class="resume-dropdown-item"
                            :class="{ active: selectedRound === option.value }"
                            @click.stop="selectRound(option.value)"
                          >
                            <div class="resume-dropdown-item__name">{{ option.label }}</div>
                            <div class="resume-dropdown-item__date">{{ option.summary }}</div>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </div>

                  <div class="job-row__detail-block">
                    <div class="job-row__detail-label">风格</div>
                    <div class="resume-selector" :class="{ open: styleDropdownOpen }">
                      <button class="resume-selector__trigger" @click.stop="toggleStyleDropdown">
                        <span class="resume-selector__value">{{ currentStyleLabel }}</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                          class="resume-selector__arrow">
                          <polyline points="6 9 12 15 18 9"/>
                        </svg>
                      </button>
                      <transition name="dropdown">
                        <div v-if="styleDropdownOpen" class="resume-selector__dropdown">
                          <div
                            v-for="option in styleOptions"
                            :key="option.value"
                            class="resume-dropdown-item"
                            :class="{ active: selectedInterviewStyle === option.value }"
                            @click.stop="selectInterviewStyle(option.value)"
                          >
                            <div class="resume-dropdown-item__name">{{ option.label }}</div>
                            <div class="resume-dropdown-item__date">{{ option.summary }} · {{ option.tone }}</div>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </div>

                  <div class="job-row__detail-block">
                    <div class="job-row__detail-label">来源</div>
                    <div class="resume-selector" :class="{ open: sourceDropdownOpen }">
                      <button class="resume-selector__trigger" @click.stop="toggleSourceDropdown">
                        <span class="resume-selector__value">{{ currentSourceLabel }}</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                          class="resume-selector__arrow">
                          <polyline points="6 9 12 15 18 9"/>
                        </svg>
                      </button>
                      <transition name="dropdown">
                        <div v-if="sourceDropdownOpen" class="resume-selector__dropdown">
                          <div
                            v-for="option in sourceOptions"
                            :key="option.value"
                            class="resume-dropdown-item"
                            :class="{ active: selectedSource === option.value }"
                            @click.stop="selectInterviewSource(option.value)"
                          >
                            <div class="resume-dropdown-item__name">{{ option.label }}</div>
                            <div class="resume-dropdown-item__date">{{ option.summary }}</div>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </div>

                </div>

                <div v-if="availableProfiles.length > 0" class="job-row__preview">
                  <div class="job-row__preview-content">
                    <div class="job-row__preview-title">预览策略</div>
                    <div class="job-row__preview-line">题型分布：Technical {{ currentStrategy.technique }}% / Project {{ currentStrategy.project }}% / Scenario {{ currentStrategy.scenario }}% / Behavioral {{ currentStrategy.behavioral }}%</div>
                    <div class="job-row__preview-line">难度倾向：Easy {{ currentStrategy.easy }}% / Medium {{ currentStrategy.medium }}% / Hard {{ currentStrategy.hard }}%</div>
                    <div class="job-row__preview-line">风格：{{ currentStyleLabel }}{{ selectedStyleTone ? ' · ' + selectedStyleTone : '' }}</div>
                    <div class="job-row__preview-line">来源：{{ currentSourceLabel }}</div>
                    <div class="job-row__preview-line" v-if="selectedProfile">
                      维度：{{ selectedProfile.enabled_dimensions && selectedProfile.enabled_dimensions.length ? selectedProfile.enabled_dimensions.join(', ') : '-' }}
                    
                    </div>
                    <div class="job-row__preview-line" v-if="selectedProfile && selectedProfile.tone_descriptor">
                      风格说明：{{ selectedProfile.tone_descriptor }}
                    </div>
                  </div>
                </div>

              </div>
            </transition>
          </div>
        </div>

        <!-- 搜索空态 -->
        <div v-else class="empty-state-wrap">
          <span style="font-size:48px">🔍</span>
          <p>没有找到匹配的岗位</p>
          <button class="btn-ghost-sm" @click="searchQuery = ''; activeFilter = 'all'">清空筛选</button>
        </div>
      </div>
      <!-- /left-pane -->

      <!-- ── 右栏：面试配置 ── -->
      <div class="right-pane">
        <div class="config-card">

          <!-- 当前选中岗位提示 -->
          <div class="selected-job-hint" :class="{ 'has-job': !!currentSelected }">
            <template v-if="currentSelected">
              <span class="selected-job-hint__icon">
                <img
                  v-if="isImageUrl(currentSelected.iconUrl || currentSelected.icon)"
                  :src="currentSelected.iconUrl || currentSelected.icon"
                  alt="岗位图标"
                  class="selected-job-hint__icon-img"
                />
                <span v-else>{{ currentSelected.icon }}</span>
              </span>
              <span class="selected-job-hint__name">{{ currentSelected.name }}</span>
              <span class="selected-job-hint__badge">已选</span>
            </template>
            <template v-else>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                class="selected-job-hint__empty-icon">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="16"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              <span class="selected-job-hint__placeholder">请先从左侧选择岗位</span>
            </template>
          </div>

          <!-- ─── 简历选择 ─── -->
          <div class="config-section">
            <div class="config-section__label">
              选择面试简历
              <span class="config-section__required">*</span>
            </div>

            <!-- 下拉简历选择器 -->
            <div class="resume-selector" :class="{ open: resumeDropdownOpen }">
              <button
                class="resume-selector__trigger"
                :class="{ 'has-value': !!selectedResume, 'is-invalid': resumeValidationFailed }"
                @click="toggleResumeDropdown"
              >
                <span v-if="selectedResume" class="resume-selector__value">
                  {{ selectedResume.title }}
                  <span v-if="selectedResume.isMain" class="resume-main-badge">主</span>
                </span>
                <span v-else class="resume-selector__placeholder">请选择简历...</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  class="resume-selector__arrow">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              <!-- 下拉列表 -->
              <transition name="dropdown">
                <div v-if="resumeDropdownOpen" class="resume-selector__dropdown">
                  <div v-if="resumeListLoading" class="resume-dropdown-loading">
                    <span class="spinner"></span> 加载中...
                  </div>
                  <div v-else-if="resumeList.length === 0" class="resume-dropdown-empty">
                    暂无简历，
                    <span class="resume-dropdown-link" @click="$router.push('/resume')">去创建 →</span>
                  </div>
                  <div
                    v-for="r in resumeList"
                    :key="r.id"
                    class="resume-dropdown-item"
                    :class="{ active: selectedResume && selectedResume.id === r.id }"
                    @click="selectResume(r)"
                  >
                    <div class="resume-dropdown-item__name">
                      {{ r.title }}
                      <span v-if="r.isMain" class="resume-main-badge">主</span>
                    </div>
                    <div v-if="r.updatedAt" class="resume-dropdown-item__date">
                      {{ formatDate(r.updatedAt) }}
                    </div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- 简历校验未通过提示 -->
            <transition name="fade-in">
              <div v-if="resumeValidationFailed" class="resume-validation-alert">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round"
                  style="width:14px;height:14px;flex-shrink:0;color:#dc2626">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>简历必填信息不完整：{{ missingFieldsText }}</span>
              </div>
            </transition>
           <!-- ─── 简历操作 ─── -->

              <div class="resume-actions">
                <button class="rva-btn rva-btn--view" @click="showResumeDetailModal = true">查看简历</button>
                <button class="rva-btn rva-btn--edit" @click="$router.push('/resume')">前往编辑</button>
              </div>
          </div>
          <!-- /简历选择 -->



          <!-- ─── 面试模式 ─── -->
          <div class="config-section">
            <div class="config-section__label">
              面试模式
            </div>

            <div class="mode-action-row">
              <div class="mode-switch">
                <!-- 文字面试 -->
                <div
                  class="mode-option"
                  :class="{ active: !voiceMode }"
                  @click="voiceMode = false"
                >
                  <div class="mode-option__radio">
                    <div class="mode-option__dot"></div>
                  </div>
                  <div class="mode-option__content">
                    <div class="mode-option__title">
                      文字面试
                    </div>
                  </div>
                </div>

                <!-- 语音面试 -->
                <div
                  class="mode-option"
                  :class="{ active: voiceMode }"
                  @click="voiceMode = true"
                >
                  <div class="mode-option__radio">
                    <div class="mode-option__dot"></div>
                  </div>
                  <div class="mode-option__content">
                    <div class="mode-option__title">
                      语音面试
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="selectedProfile" class="mode-toggle-row">
                <div class="voice-config-item voice-config-toggle">
                  <label class="switch-label">
                    <input type="checkbox" v-model="selectedProfile.is_dynamic_adjust" />
                    <span class="switch-slider"></span>
                    <label class="voice-config-label">动态调整</label>
                  </label>
                </div>
              </div>
            </div>

            <!-- 语音面试：语音配置 -->
            <transition name="voice-expand">
              <div v-if="voiceMode" class="voice-role-section voice-settings-card">
                <div class="voice-role-section__title">
                  面试语音配置
                </div>

                <div v-if="selectedProfile" class="voice-config-row">
                  <div class="voice-config-item voice-config-field">
                    <label class="voice-config-label">面试官声音</label>
                    <select v-model="selectedVoiceRole" class="voice-config-select">
                      <option
                        v-for="role in voiceRoles"
                        :key="role.id"
                        :value="role.id"
                      >
                        {{ role.label || role.name || role.id }}
                      </option>
                    </select>
                  </div>
                  <div class="voice-config-item voice-config-field voice-config-field--speed">
                    <label class="voice-config-label">语速</label>
                    <select v-model.number="selectedProfile.speech_speed" class="voice-config-select voice-config-select--speed">
                      <option v-for="speed in speechSpeedOptions" :key="speed" :value="speed">{{ speed }}x</option>
                    </select>
                  </div>
                </div>
              </div>
            </transition>
          </div>
          <!-- /面试模式 -->

          <!-- ─── 开始面试按钮 ─── -->
          <div class="start-action">
            <div v-if="!canStart" class="start-tips">
              <template v-if="!currentSelected">请先选择面试岗位</template>
              <template v-else-if="!selectedResume">请选择面试简历</template>
              <template v-else-if="resumeValidationFailed">请完善简历必填信息后再开始</template>
            </div>
            <button
              class="start-btn"
              :class="{ disabled: !canStart }"
              :disabled="!canStart"
              @click="canStart && (showStartConfirm = true)"
            >
              <template v-if="canStart">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                开始面试
                <span class="start-btn__job">{{ currentSelected && currentSelected.name }}</span>
              </template>
              <template v-else>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;opacity:.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                开始面试
              </template>
            </button>
          </div>

        </div>
        <!-- /config-card -->
      </div>
      <!-- /right-pane -->

    </div>
    <!-- /dual-layout -->

    <!-- ===== 开始面试确认弹窗 ===== -->
    <transition name="modal">
      <div v-if="showStartConfirm" class="modal-overlay" @click.self="showStartConfirm = false">
        <div class="modal-sheet">
          <div class="modal-header-bar">
            <h2 class="modal-header-title">准备好了吗？</h2>
            <p class="modal-header-sub">{{ currentSelected && currentSelected.name }} · {{ voiceMode ? '语音面试' : '文字面试' }}</p>
          </div>
          <div class="modal-body">
            <div class="interview-mode-tag" :class="voiceMode ? 'mode-voice' : 'mode-text'">
              <svg v-if="voiceMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              {{ voiceMode ? '语音模式 · 每题 3 分钟' : '文字模式 · 每题 5 分钟' }}
            </div>

            <ul class="rules-list">
              <li>
                <span class="rule-dot rule-dot--blue"/>
                AI 将逐题提问，请认真作答，回答后 AI 可能追问
              </li>
              <li>
                <span class="rule-dot rule-dot--purple"/>
                每题均有时间限制，超时将自动跳题
              </li>
              <li v-if="voiceMode">
                <span class="rule-dot rule-dot--green"/>
                语音模式下 AI 回答完毕后将自动开始录音
              </li>
              <li v-else>
                <span class="rule-dot rule-dot--green"/>
                使用 Enter 发送回答，Shift+Enter 换行
              </li>
              <li>
                <span class="rule-dot rule-dot--orange"/>
                面试结束后将生成专属评估报告，可在历史记录中查看
              </li>
            </ul>

            <div class="modal-actions">
              <button class="btn-cancel" @click="showStartConfirm = false">再想想</button>
              <button class="btn-confirm" @click="confirmStart">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                开始面试
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- ===== 简历详情查看弹窗 ===== -->
    <transition name="modal">
      <div v-if="showResumeDetailModal" class="modal-overlay" @click.self="showResumeDetailModal = false">
        <div class="modal-sheet" style="width: 90%; max-width: 900px; max-height: 85vh; display: flex; flex-direction: column;">
          <div class="modal-header-bar" style="background: #fff; border-bottom: 1px solid #e5e7eb; flex-shrink: 0;">
            <h2 class="modal-header-title" style="color: #1f2937;">简历预览</h2>
            <p class="modal-header-sub" style="color: #6b7280;">{{ selectedResume && selectedResume.title }}</p>
          </div>
          <div class="modal-body" style="flex: 1; overflow-y: auto; padding: 0;">
            <ResumePreview :content="resumeContent" />
          </div>
          <div class="modal-footer-bar" style="background: #f9fafb; border-top: 1px solid #e5e7eb; padding: 16px; flex-shrink: 0; display: flex; gap: 12px; justify-content: flex-end; align-items: center;">
            <p v-if="missingFields.length > 0" style="font-size:12px; color:#dc2626; margin: 0; flex: 1; text-align: left; line-height: 1.4;">
              <strong>⚠ 必填信息不完整：</strong>{{ missingFieldsText }}
            </p>
            <button class="btn-cancel" @click="showResumeDetailModal = false">关闭</button>
            <button class="btn-confirm" style="background: #6366f1; box-shadow: 0 4px 16px rgba(99,102,241,.2)"
              @click="showResumeDetailModal = false; $router.push('/resume')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              编辑简历
            </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import ResumePreview from '@/components/interview/ResumePreview.vue'
import { VOICE_ID_OPTIONS } from '@/constants/ttsVoices'

// ===================== 简历必填字段定义 =====================
const REQUIRED_FIELDS = [
  { key: 'name',    label: '姓名',   path: r => r?.personal?.name },
  { key: 'gender',  label: '性别',   path: r => r?.personal?.gender },
  { key: 'phone',   label: '手机号码', path: r => r?.personal?.phone },
  { key: 'email',   label: '电子邮箱', path: r => r?.personal?.email },
  // 教育 - 前端需要校验学校、专业、学历
  { key: 'school',  label: '就读院校', path: r => {
    const edu = r?.education
    if (Array.isArray(edu) && edu.length > 0) return edu[0].school
    return r?.personal?.school
  }},
  { key: 'major',  label: '专业', path: r => {
    const edu = r?.education
    if (Array.isArray(edu) && edu.length > 0) return edu[0].major
    return null
  }},
  { key: 'degree', label: '学历', path: r => {
    const edu = r?.education
    if (Array.isArray(edu) && edu.length > 0) return edu[0].degree
    return null
  }}
]

// ===================== 语音角色配置 =====================
// 统一使用管理员端可选的 TTS 音色列表

const INTERVIEW_ROUNDS = [
  { value: 1, label: '一面', summary: '基础能力 + 表达清晰度' },
  { value: 2, label: '二面', summary: '项目深度 + 系统设计' },
  { value: 3, label: '三面', summary: '复杂问题拆解 + 高压判断' }
]

const INTERVIEW_STYLES = [
  { value: 'pressure', label: '压力面', summary: '更具挑战的追问风格', tone: '强势/严厉，追问深挖' },
  { value: 'confident', label: '自信面', summary: '鼓励型交流与清晰反馈', tone: '自然/自信，强调表达' },
  { value: 'teaching', label: '教学面', summary: '引导式提问与知识串联', tone: '温和/耐心，注重解释' }
]

const DEFAULT_SOURCE_OPTIONS = [
  { value: '通用', label: '通用', summary: '通用题库，不限定公司' }
]

export default {
  name: 'JobSelection',

  components: {
    ResumePreview
  },

  data() {
    return {
      // ── 岗位列表 ──
      searchQuery: '',
      activeFilter: 'all',
      currentSelected: null,
      filterTabs: [
        { key: 'all',     label: '全部岗位' },
        { key: 'popular', label: '热门岗位' }
      ],
      jobs: [],
      popularIds: [],

      // ── 旧的简历检测（保留，用于顶部警告横幅） ──
      hasResume: true,
      resumeWarning: null,
      resumeChecked: false,

      // ── 简历选择（新增） ──
      resumeList: [],
      resumeListLoading: false,
      selectedResume: null,
      resumeDropdownOpen: false,
      resumeValidationFailed: false,
      missingFields: [],          // [{ key, label }]
      showResumeDetailModal: false,
      resumeContent: {},          // 完整的简历内容用于预览

      // ── 面试模式 ──
      voiceMode: false,

      // ── 套餐选择（新增） ──
      availableProfiles: [],
      selectedProfile: null,
      profileLoading: false,

      // ── 轮次与风格选择 ──
      selectedRound: 1,
      selectedInterviewStyle: 'confident',
      selectedSource: '通用',
      styleManuallySelected: false,
      roundOptions: INTERVIEW_ROUNDS,
      styleOptions: INTERVIEW_STYLES,
      sourceOptions: DEFAULT_SOURCE_OPTIONS,
      roundDropdownOpen: false,
      styleDropdownOpen: false,
      sourceDropdownOpen: false,

      // ── 语音角色（与管理员端保持一致） ──
      voiceRoles: VOICE_ID_OPTIONS,
      selectedVoiceRole: VOICE_ID_OPTIONS[0]?.id || '',
      speechSpeedOptions: [0.5, 0.7, 1.0, 1.5, 2.0],
      // TODO: 后端接口就绪后在 fetchVoiceRoles() 中替换 voiceRoles 数据
      // voiceRolesLoading: false,

      // ── 弹窗 ──
      showStartConfirm: false,
    }
  },

  computed: {
    filteredJobs() {
      let jobs = this.jobs
      if (this.activeFilter === 'popular') {
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

    normalizedDefaultJobId() {
      let id = this.$store.getters['user/defaultJobId']
      if (id == null) id = this.$store.getters['user/defaultJob']
      return id != null ? String(id) : null
    },

    missingFieldsText() {
      return this.missingFields.map(f => f.label).join('、')
    },

    currentRoundLabel() {
      const item = this.roundOptions.find(opt => opt.value === this.selectedRound)
      return item ? item.label : '一面'
    },

    currentStyleLabel() {
      const item = this.styleOptions.find(opt => opt.value === this.selectedInterviewStyle)
      return item ? item.label : '自信面'
    },

    selectedStyleSummary() {
      const item = this.styleOptions.find(opt => opt.value === this.selectedInterviewStyle)
      return item ? item.summary : ''
    },

    selectedStyleTone() {
      const item = this.styleOptions.find(opt => opt.value === this.selectedInterviewStyle)
      return item ? item.tone : ''
    },

    currentSourceLabel() {
      const item = this.sourceOptions.find(opt => opt.value === this.selectedSource)
      return item ? item.label : '通用'
    },

    formattedPersonality() {
      if (!this.selectedProfile || !this.selectedProfile.custom_personality_json) return ''
      try {
        return typeof this.selectedProfile.custom_personality_json === 'string'
          ? JSON.stringify(JSON.parse(this.selectedProfile.custom_personality_json), null, 2)
          : JSON.stringify(this.selectedProfile.custom_personality_json, null, 2)
      } catch (e) {
        return String(this.selectedProfile.custom_personality_json)
      }
    },

    currentStrategy() {
      const defaults = {
        confident: { technique: 60, project: 10, scenario: 10, behavioral: 20, easy: 35, medium: 55, hard: 10 },
        teaching: { technique: 50, project: 15, scenario: 15, behavioral: 20, easy: 30, medium: 50, hard: 20 },
        pressure: { technique: 70, project: 10, scenario: 10, behavioral: 10, easy: 20, medium: 50, hard: 30 }
      }
      const base = defaults[this.selectedInterviewStyle] || defaults.confident
      if (!this.selectedProfile) {
        return base
      }
      return {
        technique: this.selectedProfile.technique_percentage != null ? this.selectedProfile.technique_percentage : base.technique,
        project: this.selectedProfile.project_deep_dive_percentage != null ? this.selectedProfile.project_deep_dive_percentage : base.project,
        scenario: this.selectedProfile.scenario_percentage != null ? this.selectedProfile.scenario_percentage : base.scenario,
        behavioral: this.selectedProfile.behavioral_percentage != null ? this.selectedProfile.behavioral_percentage : base.behavioral,
        easy: this.selectedProfile.difficulty_low_percentage != null ? this.selectedProfile.difficulty_low_percentage : base.easy,
        medium: this.selectedProfile.difficulty_medium_percentage != null ? this.selectedProfile.difficulty_medium_percentage : base.medium,
        hard: this.selectedProfile.difficulty_high_percentage != null ? this.selectedProfile.difficulty_high_percentage : base.hard
      }
    },

    // 仅当岗位、简历均已选且简历必填字段完整时，按钮解禁
    canStart() {
      return !!(this.currentSelected && this.selectedResume && !this.resumeValidationFailed)
    }
  },

  watch: {
    activeFilter(newVal) {
      if (newVal === 'popular') this.refreshPopular()
    }
  },

  async created() {
    if (!this.$store.getters['user/userInfo']) {
      await this.$store.dispatch('user/fetchUserInfo')
    }

    // 加载岗位列表
    await this.loadJobs()
    this.applyDefaultJob()
    if (this.currentSelected) {
      await this.loadProfileOptions(this.currentSelected.id)
    }

    // 检测旧的简历状态（顶部横幅警告）
    try {
      const { checkResume } = await import('@/api/interview')
      const res = await checkResume()
      this.hasResume = res.has_resume
      this.resumeWarning = res.warning
    } catch (e) {
      console.warn('简历检测失败', e)
      this.hasResume = true
    } finally {
      this.resumeChecked = true
    }

    // 加载用户简历列表（新增）
    await this.loadResumeList()

    const storeVoice = this.$store.getters['interview/ttsVoice']
    if (storeVoice && this.voiceRoles.some(role => role.id === storeVoice)) {
      this.selectedVoiceRole = storeVoice
    }

    // 监听
    this.$watch(() => this.normalizedDefaultJobId, () => this.applyDefaultJob())
    this.$watch(() => this.jobs, () => this.applyDefaultJob())
  },

  mounted() {
    // 点击外部关闭下拉
    document.addEventListener('click', this.handleOutsideClick)
  },

  beforeDestroy() {
    document.removeEventListener('click', this.handleOutsideClick)
  },

  methods: {
    async primeAudioPlayback() {
      if (!this.voiceMode || typeof window === 'undefined') return
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext
        if (!AudioCtx) return

        if (!window.__aiInterviewAudioContext) {
          window.__aiInterviewAudioContext = new AudioCtx()
        }

        const ctx = window.__aiInterviewAudioContext
        if (ctx.state === 'suspended') {
          await ctx.resume()
        }

        if (window.__dummyOsc) {
          try { window.__dummyOsc.stop() } catch (e) {}
        }
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        gain.gain.value = 0.00001
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.start()
        // Keep it running to prevent iOS Safari/Chrome from relocking the context during long TTS fetch
        window.__dummyOsc = osc
      } catch (err) {
        console.warn('语音播放预解锁失败', err)
      }
    },

    // ─── 岗位加载 ───
    async loadJobs() {
      try {
        const { fetchJobs, fetchJobAvgScores, fetchPopularJobs } = await import('@/api/job')
        let [jobs, avgList, popular] = await Promise.allSettled([
          fetchJobs(), fetchJobAvgScores(), fetchPopularJobs()
        ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : []))

        const avgMap = {}
        ;(avgList || []).forEach(a => { if (a.id != null) avgMap[a.id] = a.avg_score })
        this.popularIds = (popular || []).map(p => p.id)

        jobs = (jobs || []).map(j => ({
          ...j,
          techStack: j.tech_stack || [],
          iconUrl: j.icon_url || null,
          icon: j.icon || '💼',
          level: j.level || '',
          avg_score: avgMap[j.id] != null ? avgMap[j.id] : (j.avg_score || 0),
          questionTypes: j.question_types || [],
          color: j.color || '#888',
          colorBg: j.color_bg || '#f3f3f3'
        }))
        jobs.forEach(j => {
          const idx = this.popularIds.indexOf(j.id)
          j.popularRank = idx >= 0 ? idx + 1 : null
        })
        this.jobs = jobs
      } catch (e) {
        this.jobs = []
        console.warn('加载岗位列表失败', e)
      }
    },

    applyDefaultJob() {
      const storeJob = this.$store.getters['interview/selectedJob']
      if (storeJob) { this.currentSelected = storeJob; return }
      const defaultJobId = this.normalizedDefaultJobId
      if (defaultJobId && this.jobs.length) {
        const found = this.jobs.find(j => String(j.id) === defaultJobId || String(j.dbId) === defaultJobId)
        if (found) { this.currentSelected = found }
      }
    },

    isImageUrl(value) {
      return typeof value === 'string' && value.trim() !== '' && /^(\/|https?:\/\/)/.test(value)
    },

    async toggleSelect(job) {
      this.currentSelected = this.currentSelected?.id === job.id ? null : job
      this.showProfileDetail = false
      if (this.currentSelected) {
        await this.loadProfileOptions(this.currentSelected.id)
        // 选择岗位后重新验证简历是否符合要求
        if (this.selectedResume) {
          // 获取完整简历内容用于校验
          let content = this.selectedResume.content
          if (!content) {
            try {
              const { getResume } = await import('@/api/resume')
              const full = await getResume(this.selectedResume.id)
              content = full.content || {}
            } catch (e) {
              console.warn('获取简历详情失败', e)
              content = {}
            }
          }
          this.resumeContent = content
          this.validateResume(content)
        }
      } else {
        this.availableProfiles = []
        this.selectedProfile = null
        this.sourceOptions = DEFAULT_SOURCE_OPTIONS
        this.selectedSource = '通用'
        this.$store.dispatch('interview/selectInterviewProfile', null)
        // 取消选择岗位后重新验证简历
        if (this.selectedResume) {
          this.validateResume(this.resumeContent)
        }
      }
    },

    async setDefault(job) {
      try {
        await this.$store.dispatch('user/updateDefaultJob', job.id)
        this.currentSelected = job
      } catch (err) {
        console.error('设置默认岗位失败', err)
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

    // ─── 简历加载 ───
    async loadResumeList() {
      this.resumeListLoading = true
      try {
        const { listResumes } = await import('@/api/resume')
        const list = await listResumes()
        this.resumeList = list || []
        // 默认选中主简历
        const main = this.resumeList.find(r => r.isMain)
        if (main) this.selectResume(main)
      } catch (e) {
        console.warn('加载简历列表失败', e)
        this.resumeList = []
      } finally {
        this.resumeListLoading = false
      }
    },

    async loadProfileOptions(jobId) {
      this.profileLoading = true
      this.availableProfiles = []
      this.selectedProfile = null
      this.showProfileDetail = false
      try {
        const { fetchInterviewProfiles, fetchInterviewSourceOptions } = await import('@/api/interview')
        const [profiles, sources] = await Promise.all([
          fetchInterviewProfiles(jobId),
          fetchInterviewSourceOptions(jobId)
        ])
        this.availableProfiles = profiles || []
        this.sourceOptions = this.normalizeSourceOptions(sources)
        const sourceExists = this.sourceOptions.some(opt => opt.value === this.selectedSource)
        if (!sourceExists) {
          this.selectedSource = '通用'
        }
        if (this.availableProfiles.length > 0) {
          const match = this.availableProfiles.find(
            p =>
              Number(p.round) === Number(this.selectedRound) &&
              (p.interviewer_style || 'confident') === this.selectedInterviewStyle &&
              this.getProfileSource(p) === this.selectedSource
          )
          this.selectedProfile = match || null
          if (this.selectedProfile) {
            this.selectedRound = this.selectedProfile.round || this.selectedRound
            if (!this.styleManuallySelected) {
              this.selectedInterviewStyle = this.selectedProfile.interviewer_style || this.selectedInterviewStyle
            }
            if (this.selectedProfile.voice_id) {
              this.selectedVoiceRole = this.selectedProfile.voice_id
            }
            this.$store.dispatch('interview/selectInterviewProfile', this.selectedProfile.id)
          } else {
            this.$store.dispatch('interview/selectInterviewProfile', null)
          }
        } else {
          this.selectedProfile = null
          this.$store.dispatch('interview/selectInterviewProfile', null)
        }
      } catch (e) {
        console.warn('加载面试套餐失败', e)
        this.availableProfiles = []
        this.sourceOptions = DEFAULT_SOURCE_OPTIONS
        this.selectedSource = '通用'
      } finally {
        this.profileLoading = false
      }
    },

    normalizeSourceOptions(sources) {
      const values = Array.isArray(sources) ? sources : []
      const deduped = ['通用', ...values.filter(v => v && v !== '通用')]
      return deduped.map(item => ({
        value: item,
        label: item,
        summary: item === '通用' ? '通用题库，不限定公司' : '企业真题来源'
      }))
    },

    getProfileSource(profile) {
      if (!profile) return '通用'
      return profile.target_source || '通用'
    },

    selectInterviewProfile(profile) {
      this.selectedProfile = profile
      if (profile) {
        this.selectedRound = profile.round || this.selectedRound
        if (!this.styleManuallySelected) {
          this.selectedInterviewStyle = profile.interviewer_style || this.selectedInterviewStyle
        }
        if (profile.voice_id) {
          this.selectedVoiceRole = profile.voice_id
        }
      }
      this.$store.dispatch('interview/selectInterviewProfile', profile ? profile.id : null)
    },

    selectRound(roundValue) {
      this.selectedRound = roundValue
      this.roundDropdownOpen = false
      this.syncProfileSelection()
    },

    selectInterviewStyle(styleValue) {
      this.selectedInterviewStyle = styleValue
      this.styleManuallySelected = true
      this.styleDropdownOpen = false
      this.$store.commit('interview/SET_INTERVIEW_STYLE', styleValue)
      this.syncProfileSelection()
    },

    selectInterviewSource(sourceValue) {
      this.selectedSource = sourceValue || '通用'
      this.sourceDropdownOpen = false
      this.$store.commit('interview/SET_INTERVIEW_SOURCE', this.selectedSource)
      this.syncProfileSelection()
    },

    syncProfileSelection() {
      if (!this.availableProfiles.length) return
      const match = this.availableProfiles.find(
        p =>
          Number(p.round) === Number(this.selectedRound) &&
          (p.interviewer_style || 'confident') === this.selectedInterviewStyle &&
          this.getProfileSource(p) === this.selectedSource
      )
      if (match) {
        this.selectInterviewProfile(match)
      } else {
        this.selectedProfile = null
        this.$store.dispatch('interview/selectInterviewProfile', null)
      }
    },

    toggleRoundDropdown() {
      this.roundDropdownOpen = !this.roundDropdownOpen
      if (this.roundDropdownOpen) {
        this.styleDropdownOpen = false
        this.sourceDropdownOpen = false
      }
    },

    toggleStyleDropdown() {
      this.styleDropdownOpen = !this.styleDropdownOpen
      if (this.styleDropdownOpen) {
        this.roundDropdownOpen = false
        this.sourceDropdownOpen = false
      }
    },

    toggleSourceDropdown() {
      this.sourceDropdownOpen = !this.sourceDropdownOpen
      if (this.sourceDropdownOpen) {
        this.roundDropdownOpen = false
        this.styleDropdownOpen = false
      }
    },

    toggleResumeDropdown() {
      this.resumeDropdownOpen = !this.resumeDropdownOpen
    },

    handleOutsideClick(e) {
      const selectors = this.$el && this.$el.querySelectorAll('.resume-selector')
      if (!selectors || selectors.length === 0) return
      const clickedInside = Array.from(selectors).some(selector => selector.contains(e.target))
      if (!clickedInside) {
        this.resumeDropdownOpen = false
        this.roundDropdownOpen = false
        this.styleDropdownOpen = false
        this.sourceDropdownOpen = false
      }
    },

    async selectResume(resume) {
      this.selectedResume = resume
      this.resumeDropdownOpen = false

      // 获取完整简历内容用于校验（若列表接口已含 content 则直接用）
      let content = resume.content
      if (!content) {
        try {
          const { getResume } = await import('@/api/resume')
          const full = await getResume(resume.id)
          content = full.content || {}
        } catch (e) {
          console.warn('获取简历详情失败', e)
          content = {}
        }
      }

      this.resumeContent = content
      this.validateResume(content)
    },

    validateResume(content) {
      const missing = []

      // 基本必填项（保留原有）
      REQUIRED_FIELDS.forEach(f => {
        const val = f.path(content)
        if (!val || (typeof val === 'string' && val.trim() === '')) {
          missing.push({ key: f.key, label: f.label, section: null })
        }
      })

      // 目标岗位：前端强校验（必填且需与所选岗位对应）
      const resumeJobId = this.selectedResume && this.selectedResume.jobId
      if (!resumeJobId) {
        missing.push({ key: 'target_job_missing', label: '目标岗位：未设置（必填）' })
      } else if (this.currentSelected && String(resumeJobId) !== String(this.currentSelected.id)) {
        missing.push({ key: 'target_job_mismatch', label: '目标岗位与所选岗位不符' })
      }

      // 核心技术栈：至少 5 项
      const skills = Array.isArray(content.skills) ? content.skills.filter(s => s && s.name && s.name.trim()) : []
      if (skills.length < 5) {
        missing.push({ key: 'core_stack', label: '核心技术栈不足 5 项（需 ≥5）' })
      }

      // 项目经验：视为 校园经历 或 实习经历 中任意一条，且该条目必须包含 start,end,title,description,achievements
      const campus = Array.isArray(content.campusExperiences) ? content.campusExperiences : []
      const interns = Array.isArray(content.internshipExperiences) ? content.internshipExperiences : []
      const qualifying = (arr) => arr.some(item => item && (item.start || item.end) && item.title && item.title.toString().trim() && item.description && item.description.toString().trim() && item.achievements && item.achievements.toString().trim())
      if (!(qualifying(campus) || qualifying(interns))) {
        missing.push({ key: 'project_req', label: '至少 1 条校园/实习经历，且需填写起止时间、经历名称、详细描述与业绩' })
      }

      // 教育：学校、专业、学历阶段必填（以第一条教育记录为准）
      const edu = Array.isArray(content.education) && content.education.length ? content.education[0] : null
      if (!edu || !edu.school || !edu.school.trim()) missing.push({ key: 'edu_school', label: '教育：学校 未填写' })
      if (!edu || !edu.major || !edu.major.trim()) missing.push({ key: 'edu_major', label: '教育：专业 未填写' })
      if (!edu || !edu.degree || !edu.degree.trim()) missing.push({ key: 'edu_degree', label: '教育：学历 未填写' })

      this.missingFields = missing
      this.resumeValidationFailed = missing.length > 0
    },

    goToResumeField(item) {
      // Navigate to resume builder and focus the requested section/field via query params
      const resumeId = this.selectedResume && this.selectedResume.id
      const query = {}
      if (item && item.section) query.focusSection = item.section
      if (item && item.field) query.focusField = item.field
      if (resumeId) query.resumeId = resumeId
      this.resumeDropdownOpen = false
      // Open resume builder page with focus instructions
      this.$router.push({ path: '/resume', query })
    },

    // ─── 语音角色选择（预留，后续替换为接口数据）───
    selectVoiceRole(roleId) {
      this.selectedVoiceRole = roleId
      this.$store.commit('interview/SET_TTS_VOICE', roleId)
    },

    openCustomInterviewConfig(job) {
      console.log('打开自定义面试配置：', job)
      // TODO: 跳转到自定义面试配置页或展开配置弹窗
    },

    // TODO: 后端接口就绪后取消注释并调用
    // async fetchVoiceRoles() {
    //   try {
    //     // const res = await request.get('/interviews/voice-roles')
    //     // this.voiceRoles = res || VOICE_ROLES_PLACEHOLDER
    //   } catch (e) {
    //     this.voiceRoles = VOICE_ROLES_PLACEHOLDER
    //   }
    // },

    // ─── 面试启动 ───
    resolveInterviewStyle() {
      if (this.selectedInterviewStyle) {
        return this.selectedInterviewStyle
      }
      if (!this.voiceMode) {
        return 'technical'
      }
      if (this.selectedVoiceRole === 'role_strict') {
        return 'pressure'
      }
      return 'confident'
    },

    async handleStart() {
      if (!this.currentSelected) return
      try {
        await this.primeAudioPlayback()
        const jobDbId = this.currentSelected.id
        const interviewStyle = this.selectedInterviewStyle || this.resolveInterviewStyle()
        await this.$store.dispatch('interview/resetInterview')
        this.$store.commit('interview/SET_JOB_DB_ID', jobDbId)
        this.$store.commit('interview/SET_VOICE_MODE', this.voiceMode)
        this.$store.commit('interview/SET_INTERVIEW_STYLE', interviewStyle)
        this.$store.commit('interview/SET_INTERVIEW_SOURCE', this.selectedSource || '通用')
        this.$store.commit('interview/SET_VOICE_ROLE', this.voiceMode ? this.selectedVoiceRole : 'role_calm')
        if (this.voiceMode) {
          this.$store.commit('interview/SET_TTS_VOICE', this.selectedVoiceRole)
        }

        // 存储选中的面试套餐和会话配置
        if (this.selectedProfile) {
          this.$store.commit('interview/SET_SELECTED_PROFILE_ID', this.selectedProfile.id)
          this.$store.commit('interview/SET_SELECTED_PROFILE_CONFIG', {
            profile_id: this.selectedProfile.id,
            interview_round: this.selectedRound,
            interviewer_style: this.selectedProfile.interviewer_style,
            tech_ratio: this.selectedProfile.technique_percentage,
            scenario_ratio: this.selectedProfile.scenario_percentage,
            project_deep_dive_percentage: this.selectedProfile.project_deep_dive_percentage,
            behavioral_percentage: this.selectedProfile.behavioral_percentage,
            difficulty_low_percentage: this.selectedProfile.difficulty_low_percentage,
            difficulty_medium_percentage: this.selectedProfile.difficulty_medium_percentage,
            difficulty_high_percentage: this.selectedProfile.difficulty_high_percentage,
            is_dynamic_adjust: this.selectedProfile.is_dynamic_adjust,
            voice_id: this.selectedProfile.voice_id,
            speech_speed: this.selectedProfile.speech_speed,
            tone_descriptor: this.selectedProfile.tone_descriptor,
            enabled_dimensions: this.selectedProfile.enabled_dimensions,
            difficulty_level: this.selectedProfile.difficulty_level,
            target_source: this.selectedSource || '通用'
          })
        } else {
          this.$store.commit('interview/SET_SELECTED_PROFILE_ID', null)
          this.$store.commit('interview/SET_SELECTED_PROFILE_CONFIG', {
            interview_round: this.selectedRound,
            interview_style: interviewStyle,
            target_source: this.selectedSource || '通用'
          })
        }

        // 存储选中的简历ID
        this.$store.commit('interview/SET_RESUME_ID', this.selectedResume?.id)
        await this.$store.dispatch('interview/selectJob', this.currentSelected)
        // 根据面试模式跳转到不同页面
        if (this.voiceMode) {
          this.$router.push('/interview/voice-session')
        } else {
          this.$router.push('/interview/session')
        }
      } catch (err) {
        console.error('启动面试失败：', err)
        // 提取后端错误信息
        const errorMessage = err?.response?.data?.message || err?.message || '启动面试失败，请重试！'
        alert('启动面试失败：' + errorMessage)
      }
    },

    async confirmStart() {
      this.showStartConfirm = false
      await this.handleStart()
    },

    // ─── 工具 ───
    formatDate(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      return `${d.getMonth() + 1}/${d.getDate()} 更新`
    }
  }
}
</script>

<style lang="scss" scoped>

// ──────────────────────────────────────────────
//  页面基础
// ──────────────────────────────────────────────
.job-selection-page {
  min-height: 100vh;
  background: $bg-page;
}

// ──────────────────────────────────────────────
//  Header（与原版保持完全一致）
// ──────────────────────────────────────────────
.page-header {
  background: #ffffff;
  padding: 20px $spacing-base 0;
  position: sticky;
  top: 0;
  z-index: 30;
  border-bottom: 1px solid #eef0f6;
  box-shadow: 0 2px 12px rgba(67, 56, 202, 0.06);
}

.header-inner,
.search-row {
  max-width: 1500px;
  margin-left: auto;
  margin-right: auto;
}

.header-inner {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: 14px;
}

.back-btn {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: #f3f4f6;
  border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0;
  transition: background $transition-fast;
  color: #374151;
  svg { width: 18px; height: 18px; }
  &:hover { background: #e5e7eb; }
}

.header-text {
  padding-inline: 3%;
  h1 {
    font-family: $font-family-display;
    font-size: $font-size-2xl;
    font-weight: $font-weight-extrabold;
    color: #111827;
    margin-bottom: 2px;
    line-height: 1.2;
  }
  p { font-size: $font-size-base; color: #9ca3af; }
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-inline: 5%;
  padding-bottom: 14px;
}

.search-box {
  position: relative;
  flex: 1;

  &__icon {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    color: #9ca3af; display: flex; align-items: center; pointer-events: none;
    transition: color 0.2s;
    svg { width: 16px; height: 16px; }
  }

  &__input {
    width: 100%; height: 46px;
    padding: 0 40px 0 44px;
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 12px;
    font-size: $font-size-base; color: $text-primary;
    outline: none; font-family: $font-family-base;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
    box-sizing: border-box;

    &::placeholder { color: #c4c9d4; }

    &:focus {
      border-color: $primary;
      background: #fff;
      box-shadow: 0 0 0 3px rgba(67, 56, 202, 0.1);
    }
  }

  &:focus-within &__icon { color: $primary; }

  &__clear {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    background: #e5e7eb; border: none;
    width: 20px; height: 20px; border-radius: 50%;
    cursor: pointer; font-size: 10px; color: #6b7280;
    display: flex; align-items: center; justify-content: center;
    transition: background $transition-fast;
    &:hover { background: #d1d5db; color: #374151; }
  }
}

/* 简历未完善警告横幅 */
.resume-warning-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  background: #fffbeb;
  border-top: 1px solid #fde68a;
  font-size: 12px;
  color: #92400e;
  max-width: 1500px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}
.resume-warning-bar__icon { width: 15px; height: 15px; flex-shrink: 0; color: #f59e0b; }
.resume-warning-bar span { flex: 1; line-height: 1.4; }
.resume-warning-bar__btn {
  flex-shrink: 0;
  padding: 4px 10px; border-radius: 8px;
  border: 1px solid #f59e0b; background: white; color: #b45309;
  font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap;
  transition: all 0.15s;
  &:hover { background: #fef3c7; }
}

// ──────────────────────────────────────────────
//  双栏主体布局
// ──────────────────────────────────────────────
.dual-layout {
  display: grid;
  grid-template-columns: 1fr 450px;
  gap: 25px;
  max-width: 1300px;
  margin: 0 auto;
  padding: 24px 24px 48px;
  align-items: start;

  @media (max-width: 960px) {
    grid-template-columns: 1fr;
  }
}

// ──────────────────────────────────────────────
//  左栏：岗位列表
// ──────────────────────────────────────────────
//.left-pane {}

.pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;
}

.pane-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.filter-tabs {
  display: flex;
  gap: $spacing-sm;
}

.filter-tab {
  padding: 5px 15px;
  border-radius: 6px;
  border: 1px solid $border-color;
  background: transparent;
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  color: rgba(49, 40, 164, 0.5);
  cursor: pointer;
  font-family: $font-family-base;
  transition: all $transition-fast;
  white-space: nowrap;
  border-color: rgba(27, 21, 109, 0.6);

  &.active { background: $primary; border-color: $primary; color: #fff; box-shadow: 0 4px 12px rgba(67,56,202,0.3); }
  &:not(.active):hover { border-color: $primary; color: $primary; }
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 18px;
  border: 1px solid #e9ebf0;
  border-radius: 12px;
  cursor: pointer;
  background: #fff;
  position: relative;
  transition: background 0.15s, box-shadow 0.15s, border-color 0.15s;
  animation: fadeSlideUp 0.4s ease both;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);

  &:hover {
    background: #f8f9ff;
    border-color: rgba(67, 56, 202, 0.25);
    box-shadow: 0 2px 10px rgba(67, 56, 202, 0.08);
  }

  &.selected {
    background: #f0f4ff;
    border-color: $primary;
    border-left: 3px solid $primary;
    padding-left: 13px;
    box-shadow: 0 2px 12px rgba(67, 56, 202, 0.12);
  }

  &.job-row--default {
    border-left: 3px solid #3b82f6;
    padding-left: 13px;
  }

  &__check {
    position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
    width: 22px; height: 22px; border-radius: 50%;
    background: $primary; display: flex; align-items: center; justify-content: center;
    color: white; flex-shrink: 0;
    svg { width: 11px; height: 11px; }
  }

  &__rank {
    position: absolute; left: 0; top: 0;
    font-size: 10px; font-weight: bold;
    padding: 2px 6px; border-radius: 0 0 6px 0;
  }

  &__icon {
    font-size: 22px; width: 40px; height: 40px;
    border-radius: 10px; background: #f3f4f6;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    overflow: hidden;

    &-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  &__body { flex: 1; min-width: 0; }

  &__title-line {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 2px;
  }

  &__name { font-size: 15px; font-weight: 600; color: #111; }

  &__score {
    font-size: 11px; color: #6366f1;
    background: #ede9fe; padding: 1px 7px;
    border-radius: 4px; flex-shrink: 0;
  }

  &__desc {
    font-size: 13px; color: #9ca3af;
    margin: 0 0 4px; line-height: 1.4;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  &__stack { display: flex; flex-wrap: wrap; gap: 3px; }

  &__actions {
    flex-shrink: 0; margin-left: 8px;
    display: flex; align-items: center;
    padding-right: 28px;

  }
}

.top-badge {
  &-1 { background: #fef3c7; color: #d97706; }
  &-2 { background: #f3f4f6; color: #4b5563; }
  &-3 { background: #fde8d8; color: #c2410c; }
}

.btn-set-default {
  font-size: 13px; color: #6b7280;
  border: 1px solid #e5e7eb; background: white;
  padding: 3px 9px; border-radius: 8px;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
  font-family: $font-family-base;
  &:hover { border-color: $primary; color: $primary; }
}

.default-badge {
  font-size: 13px; color: #3b82f6;
  background: #eff6ff; padding: 3px 9px;
  border-radius: 8px; white-space: nowrap;
}

.stack-tag {
  background: #f1f5f9; color: #64748b;
  font-size: 10px; border-radius: 3px; padding: 1px 6px;
}

.empty-state-wrap {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: $spacing-4xl $spacing-xl;
  gap: $spacing-md;
  p { color: $text-muted; font-size: $font-size-base; }
}

.btn-ghost-sm {
  padding: 6px 16px; border-radius: 8px;
  border: 1px solid #e5e7eb; background: white;
  font-size: 13px; color: #6b7280; cursor: pointer;
  font-family: $font-family-base;
  &:hover { border-color: $primary; color: $primary; }
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

.fade-slide-down-enter-active,
.fade-slide-down-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-slide-down-enter-from,
.fade-slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.fade-slide-down-enter-to,
.fade-slide-down-leave-from {
  opacity: 1;
  transform: translateY(0);
}

// ──────────────────────────────────────────────
//  右栏：面试配置
// ──────────────────────────────────────────────
.right-pane {
  position: sticky;
  top: calc(140px); // header 高度
  
  @media (max-width: 960px) {
    position: static;
    order: -1;  // 移动端配置区置顶
  }
}

.config-card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #eef0f6;
  box-shadow: 0 4px 24px rgba(67, 56, 202, 0.07);
  overflow: hidden;
}

// 当前选中岗位提示条
.selected-job-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  background: #f8f9ff;
  border-bottom: 1px solid #eef0f6;
  min-height: 52px;

  &.has-job { background: linear-gradient(90deg, #f0f4ff 0%, #f8f9ff 100%); }

  &__icon {
    font-size: 20px; flex-shrink: 0;

    &-img {
      width: 20px;
      height: 20px;
      object-fit: cover;
      border-radius: 4px;
      display: inline-block;
    }
  }
  &__name { font-size: 14px; font-weight: 600; color: #111827; flex: 1; }
  &__badge {
    font-size: 11px; color: $primary; background: #e0e7ff;
    padding: 2px 8px; border-radius: 6px; flex-shrink: 0;
  }
  &__empty-icon { width: 18px; height: 18px; color: #d1d5db; flex-shrink: 0; }
  &__placeholder { font-size: 13px; color: #9ca3af; }
}

// 配置区块通用
.config-section {
  padding: 24px 20px 0;
  margin-bottom: 22px; /* 新增：区块之间更大间距 */

  &:last-of-type {
    padding-bottom: 18px;
    margin-bottom: 0; /* 最后一个区块不额外加间距 */
  }


  &__label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: #262d38;
    margin-bottom: 10px;
  }

  &__icon {
    width: 15px; height: 15px;
    color: $primary; flex-shrink: 0;
  }

  &__required { color: #ef4444; font-size: 14px; }
}

// ─── 简历下拉选择器 ───
.resume-selector {
  position: relative;

  &.open .resume-selector__arrow {
    transform: rotate(180deg);
  }

  &__trigger {
    width: 100%; height: 44px;
    display: flex; align-items: center; gap: 8px;
    padding: 0 14px;
    background: #f9fafb;
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    cursor: pointer; font-family: $font-family-base;
    transition: border-color 0.2s, box-shadow 0.2s;
    text-align: left;

    &:hover { border-color: rgba(67,56,202,0.4); }
    &:focus { outline: none; }
  }

  &__value {
    flex: 1; display: flex; align-items: center; gap: 6px;
    font-size: 13px; color: #111827; font-weight: 500;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  }

  &__placeholder {
    flex: 1; font-size: 13px; color: #9ca3af;
  }

  &__arrow {
    width: 16px; height: 16px; color: #9ca3af;
    flex-shrink: 0; transition: transform 0.2s;
  }

  &__dropdown {
    position: absolute; left: 0; right: 0; top: calc(100% + 6px);
    background: #fff;
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    z-index: 50;
    overflow: hidden;
    max-height: 280px;
    overflow-y: auto;
  }
}

.resume-dropdown-loading,
.resume-dropdown-empty {
  padding: 16px 14px;
  font-size: 13px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 8px;
}

.resume-dropdown-link {
  color: $primary; cursor: pointer; font-weight: 600;
  &:hover { text-decoration: underline; }
}

.resume-dropdown-item {
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f3f4f6;

  &:last-child { border-bottom: none; }
  &:hover { background: #f8f9ff; }
  &.active { background: #f0f4ff; }

  &__name {
    font-size: 13px; font-weight: 500; color: #111827;
    display: flex; align-items: center; gap: 6px;
  }
  &__date { font-size: 11px; color: #9ca3af; margin-top: 2px; }
}

.job-row__details {
  margin-top: 8px;
  padding: 18px 18px 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.job-row__detail-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  align-items: end;
  margin-bottom: 16px;
}

.job-row__detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.job-row__detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  align-items: flex-end;
}

.job-row__detail-footer--single {
  margin-top: 4px;
}

.profile-detail-btn,
.custom-config-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.profile-detail-btn:hover,
.custom-config-btn:hover {
  border-color: rgba(67,56,202,0.45);
  box-shadow: 0 8px 24px rgba(67,56,202,0.08);
}

.profile-detail-section {
  margin-bottom: 24px;
}

.profile-detail-section h3 {
  margin-bottom: 14px;
  color: #111827;
  font-size: 15px;
  font-weight: 700;
}

.profile-detail-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.profile-detail-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-detail-field--full {
  grid-column: span 3;
}

.profile-detail-field label {
  color: #6b7280;
  font-size: 12px;
}

.profile-detail-field input,
.profile-detail-field select,
.profile-detail-field textarea {
  width: 100%;
  min-height: 40px;
  padding: 10px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
  color: #111827;
  transition: border-color 0.2s ease;
}

.profile-detail-field textarea {
  min-height: 92px;
  resize: vertical;
}

.profile-detail-field input:focus,
.profile-detail-field select:focus,
.profile-detail-field textarea:focus {
  outline: none;
  border-color: rgba(67,56,202,0.4);
}

.profile-detail-checkbox {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
}

.profile-detail-checkbox label {
  margin: 0;
  font-size: 13px;
}

.btn-confirm.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.job-row__detail-expand {
  margin-top: 18px;
  padding: 16px 14px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.job-row__detail-expand-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.job-row__detail-expand-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.job-row__detail-expand-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.job-row__detail-expand-label {
  font-size: 12px;
  color: #6b7280;
}

.job-row__detail-expand-value {
  font-size: 13px;
  color: #111827;
  white-space: pre-wrap;
  word-break: break-word;
}

.custom-config-btn {
  padding: 10px 18px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
  font-size: 13px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.custom-config-btn:hover {
  border-color: rgba(67,56,202,0.45);
  box-shadow: 0 6px 16px rgba(67,56,202,0.08);
}

.job-row__detail-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-row__detail-label {
  font-size: 13px;
  color: #6b7280;
}

.job-row__preview {
  padding: 14px 0 0;
  border-top: 1px solid #eef0f6;
}

.job-row__no-profile {
  font-size: 13px;
  color: #6b7280;
  background: #f8fafc;
  border: 1px dashed #d1d5db;
  border-radius: 10px;
  padding: 12px 14px;
}

.job-row__preview-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-row__preview-title {
  font-size: 14px;
  color: #111827;
  font-weight: 600;
}

.job-row__preview-line {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

.resume-main-badge {
  font-size: 10px; font-weight: 700; color: $primary;
  background: #e0e7ff; padding: 1px 6px; border-radius: 4px;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid #e5e7eb;
  border-top-color: $primary;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

// ─── 简历校验提示 ───
.resume-validation-alert {
  margin-top: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 6px;
  font-size: 14px;
  color: #d81919;
  line-height: 1;

  span { flex: 1; min-width: 160px; }

  &__actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
}

.resume-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
  margin-left: 2%;
}

.rva-btn {
  padding: 5px 10px; border-radius: 6px;
  font-size: 13px; font-weight: 520; cursor: pointer;
  font-family: $font-family-base; transition: all 0.15s;

  &--view {
    border: 1px solid #6366f1; background: white; color: #6366f1;
    &:hover { background: #eef2ff; border-color: #4f46e5; }
  }

  &--edit {
    border: none; background: #6366f1; color: white;
    &:hover { background: #4f46e5; }
  }
}

// ─── 面试模式切换 ───
.mode-action-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 18px;
  flex-wrap: nowrap;
  margin-bottom: 14px;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-toggle-row {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 12px 10px;
  min-width: 120px;
  justify-content: center;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s;
  background: #fafafa;

  &:hover { background: #f8f9ff; }

  &.active {
    background: #f0f4ff;
  }

  &__radio {
    width: 18px; height: 18px;
    border-radius: 50%;
    border: 2px solid #d1d5db;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: border-color 0.18s;

    .active & { border-color: $primary; }
  }

  &__dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: $primary; opacity: 0;
    transition: opacity 0.18s;
    .active & { opacity: 1; }
  }

  &__content { flex: 1; min-width: 0; }

  &__title {
    font-size: 13px; font-weight: 600; color: #111827;
    display: flex; align-items: center; gap: 5px;
  }
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.selection-card {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  transition: all 0.18s;
  min-height: 96px;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &:hover {
    border-color: rgba(67,56,202,0.35);
    background: #f8f9ff;
  }

  &.active {
    border-color: $primary;
    background: #eef2ff;
  }

  &__title {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
  }

  &__summary {
    font-size: 12px;
    color: #6b7280;
    line-height: 1.5;
  }

  &__tone {
    font-size: 12px;
    color: #2563eb;
  }
}

.strategy-summary-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 22px;

  &__label {
    font-size: 15px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 10px;
  }

  &__body {
    display: grid;
    gap: 8px;
  }

  &__item {
    font-size: 13px;
    color: #374151;
    font-weight: 600;
  }

  &__hint {
    font-size: 12px;
    color: #6b7280;
  }

  &__detail {
    font-size: 13px;
    color: #4b5563;
  }
}

// ─── 语音角色选择 ───
.voice-role-section {
  margin-bottom: 6px;
  padding: 18px 20px;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dbeafe;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);

  &__title {
    font-size: 15px;
    font-weight: 700;
    color: #6366f1;
    margin-bottom: 16px;
  }
}

.voice-role-grid {
  display: none;
}

.voice-config-row {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 28px;
  margin-top: 0;
  flex-wrap: nowrap;
}

.voice-config-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.voice-config-item.voice-config-field {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 220px;
}

.voice-config-select {
  min-width: 220px;
  width: 220px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  color: #111827;
}

.voice-config-select--speed {
  min-width: 90px;
  width: 90px;
}

.voice-config-toggle {
  min-width: 180px;
}

.voice-config-label {
  font-size: 13px;
  color: #374151;
  font-weight: 600;
}

.switch-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.switch-label input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  width: 40px;
  height: 20px;
  border-radius: 999px;
  background: #d1d5db;
  position: relative;
  transition: background-color 0.2s ease;
}

.switch-slider::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s ease;
}

.switch-label input:checked + .switch-slider {
  background: #4f46e5;
}

.switch-label input:checked + .switch-slider::before {
  transform: translateX(20px);
}

.switch-text {
  font-size: 13px;
  color: #4b5563;
}


.voice-role-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: white;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover { border-color: rgba(67,56,202,0.35); }

  &.active {
    border-color: $primary;
    background: #f0f4ff;
  }

  &__info { flex: 1; min-width: 0; }

  &__name { font-size: 12px; font-weight: 600; color: #111827; }

  &__style { font-size: 11px; color: #9ca3af; }

  &__check {
    width: 18px; height: 18px; border-radius: 50%;
    background: $primary; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; color: white;
    svg { width: 9px; height: 9px; }
  }
}

// ─── 开始面试按钮区 ───
.start-action {
  padding: 14px 18px 20px;
  border-top: 1px solid #f3f4f6;
}

.start-tips {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  margin-bottom: 8px;
}

.start-btn {
  width: 100%; height: 50px;
  background: $gradient-primary;
  border: none; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  gap: 8px; cursor: pointer;
  box-shadow: $shadow-primary;
  transition: all 0.2s;
  color: white; font-family: $font-family-base;
  font-size: 15px; font-weight: 700;

  &:hover:not(.disabled) { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(67,56,202,0.4); }
  &:active:not(.disabled) { transform: scale(0.98); }

  &.disabled {
    background: #e5e7eb;
    color: #9ca3af;
    box-shadow: none;
    cursor: not-allowed;
  }

  &__job {
    font-size: 11px; opacity: 0.8;
    background: rgba(255,255,255,0.2);
    padding: 2px 8px; border-radius: 8px;
  }
}

// ──────────────────────────────────────────────
//  弹窗
// ──────────────────────────────────────────────
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 10, 40, 0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 200;
  display: flex; align-items: center; justify-content: center;
  padding: 0 16px;
}

.modal-sheet {
  width: 100%; max-width: 480px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 -8px 40px rgba(67, 56, 202, 0.2);
  animation: sheetUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes sheetUp {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header-bar {
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  padding: 28px 24px 20px;
  text-align: center;
}
.modal-header-title { font-size: 20px; font-weight: 700; color: white; margin: 0 0 4px; }
.modal-header-sub   { font-size: 13px; color: rgba(255,255,255,0.7); margin: 0; }

.modal-body { padding: 20px 24px 28px; }

.interview-mode-tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 12px;
  font-size: 12px; font-weight: 600; margin-bottom: 16px;

  &.mode-voice { background: rgba(67,56,202,0.08); color: #4338ca; border: 1px solid rgba(67,56,202,0.2); }
  &.mode-text  { background: rgba(124,58,237,0.08); color: #7c3aed; border: 1px solid rgba(124,58,237,0.2); }
}

.rules-list {
  list-style: none; padding: 0; margin: 0 0 24px;
  display: flex; flex-direction: column; gap: 12px;

  li { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #374151; line-height: 1.5; }
}

.rule-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0; margin-top: 4px;
  &--blue   { background: #5495ff; }
  &--purple { background: #9d65fe; }
  &--green  { background: #61fdc9; }
  &--orange { background: #f7b84c; }
}

.modal-actions { display: flex; gap: 12px; }

.btn-cancel {
  flex: 0 0 80px; height: 48px;
  border-radius: 24px; border: 1.5px solid #e5e7eb;
  background: white; color: #6b7280;
  font-size: 14px; font-weight: 500; cursor: pointer;
  transition: all 0.2s; font-family: $font-family-base;
  &:hover { border-color: #d1d5db; background: #f9fafb; }
}

.btn-confirm {
  flex: 1; height: 48px;
  border-radius: 24px; border: none;
  background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
  color: white; font-size: 15px; font-weight: 700;
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; gap: 8px;
  font-family: $font-family-base;
  box-shadow: 0 4px 16px rgba(67, 56, 202, 0.4);
  transition: all 0.2s;
  &:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(67, 56, 202, 0.5); }
  &:active { transform: scale(0.98); }
}

// ─── 简历详情弹窗 ───
.missing-fields-list {
  display: flex; flex-direction: column; gap: 8px;
}

.missing-field-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #374151;
  padding: 8px 12px;
  background: #fffbeb;
  border-radius: 8px;
  border: 1px solid #fde68a;
}

// ──────────────────────────────────────────────
//  过渡动画
// ──────────────────────────────────────────────
.modal-enter-active  { animation: overlayIn 0.3s ease both; }
.modal-leave-active  { animation: overlayIn 0.2s ease reverse both; }
@keyframes overlayIn { from { opacity: 0; } to { opacity: 1; } }

.dropdown-enter-active { transition: all 0.18s ease; }
.dropdown-leave-active { transition: all 0.14s ease; }
.dropdown-enter, .dropdown-leave-to { opacity: 0; transform: translateY(-6px); }

.fade-in-enter-active { transition: all 0.2s ease; }
.fade-in-leave-active { transition: all 0.15s ease; }
.fade-in-enter, .fade-in-leave-to { opacity: 0; transform: translateY(-4px); }

.voice-expand-enter-active { transition: all 0.25s ease; }
.voice-expand-leave-active { transition: all 0.2s ease; }
.voice-expand-enter, .voice-expand-leave-to { opacity: 0; transform: translateY(-8px); }
</style>