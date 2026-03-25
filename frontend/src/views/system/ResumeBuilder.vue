<template>
  <div class="resume-builder-page">
    <aside class="builder-left-panel" :class="{ open: panelOpen }">
      <div class="builder-panel-header">
        <h2>简历编辑</h2>
      </div>

      <div v-if="panelOpen" class="panel-body">
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
            <label>姓名</label>
            <input v-model="personal.name" type="text" placeholder="输入你的真实姓名" maxlength="20" />
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
            <label>联系方式</label>
            <input v-model="personal.contact" type="text" placeholder="手机号" />
          </div>
        </section>

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

        <section class="section-config" v-else-if="activeSection === 'education'">
          <h3>教育背景</h3>
          <div
            class="entry-editor"
            v-for="(item, idx) in education"
            :key="item.id"
          >
            <div class="row"><label>起止时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>学校名称</label><input v-model="item.school" type="text" maxlength="40" /><span class="char-count">{{ item.school.length }}/40</span></div>
            <div class="row"><label>专业名称</label><input v-model="item.major" type="text" maxlength="20" /><span class="char-count">{{ item.major.length }}/20</span></div>
            <div class="row"><label>学历学位</label><input v-model="item.degree" type="text" maxlength="20" /></div>
            <button class="btn-danger" v-if="education.length>1" @click="removeEducation(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addEducation">添加学历</button>
        </section>

        <section class="section-config" v-else-if="activeSection === 'prices'">
          <h3>荣誉奖项</h3>
          <div class="entry-editor" v-for="(item, idx) in prices" :key="item.id">
            <div class="row"><label>获奖名称</label><input v-model="item.award" type="text" maxlength="50" /></div>
            <div class="row"><label>获奖时间</label><input v-model="item.period" type="date" maxlength="30" placeholder="2025.06" /></div>
            <div class="row"><label>获奖等级</label><input v-model="item.level" type="text" maxlength="20" placeholder="一等奖" /></div>
            <button class="btn-danger" v-if="prices.length>1" @click="removePrice(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addPrice">添加奖项</button>
        </section>

        <section class="section-config" v-else-if="activeSection === 'skills'">
          <h3>技能特长</h3>
          <div class="skill-row" v-for="(item, idx) in skills" :key="item.id">
            <input v-model="item.name" placeholder="熟练掌握该项技术" maxlength="40" />
            <button class="btn-danger" @click="removeSkill(idx)">-</button>
            <button class="btn-success" @click="addSkillAt(idx)">+</button>
          </div>
          <button class="btn-success" @click="addSkill">添加技能</button>
        </section>

        <section class="section-config" v-else-if="activeSection === 'experience'">
          <h3>校园经历</h3>
          <div class="entry-editor" v-for="(item, idx) in campusExperiences" :key="item.id">
            <div class="row"><label>起止时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>经历名称</label><input v-model="item.title" type="text" /></div>
            <div class="row"><label>详情描述</label><textarea v-model="item.description" rows="3"></textarea></div>
            <button class="btn-danger" v-if="campusExperiences.length>1" @click="removeCampusExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addCampusExperience">添加经历</button>

          <h3>实习经历</h3>
          <div class="entry-editor" v-for="(item, idx) in internshipExperiences" :key="item.id">
            <div class="row"><label>起止时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>实习公司</label><input v-model="item.place" type="text" /></div>
            <div class="row"><label>实习岗位</label><input v-model="item.title" type="text" /></div>
            <div class="row"><label>详情描述</label><textarea v-model="item.description" rows="3"></textarea></div>
            <button class="btn-danger" v-if="internshipExperiences.length>1" @click="removeInternshipExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addInternshipExperience">添加经历</button>

          <h3>工作经验</h3>
          <div class="entry-editor" v-for="(item, idx) in workExperiences" :key="item.id">
            <div class="row"><label>时间</label><input v-model="item.start" type="date" /><span>至</span><input v-model="item.end" type="date" /></div>
            <div class="row"><label>公司名称</label><input v-model="item.company" type="text" maxlength="35" /><span class="char-count">{{ item.company.length }}/35</span></div>
            <div class="row"><label>主要职责</label><input v-model="item.role" type="text" maxlength="35" /><span class="char-count">{{ item.role.length }}/35</span></div>
            <div class="row"><label>工作内容</label><textarea v-model="item.description" rows="4" maxlength="200"></textarea></div>
            <div class="content-count">{{ item.description.length }}/200</div>
            <button class="btn-danger" v-if="workExperiences.length>1" @click="removeWorkExperience(idx)">删除</button>
            <hr />
          </div>
          <button class="btn-success" @click="addWorkExperience">添加经历</button>
        </section>

        <section class="section-config action-footer">
          <button class="btn-action" @click="resetData">重置</button>
          <button class="btn-action" @click="saveData">保存</button>
          <button class="btn-action" @click="exportPdf">导出 PDF</button>
        </section>
      </div>
    </aside>

    <main class="builder-main">
      <div class="preview-header">
        <h2>简历预览</h2>
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
            <div class="block-handle"></div>
            <div class="block-head">
              <div class="section-title" v-if="block.type !== 'profile'">
                <h3 :style="{ color: config.titleColor }">{{ block.title }}</h3>
                <span class="section-underline"></span>
                <span class="section-underline-light"></span>
              </div>
              <button class="delete-btn" v-if="block.type !== 'profile'" v-show="hoverIndex === index" @click="confirmDelete(index)">🗑</button>
            </div>

            <div class="block-content" :style="{ color: config.bodyColor }">
              <template v-if="block.type === 'profile'">
                <div class="profile-row">
                  <div class="profile-avatar-box">
                    <img v-if="personal.avatar" class="profile-avatar" :src="personal.avatar" alt="证件照" />
                    <div v-else class="profile-avatar-placeholder">证件照</div>
                  </div>
                  <div class="profile-info-inline">
                    <h2>{{personal.name||"未设置"}}</h2>
                    <div class="label-row"><span>年龄：{{ personal.age || "未设置" }} 岁</span><span>籍贯：{{personal.address||未设置}}</span></div>
                    <div class="label-row"><span>工作经验：{{ personal.experience || 0 }} 年经验</span><span>联系方式：{{ personal.contact || '未设置' }}</span></div>
                  </div>
                </div>
              </template>

              <template v-else-if="block.type === 'objective'">
                <div class="info-grid">
                  <div>求职类型：{{ objective.jobType || '未设置' }}</div>
                  <div>意向岗位：{{ objective.position || '未设置' }}</div>
                  <div>意向城市：{{ objective.city || '未设置' }}</div>
                  <div>到岗时间：{{ objective.status || '未设置' }}</div>
                </div>
              </template>

              <template v-else-if="block.type === 'education'">
                <div class="experience-list">
                  <div v-for="item in education" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '未设置' }} - {{ item.end || '未设置' }}</div>
                      <div>学校：{{ item.school || '未设置' }}</div>
                      <div>专业：{{ item.major || '未设置' }}</div>
                      <div>学历学位：{{ item.degree || '未设置' }}</div>
                    </div>
                  </div>
                </div>
              </template>
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
                    <div>获奖名称：未设置</div>
                    <div>时间：未设置</div>
                    <div>等级：未设置</div>
                  </div>
                </div>
              </template>

              <template v-else-if="block.type === 'skills'">
                <p>{{ skills.length ? skills.map(s => s.name).filter(Boolean).join('，') : '熟练掌握该项技术' }}</p>
              </template>

              <template v-else-if="block.type === 'campus'">
                <div v-if="campusExperiences.length" class="experience-list">
                  <div v-for="item in campusExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '起止时间' }} - {{ item.end || '起止时间' }}</div>
                      <div>经历简要：{{ item.title || '如社团名称' }}</div>
                      <div>主要职责：{{ item.description || '如岗位职责描述' }}</div>
                    </div>
                    <p>经历描述：{{ item.description || '经历经历描述...' }}</p>
                  </div>
                </div>
                <div v-else class="experience-item">
                  <div class="info-grid">
                    <div>时间：起止时间</div>
                    <div>经历简要：如社团名称</div>
                    <div>主要职责：如岗位职责描述</div>
                  </div>
                  <p>经历描述：经历经历描述...</p>
                </div>
              </template>

              <template v-else-if="block.type === 'internship'">
                <div v-if="internshipExperiences.length" class="experience-list">
                  <div v-for="item in internshipExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.period || '起止时间' }}</div>
                      <div>公司：{{ item.place || '实习公司' }}</div>
                      <div>岗位：{{ item.title || '实习岗位' }}</div>
                    </div>
                    <p>实习内容：{{ item.description || '主要工作内容是打杂...' }}</p>
                  </div>
                </div>
                <div v-else class="experience-item">
                  <div class="info-grid">
                    <div>时间：起止时间</div>
                    <div>公司：公司名称</div>
                    <div>岗位：岗位名称</div>
                  </div>
                  <p>实习内容：主要工作内容是打杂...</p>
                </div>
              </template>

              <template v-else-if="block.type === 'work'">
                <div v-if="workExperiences.length" class="experience-list">
                  <div v-for="item in workExperiences" :key="item.id" class="experience-item">
                    <div class="info-grid">
                      <div>时间：{{ item.start || '起' }} - {{ item.end || '止' }}</div>
                      <div>公司：{{ item.company || '公司名称' }}</div>
                      <div>岗位：{{ item.role || '岗位名称' }}</div>
                    </div>
                    <p>工作内容：{{ item.description || '工作内容...' }}</p>
                  </div>
                </div>
                <div v-else class="experience-item">
                  <div class="info-grid">
                    <div>时间：起止时间</div>
                    <div>公司：公司名称</div>
                    <div>岗位：岗位名称</div>
                  </div>
                  <p>工作内容：工作内容...</p>
                </div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <button class="float-btn" @click="goBack">← 返回</button>
      <button class="float-btn switch" @click="togglePanel">⇆ 切换</button>
    </main>
  </div>
