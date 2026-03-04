// =============================================
// 全局常量 - 集中管理，便于维护和后端对接
// =============================================

// Token存储Key
export const TOKEN_KEY = 'ai_interview_token'
export const USER_INFO_KEY = 'ai_interview_user'

// API基础地址（通过环境变量控制，见.env文件）
export const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || '/api'

// 岗位信息（与后端枚举保持一致）
export const JOB_TYPES = [
  {
    id: 'java-backend',
    name: 'Java后端开发',
    icon: '☕',
    color: '#F59E0B',
    colorBg: '#FEF3C7',
    description: '掌握Spring Boot、JVM、数据库等核心技术栈',
    techStack: ['Java', 'Spring Boot', 'MySQL', 'Redis', 'JVM'],
    questionTypes: ['系统设计', '算法题', 'JVM调优', '框架原理'],
    level: '中级',
    avgScore: 72
  },
  {
    id: 'web-frontend',
    name: 'Web前端开发',
    icon: '🎨',
    color: '#3B82F6',
    colorBg: '#DBEAFE',
    description: '精通Vue/React、工程化工具链和性能优化',
    techStack: ['Vue3', 'React', 'TypeScript', 'Webpack', 'CSS3'],
    questionTypes: ['框架原理', '浏览器原理', '性能优化', 'CSS布局'],
    level: '中级',
    avgScore: 75
  },
  {
    id: 'python-algorithm',
    name: 'Python算法工程师',
    icon: '🐍',
    color: '#10B981',
    colorBg: '#D1FAE5',
    description: '深入机器学习、数据处理和算法实现',
    techStack: ['Python', 'PyTorch', 'NumPy', 'Pandas', 'Sklearn'],
    questionTypes: ['算法推导', '模型选择', '代码实现', '场景设计'],
    level: '高级',
    avgScore: 68
  },
  {
    id: 'fullstack',
    name: '全栈开发工程师',
    icon: '⚡',
    color: '#8B5CF6',
    colorBg: '#F5F3FF',
    description: '前后端全链路开发能力，熟悉微服务架构',
    techStack: ['Node.js', 'Vue3', 'Docker', 'MySQL', 'Redis'],
    questionTypes: ['架构设计', '前后端联调', '性能优化', '安全'],
    level: '中级',
    avgScore: 70
  },
  {
    id: 'android',
    name: 'Android开发',
    icon: '🤖',
    color: '#EF4444',
    colorBg: '#FEE2E2',
    description: '原生Android开发、Kotlin及性能调优',
    techStack: ['Kotlin', 'Jetpack', 'MVVM', 'OkHttp', 'Room'],
    questionTypes: ['Activity生命周期', 'Kotlin协程', '性能优化', 'UI绘制'],
    level: '中级',
    avgScore: 71
  },
  {
    id: 'devops',
    name: 'DevOps工程师',
    icon: '🛠️',
    color: '#6366F1',
    colorBg: '#EEF2FF',
    description: '持续集成、容器化部署和云原生实践',
    techStack: ['Docker', 'K8s', 'Jenkins', 'Linux', 'Ansible'],
    questionTypes: ['CI/CD流程', '容器编排', '监控告警', '网络安全'],
    level: '高级',
    avgScore: 66
  }
]

// 年级选项
export const GRADE_OPTIONS = [
  { label: '大一', value: '大一' },
  { label: '大二', value: '大二' },
  { label: '大三', value: '大三' },
  { label: '大四', value: '大四' },
  { label: '研一', value: '研一' },
  { label: '研二', value: '研二' },
  { label: '研三', value: '研三' },
  { label: '其他', value: '其他' }
]

// 面试维度（与后端评分维度对应）
export const INTERVIEW_DIMENSIONS = [
  { key: 'technical', label: '技术正确性' },
  { key: 'logic', label: '逻辑严谨性' },
  { key: 'matching', label: '岗位匹配度' },
  { key: 'expression', label: '表达沟通' },
  { key: 'adaptability', label: '应变能力' }
]

// 分页大小
export const PAGE_SIZE = 10

// 面试默认题数
export const DEFAULT_QUESTION_COUNT = 10

// 面试每题时限（秒）
export const DEFAULT_QUESTION_TIME_LIMIT = 120