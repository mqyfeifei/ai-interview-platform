<!--
  =============================================
  frontend/src/components/common/HelpGuideModal.vue
  使用帮助指南弹窗（前端本地存储控制首次展示）
  =============================================
-->
<template>
  <transition name="helpModal">
    <div v-if="modelValue" class="help-modal-overlay" @click.self="handleClose">
      <div class="help-modal-sheet" role="dialog" aria-modal="true" aria-label="使用帮助">
        <div class="help-modal-header">
          <div class="help-modal-title">
            <span class="help-modal-title__icon">📌</span>
            <span class="help-modal-title__text">使用帮助指南</span>
          </div>
          <button class="help-modal-close" type="button" @click="handleClose">✕</button>
        </div>

        <div class="help-modal-body">
          <div class="help-card">
            <p class="help-card__lead">每张卡片对应一个具体功能：</p>

            <div class="help-carousel" aria-label="帮助指南轮播">
              <div class="help-slide" :key="activeSlide.key">
                <div class="help-slide__top">
                  <div class="help-slide__icon" :class="activeSlide.iconClass">{{ activeSlide.icon }}</div>
                  <div class="help-slide__meta">
                    <div class="help-slide__title">{{ activeSlide.title }}</div>
                    <div class="help-slide__progress">{{ activeIndex + 1 }} / {{ slides.length }}</div>
                  </div>
                </div>

                <div class="help-slide__desc">{{ activeSlide.desc }}</div>

                <div class="help-slide__how" v-if="activeSlide.how">
                  <div class="help-slide__how-title">怎么进入</div>
                  <div class="help-slide__how-text">{{ activeSlide.how }}</div>
                </div>
              </div>

              <div class="help-carousel__controls">
                <button
                  class="help-nav-btn"
                  type="button"
                  @click="prev"
                  :disabled="activeIndex === 0"
                  aria-label="上一张"
                >
                  ← 上一张
                </button>

                <div class="help-dots" aria-label="轮播页码">
                  <button
                    v-for="(s, idx) in slides"
                    :key="s.key"
                    type="button"
                    class="help-dot"
                    :class="{ 'is-active': idx === activeIndex }"
                    @click="goTo(idx)"
                    :aria-label="`第 ${idx + 1} 张`"
                  ></button>
                </div>

                <button
                  class="help-nav-btn"
                  type="button"
                  @click="next"
                  :disabled="activeIndex === slides.length - 1"
                  aria-label="下一张"
                >
                  下一张 →
                </button>
              </div>
            </div>

            <div class="help-tip">
              <span class="help-tip__icon">💡</span>
              <span class="help-tip__text">提示：该指南会在你首次登录进入系统时自动弹出一次，你也可以在“个人中心 → 使用帮助”随时查看。</span>
            </div>
          </div>
        </div>

        <div class="help-modal-footer">
          <button class="help-btn help-btn--primary" type="button" @click="handleClose">我知道了</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'HelpGuideModal',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'dismiss'],
  data() {
    return {
      activeIndex: 0,
      slides: [
        {
          key: 'interview',
          icon: '🚀',
          iconClass: 'help-slide__icon--primary',
          title: '开始模拟面试',
          desc: '选择岗位后即可开始模拟面试，系统会根据岗位特点进行提问。',
          how: '首页 → 选择岗位 → 开始面试'
        },
        {
          key: 'report',
          icon: '📊',
          iconClass: 'help-slide__icon--success',
          title: '查看面试报告',
          desc: '面试结束会生成报告，帮助你复盘优缺点并制定改进方向。',
          how: '历史记录 → 查看报告'
        },
        {
          key: 'learning',
          icon: '📚',
          iconClass: 'help-slide__icon--warning',
          title: '学习中心提升',
          desc: '展示多维度能力曲线，针对薄弱点进行学习与练习，持续提升面试表现。',
          how: '学习中心 → 查看能力评价 → 根据学习资源进行学习'
        },
        {
          key: 'profile',
          icon: '👤',
          iconClass: 'help-slide__icon--neutral',
          title: '个人中心管理',
          desc: '上传头像、完善基本信息，并在账号安全中修改密码等。',
          how: '个人中心 → 信息完善'
        }
      ]
    }
  },
  computed: {
    activeSlide() {
      return this.slides[this.activeIndex] || this.slides[0]
    }
  },
  watch: {
    modelValue(val) {
      if (val) this.activeIndex = 0
    }
  },
  methods: {
    handleClose() {
      this.$emit('update:modelValue', false)
      this.$emit('dismiss')
    },
    prev() {
      if (this.activeIndex <= 0) return
      this.activeIndex -= 1
    },
    next() {
      if (this.activeIndex >= this.slides.length - 1) return
      this.activeIndex += 1
    },
    goTo(idx) {
      const nextIndex = Number(idx)
      if (!Number.isFinite(nextIndex)) return
      if (nextIndex < 0 || nextIndex > this.slides.length - 1) return
      this.activeIndex = nextIndex
    }
  }
}
</script>

<style lang="scss" scoped>
.help-modal-overlay {
  position: fixed;
  inset: 0;
  background: $bg-overlay;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: $spacing-base;
  z-index: 999;
}

.help-modal-sheet {
  width: 100%;
  max-width: 560px;
  background: $bg-card;
  border-radius: $border-radius-xl;
  box-shadow: $shadow-lg;
  overflow: hidden;
}

.help-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-base $spacing-base;
  border-bottom: 1px solid $border-color;
}

