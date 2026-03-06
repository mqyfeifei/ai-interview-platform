// =============================================
// frontend/src/App.vue

<template>
  <div id="app-root">
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style lang="scss">
#app-root {
  width: 100%;
  min-height: 100vh;
}

// 页面切换过渡
.page-enter-active {
  animation: pageEnter 0.3s ease both;
}
.page-leave-active {
  animation: pageLeave 0.2s ease both;
}

@keyframes pageEnter {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pageLeave {
  from { opacity: 1; transform: translateY(0); }
  to   { opacity: 0; transform: translateY(-8px); }
}
</style>