</template>

<script>
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

const STORAGE_KEY = 'resumeBuilderState'

export default {
  name: 'ResumeBuilder',
  data() {
    return {
      panelOpen: true,
      activeSection: 'personal',
      resumeName: '我的简历',
      modules: [
        { key: 'personal', label: '个人信息' },
        { key: 'objective', label: '求职意向' },
        { key: 'education', label: '教育背景' },
        { key: 'experience', label: '经历与经验' },
        { key: 'prices', label: '荣誉奖项' },
        { key: 'skills', label: '技能特长' }
      ],
      prices: [
        { id: 1, award: '', period: '', level: '' }
      ],
      blockOrder: ['profile', 'objective', 'education', 'campus', 'internship', 'work', 'project','prices','skills'],
      dragIndex: -1,
      overIndex: -1,
      hoverIndex: -1,
      personal: {
        name: '代易函',
        age: 22,
        experience: 0,
        email: 'zijia@example.com',
        avatar: 'https://i.pravatar.cc/150?img=47',
        address: '北京市',
        contact: '18954600198',
        summary: '专注前端研发，擅长组件化与性能优化。'
      },
      objective: {
        jobType: '实习',
        position: '软件工程师',
        city: '北京',
        salary: '',
        status: ''
      },
      education: [
        { id: 1, start: '2015-05', end: '2019-06', school: '小聚大学', major: '通信工程', degree: '本科' }
      ],
      skills: [
        { id: 1, name: 'JavaScript' }
      ],
      campusExperiences: [],
      internshipExperiences: [],
      workExperiences: [
        {
          id: 1,
          start: '2021-09',
          end: '2022-10',
          company: '业绩公司',
          role: '前端开发工程师',
          description: '参与核心产品页面开发；负责数据展示与组件重构；协助优化整体交互与性能。'
        }
      ],
      config: {
        titleColor: '#2B2B2B',
        bodyColor: '#4F4F4F',
        fontSize: 14,
        padding: 20,
        templateId: 'classic'
      }
    }
  },
  computed: {
    previewStyles() {
      return {
        padding: `${this.config.padding}px`,
        fontSize: `${this.config.fontSize}px`,
        fontFamily: '微软雅黑, PingFang SC, sans-serif',
        background: '#fff',
        borderColor: '#c2c2c2'
      }
    },
    visibleBlocks() {
      return this.blockOrder.map(key => {
        switch (key) {
          case 'profile':
            return { id: key, type: 'profile', title: '个人信息' }
          case 'objective':
            return { id: key, type: 'objective', title: '求职意向' }
          case 'education':
            return { id: key, type: 'education', title: '教育背景' }
          case 'skills':
            return { id: key, type: 'skills', title: '技能特长' }
          case 'prices':
            return { id: key, type: 'prices', title: '荣誉奖项' }
          case 'campus':
            return { id: key, type: 'campus', title: '校园经历' }
          case 'internship':
            return { id: key, type: 'internship', title: '实习经验' }
          case 'work':
            return { id: key, type: 'work', title: '工作经验' }
          case 'prices':
            return { id: key, type: 'prices', title: '荣誉奖项' }
          case 'project':
            return { id: key, type: 'project', title: '项目经验' }
          default:
            return { id: key, type: key, title: '未知模块' }
        }
      })
    }
  },
  created() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      try {
        const parsed = JSON.parse(raw)
        if (parsed) {
          Object.assign(this, parsed)
        }
      } catch (e) {
        console.warn('恢复布局失败', e)
      }
    }
  },
  watch: {
    personal: {
      handler() { this.persistState() },
      deep: true
    },
    objective: {
      handler() { this.persistState() },
      deep: true
    },
    prices:{
      handler() { this.persistState() },
      deep: true
    },
    education: {
      handler() { this.persistState() },
      deep: true
    },
    skills: {
      handler() { this.persistState() },
      deep: true
    },
    campusExperiences: {
      handler() { this.persistState() },
      deep: true
    },
    internshipExperiences: {
      handler() { this.persistState() },
      deep: true
    },
    workExperiences: {
      handler() { this.persistState() },
      deep: true
    },
    activeSection(newSection) {
      const sectionToBlockType = {
        personal: 'profile',
        objective: 'objective',
        education: 'education',
        skills: 'skills',
        experience: 'campus',
        prices:'prices'
      }
      const blockType = sectionToBlockType[newSection]
      if (blockType) {
        this.ensureBlockVisible(blockType)
      }
    },
    resumeName() {
      this.persistState()
    }
  },
  methods: {
    persistState() {
      const payload = {
        panelOpen: this.panelOpen,
        activeSection: this.activeSection,
        resumeName: this.resumeName,
        personal: this.personal,
        prices: this.prices,
        objective: this.objective,
        education: this.education,
        skills: this.skills,
        campusExperiences: this.campusExperiences,
        internshipExperiences: this.internshipExperiences,
        workExperiences: this.workExperiences,
        blockOrder: this.blockOrder,
        config: this.config
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    },
    dragStart(index) {
      this.dragIndex = index
    },
    dragOver(index) {
      this.overIndex = index
    },
    dragEnd() {
      this.dragIndex = -1
      this.overIndex = -1
    },
    drop(index) {
      if (this.dragIndex < 0 || this.dragIndex === index) return
      const newOrder = [...this.blockOrder]
      const [moved] = newOrder.splice(this.dragIndex, 1)
      newOrder.splice(index, 0, moved)
      this.blockOrder = newOrder
      this.dragIndex = -1
      this.overIndex = -1
      this.persistState()
    },
    confirmDelete(index) {
      if (confirm('确认删除本模块？')) {
        this.blockOrder.splice(index, 1)
        this.persistState()
      }
    },
    triggerAvatarInput() {
      this.$refs.avatarInput.click()
    },
    onAvatarChange(e) {
      const file = e.target.files[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = () => {
        this.personal.avatar = reader.result
      }
      reader.readAsDataURL(file)
    },
    addEducation() {
      const nextId = Math.max(0, ...this.education.map(item => item.id)) + 1
      this.education.push({ id: nextId, start: '', end: '', school: '', major: '', degree: '' })
      this.ensureBlockVisible('education')
    },
    removeEducation(index) {
      this.education.splice(index, 1)
    },
    addSkill() {
      const nextId = Math.max(0, ...this.skills.map(item => item.id)) + 1
      this.skills.push({ id: nextId, name: '' })
      this.ensureBlockVisible('skills')
    },
    addSkillAt(index) {
      this.skills.splice(index + 1, 0, { id: Date.now(), name: '' })
    },
    removeSkill(index) {
      this.skills.splice(index, 1)
    },
    ensureBlockVisible(type) {
      if (!this.blockOrder.includes(type)) {
        this.blockOrder.push(type)
        this.persistState()
      }
    },
    addCampusExperience() {
      this.campusExperiences.push({ id: Date.now(), start: '', end: '', title: '', description: '' })
      this.ensureBlockVisible('campus')
    },
    removeCampusExperience(index) {
      this.campusExperiences.splice(index, 1)
    },
    addInternshipExperience() {
      this.internshipExperiences.push({ id: Date.now(), start: '', end: '', place: '', title: '', description: '' })
      this.ensureBlockVisible('internship')
    },
    removeInternshipExperience(index) {
      this.internshipExperiences.splice(index, 1)
    },
    addWorkExperience() {
      this.workExperiences.push({ id: Date.now(), start: '', end: '', company: '', role: '', description: '' })
      this.ensureBlockVisible('work')
    },
    removeWorkExperience(index) {
      this.workExperiences.splice(index, 1)
    },
    addPrice() {
      this.prices.push({ id: Date.now(), award: '', period: '', level: '' })
      this.ensureBlockVisible('prices')
    },
    removePrice(index) {
      this.prices.splice(index, 1)
    },
    removeInternshipExperience(index) {
      this.internshipExperiences.splice(index, 1)
    },
    addWorkExperience() {
      this.workExperiences.push({ id: Date.now(), start: '', end: '', company: '', role: '', description: '' })
      this.ensureBlockVisible('work')
    },
    removeWorkExperience(index) {
      this.workExperiences.splice(index, 1)
    },
    resetData() {
      if (confirm('确认重置所有内容吗？')) {
        this.resumeName = '我的简历'
        this.personal = { name: '', age: 0, experience: 0, email: '', avatar: '', address: '', contact: '', summary: '' }
        this.objective = { jobType: '实习', position: '', city: '北京', salary: '', status: '' }
        this.education = [{ id: 1, start: '2015-05', end: '2019-06', school: '小聚大学', major: '通信工程', degree: '本科' }]
        this.skills = [{ id: 1, name: '' }]
        this.campusExperiences = []
        this.internshipExperiences = []
        this.workExperiences = [{ id: 1, start: '2021-09', end: '2022-10', company: '业绩公司', role: '前端开发工程师', description: '' }]
        this.config = { titleColor: '#2B2B2B', bodyColor: '#4F4F4F', fontSize: 14, padding: 20, templateId: 'classic' }
      }
    },
    saveData() {
      this.persistState()
      alert('已保存')
    },
    togglePanel() {
      this.panelOpen = !this.panelOpen
    },
    goBack() {
      window.history.back()
    },
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
      pdf.save('resume.pdf')
    }
  }
}
</script>

