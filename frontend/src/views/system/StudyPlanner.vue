<template>
  <div class="study-planner-page">
    <div class="study-planner-nav">
      <h2 style="margin:0;">智能练习规划</h2>
    </div>

    <div class="page-container study-planner-body" style="padding: 20px 16px 40px;">
      <div style="display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr);gap:12px;align-items:start;">
      <div>
        <div class="card" style="padding:12px;margin-bottom:12px;">
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <span>每日学习强度：</span>
            <input v-model.number="dailyHours" type="number" min="0.5" step="0.5" style="width:90px;padding:6px 8px;" />
            <span>小时/天</span>
            <button class="btn btn-primary btn-sm" @click="loadPlan">生成计划</button>
          </div>
        </div>

        <div v-if="plan" class="card" style="padding:12px;">
          <div v-for="day in plan.calendar || []" :key="day.dayIndex" style="border-top:1px solid #eee;padding:8px 0;">
            <p style="margin:0 0 6px;"><b>Day {{ day.dayIndex }}</b>（{{ day.date }}，{{ day.hours }}h）</p>
            <p v-for="item in day.items || []" :key="`${day.dayIndex}-${item.resourceId}-${item.title}`" style="margin:2px 0;color:#555;">
              - {{ item.title }}（{{ item.hours }}h，{{ item.relatedWeakness || '通用补强' }}）
            </p>
          </div>
        </div>
      </div>

      <div class="card" style="padding:12px;position:sticky;top:12px;">
        <h3 style="margin:0 0 10px;">学习总目标</h3>
        <p style="margin:0 0 8px;">总学习时长：<b>{{ plan?.totalEstimatedHours || 0 }}h</b></p>
        <p style="margin:0 0 8px;">预计天数：<b>{{ plan?.estimatedDays || 0 }}</b> 天</p>
        <p style="margin:0;">预计完成：<b>{{ plan?.targetFinishDate || '--' }}</b></p>
        <div v-if="plan?.items?.length" class="resource-goal-list">
          <h4 class="resource-goal-list__title">全部计划学习资源</h4>
          <a
            v-for="item in plan.items"
            :key="`plan-resource-${item.id}-${item.title}`"
            class="resource-goal-item"
            :href="item.url || '#'"
            target="_blank"
            rel="noopener noreferrer"
            @click.prevent="openResource(item)"
          >
            <span class="resource-goal-item__title">{{ item.title }}</span>
            <span class="resource-goal-item__meta">
              {{ item.estimatedHours || 0 }}h · {{ item.relatedWeakness || '通用补强' }}
            </span>
          </a>
        </div>
      </div>
    </div>
    </div>
    <button class="float-btn" @click="goLearningHome">← 返回</button>
  </div>
</template>

<script>
import { getStudyPlan } from '@/api/learning'

export default {
  name: 'StudyPlanner',
  data() {
    return {
      dailyHours: 2,
      plan: null,
      reportId: null
    }
  },
  async created() {
    this.reportId = this.$route.query?.reportId ? Number(this.$route.query.reportId) : null
    this.dailyHours = this.$store.getters['learning/learningSettings']?.dailyHours || 2
    await this.loadPlan()
  },
  methods: {
    async loadPlan() {
      this.plan = await getStudyPlan({ dailyHours: this.dailyHours, reportId: this.reportId })
      await this.$store.dispatch('learning/updateLearningSettings', { dailyHours: this.dailyHours })
    },
    openResource(item) {
      const url = (item && item.url) ? String(item.url) : ''
      if (!url) return
      window.open(url, '_blank', 'noopener')
    },
    goLearningHome() {
      this.$router.push({ path: '/learning', query: { reportId: this.reportId || undefined } })
    }
  }
}
</script>

<style scoped>
.study-planner-page {
  min-height: 100vh;
  background: #f5f7fb;
}

.study-planner-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.study-planner-body {
  margin-top: 0;
}

.resource-goal-list {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #e5e7eb;
}

.resource-goal-list__title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.resource-goal-item {
  display: flex;
  flex-direction: column;
  padding: 8px;
  margin-bottom: 6px;
  border-radius: 8px;
  background: #f8fafc;
  text-decoration: none;
}

.resource-goal-item__title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  line-height: 1.35;
}

.resource-goal-item__meta {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}

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
  z-index: 30;
}

.float-btn:hover {
  opacity: 0.88;
}
</style>
