<!--
  =============================================
  QuestionDetail.vue - 技术热文详情（支持站内阅读全文）
  ============================================= -->
<template>
  <div class="article-detail-page">
    <!-- 顶部导航 -->
    <div class="detail-nav">
      <button class="detail-nav__back" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <h1 class="detail-nav__title">{{ navTitle }}</h1>
      <a v-if="question && question.url" class="detail-nav__link" :href="question.url" target="_blank" rel="noopener noreferrer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
      </a>
      <div v-else class="detail-nav__placeholder"></div>
    </div>

    <!-- 加载中 -->
    <div class="loading-state" v-if="loading">
      <div class="loading-spinner"></div>
      <p>正在加载文章内容...</p>
    </div>

    <template v-else-if="question">
      <!-- 文章头部信息 -->
      <div class="article-header">
        <div class="article-header__badges">
          <span class="badge badge--source" :class="'badge--' + (question.source || 'juejin')">
            {{ question.sourceLabel || '掘金' }}
          </span>
          <span class="badge badge--tag" :style="{ background: question.tagBg, color: question.tagColor }">
            {{ question.tag }}
          </span>
        </div>
        <h2 class="article-header__title">{{ question.title || question.text }}</h2>
        <div class="article-header__meta">
          <span v-if="articleDetail && articleDetail.user">✍️ {{ articleDetail.user }}</span>
          <span v-if="articleDetail && articleDetail.reading_time">⏱ {{ articleDetail.reading_time }}分钟</span>
          <span v-if="question.views">👁 {{ formatNum(question.views) }}</span>
          <span v-if="question.likes">👍 {{ formatNum(question.likes) }}</span>
          <span v-if="question.comments">💬 {{ question.comments }}</span>
        </div>
        <!-- 标签 -->
        <div class="article-header__tags" v-if="displayTags.length">
          <span class="tech-tag" v-for="(t, i) in displayTags" :key="i">{{ t }}</span>
        </div>
      </div>

      <!-- 全文内容区（Dev.to 来源，站内直接阅读） -->
      <div class="article-body" v-if="articleDetail && articleDetail.body_html && !articleDetail.fallback">
        <div class="article-body__content" v-html="articleDetail.body_html"></div>
      </div>

      <!-- 摘要内容区（掘金来源，无法获取全文） -->
      <div class="article-summary" v-else-if="question.brief">
        <div class="article-summary__header">
          <span>📋</span>
          <h3>内容摘要</h3>
        </div>
        <p class="article-summary__text">{{ question.brief }}</p>
        <a class="read-original" :href="question.url" target="_blank" rel="noopener noreferrer" v-if="question.url">
          <span class="read-original__icon">🔗</span>
          <span class="read-original__text">阅读原文全文</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </a>
      </div>

      <!-- 相关知识点 -->
      <div class="tags-block" v-if="displayTags.length">
        <div class="tags-block__header">
          <span>🏷️</span>
          <h3>相关技术栈</h3>
        </div>
        <div class="tags-block__list">
          <span class="knowledge-tag" v-for="(t, i) in displayTags" :key="i">{{ t }}</span>
        </div>
      </div>
    </template>

  </div>
</template>

<script>
import { getArticleDetail } from '@/api/job'

export default {
  name: 'QuestionDetail',
  data() {
    return {
      question: null,
      articleDetail: null,
      loading: false
    }
  },
  computed: {
    navTitle() {
      if (!this.question) return '文章详情'
      return this.question.sourceLabel === 'Dev.to' ? '技术博文' : '技术热文'
    },
    displayTags() {
      if (!this.question) return []
      return (this.question.tags || []).filter(Boolean)
    }
  },
  async created() {
    const q = this.$route.query
    if (q && q.data) {
      try {
        this.question = JSON.parse(decodeURIComponent(q.data))
        // 如果文章支持全文阅读，自动加载内容
        if (this.question.hasContent) {
          await this.loadArticleContent()
        }
      } catch (e) {
        console.warn('解析数据失败', e)
        this.$router.replace('/dashboard')
      }
    } else {
      this.$router.replace('/dashboard')
    }
  },
  methods: {
    async loadArticleContent() {
      this.loading = true
      try {
        const res = await getArticleDetail(this.question.id, this.question.source)
        // 响应拦截器已自动解包
        this.articleDetail = Array.isArray(res) ? null : (res || null)
      } catch (e) {
        console.warn('加载文章内容失败', e)
      } finally {
        this.loading = false
      }
    },
    formatNum(n) {
      if (!n) return '0'
      if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
      if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
      return String(n)
    }
  }
}
</script>