<style scoped>
.resume-builder-page {
  display: flex;
  justify-content: center;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  height: calc(100vh - 60px);
  background: #f2f3f7;
  overflow: hidden;
  padding: 16px;
}

.builder-left-panel {
  width: 340px;
  background: #ffffff;
  border-right: 1px solid #e1e1e6;
  padding: 16px;
  overflow-y: auto;
  transition: transform 0.25s ease;
  z-index: 10;
}

.builder-left-panel.open {
  transform: translateX(0);
}

.builder-panel-header {
  display: block;
  margin-bottom: 12px;
  padding: 0;
  border: none;
}

.builder-panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #333;
  line-height: 1.3;
}

.preview-header h2,
.builder-panel-header h2 {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}


.btn-toggle,
.btn-action,
.template-btn {
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  padding: 6px 10px;
  cursor: pointer;
  margin-top: 8px;
}

.template-btn {
  margin-right: 6px;
}

.template-btn.active {
  background: #7c56ff;
  color: #fff;
  border-color: #6c42ee;
}

.panel-body .row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
}

.panel-body .row label {
  margin-right: 8px;
  width: 80px;
}

.builder-left-panel {
  width: 30%;
  max-width: 520px;
  background: #f2f3f7;
  border-right: 1px solid #dcdcdc;
  padding: 16px;
  overflow-y: auto;
  transition: transform 0.25s ease;
  z-index: 10;
}

