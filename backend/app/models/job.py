
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from .associations import job_tags, job_questions

# ================= 新增：全局统一的岗位映射字典 =================
# 集中维护岗位默认映射，避免在导入脚本和 API 路由中重复硬编码
DEFAULT_JOBS = {
    'backend': {
        'name': 'Java后端开发', 
        'desc': 'Java基础、并发、JVM、框架及中间件等',
        'tech_stack': ['Java', 'Spring Boot', 'Spring MVC', 'Spring Security', 'Spring Data', 'JVM', 'MySQL', 'Redis', 'Spring Cloud', 'Kafka', 'RabbitMQ', 'Docker', '分布式事务', '微服务', '并发编程', '消息队列', '工程化', '可观测性'],
        'icon_url': 'job_icon/backend.png'
    },
    'frontend': {
        'name': 'Web前端开发', 
        'desc': 'JS核心、Vue/React架构、工程化等',
        'tech_stack': ['JavaScript', 'HTML5', 'CSS3', 'Vue.js', 'React', 'Webpack', 'Vite', 'ES6+', 'Promise', 'async/await', 'BFC', 'Flexbox', 'Grid', '响应式设计', '浏览器渲染原理', 'CORS', '前端安全'],
        'icon_url': 'job_icon/frontend.png'
    },
    'cv': {
        'name': '计算机视觉', 
        'desc': '经典机器学习、CNN/Transformer架构、工程部署优化等',
        'tech_stack': ['Python', 'PyTorch', 'TensorFlow', 'OpenCV', 'CNN', 'Transformer', 'ResNet', 'ViT', 'YOLO', 'Mask R-CNN', 'SAM', 'ONNX', 'TensorRT', '图像处理', '特征提取', '多模态', '生成式AI'],
        'icon_url': 'job_icon/cv.png'
    },
    'network': {
        'name': '网络工程', 
        'desc': 'TCP/IP协议栈、OSPF/BGP路由控制、SD-WAN等',
        'tech_stack': ['TCP/IP', 'HTTP/HTTPS', 'OSPF', 'BGP', 'VLAN', 'STP', 'LACP', 'Spine-Leaf', 'VXLAN', 'EVPN', 'SDN', 'SD-WAN', 'WLAN', 'Wi-Fi 6', '网络自动化', 'Ansible', 'Netconf'],
        'icon_url': 'job_icon/network.png'
    },
    'qa': {
        'name': '测试开发', 
        'desc': '白盒/黑盒理论、UI/接口自动化、性能调优等',
        'tech_stack': ['Python', 'Selenium', 'Playwright', 'Appium', 'Postman', 'JMeter', 'JUnit', 'Jenkins', 'GitLab CI', 'Docker', 'Linux', 'Shell', 'MySQL', 'Redis', '安全测试', '性能测试', '持续集成'],
        'icon_url': 'job_icon/qa.png'
    }
}
# ==============================================================


# ======== 新增：统一的 Job 转前端 Key 方法 ========
def get_job_front_key(job):
    if not job:
        return None
    # 精确匹配（修复了原来 value 和 job.name 对比的 bug）
    for key, info in DEFAULT_JOBS.items():
        if info['name'] == job.name:
            return key

    # 兼容性/模糊匹配兜底
    name = (job.name or '').lower()
    if 'java' in name or '后端' in name or 'backend' in name:
        return 'backend'
    if '前端' in name or 'frontend' in name or 'web' in name:
        return 'frontend'
    if '视觉' in name or 'cv' in name:
        return 'cv'
    if '网络' in name or 'network' in name:
        return 'network'
    if '测试' in name or 'qa' in name:
        return 'qa'
    return None
# =================================================


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 如 "Java后端开发"
    description = db.Column(db.Text)
    tech_stack = db.Column(JSONB)  # JSON数组存储技术栈
    icon_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系：岗位知识大纲（Job <-> KnowledgeTag）
    knowledge_tags = db.relationship(
        'KnowledgeTag',
        secondary=job_tags,
        backref=db.backref('jobs', lazy='dynamic'),
        lazy='dynamic'
    )

    # 关系：岗位题库（Job <-> Question）
    questions = db.relationship(
        'Question',
        secondary=job_questions,
        back_populates='jobs',
        lazy='dynamic'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tech_stack': self.tech_stack,
            'icon_url': self.icon_url
        }