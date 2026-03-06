// =============================================
// frontend/src/App.vue

<template>
  <div id="app-root" class="app-shell">
    <!-- 根据路由元信息控制侧边栏显示 -->
    <SideNav 
      v-if="!route.meta.hideNavigation && !route.meta.hideSideNav" 
      class="app-shell__side" 
    />

    <main class="app-shell__main" :class="{ 'no-nav': hideAllNav }">
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <!-- 根据路由元信息控制底部导航显示 -->
    <BottomNav 
      v-if="!route.meta.hideNavigation && !route.meta.hideBottomNav" 
      class="app-shell__bottom" 
    />
  </div>
</template>

<script>
import BottomNav from '@/components/common/BottomNav.vue'
import SideNav from '@/components/common/SideNav.vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'App',
  components: {
    SideNav,
    BottomNav
  },
  setup() {
    const route = useRoute()
    
    const hideAllNav = computed(() => {
      return route.meta.hideNavigation === true
    })
    
    return {
      route,
      hideAllNav
    }
  }
}
</script>

<style lang="scss">
#app-root {
  width: 100%;
  min-height: 100vh;
}

.app-shell {
  display: block;

  &__side {
    display: none;
  }

  &__main {
    min-height: 100vh;
    padding-bottom: $bottom-nav-height;
  }

  &__bottom {
    display: flex;
  }
}

@media (min-width: 1024px) {
  .app-shell {
    /* PC端全屏布局，无边距 */
    width: 100vw;
    height: 100vh;
    overflow: hidden; /* 禁用外层滚动 */
    display: flex;
    margin: 0;
    padding: 0;

    &__side {
      display: block;
      width: 256px; /* 侧边栏宽度 */
      flex-shrink: 0;
      overflow-y: auto; /* 侧边栏内容过多时可内部滚动 */
    }

    &__main {
      flex: 1;
      height: 100%;
      overflow-y: auto; /* 主内容区域独立滚动 */
      padding-bottom: 0;
    }

    &__bottom {
      display: none !important;
    }
  }
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



.app-shell__main {
  min-height: 100vh;
  padding-bottom: $bottom-nav-height;
  
  &.no-nav {
    padding-bottom: 0;
  }
}

@media (min-width: 1024px) {
  .app-shell__main.no-nav {
    // PC端无导航时的样式调整
  }
}
</style>