.builder-main {
  width: 70%;
  padding: 16px;
  overflow: auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.resume-preview {
  min-height: 84vh;
  border: 1px solid #c2c2c2;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
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
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.08);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px 16px;
  font-size: 13px;
  color: #4a4a4a;
  margin-bottom: 8px;
  word-break: break-all;
}

.label-row {
  display: flex;
  gap: 14px;
  font-size: 13px;
  color: #4a4a4a;
}

.profile-avatar-box {
  width: 90px;
  height: 110px;
  border: 1px solid #f3f3f3;
  background: #f3f3f3;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.profile-avatar-placeholder {
  color: f3f3f3;
  font-size: 12px;
}

.profile-info-inline {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.section-title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 12px;
}

.section-title h3 {
  font-weight: 700;
  font-size: 16px;
  margin: 0 0 6px;
}

.section-underline {
  width: 100%;
  height: 1px;
  background-color: #4a4a4a;
  opacity: 0.45;
}

.section-underline-light {
  width: 100%;
  height: 1px;
  background-color: #dcdcdc;
  opacity: 0.5;
  margin-top: 2px;
}

.section-config {
  margin-bottom: 16px;
  border: 1px solid #eee;
  padding: 12px;
  border-radius: 8px;
  background: #fafafa;
}

.section-config h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.section-config .row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.section-config .row label {
  width: 100px;
  font-size: 13px;
  color: #333;
}

