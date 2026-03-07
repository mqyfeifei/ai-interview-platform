# backend/import_kb_v2.py
import os
import sys
import yaml
from sentence_transformers import SentenceTransformer

# 确保能正确导入 app (根据你的项目结构可能需要调整路径)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.job import Job
from app.models.knowledge import KnowledgeItem
from app.models.learning import KnowledgeTag, Resource

# 知识库基准路径配置 (当前脚本和 FuChuangTiKu 文件夹在同级)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FUCHUANG_DIR = os.path.join(BASE_DIR, 'FuChuangTiKu')
INDEX_YAML_PATH = os.path.join(FUCHUANG_DIR, 'index.yaml')

# 资源类型映射字典
RESOURCE_TYPE_MAPPING = {
    "视频": "video",
    "官方文档": "article",
    "技术博客": "article",
    "技术文章": "article",
    "书籍": "course",
    "快速入门": "article"
}

# 岗位信息映射
JOB_INFOS = {
    'backend': {'name': 'Java后端开发', 'desc': 'Java基础、并发、JVM、框架及中间件等'},
    'frontend': {'name': 'Web前端开发', 'desc': 'JS核心、Vue/React架构、工程化等'},
    'cv': {'name': '计算机视觉', 'desc': '经典机器学习、CNN/Transformer架构、工程部署优化等'},
    'network': {'name': '网络工程', 'desc': 'TCP/IP协议栈、OSPF/BGP路由控制、SD-WAN等'},
    'qa': {'name': '测试开发', 'desc': '白盒/黑盒理论、UI/接口自动化、性能调优等'}
}


def clear_existing_data():
    """级联清空知识库相关的表数据"""
    print("🧹 正在清空旧数据...")
    # 使用 TRUNCATE CASCADE 可以安全彻底地清空表，并重置自增 ID
    db.session.execute(db.text('TRUNCATE TABLE knowledge_items RESTART IDENTITY CASCADE;'))
    db.session.execute(db.text('TRUNCATE TABLE resources RESTART IDENTITY CASCADE;'))
    db.session.execute(db.text('TRUNCATE TABLE knowledge_tags RESTART IDENTITY CASCADE;'))
    db.session.commit()
    print("✅ 旧数据已清空。")


def get_or_create_job(domain_key):
    """根据领域 key 获取或创建目标岗位"""
    job_info = JOB_INFOS.get(domain_key, {'name': f'{domain_key}工程师', 'desc': '自动生成的岗位'})
    job_name = job_info['name']

    job = Job.query.filter_by(name=job_name).first()
    if not job:
        job = Job(name=job_name, description=job_info['desc'])
        db.session.add(job)
        db.session.commit()
    return job.id


def import_knowledge_base():
    app = create_app('development')

    with app.app_context():
        # 1. 清空旧数据
        clear_existing_data()

        # 2. 加载本地向量模型
        print("⏳ 正在加载向量模型 (BAAI/bge-small-zh-v1.5)...")
        model = SentenceTransformer('BAAI/bge-small-zh-v1.5', local_files_only=False)

        # 3. 读取全局索引文件
        if not os.path.exists(INDEX_YAML_PATH):
            print(f"❌ 找不到索引文件: {INDEX_YAML_PATH}")
            return

        with open(INDEX_YAML_PATH, 'r', encoding='utf-8') as f:
            index_data = yaml.safe_load(f)

        datasets = index_data.get('datasets', [])
        print(f"🔍 发现 {len(datasets)} 个数据集，准备开始导入...\n")

        # 4. 遍历所有数据集并进行分类导入
        for dataset in datasets:
            ds_type = dataset.get('type', '')
            ds_path = os.path.join(FUCHUANG_DIR, dataset.get('path', ''))

            # 从类型后缀解析领域 (如 technical_interview_questions_backend -> backend)
            domain = ds_type.split('_')[-1]
            job_id = get_or_create_job(domain)

            if not os.path.exists(ds_path):
                print(f"⚠️ [跳过] 找不到文件: {ds_path}")
                continue

            print(f"📖 正在解析导入: [{domain.upper()}] {ds_path}")
            with open(ds_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # =====================================================================
            # 分支 A: 导入知识点及学习资源
            # =====================================================================
            if 'knowledge_points' in ds_type:
                for module in data.get('modules', []):
                    category = module.get('name')

                    for pt in module.get('points', []):
                        if isinstance(pt, str):
                            point_name = pt
                            resources = []
                        else:
                            point_name = pt.get('point')
                            resources = pt.get('resources', [])

                        # 创建知识点标签
                        tag = KnowledgeTag.query.filter_by(name=point_name).first()
                        if not tag:
                            tag = KnowledgeTag(name=point_name, category=category)
                            db.session.add(tag)
                            db.session.flush()

                        # 遍历关联的学习资源
                        for res in resources:
                            res_title = res.get('name')
                            res_url = res.get('url')
                            yaml_type = res.get('type')

                            mapped_type = RESOURCE_TYPE_MAPPING.get(yaml_type, "article")
                            res_content = f"领域: {domain.upper()} | 所属模块: {category} | 知识点: {point_name} | 来源: {yaml_type}"

                            res_embedding = model.encode(f"{res_title} {point_name} {category}").tolist()

                            resource_obj = Resource(
                                title=res_title,
                                type=mapped_type,
                                url=res_url,
                                content=res_content,
                                source=yaml_type,
                                difficulty="medium",
                                embedding=res_embedding
                            )
                            resource_obj.knowledge_tags.append(tag)
                            db.session.add(resource_obj)

                db.session.commit()

            # =====================================================================
            # 分支 B: 导入面试题库 / 优秀回答范例
            # =====================================================================
            else:
                for item in data.get('items', []):
                    title = item.get('question', '')
                    tags = item.get('tags', [])
                    ki_type = item.get('type', 'practice')

                    # 区别处理普通的题目 (含 key_points) 和 优秀回答范例 (含 answer)
                    if 'key_points' in item:
                        content = "\n".join([f"- {kp}" for kp in item.get('key_points', [])])
                        text_to_encode = f"问题: {title} 答案要点: {content}"
                    elif 'answer' in item:
                        framework = item.get('framework', '无')
                        content = f"回答框架: {framework}\n具体回答:\n{item.get('answer', '')}"
                        text_to_encode = f"问题: {title} 框架: {framework} 回答内容: {content}"
                        ki_type = f"example_{ki_type}" # 将其标记为范例题
                    else:
                        content = ""
                        text_to_encode = f"问题: {title}"

                    embedding = model.encode(text_to_encode).tolist()

                    ki = KnowledgeItem(
                        title=title,
                        content=content,
                        type=ki_type,
                        job_id=job_id,
                        tags=tags,
                        embedding=embedding
                    )
                    db.session.add(ki)
                db.session.commit()

        print("\n🎉 知识库自动化构建全部完成！所有领域的面试题、知识点和资源均已入库！")


if __name__ == '__main__':
    import_knowledge_base()