<style lang="scss" scoped>
.article-detail-page {
  min-height: 100vh;
  background: #f1f5f9;
  padding-bottom: 90px;
}

// 顶部导航
.detail-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  z-index: 10;

  &__back, &__link {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    cursor: pointer;
    border-radius: 50%;
    text-decoration: none;
    color: #0f172a;
    transition: background 0.2s;

    svg { width: 20px; height: 20px; }
    &:hover { background: #f5f5f5; }
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: #0f172a;
  }

  &__placeholder { width: 36px; }
}

// 加载状态
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  gap: 16px;
  color: #64748b;
  font-size: 14px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 文章头部
.article-header {
  background: white;
  padding: 20px 16px 16px;

  &__badges {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }

  &__title {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.5;
    margin: 0 0 12px;
  }

  &__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 13px;
    color: #64748b;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
  }
}

.badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 20px;
  font-weight: 600;
  letter-spacing: 0.3px;

  &--juejin {
    background: #1E80FF;
    color: white;
  }

  &--devto {
    background: #0a0a0a;
    color: white;
  }

  &--tag {
    font-weight: 500;
  }
}

.tech-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 16px;
  background: #f0f0ff;
  color: #6366f1;
  font-weight: 500;
}

// 全文内容区
.article-body {
  margin: 12px 0;
  background: white;
  padding: 20px 16px;

  &__content {
    font-size: 15px;
    line-height: 1.85;
    color: #1e293b;
    word-break: break-word;

    // 全局样式覆盖 v-html 中的元素
    :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
      margin: 24px 0 12px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.4;
    }
    :deep(h1) { font-size: 22px; }
    :deep(h2) { font-size: 19px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
    :deep(h3) { font-size: 17px; }

    :deep(p) {
      margin: 10px 0;
    }

    :deep(a) {
      color: #6366f1;
      text-decoration: none;
      &:hover { text-decoration: underline; }
    }

    :deep(code) {
      background: #f1f5f9;
      color: #e11d48;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }

    :deep(pre) {
      background: #1e293b;
      color: #e2e8f0;
      padding: 16px;
      border-radius: 10px;
      overflow-x: auto;
      margin: 16px 0;
      font-size: 13px;
      line-height: 1.6;

      code {
        background: none;
        color: inherit;
        padding: 0;
        font-size: inherit;
      }
    }

    :deep(blockquote) {
      border-left: 3px solid #6366f1;
      margin: 16px 0;
      padding: 8px 16px;
      background: #f8fafc;
      color: #475569;
      border-radius: 0 8px 8px 0;
    }

    :deep(ul), :deep(ol) {
      padding-left: 20px;
      margin: 10px 0;
    }

    :deep(li) {
      margin: 6px 0;
    }

    :deep(img) {
      max-width: 100%;
      border-radius: 8px;
      margin: 12px 0;
    }

    :deep(table) {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 13px;
    }

    :deep(th), :deep(td) {
      border: 1px solid #e2e8f0;
      padding: 8px 12px;
      text-align: left;
    }

    :deep(th) {
      background: #f8fafc;
      font-weight: 600;
    }

    :deep(hr) {
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20px 0;
    }

    :deep(strong) {
      font-weight: 600;
      color: #0f172a;
    }
  }
}

// 摘要区（掘金等无全文来源）
.article-summary {
  margin: 12px 16px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);

  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    h3 { font-size: 15px; font-weight: 600; color: #0f172a; margin: 0; }
  }

  &__text {
    font-size: 14px;
    line-height: 1.8;
    color: #374151;
    margin: 0 0 16px;
  }
}

.read-original {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  border-radius: 10px;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;

  &__icon { font-size: 16px; }
  &__text { flex: 1; font-size: 14px; font-weight: 500; color: #6366f1; }
  svg { color: #6366f1; }
  &:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15); }
}

// 标签区
.tags-block {
  margin: 12px 16px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);

  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    h3 { font-size: 15px; font-weight: 600; color: #0f172a; margin: 0; }
  }

  &__list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.knowledge-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: #f0f0ff;
  color: #6366f1;
  font-weight: 500;
}

// 底部操作
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 13px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.3s;

  &--primary {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    &:hover { box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4); transform: translateY(-1px); }
  }

  &--secondary {
    background: #f5f5f5;
    color: #475569;
    &:hover { background: #ebebeb; }
  }
}
</style>
