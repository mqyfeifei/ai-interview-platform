<template>
  <div class="loading-wrapper" :class="fullscreen ? 'fullscreen' : ''">
    <div class="spinner" :style="{ width: size + 'px', height: size + 'px' }">
      <div class="spinner__ring" />
      <div class="spinner__ring spinner__ring--delay" />
    </div>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    size: { type: Number, default: 40 },
    text: { type: String, default: '' },
    fullscreen: { type: Boolean, default: false }
  }
}
</script>

<style lang="scss" scoped>
.loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $spacing-md;
  padding: $spacing-2xl;

  &.fullscreen {
    position: fixed;
    inset: 0;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(4px);
    z-index: 999;
  }
}

.spinner {
  position: relative;
  &__ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 3px solid transparent;
    border-top-color: $primary;
    animation: spin 0.9s linear infinite;

    &--delay {
      border-top-color: transparent;
      border-right-color: $primary-light;
      animation-duration: 1.3s;
      animation-direction: reverse;
      opacity: 0.6;
    }
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: $font-size-sm;
  color: $text-muted;
}
</style>