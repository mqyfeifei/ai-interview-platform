<!-- 简历预览组件 
 frontend/src/components/interview/ResumePreview.vue
 -->
<template>
  <div class="resume-preview-container">
    <section class="resume-preview" :style="previewStyles">
      <div class="a4-paper">
        <!-- 个人信息块 -->
        <div class="resume-block">
          <div class="block-content" :style="{ color: config.bodyColor }">
            <template v-if="content && content.personal">
              <div class="profile-row">
                <div class="profile-avatar-box">
                  <img
                    v-if="content.personal.avatar"
                    class="profile-avatar"
                    :src="content.personal.avatar"
                    alt="证件照"
                  />
                  <div v-else class="profile-avatar-placeholder">证件照</div>
                </div>
                <div class="profile-info-inline">
                  <h2>{{ content.personal.name || '未设置' }}</h2>
                  <div class="label-row">
                    <span>性别：{{ content.personal.gender || '未设置' }}</span>
                    <span>年龄：{{ content.personal.age || '未设置' }} 岁</span>
                  </div>
                  <div class="label-row">
                    <span>籍贯：{{ content.personal.address || '未设置' }}</span>
                    <span>工作经验：{{ content.personal.experience || 0 }} 年</span>
                  </div>
                  <div class="label-row">
                    <span>电话：{{ content.personal.phone || '未设置' }}</span>
                    <span>邮箱：{{ content.personal.email || '未设置' }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 求职意向块 -->
        <div v-if="content && content.objective" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">求职意向</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="info-grid">
              <div>求职类型：{{ content.objective.jobType || '未设置' }}</div>
              <div>意向岗位：{{ content.objective.position || '未设置' }}</div>
              <div>意向城市：{{ content.objective.city || '未设置' }}</div>
              <div>期望薪酬：{{ content.objective.salary || '未设置' }}</div>
              <div>到岗时间：{{ content.objective.status || '未设置' }}</div>
            </div>
          </div>
        </div>

        <!-- 教育背景块 -->
        <div v-if="content && Array.isArray(content.education) && content.education.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">教育背景</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.education" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '未设置' }} — {{ item.end || '未设置' }}</div>
                  <div>学校：{{ item.school || '未设置' }}</div>
                  <div>专业：{{ item.major || '未设置' }}</div>
                  <div>学历：{{ item.degree || '未设置' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 校园经历块 -->
        <div v-if="content && Array.isArray(content.campusExperiences) && content.campusExperiences.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">校园经历</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.campusExperiences" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>名称：{{ item.title || '经历名称' }}</div>
                </div>
                <p>{{ item.description || '经历描述…' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 实习经验块 -->
        <div v-if="content && Array.isArray(content.internshipExperiences) && content.internshipExperiences.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">实习经验</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.internshipExperiences" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>公司：{{ item.place || '公司名称' }}</div>
                  <div>岗位：{{ item.title || '岗位名称' }}</div>
                </div>
                <p>{{ item.description || '实习内容…' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 工作经验块 -->
        <div v-if="content && Array.isArray(content.workExperiences) && content.workExperiences.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">工作经验</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.workExperiences" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>时间：{{ item.start || '起' }} — {{ item.end || '止' }}</div>
                  <div>公司：{{ item.company || '公司名称' }}</div>
                  <div>岗位：{{ item.role || '岗位名称' }}</div>
                </div>
                <p>{{ item.description || '工作内容…' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 项目经验块 -->
        <div v-if="content && Array.isArray(content.projectExperiences) && content.projectExperiences.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">项目经验</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.projectExperiences" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>项目：{{ item.name || '项目名称' }}</div>
                  <div>角色：{{ item.role || '角色' }}</div>
                  <div>技术栈：{{ item.techStack || '技术栈' }}</div>
                </div>
                <p>{{ item.description || '项目描述…' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 技能特长块 -->
        <div v-if="content && Array.isArray(content.skills) && content.skills.some(s => s.name)" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">技能特长</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <p>{{ content.skills.map(s => s.name).filter(Boolean).join('、') }}</p>
          </div>
        </div>

        <!-- 荣誉奖项块 -->
        <div v-if="content && Array.isArray(content.prices) && content.prices.length" class="resume-block">
          <div class="block-head">
            <div class="section-title">
              <h3 :style="{ color: config.titleColor }">荣誉奖项</h3>
              <span class="section-underline"></span>
            </div>
          </div>
          <div class="block-content" :style="{ color: config.bodyColor }">
            <div class="experience-list">
              <div v-for="item in content.prices" :key="item.id" class="experience-item">
                <div class="info-grid">
                  <div>获奖名称：{{ item.award || '未设置' }}</div>
                  <div>时间：{{ item.period || '未设置' }}</div>
                  <div>等级：{{ item.level || '未设置' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'ResumePreview',

  props: {
    content: {
      type: Object,
      default: () => ({})
    }
  },

  computed: {
    config() {
      return (this.content && this.content.config) || {
        titleColor: '#2B2B2B',
        bodyColor: '#4F4F4F',
        fontSize: 14,
        padding: 20
      }
    },

    previewStyles() {
      const fontSize = this.config.fontSize || 14
      const padding = this.config.padding || 20
      return {
        fontSize: fontSize + 'px',
        '--resume-font-size': fontSize + 'px',
        '--resume-padding': padding + 'px'
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.resume-preview-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background: #f9fafb;
  padding: 20px;
}

.resume-preview {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 0;
  background: transparent;
  min-height: 100%;
}

.a4-paper {
  width: 210mm;
  min-height: 297mm;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  box-sizing: border-box;
  font-size: var(--resume-font-size, 14px);
  line-height: 1.6;
  color: #333;
  border: 1px solid #e5e7eb;
}

.resume-block {
  padding: 12px;
  margin-bottom: 10px;
  background: #fff;
  border-radius: 4px;
  position: relative;
  border: 1px solid transparent;

  &:last-child {
    margin-bottom: 0;
  }
}

.block-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
  position: relative;
}

.section-title {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  margin-bottom: 10px;

  h3 {
    font-size: 16px;
    font-weight: 700;
    margin: 0 0 4px;
    letter-spacing: 0;
    color: #1f2937;
  }
}

.section-underline {
  width: 150px;
  height: 3px;
  background: #6d28d9;
  opacity: 0.25;
  margin: 0;
}

.block-content {
  line-height: 1.6;
  margin-top: 4px;
  font-size: 13px;
  color: #4b5563;

  p {
    margin: 0;
    word-wrap: break-word;
  }
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.profile-avatar-box {
  flex-shrink: 0;
  width: 90px;
  height: 110px;
  border-radius: 4px;
  overflow: hidden;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e5e7eb;
}

.profile-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  color: #aaa;
  font-size: 12px;
}

.profile-info-inline {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;

  h2 {
    font-size: 22px;
    font-weight: 700;
    margin: 0;
    color: #1f2937;
  }
}

.label-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 13px;
  color: #6b7280;

  span {
    flex: 1;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 6px 16px;
  font-size: 13px;
  color: #4a5563;
  margin-bottom: 8px;

  > div {
    word-break: break-word;
  }
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
  border-radius: 0 4px 4px 0;
  color: #4a5563;

  &:last-child {
    margin-bottom: 0;
  }

  .info-grid {
    margin-bottom: 6px;
  }

  > p {
    margin: 4px 0 0;
    font-size: 13px;
    color: #555;
    line-height: 1.5;
  }
}
</style>
