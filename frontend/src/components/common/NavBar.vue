<template>
  <header class="nav-bar" :class="{ transparent: transparent }">
    <button v-if="showBack" class="nav-bar__back" @click="handleBack">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 18 9 12 15 6"/>
      </svg>
    </button>
    <div class="nav-bar__title">{{ title }}</div>
    <div class="nav-bar__right">
      <slot name="right" />
    </div>
  </header>
</template>

<script>
export default {
  name: 'NavBar',
  props: {
    title: { type: String, default: '' },
    showBack: { type: Boolean, default: true },
    transparent: { type: Boolean, default: false },
    backPath: { type: String, default: null }
  },
  methods: {
    handleBack() {
      if (this.backPath) {
        this.$router.push(this.backPath)
      } else {
        this.$router.back()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.nav-bar {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: $top-nav-height;
  padding: 0 $spacing-base;
  background: rgba(230, 234, 254, 0);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid $border-color;
  z-index: 90;
  box-shadow: $shadow-sm;

  &.transparent {
    background: transparent;
    border-bottom: none;
    box-shadow: none;
  }

  &__back {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: $gray-100;
    border: none;
    border-radius: $border-radius-full;
    cursor: pointer;
    transition: all $transition-fast;
    color: $text-primary;

    svg { width: 18px; height: 18px; }

    &:hover { background: $gray-200; }
    &:active { transform: scale(0.92); }
  }

  &__title {
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    color: $text-primary;
    flex: 1;
    text-align: center;
    margin: 0 $spacing-sm;
  }

  &__right {
    min-width: 36px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }
}
</style>