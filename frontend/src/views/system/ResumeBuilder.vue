<!-- 简历构建器
frontend/src/views/system/ResumeBuilder.vue
-->
 
<template>
  <div class="resume-builder-page">

    <!-- ============================================================
         左侧编辑面板
    ============================================================ -->
    <aside class="builder-left-panel" :class="{ open: panelOpen }">
      <div class="builder-panel-header">
        <!-- 简历切换标签栏 -->
        <div class="resume-tabs-bar">
          <div class="resume-tabs-scroll">
            <button
              v-for="r in resumeList"
              :key="r.id"
              class="resume-tab"
              :class="{ active: currentResumeId === r.id }"
              @click="switchResume(r.id)"
            >
              <span class="tab-dot" :class="{ main: r.isMain }"></span>
              <span class="tab-label">{{ r.isMain ? '主简历' : r.title }}</span>
              <span
                v-if="!r.isMain"
                class="tab-close"
                @click.stop="confirmDeleteResume(r)"
                title="删除此简历"
              >✕</span>
            </button>
          </div>
          <button class="tab-add-btn" @click="openCreateDialog" title="新建岗位定制简历">
            <span>＋</span>
          </button>
        </div>

        <!-- 当前简历标题 -->
        <div class="resume-title-row">
          <input
            v-model="resumeTitle"
            class="resume-title-input"
            placeholder="简历名称"
            maxlength="40"
            @blur="autoSaveTitle"
          />
          <span class="save-indicator" :class="saveState">
            {{ saveStateLabel }}
          </span>
        </div>
      </div>

      <div v-if="panelOpen" class="panel-body">
        <!-- 模块导航 -->
        <section class="section-config section-nav">
          <div class="module-tabs">
            <button
              v-for="item in modules"
              :key="item.key"
              :class="{ active: activeSection === item.key }"
              @click="activeSection = item.key"
            >
              {{ item.label }}
            </button>
          </div>
        </section>
      <!-- 必填项状态栏 -->
      <div v-if="missingRequiredFields.length > 0" class="required-bar">
        <span class="required-bar-title">⚠ 待填必填项</span>
        <div class="required-tags">
          <button
            v-for="item in missingRequiredFields"
            :key="item.field"
            class="required-tag"
            @click="navigateToRequired(item)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
      <div v-else class="required-bar required-bar--done">
        ✓ 所有必填项已完成
      </div>
        <!-- 个人信息 -->
        <section class="section-config" v-if="activeSection === 'personal'">
          <h3>个人信息</h3>
          <div class="row avatar-row">
            <label>证件照上传</label>
            <div class="avatar-upload" @click="triggerAvatarInput">
              <img v-if="personal.avatar" :src="personal.avatar" alt="证件照" />
              <span v-else>+</span>
              <input ref="avatarInput" type="file" accept="image/*" @change="onAvatarChange" hidden />
            </div>
          </div>
        <div class="row">
          <label>姓名 <span class="req-star">*</span></label>
          <input
            v-model="personal.name"
            data-field="name"
            type="text"
            placeholder="输入你的真实姓名"
            maxlength="20"
            :class="{ 'input-required': !personal.name?.trim() }"
          />
        </div>
          <div class="row">
          <label>性别 <span class="req-star">*</span></label>
          <!-- <input
            v-model="personal.gender"
            data-field="gender"
            type="text"
            placeholder="男/女"
            maxlength="20"
            :class="{ 'input-required': !personal.gender?.trim() }"
          /> -->
          <select
            v-model="personal.gender"
            data-field="gender"
            :class="{ 'input-required': !personal.gender?.trim() }"
          >
            <option value="">请选择性别</option>
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
        </div>
          <div class="row">
            <label>年龄</label>
            <input v-model.number="personal.age" type="number" min="0" max="99" />
          </div>
          <div class="row">
            <label>籍贯</label>
            <input v-model="personal.address" type="text" />
          </div>
          <div class="row">
            <label>工作经验（年）</label>
            <input v-model.number="personal.experience" type="number" min="0" max="40" />
          </div>
          <div class="row">
            <label>手机号码 <span class="req-star">*</span></label>
            <input
              v-model="personal.phone"
              data-field="phone"
              type="text"
              placeholder="手机号"
              :class="{ 'input-required': !personal.phone?.trim() }"
            />
          </div>
          <div class="row">
            <label>电子邮箱 <span class="req-star">*</span></label>
            <input
              v-model="personal.email"
              data-field="email"
              type="email"
              placeholder="邮箱地址"
              :class="{ 'input-required': !personal.email?.trim() }"
            />
          </div>
        </section>

        <!-- 求职意向 -->
        <section class="section-config" v-else-if="activeSection === 'objective'">
          <h3>求职意向</h3>
          <div class="row">
            <label>求职类型</label>
            <select v-model="objective.jobType">
              <option>实习</option>
              <option>全职</option>
              <option>兼职</option>
            </select>
          </div>
          <div class="row">
            <label>意向岗位</label>
            <input v-model="objective.position" type="text" maxlength="15" />
            <span class="char-count">{{ objective.position.length }}/15</span>
          </div>
          <div class="row">
            <label>意向城市</label>
            <input v-model="objective.city" type="text" maxlength="15" />
            <span class="char-count">{{ objective.city.length }}/15</span>
          </div>
          <div class="row">
            <label>期望薪酬</label>
            <select v-model="objective.salary">
              <option value="">Select</option>
              <option>5k-8k</option>
              <option>8k-12k</option>
              <option>12k-20k</option>
              <option>20k+</option>
              <option>其它</option>
            </select>
          </div>
          <div class="row">
            <label>求职状态</label>
            <select v-model="objective.status">
              <option value="">Select</option>
              <option>随时到岗</option>
              <option>一周内</option>
              <option>一个月内</option>
            </select>
          </div>
        </section>

        <!-- 教育背景 -->
        <section class="section-config" v-else-if="activeSection === 'education'">
          <h3>教育背景</h3>
          <div class="entry-editor" v-for="(item, idx) in education" :key="item.id">
            <div class="row">
              <label>起止时间</label>
              <input v-model="item.start" type="date" />
              <span>至</span>
              <input v-model="item.end" type="date" />
            </div>
            <div class="row">
              <label>学校名称 <span class="req-star">*</span></label>
              <input
                v-model="item.school"
                data-field="school"
                type="text"
                maxlength="40"
                :class="{ 'input-required': !item.school?.trim() }"
              />
              <span class="char-count">{{ item.school.length }}/40</span>
            </div>
            <div class="row">
              <label>专业名称</label>
              <input v-model="item.major" type="text" maxlength="20" />
              <span class="char-count">{{ item.major.length }}/20</span>
            </div>
            <div class="row">
              <label>学历学位</label>
              <input v-model="item.degree" type="text" maxlength="20" />
            </div>
            <button class="btn-danger" v-if="education.length > 1" @click="removeEducation(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addEducation">添加学历</button>
        </section>

        <!-- 荣誉奖项 -->
        <section class="section-config" v-else-if="activeSection === 'prices'">
          <h3>荣誉奖项</h3>
          <div class="entry-editor" v-for="(item, idx) in prices" :key="item.id">
            <div class="row"><label>获奖名称</label><input v-model="item.award" type="text" maxlength="50" /></div>
            <div class="row"><label>获奖时间</label><input v-model="item.period" type="date" /></div>
            <div class="row"><label>获奖等级</label><input v-model="item.level" type="text" maxlength="20" placeholder="一等奖" /></div>
            <button class="btn-danger" v-if="prices.length > 1" @click="removePrice(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addPrice">添加奖项</button>
        </section>

        <!-- 技能特长 -->
        <section class="section-config" v-else-if="activeSection === 'skills'">
          <h3>技能特长</h3>
          <div class="skill-row" v-for="(item, idx) in skills" :key="item.id">
            <input v-model="item.name" placeholder="熟练掌握该项技术" maxlength="40" />
            <button class="btn-danger" @click="removeSkill(idx)">-</button>
            <button class="btn-success" @click="addSkillAt(idx)">+</button>
          </div>
          <button class="btn-success" @click="addSkill">添加技能</button>
        </section>

        <!-- 经历与经验 -->
        <section class="section-config" v-else-if="activeSection === 'experience'">
          <h3>校园经历</h3>
          <div class="entry-editor" v-for="(item, idx) in campusExperiences" :key="item.id">
            <div class="row"><label>起止时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>经历名称</label><input v-model="item.title" type="text" /></div>
            <div class="row"><label>详情描述</label><textarea v-model="item.description" rows="3"></textarea></div>
            <div class="row"><label>业绩/成就 <span style="color:#ef4444;font-size:11px">（技术岗必填，请用数据量化）</span></label><textarea v-model="item.achievements" rows="3" maxlength="200" placeholder="如：独立完成xx模块开发，上线后降低bug率40%"></textarea></div> 
            <button class="btn-danger" v-if="campusExperiences.length > 1" @click="removeCampusExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addCampusExperience">添加经历</button>

          <h3 style="margin-top:14px">实习经历</h3>
          <div class="entry-editor" v-for="(item, idx) in internshipExperiences" :key="item.id">
            <div class="row"><label>起止时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>实习公司</label><input v-model="item.place" type="text" /></div>
            <div class="row"><label>实习岗位</label><input v-model="item.title" type="text" /></div>
            <div class="row"><label>详情描述</label><textarea v-model="item.description" rows="3"></textarea></div>
            <div class="row"><label>业绩/成就 <span style="color:#ef4444;font-size:11px">（技术岗必填，请用数据量化）</span></label><textarea v-model="item.achievements" rows="3" maxlength="200" placeholder="如：独立完成xx模块开发，上线后降低bug率40%"></textarea></div>
            <button class="btn-danger" v-if="internshipExperiences.length > 1" @click="removeInternshipExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addInternshipExperience">添加经历</button>

          <h3 style="margin-top:14px">工作经验</h3>
          <div class="entry-editor" v-for="(item, idx) in workExperiences" :key="item.id">
            <div class="row"><label>时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>公司名称</label><input v-model="item.company" type="text" maxlength="35" /><span class="char-count">{{ item.company.length }}/35</span></div>
            <div class="row"><label>主要职责</label><input v-model="item.role" type="text" maxlength="35" /><span class="char-count">{{ item.role.length }}/35</span></div>
            <div class="row"><label>工作内容</label><textarea v-model="item.description" rows="4" maxlength="200"></textarea></div>
            <div class="content-count">{{ item.description.length }}/200</div>
            <div class="row"><label>业绩/成就 <span style="color:#ef4444;font-size:11px">（技术岗必填，请用数据量化）</span></label><textarea v-model="item.achievements" rows="3" maxlength="200" placeholder="如：优化接口响应时间30%，QPS提升至5000"></textarea></div>
            <button class="btn-danger" v-if="workExperiences.length > 1" @click="removeWorkExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addWorkExperience">添加经历</button>
        </section>

        <!-- 底部操作栏 -->
        <section class="section-config action-footer">
          <button class="btn-action" @click="resetData">重置</button>
          <button class="btn-action btn-save" :disabled="saveState === 'saving'" @click="manualSave">
            {{ saveState === 'saving' ? '保存中…' : '保存' }}
          </button>
          <button class="btn-action" @click="exportPdf">导出 PDF</button>
        </section>
      </div>
    </aside>

    <!-- ============================================================
         右侧预览区域
    ============================================================ -->
    <main class="builder-main">
      <div class="preview-header">
        <h2>简历预览</h2>
        <span class="preview-badge" v-if="currentResume && !currentResume.isMain">
          岗位定制 · {{ currentResume.jobName || currentResume.title }}
        </span>
      </div>

      <section class="resume-preview" id="resume-preview" :style="previewStyles">
        <div class="a4-paper">
          <div
            v-for="(block, index) in visibleBlocks"
            :key="block.id"
            class="resume-block"
            draggable="true"
            @dragstart="dragStart(index)"
            @dragover.prevent="dragOver(index)"
            @dragend="dragEnd"
            @drop="drop(index)"
            @mouseenter="hoverIndex = index"
            @mouseleave="hoverIndex = -1"
            :class="{ dragging: dragIndex === index, 'drag-over': overIndex === index }"
          >
            <div class="block-handle">⠿</div>
            <div class="block-head">
              <div class="section-title" v-if="block.type !== 'profile'">
                <h3 :style="{ color: config.titleColor }">{{ block.title }}</h3>
                <span class="section-underline"></span>
                <span class="section-underline-light"></span>
              </div>
              <button class="delete-btn" v-if="block.type !== 'profile'" v-show="hoverIndex === index" @click="confirmDelete(index)">🗑</button>
            </div>

            <div class="block-content" :style="{ color: config.bodyColor }">
              <!-- 个人信息 -->
              <template v-if="block.type === 'profile'">
                <div class="profile-row">
                  <div class="profile-avatar-box">
                    <img v-if="personal.avatar" class="profile-avatar" :src="personal.avatar" alt="证件照" />
                    <div v-else class="profile-avatar-placeholder">证件照</div>
                  </div>
                  <div class="profile-info-inline">
                    <h2>{{ personal.name || '未设置' }}</h2>
                    <div class="label-row">
                      <span>年龄：{{ personal.age || '未设置' }} 岁</span>
                      <span>籍贯：{{ personal.address || '未设置' }}{{ personal.gender ? ' 性别：' + personal.gender : '' }}</span>
                    </div>
                    <div class="label-row">
                      <span>工作经验：{{ personal.experience || 0 }} 年</span>
                      <span>联系方式：{{ contactInfo }}</span>
                    </div>
                  </div>
                </div>
              </template>

              <!-- 求职意向 -->
              <template v-else-if="block.type === 'objective'">
                <div class="info-grid">
                  <div>求职类型：{{ objective.jobType || '未设置' }}</div>
                  <div>意向岗位：{{ objective.position || '未设置' }}</div>
                  <div>意向城市：{{ objective.city || '未设置' }}</div>
                  <div>到岗时间：{{ objective.status || '未设置' }}</div>
                </div>
              </template>

              <!-- 教育背景 -->
              <template v-else-if="block.type === 'education'">
                <div class="experience-list">
                  <div v-for="item in education" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '未设置' }} — {{ item.end || '未设置' }}</div>
                      <div>学校：{{ item.school || '未设置' }}</div>
                      <div>专业：{{ item.major || '未设置' }}</div>
                      <div>学历：{{ item.degree || '未设置' }}</div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- 荣誉奖项 -->
              <template v-else-if="block.type === 'prices'">
                <div v-if="prices.length" class="experience-list">
                  <div v-for="item in prices" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>获奖名称：{{ item.award || '未设置' }}</div>
                      <div>时间：{{ item.period || '未设置' }}</div>
                      <div>等级：{{ item.level || '未设置' }}</div>
                    </div>
                  </div>
                </div>
                <div v-else class="experience-item">
                  <div class="info-grid">
                    <div>获奖名称：未设置</div><div>时间：未设置</div><div>等级：未设置</div>
                  </div>
                </div>
              </template>

              <!-- 技能特长 -->
              <template v-else-if="block.type === 'skills'">
                <p>{{ skills.length ? skills.map(s => s.name).filter(Boolean).join('、') : '暂未填写技能' }}</p>
              </template>

              <!-- 校园经历 -->
              <template v-else-if="block.type === 'campus'">
                <div v-if="campusExperiences.length" class="experience-list">
                  <div v-for="item in campusExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                      <div>名称：{{ item.title || '经历名称' }}</div>
                    </div>
                    <p>详情描述：{{ renderDetailText(item, '经历描述…') }}</p>
                  </div>
                </div>
                <div v-else class="experience-item">
                  <p>暂无校园经历</p>
                </div>
              </template>

              <!-- 实习经验 -->
              <template v-else-if="block.type === 'internship'">
                <div v-if="internshipExperiences.length" class="experience-list">
                  <div v-for="item in internshipExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                      <div>公司：{{ item.place || '公司名称' }}</div>
                      <div>岗位：{{ item.title || '岗位名称' }}</div>
                    </div>
                    <p>详情描述：{{ renderDetailText(item, '实习内容…') }}</p>
                  </div>
                </div>
                <div v-else class="experience-item"><p>暂无实习经历</p></div>
              </template>

              <!-- 工作经验 -->
              <template v-else-if="block.type === 'work'">
                <div v-if="workExperiences.length" class="experience-list">
                  <div v-for="item in workExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                      <div>公司：{{ item.company || '公司名称' }}</div>
                      <div>岗位：{{ item.role || '岗位名称' }}</div>
                    </div>
                    <p>详情描述：{{ renderDetailText(item, '工作内容…') }}</p>
                  </div>
                </div>
                <div v-else class="experience-item"><p>暂无工作经验</p></div>
              </template>

              <!-- 项目经验 -->
              <template v-else-if="block.type === 'project'">
                <div v-if="projectExperiences.length" class="experience-list">
                  <div v-for="item in projectExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>项目：{{ item.name || '项目名称' }}</div>
                      <div>角色：{{ item.role || '角色' }}</div>
                      <div>技术栈：{{ item.techStack || '技术栈' }}</div>
                    </div>
                    <p>详情描述：{{ renderDetailText(item, '项目描述…') }}</p>
                  </div>
                </div>
                <div v-else class="experience-item"><p>暂无项目经验</p></div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <button class="float-btn" @click="goBack">← 返回</button>
      <button class="float-btn switch" @click="togglePanel">⇆ 切换</button>
    </main>

    <!-- ============================================================
         新建岗位定制简历 对话框
    ============================================================ -->
    <transition name="modal">
      <div v-if="showCreateDialog" class="modal-overlay modal-overlay--center" @click.self="showCreateDialog = false">
        <div class="modal-sheet modal-sheet--sm2">
          <div class="modal-header">
            <h3>新建岗位定制简历</h3>
            <button class="modal-close" @click="showCreateDialog = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>简历名称</label>
              <input v-model="createForm.title" class="form-control" placeholder="例：后端开发定制版" maxlength="40" />
            </div>
            <div class="form-group">
              <label>关联岗位（可选）</label>
              <select v-model="createForm.jobId" class="form-control">
                <option :value="null">不关联岗位</option>
                <option v-for="job in allJobs" :key="job.id" :value="job.id">
                  {{ job.name }}
                </option>
              </select>
            </div>
            <div class="autofill-toggle">
              <label class="toggle-label">
                <input type="checkbox" v-model="createForm.copyFromMain" />
                <span class="toggle-text">
                  <strong>从主简历导入内容</strong>
                  <small>勾选后将主简历的所有内容复制到新简历作为起点</small>
                </span>
              </label>
            </div>
            <p v-if="createForm.copyFromMain" class="autofill-hint">
              导入后可在此基础上针对岗位进行修改，主简历内容不会受到影响。
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showCreateDialog = false">取消</button>
            <button class="btn btn-primary" :disabled="creating" @click="doCreateResume">
              <span v-if="creating" class="btn-spinner"></span>
              {{ creating ? '创建中…' : '确认创建' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ============================================================
         首次打开定制简历的自动填入询问弹窗
    ============================================================ -->
    <transition name="modal">
      <div v-if="showAutoFillPrompt" class="modal-overlay modal-overlay--center">
        <div class="modal-sheet modal-sheet--sm2">
          <div class="modal-header">
            <h3>📋 导入主简历内容？</h3>
          </div>
          <div class="modal-body">
            <p class="autofill-desc">
              当前简历内容为空。是否将<strong>主简历</strong>的内容复制过来作为起点，再针对岗位进行定制？
            </p>
            <p class="autofill-note">此操作不会影响主简历，可以随时修改。</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="dismissAutoFillPrompt">不导入，从空白开始</button>
            <button class="btn btn-primary" :disabled="autoFilling" @click="doAutoFill">
              <span v-if="autoFilling" class="btn-spinner"></span>
              {{ autoFilling ? '导入中…' : '导入主简历' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ============================================================
         删除简历确认弹窗
    ============================================================ -->
    <transition name="modal">
      <div v-if="showDeleteConfirm" class="modal-overlay modal-overlay--center" @click.self="showDeleteConfirm = false">
        <div class="modal-sheet modal-sheet--sm2">
          <div class="modal-header">
            <h3>删除简历</h3>
            <button class="modal-close" @click="showDeleteConfirm = false">✕</button>
          </div>
          <div class="modal-body">
            <p>确认删除简历 <strong>{{ deleteTarget && deleteTarget.title }}</strong> 吗？此操作不可撤销。</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showDeleteConfirm = false">取消</button>
            <button class="btn btn-danger-solid" :disabled="deleting" @click="doDeleteResume">
              <span v-if="deleting" class="btn-spinner btn-spinner--dark"></span>
              {{ deleting ? '删除中…' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 全局加载遮罩 -->
    <transition name="fade">
      <div v-if="globalLoading" class="global-loading-overlay">
        <div class="loading-card">
          <div class="loading-spinner-lg"></div>
          <p>{{ globalLoadingText }}</p>
        </div>
      </div>
    </transition>

  </div>
</template>

<script>
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import request from '@/utils/request' 
import {
  listResumes,
  getResume,
  getMainResume,
  createResume,
  updateResume,
  deleteResume,
  copyFromMain,
} from '@/api/resume'
import { fetchJobs } from '@/api/job'

const LOCAL_KEY = 'resumeBuilderDraft_'           // prefix + resumeId
const AUTOFILL_SEEN_KEY = 'resumeAutoFillSeen_'   // prefix + resumeId

// Default empty content factory
function emptyContent() {
  return {
    personal: { name: '', gender: '', age: 0, experience: 0, email: '', phone: '', avatar: '', address: '', summary: '' },
    objective: { jobType: '实习', position: '', city: '', salary: '', status: '' },
    education: [{ id: 1, start: '', end: '', school: '', major: '', degree: '' }],
    skills: [{ id: 1, name: '' }],
    campusExperiences: [],
    internshipExperiences: [],
    workExperiences: [],
    projectExperiences: [],
    prices: [{ id: 1, award: '', period: '', level: '' }],
    blockOrder: ['profile', 'objective', 'education', 'campus', 'internship', 'work', 'project', 'prices', 'skills'],
    config: { titleColor: '#2B2B2B', bodyColor: '#4F4F4F', fontSize: 14, padding: 20 },
  }
}

export default {
  name: 'ResumeBuilder',

  data() {
    return {
      // ── resume list / current ──────────────────────────────────────────────
      resumeList: [],
      currentResumeId: null,

      // ── editor state (mirrors content JSON) ───────────────────────────────
      resumeTitle: '我的简历',
      panelOpen: true,
      activeSection: 'personal',

      personal: emptyContent().personal,
      objective: emptyContent().objective,
      education: emptyContent().education,
      skills: emptyContent().skills,
      campusExperiences: [],
      internshipExperiences: [],
      workExperiences: [],
      projectExperiences: [],
      prices: emptyContent().prices,
      blockOrder: emptyContent().blockOrder,
      config: emptyContent().config,
      allJobs: [],

      dragIndex: -1,
      overIndex: -1,
      hoverIndex: -1,

      // ── save state ─────────────────────────────────────────────────────────
      saveState: 'saved',   // 'saved' | 'unsaved' | 'saving' | 'error'
      autoSaveTimer: null,

      // ── dialogs ───────────────────────────────────────────────────────────
      showCreateDialog: false,
      showAutoFillPrompt: false,
      showDeleteConfirm: false,
      deleteTarget: null,

      creating: false,
      deleting: false,
      autoFilling: false,

      createForm: {
        title: '',
        jobId: null,
        copyFromMain: true,
      },

      // ── global loading ────────────────────────────────────────────────────
      globalLoading: false,
      globalLoadingText: '加载中…',

      // ── constants ─────────────────────────────────────────────────────────
 
      modules: [
        { key: 'personal',   label: '个人信息' },
        { key: 'objective',  label: '求职意向' },
        { key: 'education',  label: '教育背景' },
        { key: 'experience', label: '经历与经验' },
        { key: 'prices',     label: '荣誉奖项' },
        { key: 'skills',     label: '技能特长' },
      ],
    }
  },

  computed: {
    missingRequiredFields() {
      const missing = []
      if (!this.personal.name?.trim())
        missing.push({ label: '姓名', section: 'personal', field: 'name' })
      if (!this.personal.gender?.trim())
        missing.push({ label: '性别', section: 'personal', field: 'gender' })
      if (!this.personal.phone?.trim())
        missing.push({ label: '手机号码', section: 'personal', field: 'phone' })
      if (!this.personal.email?.trim())
        missing.push({ label: '电子邮箱', section: 'personal', field: 'email' })
      if (!this.education.length || !this.education[0]?.school?.trim())
        missing.push({ label: '就读院校', section: 'education', field: 'school' })
      return missing
    },    
    currentResume() {
      return this.resumeList.find(r => r.id === this.currentResumeId) || null
    },
    saveStateLabel() {
      return { saved: '已保存', unsaved: '有未保存更改', saving: '保存中…', error: '保存失败' }[this.saveState] || ''
    },
    previewStyles() {
      return {
        padding: `${this.config.padding}px`,
        fontSize: `${this.config.fontSize}px`,
        fontFamily: '微软雅黑, PingFang SC, sans-serif',
        background: '#fff',
      }
    },
    contactInfo() {
      if (this.personal.contact?.trim()) {
        return this.personal.contact
      }
      const items = []
      if (this.personal.phone?.trim()) items.push(this.personal.phone.trim())
      if (this.personal.email?.trim()) items.push(this.personal.email.trim())
      return items.length ? items.join(' / ') : '未设置'
    },
    visibleBlocks() {
      return this.blockOrder.map(key => {
        const map = {
          profile:     { id: key, type: 'profile',     title: '个人信息' },
          objective:   { id: key, type: 'objective',   title: '求职意向' },
          education:   { id: key, type: 'education',   title: '教育背景' },
          skills:      { id: key, type: 'skills',      title: '技能特长' },
          prices:      { id: key, type: 'prices',      title: '荣誉奖项' },
          campus:      { id: key, type: 'campus',      title: '校园经历' },
          internship:  { id: key, type: 'internship',  title: '实习经验' },
          work:        { id: key, type: 'work',        title: '工作经验' },
          project:     { id: key, type: 'project',     title: '项目经验' },
        }
        return map[key] || { id: key, type: key, title: '未知模块' }
      })
    },
  },

  async created() {
    await this.loadResumeList()
    this.loadJobList()  
  },

  watch: {
    // Deep watches — mark content as unsaved and schedule autosave
    personal:              { handler() { this.onContentChange() }, deep: true },
    objective:             { handler() { this.onContentChange() }, deep: true },
    education:             { handler() { this.onContentChange() }, deep: true },
    skills:                { handler() { this.onContentChange() }, deep: true },
    campusExperiences:     { handler() { this.onContentChange() }, deep: true },
    internshipExperiences: { handler() { this.onContentChange() }, deep: true },
    workExperiences:       { handler() { this.onContentChange() }, deep: true },
    projectExperiences:    { handler() { this.onContentChange() }, deep: true },
    prices:                { handler() { this.onContentChange() }, deep: true },
    blockOrder:            { handler() { this.onContentChange() }, deep: true },
    config:                { handler() { this.onContentChange() }, deep: true },

    activeSection(newSection) {
      const map = {
        personal: 'profile', objective: 'objective', education: 'education',
        skills: 'skills', experience: 'campus', prices: 'prices',
      }
      const blockType = map[newSection]
      if (blockType) this.ensureBlockVisible(blockType)
    },
  },

  methods: {
    // ─────────────────────────────────────────────────────────────────────────
    // Resume list & switching
    // ─────────────────────────────────────────────────────────────────────────
      navigateToRequired(item) {
        // 1. 切换到对应 section
        this.activeSection = item.section
        // 2. 等 DOM 渲染后定位并聚焦输入框
        this.$nextTick(() => {
          const el = this.$el.querySelector(`[data-field="${item.field}"]`)
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            el.focus()
          }
        })
      },
    async loadResumeList() {
      this.globalLoading = true
      this.globalLoadingText = '加载简历列表…'
      try {
        const res = await listResumes()
        this.resumeList = res || []
        // Load main resume by default
        const main = this.resumeList.find(r => r.isMain)
        if (main) {
          await this.loadResumeContent(main.id)
        } else if (this.resumeList.length > 0) {
          await this.loadResumeContent(this.resumeList[0].id)
        }
      } catch (e) {
        console.error('加载简历列表失败', e)
        // Fall back to empty state
        this.applyContent(emptyContent())
      } finally {
        this.globalLoading = false
      }
    },
    async loadJobList() {
      try {
        const jobs = await fetchJobs()
        if (Array.isArray(jobs) && jobs.length > 0) {
          this.allJobs = jobs
        }
      } catch (e) {
        console.warn('加载岗位列表失败', e)
      }
    },
    async switchResume(id) {
      if (id === this.currentResumeId) return
      // Save current before switching
      if (this.saveState === 'unsaved') {
        await this.doSave()
      }
      await this.loadResumeContent(id)
    },

    async loadResumeContent(id) {
      this.globalLoading = true
      this.globalLoadingText = '加载简历…'
      try {
        const res = await getResume(id)
        const resume = res
        this.currentResumeId = id
        this.resumeTitle = resume.title || '未命名简历'

        const content = resume.content || {}
        const isEmpty = !content || Object.keys(content).length === 0 ||
          (!content.personal?.name && !(content.education || []).some(e => e.school))

        this.applyContent(Object.keys(content).length ? content : emptyContent())
        this.saveState = 'saved'

        // Show auto-fill prompt for empty customized resumes (only once per resume)
        if (!resume.isMain && isEmpty) {
          const seenKey = AUTOFILL_SEEN_KEY + id
          if (!localStorage.getItem(seenKey)) {
            this.showAutoFillPrompt = true
          }
        }
      } catch (e) {
        console.error('加载简历内容失败', e)
        this.applyContent(emptyContent())
      } finally {
        this.globalLoading = false
      }
    },

    applyContent(c) {
      const d = emptyContent()
      this.personal             = { ...d.personal,   ...(c.personal   || {}) }
      this.objective            = { ...d.objective,  ...(c.objective  || {}) }
      this.education            = c.education             || d.education
      this.skills               = c.skills                || d.skills
      this.campusExperiences    = c.campusExperiences     || []
      this.internshipExperiences= c.internshipExperiences || []
      this.workExperiences      = c.workExperiences       || []
      this.projectExperiences   = c.projectExperiences    || []
      this.prices               = c.prices                || d.prices
      this.blockOrder           = c.blockOrder            || d.blockOrder
      this.config               = { ...d.config,     ...(c.config     || {}) }
    },

    buildContent() {
      return {
        personal:              this.personal,
        objective:             this.objective,
        education:             this.education,
        skills:                this.skills,
        campusExperiences:     this.campusExperiences,
        internshipExperiences: this.internshipExperiences,
        workExperiences:       this.workExperiences,
        projectExperiences:    this.projectExperiences,
        prices:                this.prices,
        blockOrder:            this.blockOrder,
        config:                this.config,
      }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Create customized resume
    // ─────────────────────────────────────────────────────────────────────────

    openCreateDialog() {
      this.createForm = { title: '', jobId: null, copyFromMain: true }
      this.showCreateDialog = true
    },

    async doCreateResume() {
      const title = this.createForm.title.trim()
      if (!title) { alert('请填写简历名称'); return }
      this.creating = true
      try {
        // 若勾选从主简历复制，先获取主简历内容随创建请求一起发送，避免后端空内容校验失败
        let initialContent = {}
        if (this.createForm.copyFromMain) {
          try {
            const mainRes = await getMainResume()
            initialContent = mainRes.content || {}
          } catch (e) {
            alert('获取主简历失败，请先完善主简历再创建定制简历')
            this.creating = false
            return
          }
        }

        const res = await createResume({
          title,
          isMain: false,
          jobId: this.createForm.jobId || null,
          content: initialContent,
        })
        const newResume = res
        this.resumeList.push({
          id: newResume.id,
          title: newResume.title,
          isMain: false,
          jobId: newResume.jobId,
          jobName: newResume.jobName,
        })
        if (this.createForm.copyFromMain) {
          localStorage.setItem(AUTOFILL_SEEN_KEY + newResume.id, '1')
        }
        this.showCreateDialog = false
        await this.loadResumeContent(newResume.id)
      } catch (e) {
        alert(e?.response?.data?.message || e?.message || '创建失败，请先完善主简历的姓名、性别、手机、邮箱和教育经历')
      } finally {
        this.creating = false
      }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Auto-fill prompt (shown when opening empty customized resume)
    // ─────────────────────────────────────────────────────────────────────────

    async doAutoFill() {
      this.autoFilling = true
      try {
        const res = await copyFromMain(this.currentResumeId)
        const resume = res
        this.applyContent(resume.content || emptyContent())
        this.saveState = 'saved'
        localStorage.setItem(AUTOFILL_SEEN_KEY + this.currentResumeId, '1')
        this.showAutoFillPrompt = false
      } catch (e) {
        alert(e?.message || '导入失败，主简历可能尚未填写内容')
        this.showAutoFillPrompt = false
      } finally {
        this.autoFilling = false
      }
    },

    dismissAutoFillPrompt() {
      localStorage.setItem(AUTOFILL_SEEN_KEY + this.currentResumeId, '1')
      this.showAutoFillPrompt = false
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Delete resume
    // ─────────────────────────────────────────────────────────────────────────

    confirmDeleteResume(resume) {
      this.deleteTarget = resume
      this.showDeleteConfirm = true
    },

    async doDeleteResume() {
      if (!this.deleteTarget) return
      this.deleting = true
      try {
        await deleteResume(this.deleteTarget.id)
        this.resumeList = this.resumeList.filter(r => r.id !== this.deleteTarget.id)
        this.showDeleteConfirm = false

        // If we deleted the current resume, switch to main
        if (this.currentResumeId === this.deleteTarget.id) {
          const main = this.resumeList.find(r => r.isMain)
          if (main) await this.loadResumeContent(main.id)
        }
        this.deleteTarget = null
      } catch (e) {
        alert(e?.message || '删除失败')
      } finally {
        this.deleting = false
      }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Save
    // ─────────────────────────────────────────────────────────────────────────

    onContentChange() {
      if (this.saveState === 'saving') return
      this.saveState = 'unsaved'
      clearTimeout(this.autoSaveTimer)
      this.autoSaveTimer = setTimeout(() => this.doSave(), 2500)
    },

    async autoSaveTitle() {
      if (!this.currentResumeId || !this.resumeTitle.trim()) return
      try {
        await updateResume(this.currentResumeId, { title: this.resumeTitle.trim() })
        const r = this.resumeList.find(r => r.id === this.currentResumeId)
        if (r) r.title = this.resumeTitle.trim()
      } catch (e) {
        console.warn('标题保存失败', e)
      }
    },

    async manualSave() {
      clearTimeout(this.autoSaveTimer)
      this.autoSaveTimer = null 
      await this.doSave()
    },

    async doSave() {
      if (!this.currentResumeId) return
      this.saveState = 'saving'
      try {
        await updateResume(this.currentResumeId, {
          title: this.resumeTitle,
          content: this.buildContent(),
        })
        this.saveState = 'saved'
      } catch (e) {
        console.error('保存失败', e)
        this.saveState = 'error'
        // 提取后端返回的具体校验错误信息（如"姓名为必填项"）
        const errMsg = e?.response?.data?.message || e?.response?.data?.msg || e?.message || '保存失败'
        // 仅手动保存时弹出提示，自动保存静默处理
        if (!this.autoSaveTimer) {
          alert('保存失败：' + errMsg)
        }
        localStorage.setItem(LOCAL_KEY + this.currentResumeId, JSON.stringify(this.buildContent()))
      }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Block drag-and-drop
    // ─────────────────────────────────────────────────────────────────────────

    dragStart(index) { this.dragIndex = index },
    dragOver(index)  { this.overIndex = index },
    dragEnd()        { this.dragIndex = -1; this.overIndex = -1 },
    drop(index) {
      if (this.dragIndex < 0 || this.dragIndex === index) return
      const order = [...this.blockOrder]
      const [moved] = order.splice(this.dragIndex, 1)
      order.splice(index, 0, moved)
      this.blockOrder = order
      this.dragIndex = -1
      this.overIndex = -1
    },

    confirmDelete(index) {
      if (confirm('确认删除本模块？')) this.blockOrder.splice(index, 1)
    },

    ensureBlockVisible(type) {
      if (!this.blockOrder.includes(type)) this.blockOrder.push(type)
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Section CRUD helpers
    // ─────────────────────────────────────────────────────────────────────────

    addEducation() {
      const id = Math.max(0, ...this.education.map(i => i.id)) + 1
      this.education.push({ id, start: '', end: '', school: '', major: '', degree: '' })
      this.ensureBlockVisible('education')
    },
    removeEducation(idx) { this.education.splice(idx, 1) },

    addSkill() {
      const id = Math.max(0, ...this.skills.map(i => i.id)) + 1
      this.skills.push({ id, name: '' })
      this.ensureBlockVisible('skills')
    },
    addSkillAt(idx) { this.skills.splice(idx + 1, 0, { id: Date.now(), name: '' }) },
    removeSkill(idx) { this.skills.splice(idx, 1) },

    addCampusExperience() {
      this.campusExperiences.push({ id: Date.now(), start: '', end: '', title: '', description: '', achievements: '' })
      this.ensureBlockVisible('campus')
    },
    removeCampusExperience(idx) { this.campusExperiences.splice(idx, 1) },

    addInternshipExperience() {
      this.internshipExperiences.push({ id: Date.now(), start: '', end: '', place: '', title: '', description: '', achievements: '' })
      this.ensureBlockVisible('internship')
    },
    removeInternshipExperience(idx) { this.internshipExperiences.splice(idx, 1) },

    addWorkExperience() {
      this.workExperiences.push({ id: Date.now(), start: '', end: '', company: '', role: '', description: '', achievements: '' })
      this.ensureBlockVisible('work')
    },
    removeWorkExperience(idx) { this.workExperiences.splice(idx, 1) },

    renderDetailText(item, defaultText) {
      const detail = item.description?.trim() || defaultText
      const achievement = item.achievements?.trim()
      if (achievement) {
        return `${detail}；${achievement}`
      }
      return detail
    },

    addPrice() {
      this.prices.push({ id: Date.now(), award: '', period: '', level: '' })
      this.ensureBlockVisible('prices')
    },
    removePrice(idx) { this.prices.splice(idx, 1) },

    // ─────────────────────────────────────────────────────────────────────────
    // Avatar
    // ─────────────────────────────────────────────────────────────────────────

    triggerAvatarInput() { this.$refs.avatarInput.click() },
    // 头像上传
    async onAvatarChange(e) {
      const file = e.target.files[0]
      if (!file) return

      // 校验
      if (!file.type.startsWith('image/')) {
        alert('请选择图片文件')
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        alert('图片不能超过 5MB')
        return
      }

      try {
        const formData = new FormData()
        formData.append('avatar', file)

        // 直接使用 request，走你统一的拦截器（自动带token）
        const res = await request({
          url: 'resumes/avatar/upload',    // 归属于简历接口
          method: 'post',
          data: formData,
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        // 把返回的URL存入简历数据
        this.personal.avatar = res.url
      } catch (err) {
        console.error('头像上传失败', err)
        alert('头像上传失败：' + err.message)
      }
    },
    // ─────────────────────────────────────────────────────────────────────────
    // Misc
    // ─────────────────────────────────────────────────────────────────────────

    resetData() {
      if (!confirm('确认重置所有内容吗？此操作会清空当前简历内容。')) return
      this.applyContent(emptyContent())
      this.saveState = 'unsaved'
    },

    togglePanel() { this.panelOpen = !this.panelOpen },

    goBack() { window.history.back() },

    async exportPdf() {
      const el = document.getElementById('resume-preview')
      if (!el) return
      const canvas = await html2canvas(el, { scale: 2, useCORS: true })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4')
      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const imgProps = pdf.getImageProperties(imgData)
      const ratio = Math.min(pageWidth / imgProps.width, pageHeight / imgProps.height)
      const imgWidth = imgProps.width * ratio
      const imgHeight = imgProps.height * ratio
      pdf.addImage(imgData, 'PNG', (pageWidth - imgWidth) / 2, 10, imgWidth, imgHeight)
      pdf.save(`${this.resumeTitle || 'resume'}.pdf`)
    },
  },

  beforeUnmount() {
    clearTimeout(this.autoSaveTimer)
  },
}
</script>

<style scoped>
/* ── Page layout ───────────────────────────────────────────────────────────── */
.resume-builder-page {
  display: flex;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 60px);
  background: #f2f3f7;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

/* ── Left panel ────────────────────────────────────────────────────────────── */
.builder-left-panel {
  width: 35%;
  max-width: 540px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e7ef;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.25s ease;
  z-index: 10;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* ── Panel header / resume tabs ────────────────────────────────────────────── */
.builder-panel-header {
  padding: 12px 14px 0;
  border-bottom: 1px solid #eef0f5;
  background: #fafbff;
  border-radius: 12px 12px 0 0;
}

.resume-tabs-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.resume-tabs-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  flex: 1;
  padding-bottom: 2px;
}
.resume-tabs-scroll::-webkit-scrollbar { display: none }

.resume-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 20px;
  border: 1px solid #dde1f0;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  color: #555;
  transition: all 0.15s;
}
.resume-tab:hover { border-color: #7c56ff; color: #7c56ff; }
.resume-tab.active {
  background: #7c56ff;
  border-color: #7c56ff;
  color: #fff;
  font-weight: 600;
}
.tab-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #aaa;
  flex-shrink: 0;
}
.tab-dot.main { background: #f59e0b; }
.resume-tab.active .tab-dot { background: rgba(255,255,255,0.7); }
.tab-label { max-width: 80px; overflow: hidden; text-overflow: ellipsis; }
.tab-close {
  font-size: 10px;
  opacity: 0.6;
  padding: 1px 3px;
  border-radius: 3px;
}
.tab-close:hover { opacity: 1; background: rgba(255,255,255,0.2); }

.tab-add-btn {
  flex-shrink: 0;
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 1.5px dashed #7c56ff;
  background: none;
  color: #7c56ff;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}
.tab-add-btn:hover { background: #ede9ff; }

/* ── Resume title row ─────────────────────────────────────────────────────── */
.resume-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
}
.resume-title-input {
  flex: 1;
  border: 1px solid #e2e5ef;
  border-radius: 6px;
  padding: 5px 9px;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  background: #fff;
}
.resume-title-input:focus { border-color: #7c56ff; outline: none; }

.save-indicator {
  font-size: 11px;
  white-space: nowrap;
  font-weight: 500;
}
.save-indicator.saved   { color: #10b981; }
.save-indicator.unsaved { color: #f59e0b; }
.save-indicator.saving  { color: #6b7280; }
.save-indicator.error   { color: #ef4444; }

/* ── Panel body (scrollable) ──────────────────────────────────────────────── */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

/* ── Module tabs ──────────────────────────────────────────────────────────── */
.module-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.module-tabs button {
  padding: 5px 10px;
  border: 1px solid #dde1f0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  color: #555;
  transition: all 0.15s;
}
.module-tabs button.active {
  background: #7c56ff;
  border-color: #7c56ff;
  color: #fff;
}

/* ── Section config card ──────────────────────────────────────────────────── */
.section-config {
  margin-bottom: 14px;
  border: 1px solid #eef0f5;
  padding: 12px;
  border-radius: 8px;
  background: #fafbff;
}
.section-config h3 {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.section-config .row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 6px;
}
.section-config .row label {
  width: 90px;
  font-size: 12px;
  color: #555;
  flex-shrink: 0;
}
.section-config .row input,
.section-config .row select,
.section-config .row textarea {
  flex: 1;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 5px 7px;
  font-size: 13px;
}
.section-config .row textarea { resize: vertical; }

.char-count, .content-count {
  font-size: 11px;
  color: #999;
  margin-left: 4px;
  white-space: nowrap;
}

/* ── Entry editor ─────────────────────────────────────────────────────────── */
.entry-editor {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
}
.entry-editor hr { border: none; border-top: 1px dashed #eee; margin: 8px 0 4px; }

/* ── Skill row ────────────────────────────────────────────────────────────── */
.skill-row {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}
.skill-row input { flex: 1; border: 1px solid #d9d9d9; border-radius: 4px; padding: 5px 7px; font-size: 13px; }

/* ── Action footer ────────────────────────────────────────────────────────── */
.action-footer {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.btn-action {
  border: 1px solid #ccc;
  background: #fff;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
.btn-action:hover { background: #f0eeff; border-color: #7c56ff; color: #7c56ff; }
.btn-save {
  background: #7c56ff;
  color: #fff;
  border-color: #7c56ff;
}
.btn-save:hover { background: #6c42ee; }
.btn-save:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-success {
  background: #10b981;
  color: #fff;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-danger {
  background: #fff;
  color: #ef4444;
  border: 1px solid #fecaca;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

/* ── Right main preview ───────────────────────────────────────────────────── */
.builder-main {
  flex: 1;
  padding: 0 4px;
  overflow: auto;
  position: relative;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.preview-header h2 {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}
.preview-badge {
  font-size: 12px;
  background: #ede9ff;
  color: #6d3aee;
  border-radius: 12px;
  padding: 3px 10px;
  font-weight: 500;
}

.resume-preview {
  min-height: 84vh;
  border: 1px solid #c2c2c2;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border-radius: 8px;
  max-width: calc(210mm + 40px);
  margin: 0 auto;
  padding: 20px;
}

.a4-paper {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  padding: 20px;
  background: #fff;
  border: 1px solid #d8d8d8;
  box-shadow: 0 0 10px rgba(0,0,0,0.06);
}

/* ── Resume block ─────────────────────────────────────────────────────────── */
.resume-block {
  padding: 12px;
  margin-bottom: 10px;
  background: #fff;
  border-radius: 6px;
  position: relative;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.resume-block:hover { border-color: #92b8ff; }
.resume-block.dragging { opacity: 0.4; border: 2px dashed #7c6ae8; }
.resume-block.drag-over { border: 2px dashed #519df2; }

.block-handle {
  position: absolute;
  left: -18px;
  top: 12px;
  cursor: grab;
  color: #bbb;
  font-size: 14px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.section-title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 10px;
}
.section-title h3 { margin: 0 0 4px; font-size: 16px; font-weight: 700; }
.section-underline {
  width: 150px; height: 3px;
  background: #4a2e8b;
  opacity: 0.35;
}
.section-underline-light {
  width: 100%; height: 1px;
  background: #ddd;
  margin-top: 2px;
}

.delete-btn {
  border: 1px solid #ff7e7e;
  background: #fff5f5;
  color: #d94646;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.block-content {
  margin-top: 4px;
  white-space: pre-wrap;
  font-size: 13px;
}

/* ── Preview inner elements ───────────────────────────────────────────────── */
.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}
.profile-avatar-box {
  width: 90px; height: 110px;
  border: 1px solid #f3f3f3;
  background: #f3f3f3;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}
.profile-avatar { width: 100%; height: 100%; object-fit: cover; }
.profile-avatar-placeholder { color: #aaa; font-size: 12px; }
.profile-info-inline {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.profile-info-inline h2 { margin: 0; font-size: 22px; color: #1f1f1f; }
.label-row { display: flex; gap: 14px; font-size: 13px; color: #555; }

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 6px 16px;
  font-size: 13px;
  color: #4a4a4a;
}

.experience-list { display: flex; flex-direction: column; gap: 10px; }
.experience-item { padding: 8px; border-left: 3px solid #7c56ff; background: #fafbff; border-radius: 0 6px 6px 0; }
.experience-item p { margin: 4px 0 0; font-size: 13px; color: #555; }

/* ── Float buttons ────────────────────────────────────────────────────────── */
.float-btn {
  position: fixed;
  right: 20px;
  bottom: 20px;
  height: 40px;
  padding: 0 16px;
  border-radius: 20px;
  border: none;
  background: #7c56ff;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(124, 86, 255, 0.35);
  transition: opacity 0.15s;
}
.float-btn:hover { opacity: 0.88; }
.float-btn.switch { bottom: 70px; }

/* ── Modals ───────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.modal-overlay--center { align-items: center; padding: 16px; }

.modal-sheet {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
}
.modal-sheet--sm2 { max-width: 420px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #f0f0f0;
}
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #222; }
.modal-close {
  width: 26px; height: 26px;
  border-radius: 50%;
  background: #f3f4f6;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #666;
}
.modal-close:hover { background: #e5e7eb; }

.modal-body {
  padding: 18px 20px;
}
.modal-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px 18px;
  border-top: 1px solid #f0f0f0;
}

.form-group { margin-bottom: 14px; }
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.form-control {
  width: 100%;
  border: 1px solid #dde1f0;
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 14px;
  box-sizing: border-box;
}
.form-control:focus { border-color: #7c56ff; outline: none; }

/* ── Auto-fill toggle ─────────────────────────────────────────────────────── */
.autofill-toggle {
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}
.toggle-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
}
.toggle-label input[type=checkbox] { margin-top: 3px; accent-color: #7c56ff; }
.toggle-text { display: flex; flex-direction: column; gap: 2px; }
.toggle-text strong { font-size: 14px; color: #333; }
.toggle-text small { font-size: 12px; color: #777; }
.autofill-hint { font-size: 12px; color: #6d3aee; background: #f0ebff; border-radius: 6px; padding: 8px 10px; margin: 0; }

/* ── Auto-fill prompt ─────────────────────────────────────────────────────── */
.autofill-desc { font-size: 14px; color: #333; line-height: 1.6; margin: 0 0 8px; }
.autofill-note { font-size: 12px; color: #888; margin: 0; }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.btn {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost { background: #f3f4f6; color: #555; border: 1px solid #e0e0e0; }
.btn-ghost:hover { background: #e9eaf0; }
.btn-primary { background: #7c56ff; color: #fff; }
.btn-primary:hover { background: #6c42ee; }
.btn-danger-solid { background: #ef4444; color: #fff; }
.btn-danger-solid:hover { background: #dc2626; }

.btn-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.btn-spinner--dark {
  border-color: rgba(239,68,68,0.3);
  border-top-color: #ef4444;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Avatar upload ────────────────────────────────────────────────────────── */
.avatar-row { align-items: flex-start !important; }
.avatar-upload {
  width: 76px; height: 76px;
  border: 1.5px dashed #bbb;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: #999;
  border-radius: 6px;
  overflow: hidden;
  font-size: 22px;
}
.avatar-upload img { width: 100%; height: 100%; object-fit: cover; }

/* ── Global loading overlay ───────────────────────────────────────────────── */
.global-loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255,255,255,0.7);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.loading-card {
  background: #fff;
  border-radius: 14px;
  padding: 28px 36px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.loading-card p { margin: 0; font-size: 14px; color: #555; }
.loading-spinner-lg {
  width: 36px; height: 36px;
  border: 3px solid #ede9ff;
  border-top-color: #7c56ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Modal transition ─────────────────────────────────────────────────────── */
.modal-enter-active { animation: modalFadeIn 0.25s ease both; }
.modal-leave-active { animation: modalFadeOut 0.2s ease both; }
@keyframes modalFadeIn  { from { opacity: 0; } to { opacity: 1; } }
@keyframes modalFadeOut { from { opacity: 1; } to { opacity: 0; } }

.fade-enter-active { transition: opacity 0.2s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }


/* ── Required fields bar ──────────────────────────────────────────────────── */
.required-bar {
  margin: 8px 0 4px;
  padding: 8px 12px 10px;
  background: #fff8f0;
  border: 1px solid #fde8c8;
  border-radius: 8px;
}
.required-bar--done {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #16a34a;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 12px;
  border-radius: 8px;
  margin: 8px 0 4px;
}
.required-bar-title {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #b45309;
  margin-bottom: 6px;
  letter-spacing: 0.03em;
}
.required-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.required-tag {
  padding: 3px 10px;
  border-radius: 20px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  line-height: 1.6;
}
.required-tag:hover {
  background: #fde68a;
  transform: translateY(-1px);
}

/* ── Required field indicators ───────────────────────────────────────────── */
.req-star {
  color: #ef4444;
  font-size: 13px;
  margin-left: 2px;
}
.input-required {
  border-color: #fca5a5 !important;
  background: #fff9f9 !important;
}
.input-required:focus {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15);
}
</style>