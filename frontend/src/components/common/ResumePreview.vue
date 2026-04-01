<template>
  <section class="resume-preview" :style="previewStyles">
    <div class="a4-paper">
      <div
        v-for="(block, index) in visibleBlocks"
        :key="block.id"
        class="resume-block"
      >
        <div class="block-head">
          <div class="section-title" v-if="block.type !== 'profile'">
            <h3 :style="{ color: config.titleColor }">{{ block.title }}</h3>
            <span class="section-underline"></span>
            <span class="section-underline-light"></span>
          </div>
        </div>

        <div class="block-content" :style="{ color: config.bodyColor }">
          <template v-if="block.type === 'profile'">
            <div class="profile-row">
              <div class="profile-avatar-box">
                <img v-if="personal.avatar" class="profile-avatar" :src="personal.avatar" alt="头像" />
                <div v-else class="profile-avatar-placeholder">证件照</div>
              </div>
              <div class="profile-info-inline">
                <h2>{{ personal.name || '未设置' }}</h2>
                <div class="label-row">
                  <span>年龄：{{ personal.age || '未设置' }} 岁</span>
                  <span>籍贯：{{ personal.address || '未设置' }}</span>
                </div>
                <div class="label-row">
                  <span>工作经验：{{ personal.experience || 0 }} 年</span>
                  <span>联系方式：{{ personal.contact || '未设置' }}</span>
                </div>
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
              <div v-for="item in education" :key="item.id || item.start + item.school" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '未设置' }} — {{ item.end || '未设置' }}</div>
                  <div>学校：{{ item.school || '未设置' }}</div>
                  <div>专业：{{ item.major || '未设置' }}</div>
                  <div>学历：{{ item.degree || '未设置' }}</div>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="block.type === 'prices'">
            <div v-if="prices.length" class="experience-list">
              <div v-for="item in prices" :key="item.id || item.award" class="experience-item">
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

          <template v-else-if="block.type === 'skills'">
            <p>{{ skills.length ? skills.map(s => s.name).filter(Boolean).join('、') : '暂未填写技能' }}</p>
          </template>

          <template v-else-if="block.type === 'campus'">
            <div v-if="campusExperiences.length" class="experience-list">
              <div v-for="item in campusExperiences" :key="item.id || item.title" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>名称：{{ item.title || '经历名称' }}</div>
                </div>
                <p>{{ item.description || '经历描述…' }}</p>
              </div>
            </div>
            <div v-else class="experience-item"><p>暂无校园经历</p></div>
          </template>

          <template v-else-if="block.type === 'internship'">
            <div v-if="internshipExperiences.length" class="experience-list">
              <div v-for="item in internshipExperiences" :key="item.id || item.title" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>公司：{{ item.place || '公司名称' }}</div>
                  <div>岗位：{{ item.title || '岗位名称' }}</div>
                </div>
                <p>{{ item.description || '实习内容…' }}</p>
              </div>
            </div>
            <div v-else class="experience-item"><p>暂无实习经历</p></div>
          </template>

          <template v-else-if="block.type === 'work'">
            <div v-if="workExperiences.length" class="experience-list">
              <div v-for="item in workExperiences" :key="item.id || item.company" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>公司：{{ item.company || '公司名称' }}</div>
                  <div>岗位：{{ item.role || '岗位名称' }}</div>
                </div>
                <p>{{ item.description || '工作内容…' }}</p>
              </div>
            </div>
            <div v-else class="experience-item"><p>暂无工作经验</p></div>
          </template>

          <template v-else-if="block.type === 'project'">
            <div v-if="projectExperiences.length" class="experience-list">
              <div v-for="item in projectExperiences" :key="item.id || item.name" class="experience-item">
                <div class="info-grid">
                  <div>项目：{{ item.name || '项目名称' }}</div>
                  <div>角色：{{ item.role || '角色' }}</div>
                  <div>技术栈：{{ item.techStack || '技术栈' }}</div>
                </div>
                <p>{{ item.description || '项目描述…' }}</p>
              </div>
            </div>
            <div v-else class="experience-item"><p>暂无项目经验</p></div>
          </template>

        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'ResumePreview',
  props: {
    content: { type: Object, default: () => ({}) },
    blockOrder: { type: Array, default: () => ['profile', 'objective', 'education', 'campus', 'internship', 'work', 'project', 'prices', 'skills'] },
    config: {
      type: Object,
      default: () => ({ titleColor: '#2B2B2B', bodyColor: '#4F4F4F', fontSize: 14, padding: 20 })
    }
  },
  computed: {
    personal() {
      return this.content.personal || {}
    },
    objective() {
      return this.content.objective || {}
    },
    education() {
      return Array.isArray(this.content.education) ? this.content.education : []
    },
    campusExperiences() {
      return Array.isArray(this.content.campusExperiences) ? this.content.campusExperiences : []
    },
    internshipExperiences() {
      return Array.isArray(this.content.internshipExperiences) ? this.content.internshipExperiences : []
    },
    workExperiences() {
      return Array.isArray(this.content.workExperiences) ? this.content.workExperiences : []
    },
    projectExperiences() {
      return Array.isArray(this.content.projectExperiences) ? this.content.projectExperiences : []
    },
    prices() {
      return Array.isArray(this.content.prices) ? this.content.prices : []
    },
    skills() {
      return Array.isArray(this.content.skills) ? this.content.skills : []
    },
    visibleBlocks() {
      const map = {
        profile: { id: 'profile', type: 'profile', title: '个人信息' },
        objective: { id: 'objective', type: 'objective', title: '求职意向' },
        education: { id: 'education', type: 'education', title: '教育背景' },
        campus: { id: 'campus', type: 'campus', title: '校园经历' },
        internship: { id: 'internship', type: 'internship', title: '实习经验' },
        work: { id: 'work', type: 'work', title: '工作经验' },
        project: { id: 'project', type: 'project', title: '项目经验' },
        prices: { id: 'prices', type: 'prices', title: '荣誉奖项' },
        skills: { id: 'skills', type: 'skills', title: '技能特长' },
      }
      return this.blockOrder.map(key => map[key]).filter(Boolean)
    },
    previewStyles() {
      return {
        padding: `${this.config.padding}px`,
        fontSize: `${this.config.fontSize}px`,
        fontFamily: '微软雅黑, PingFang SC, sans-serif',
        background: '#fff'
      }
    }
  }
}
</script>

<style scoped>
.resume-preview { max-width: 100%; overflow-x: auto; }
.a4-paper { width: min(920px, 100%); max-width: 920px; margin: 0 auto; }
.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}
.profile-avatar-box {
  width: 86px;
  height: 86px;
  border: 1px solid #dce2eb;
  background: #f8faff;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}
.profile-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.profile-avatar-placeholder {
  color: #9ca3af;
  font-size: 12px;
}
.profile-info-inline {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.profile-info-inline h2 {
  margin: 0;
  font-size: 22px;
  color: #1f1f1f;
}
.label-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #4b5563;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 6px 16px;
  font-size: 13px;
  color: #4a4a4a;
}
.experience-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.experience-item {
  padding: 8px;
  border-left: 3px solid #7c56ff;
  background: #fafbff;
  border-radius: 0 6px 6px 0;
}
.experience-item p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #555;
}
</style>