.help-modal-title {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  &__icon {
    width: 34px;
    height: 34px;
    border-radius: $border-radius-lg;
    background: $primary-bg;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }

  &__text {
    font-family: $font-family-display;
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }
}

.help-modal-close {
  width: 36px;
  height: 36px;
  border-radius: $border-radius-full;
  border: 1px solid $border-color;
  background: $gray-50;
  color: $gray-600;
  cursor: pointer;
  transition: transform $transition-fast, background $transition-fast;

  &:hover {
    background: $gray-100;
    transform: scale(1.03);
  }

  &:active {
    transform: scale(0.98);
  }
}

.help-modal-body {
  padding: $spacing-base;
}

.help-card {
  background: $gradient-primary-soft;
  border: 1px solid $border-color;
  border-radius: $border-radius-lg;
  padding: $spacing-base;

  &__lead {
    margin: 0 0 $spacing-base;
    color: $text-secondary;
    font-size: $font-size-base;
    line-height: $line-height-normal;
  }
}

.help-carousel {
  margin-top: $spacing-sm;
}

.help-slide {
  background: rgba(255,255,255,0.78);
  border: 1px solid rgba(226,232,240,0.9);
  border-radius: $border-radius-lg;
  padding: $spacing-base;

  &__top {
    display: flex;
    align-items: center;
    gap: $spacing-md;
  }

  &__icon {
    width: 44px;
    height: 44px;
    border-radius: $border-radius-lg;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;

    &--primary { background: $primary-bg; color: $primary-dark; }
    &--info { background: $info-bg; color: darken($info, 15%); }
    &--success { background: $success-bg; color: darken($success, 15%); }
    &--warning { background: $warning-bg; color: darken($warning, 20%); }
    &--neutral { background: $gray-100; color: $gray-700; }
  }

  &__meta {
    flex: 1;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: $spacing-sm;
  }

  &__title {
    font-weight: $font-weight-bold;
    color: $text-primary;
    font-size: $font-size-lg;
    line-height: $line-height-tight;
  }

  &__progress {
    font-size: $font-size-xs;
    color: $text-muted;
    flex-shrink: 0;
  }

  &__desc {
    margin-top: $spacing-md;
    color: $text-secondary;
    font-size: $font-size-base;
    line-height: $line-height-normal;
  }

  &__how {
    margin-top: $spacing-md;
    padding: $spacing-md;
    border-radius: $border-radius-lg;
    border: 1px dashed rgba(148, 163, 184, 0.8);
    background: rgba(255,255,255,0.65);
  }

  &__how-title {
    font-size: $font-size-xs;
    color: $text-muted;
    font-weight: $font-weight-semibold;
  }

  &__how-text {
    margin-top: 4px;
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: $line-height-normal;
  }
}

.help-carousel__controls {
  margin-top: $spacing-md;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
}

.help-nav-btn {
  height: 38px;
  padding: 0 12px;
  border-radius: $border-radius-lg;
  border: 1px solid $border-color;
  background: rgba(255,255,255,0.75);
  color: $text-secondary;
  cursor: pointer;
  font-weight: $font-weight-semibold;
  font-size: $font-size-sm;
  transition: transform $transition-fast, background $transition-fast, opacity $transition-fast;

  &:hover {
    background: rgba(255,255,255,0.95);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
}

.help-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
}

.help-dot {
  width: 10px;
  height: 10px;
  border-radius: $border-radius-full;
  border: 1px solid rgba(148, 163, 184, 0.9);
  background: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: transform $transition-fast, background $transition-fast, border-color $transition-fast;

  &.is-active {
    background: $primary;
    border-color: $primary;
    transform: scale(1.08);
  }
}

.help-tip {
  margin-top: $spacing-base;
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-radius: $border-radius-lg;
  border: 1px dashed rgba(148, 163, 184, 0.8);
  background: rgba(255,255,255,0.7);

  &__icon {
    flex-shrink: 0;
  }

  &__text {
    color: $text-secondary;
    font-size: $font-size-sm;
    line-height: $line-height-normal;
  }
}

.help-modal-footer {
  padding: 0 $spacing-base $spacing-base;
}

.help-btn {
  width: 100%;
  height: 46px;
  border-radius: $border-radius-lg;
  border: 1px solid $border-color;
  cursor: pointer;
  font-weight: $font-weight-semibold;
  font-size: $font-size-base;

  &--primary {
    background: $primary;
    border-color: $primary;
    color: white;
    box-shadow: $shadow-primary;
    transition: transform $transition-fast, filter $transition-fast;

    &:hover {
      filter: brightness(1.03);
      transform: translateY(-1px);
    }

    &:active {
      transform: translateY(0);
    }
  }
}

/* 动画：遮罩淡入 + sheet 上滑 */
@keyframes helpModalIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes helpModalOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
@keyframes helpSheetIn {
  from { transform: translateY(16px); }
  to { transform: translateY(0); }
}
@keyframes helpSheetOut {
  from { transform: translateY(0); }
  to { transform: translateY(16px); }
}

.helpModal-enter-active {
  animation: helpModalIn 0.25s ease both;
}
.helpModal-leave-active {
  animation: helpModalOut 0.2s ease both;
}
.helpModal-enter-active .help-modal-sheet {
  animation: helpSheetIn 0.25s $transition-spring both;
}
.helpModal-leave-active .help-modal-sheet {
  animation: helpSheetOut 0.2s ease both;
}

@media (min-width: 1024px) {
  .help-modal-overlay {
    align-items: center;
  }
}
</style>
