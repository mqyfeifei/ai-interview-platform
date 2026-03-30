<template>
  <div id="app-root" class="app-shell">

    <!-- PC端顶部导航（普通用户） -->
    <TopNav
      v-if="isPC && !route.meta.hideNavigation && !route.meta.showAdminNav"
      class="app-shell__topnav"
    />

    <div class="app-shell__body" :class="{ 'no-nav': hideAllNav }">

      <!-- 管理后台侧边栏（由 meta.showAdminNav 控制） -->
      <AdminSideNav
        v-if="route.meta.showAdminNav"
        class="app-shell__admin-side"
      />

      <!-- 移动端侧边栏（普通用户） -->
      <SideNav
        v-if="!isPC && !route.meta.hideNavigation && !route.meta.showAdminNav"
        class="app-shell__side"
      />

      <main class="app-shell__main">
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 移动端底部导航（普通用户） -->
    <BottomNav
      v-if="!isPC && !route.meta.hideNavigation && !route.meta.showAdminNav"
      class="app-shell__bottom"
    />

  </div>
</template>

<script>
import BottomNav from '@/components/common/BottomNav.vue'
import SideNav from '@/components/common/SideNav.vue'
import TopNav from '@/components/common/TopNav.vue'
import AdminSideNav from '@/components/admin/AdminSideNav.vue'  // 新增
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'App',
  components: {
    SideNav,
    BottomNav,
    TopNav,
    AdminSideNav  // 新增
  },
  setup() {
    const route = useRoute()
    const isPC = ref(window.innerWidth >= 1024)
    const onResize = () => { isPC.value = window.innerWidth >= 1024 }
    onMounted(() => window.addEventListener('resize', onResize))
    onUnmounted(() => window.removeEventListener('resize', onResize))

    const hideAllNav = computed(() => route.meta.hideNavigation === true)

    return { route, hideAllNav, isPC }
  }
}
</script>

<style lang="scss">
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

#app-root {
  width: 100%;
  min-height: 100vh;
}

// =============================================
// 移动端默认布局
// =============================================
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;

  &__topnav {
    display: none; // 移动端隐藏
  }

  &__body {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  &__side {
    display: none;
  }

  &__main {
    flex: 1;
    min-height: 100vh;
    padding-bottom: $bottom-nav-height;
    overflow-y: auto;
  }

  &__bottom {
    display: flex;
  }
}

// =============================================
// PC端布局（≥ 1024px）
// =============================================
@media (min-width: 1024px) {
  .app-shell {
    flex-direction: column; // 顶部导航 + 下方内容纵向排列
    height: 100vh;
    overflow: hidden;

    &__topnav {
      display: flex; // PC端显示顶部导航
      flex-shrink: 0;
    }

    &__body {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }

    &__side {
      display: none !important; // PC端侧边栏隐藏
    }

    &__main {
      flex: 1;
      min-height: 0;
      height: 100%;
      overflow-y: auto;
      padding-bottom: 0;
    }

    &__bottom {
      display: none !important;
    }
  }
}

// =============================================
// 页面切换动画
// =============================================
.page-enter-active {
  animation: pageEnter 0.25s ease both;
}
.page-leave-active {
  animation: pageLeave 0.15s ease both;
}

@keyframes pageEnter {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes pageLeave {
  from { opacity: 1; }
  to   { opacity: 0; }
}


// =============================================
// 全局页面内容容器（所有页面通用）
// =============================================
.page-container {
  width: 90%;
  max-width: 1300px;   // 最大宽度，参考第二张图的感觉
  margin: 24px auto;      // 水平居中
  padding: 24px 28px;  // 上下内边距 + 左右内边距
  box-sizing: border-box;
}

// 移动端缩小内边距
@media (max-width: 767px) {
  .page-container {
    padding: 16px 16px;
  }
}


// 管理后台布局：侧边栏 + 内容区横向排列
.app-shell__admin-side {
  flex-shrink: 0;
}

// 有管理侧边栏时，body 横向排列
.app-shell__body:has(.app-shell__admin-side) {
  flex-direction: row;
}
</style>