<template>
  <aside class="admin-sidebar">
    <div class="brand">
      <img class="brand-logo" src="@/assets/logo5.png" alt="logo" />
      <span v-if="!collapsed">码上offer 管理后台</span>
    </div>

    <nav>
      <a
        v-for="item in menus"
        :key="item.key"
        href="#"
        :class="{ active: activeTab === item.key }"
        @click.prevent="handleClick(item.key)"
      >
        {{ item.label }}
      </a>
    </nav>
  </aside>
</template>

<script>
export default {
  name: 'AdminSideNav',

  props: {
    modelValue: {
      type: String,
      default: 'home'
    }
  },

  data() {
    return {
      collapsed: false,
      menus: [
        { key: 'home', label: '首页' },
        { key: 'users', label: '用户管理' },
        { key: 'jobs', label: '岗位与题库管理' },
        { key: 'records', label: '面试记录管理' },
        { key: 'assistant', label: '面试助手管理' }
      ]
    }
  },

  computed: {
    activeTab() {
      return this.modelValue
    }
  },

  methods: {
    handleClick(key) {
      this.$emit('update:modelValue', key)
    }
  }
}
</script>

<style scoped>
.admin-sidebar {
  width: 260px;
  background: #f8f4ff;
  border-right: 1px solid #e4def5;
  color: #4a3b8a;
  padding: 24px 16px;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: #5f4bb0;
  text-align: center;
}

.brand-logo {
  width: 90px;
  height: 90px;
  border-radius: 12px;
  object-fit: contain;
}

nav a {
  display: block;
  color: #5e4fa4;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 8px;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 1.05rem;
  font-weight: 600;
}

nav a:hover {
  background: #eae4ff;
}

nav a.active {
  background: #d9cfff;
  color: #2f1f78;
  font-weight: 700;
}
</style>