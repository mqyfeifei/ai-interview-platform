<template>
  <div class="hotlist-container">
    <div class="hotlist-header">
      <div>
        <h2>技术热榜</h2>
        <small v-if="lastUpdated" class="last-updated">更新时间: {{ new Date(lastUpdated).toLocaleTimeString() }}</small>
      </div>
      <div class="hotlist-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['hotlist-tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>
    </div>

    <div class="hotlist-list">
      <div v-if="loading" class="hotlist-skeleton" v-for="n in 5" :key="n">加载中…</div>
      <div
        v-for="item in filteredItems"
        :key="item.url"
        class="hotlist-item"
        @click="openUrl(item.url)"
      >
        <div class="item-title">{{ item.name }}</div>
        <div class="item-desc">{{ item.description }}</div>
        <div class="item-meta">
          <span>⭐ {{ item.stars }}</span>
          <span v-if="item.language" class="item-lang">{{ item.language }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { JOB_TYPES } from '@/utils/constants'

// 本地缓存键
const HOTCACHE = 'tech_hotlist_cache'
function _loadHotCache() {
  try { return JSON.parse(localStorage.getItem(HOTCACHE) || '{}') } catch (e) { return {} }
}
function _saveHotCache(data) {
  try { localStorage.setItem(HOTCACHE, JSON.stringify(data)) } catch (e) {}
}

export default {
  name: 'TechHotList',
  data() {
    return {
      items: [],
      activeTab: 'all',
      loading: false,
      lastUpdated: null,
      _sinceMode: 'daily'  // rotate between daily/weekly
    }
  },
  computed: {
    tabs() {
      const base = [{ key: 'all', label: '全部' }]
      JOB_TYPES.forEach(j => {
        base.push({ key: j.id, label: j.name })
      })
      return base
    },
    filteredItems() {
      let list = []
      if (this.activeTab === 'all') {
        list = this.items
      } else {
        // language match job tech stack
        const job = JOB_TYPES.find(j => j.id === this.activeTab)
        if (!job) return []
        const langs = job.techStack.map(x => x.toLowerCase())
        list = this.items.filter(i => {
          return i.language && langs.includes(i.language.toLowerCase())
        })
      }
      // only display top 10 to avoid showing "更多" style
      return list.slice(0, 10)
    }
  },
  methods: {
    async fetchTrending() {
      this.loading = true
      const cache = _loadHotCache()
      const now = Date.now()
      // show cache quickly
      if (cache.ts && now - cache.ts < 1000 * 60 * 5) {
        this.items = cache.items || []
        this.lastUpdated = cache.ts
      }
      try {
        const res = await axios.get(`https://ghapi.huchen.dev/repositories?since=${this._sinceMode}`)
        const list = res.data.map(r => ({
          name: r.name,
          description: r.description || '',
          url: r.url || r.html_url || '',
          language: r.language,
          stars: r.stars || r.watchers || 0
        }))
        // shuffle
        this.items = list.sort(() => Math.random() - 0.5)
        this.lastUpdated = now
        _saveHotCache({ ts: now, items: list })
        // rotate mode for next time
        this._sinceMode = this._sinceMode === 'daily' ? 'weekly' : 'daily'
      } catch (e) {
        console.error('获取技术热榜失败', e)
        if (cache.items) this.items = cache.items
      } finally {
        this.loading = false
      }
    },
    openUrl(url) {
      if (url) window.open(url, '_blank', 'noopener')
    }
  },
  mounted() {
    // load cache immediately for instant view
    const cache = _loadHotCache()
    if (cache.items) {
      this.items = cache.items
      this.lastUpdated = cache.ts
    }
    // always fetch fresh in background
    this.fetchTrending()
    // 每15分钟刷新一次最新数据
    this._timer = setInterval(this.fetchTrending, 15 * 60 * 1000)
  },
  beforeUnmount() {
    clearInterval(this._timer)
  }
}
</script>

<style scoped>
.hotlist-container {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-top: 24px;
}
.hotlist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hotlist-tabs {
  display: flex;
  gap: 8px;
}
.hotlist-tab {
  padding: 4px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.hotlist-tab.active {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}
.last-updated {
  font-size: 11px;
  color: #555;
}
.hotlist-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hotlist-item {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.hotlist-item:hover {
  background: #f3f4f6;
}
.item-title {
  font-weight: 600;
}
.item-desc {
  font-size: 12px;
  color: #555;
  margin: 4px 0;
}
.item-meta {
  font-size: 11px;
  color: #888;
  display: flex;
  gap: 8px;
}
.item-lang {
  background: #e5e7eb;
  border-radius: 2px;
  padding: 1px 4px;
}
.hotlist-skeleton {
  height: 40px;
  background: #f3f4f6;
  border-radius: 4px;
  animation: pulse 1.2s infinite;
}
@keyframes pulse { 0% { opacity: 1 } 50% { opacity: 0.6 } 100% { opacity: 1 } }
</style>