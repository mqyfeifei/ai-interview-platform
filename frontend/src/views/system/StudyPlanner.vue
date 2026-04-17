<template>
  <div class="page-container" style="padding: 20px 16px 40px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <h2 style="margin:0;">智能练习规划</h2>
      <button class="btn btn-ghost btn-sm" @click="$router.push({ path: '/learning', query: { reportId: reportId || undefined } })">返回学习中心</button>
    </div>

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

      <div class="card" style="padding:12px;position:sticky;top:76px;">
        <h3 style="margin:0 0 10px;">学习总目标</h3>
        <p style="margin:0 0 8px;">总学习时长：<b>{{ plan?.totalEstimatedHours || 0 }}h</b></p>
        <p style="margin:0 0 8px;">预计天数：<b>{{ plan?.estimatedDays || 0 }}</b> 天</p>
        <p style="margin:0;">预计完成：<b>{{ plan?.targetFinishDate || '--' }}</b></p>
      </div>
    </div>
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
    }
  }
}
</script>