.section-config .row input,
.section-config .row select,
.section-config .row textarea {
  flex: 1;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 13px;
}

.section-config .row textarea {
  resize: vertical;
}

.module-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.module-tabs button {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}

.module-tabs button.active {
  background: #7c56ff;
  border-color: #6c42ee;
  color: #fff;
}

.character-count,
.char-count,
.content-count {
  font-size: 12px;
  color: #888;
  margin-left: 8px;
}

.avatar-row .avatar-upload {
  width: 80px;
  height: 80px;
  border: 1px dashed #bbb;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: #999;
  border-radius: 6px;
  overflow: hidden;
}

.avatar-row .avatar-upload img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-section {
  margin-bottom: 14px;
}

.preview-section h3 {
  margin-bottom: 6px;
  color: #444;
  border: 1px solid #ccc;
  padding-bottom: 4px;
}

.preview-section .entry-row {
  margin-bottom: 8px;
}

.personal-grid {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.avatar-preview img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 1px solid #ddd;
}

.btn-success {
  background: #27ae60;
  color: #fff;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

.btn-danger {
    background:#fff;
  color:red;
  border: none;
  padding: 5px 6px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 6px;
}

.btn-action {
  border: 1px solid #ccc;
  background: #fff;
  border-radius: 6px;
  padding: 6px 10px;
  cursor: pointer;
  margin-top: 8px;
}

.float-btn {
  position: fixed;
  right: 16px;
  bottom: 16px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: #7c56ff;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
  margin-left: 6px;
}

.float-btn.switch {
  bottom: 70px;
  overflow: hidden;
}


.resume-block {
  padding: 12px;
  margin-bottom: 10px;
  background: #fff;
  border-radius: 6px;
  position: relative;
  transition: all 0.2s ease;
}

.resume-block:hover {
  border: 1px dashed #92b8ff;
}

.resume-block.dragging {
  opacity: 0.4;
  border: 2px dashed #7c6ae8;
}

.resume-block.drag-over {
  border: 2px dashed #519df2;
}

.block-handle {
  position: absolute;
  left: -24px;
  top: 12px;
  cursor: grab;
  color: #999;
  font-size: 16px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile-avatar {
  width: 90px;
  height: 110px;
  border-radius: 8px;
  object-fit: cover;
  border: 2px solid f3f3f3;
}

.profile-info h1 {
  margin: 0;
  font-size: 26px;
  color: #1f1f1f;
}

.profile-info p {
  margin: 4px 0;
  color: #515151;
  font-size: 14px;
}

.divider {
  border-top: 1px solid #ddd;
  margin-top: 10px;
}

.section-title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 12px;
}

.section-title h3 {
  margin: 0 0 6px;
  font-size: 18px;
  letter-spacing: 0.5px;
  font-weight: 700;
}

.section-underline {
  width: 150px;
  height: 4px;
  background: #4a2e8b;
  opacity: 0.35;
}

.section-underline-light {
  width: 700px;
  height: 2px;
  background: #d656c5ff;
  margin-top: 2px;
}

.entry-row {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}

.entry-time {
  width: 120px;
  color: #666;
  font-size: 13px;
}

.entry-main {
  flex: 1;
}

.entry-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.entry-sub {
  color: #555;
  font-size: 13px;
  margin-bottom: 6px;
}

.block-content {
  margin-top: 6px;
}

.delete-btn {
  border: 1px solid #ff7e7e;
  background: #fdf9f9ff;
  color: #d94646;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
}

.block-content {
  margin-top: 6px;
  white-space: pre-wrap;
}
</style>
