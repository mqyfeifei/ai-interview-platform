# backend/import_kb.py
import os
import sys
import yaml
from sentence_transformers import SentenceTransformer

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.job import Job
from app.models.knowledge import KnowledgeItem
from app.models.learning import KnowledgeTag, Resource

# 知识库 YAML 文件的相对路径配置
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
QUESTIONS_YAML_PATH = os.path.join(BASE_DIR, 'backend', 'FuChuangTiKu', 'FuChuangTiKu', 'data', 'questions', 'technical_interview_questions.yaml')
KNOWLEDGE_POINTS_YAML_PATH = os.path.join(BASE_DIR, 'backend','FuChuangTiKu', 'FuChuangTiKu', 'data', 'knowledge_points',
                                          'java_backend_knowledge_points.yaml')

# 资源类型映射字典
RESOURCE_TYPE_MAPPING = {
    "视频": "video",
    "官方文档": "article",
    "技术博客": "article",
    "技术文章": "article",
    "书籍": "course",
    "快速入门": "article"
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


def get_or_create_job():
    """获取目标岗位，如果没有则创建"""
    job = Job.query.filter_by(name="Java后端开发").first()
    if not job:
        job = Job(name="Java后端开发", description="Java基础、并发、JVM、框架及中间件等")
        db.session.add(job)
        db.session.commit()
    return job.id


def import_knowledge_base():
    app = create_app('development')

    with app.app_context():
        # 1. 清空旧数据
        clear_existing_data()
        job_id = get_or_create_job()

        # 2. 加载本地向量模型
        print("⏳ 正在加载向量模型 (BAAI/bge-small-zh-v1.5)...")
        model = SentenceTransformer('BAAI/bge-small-zh-v1.5', local_files_only=False)

        # =====================================================================
        # 3. 导入面试题 -> KnowledgeItem (用于面试中的追问与提示)
        # =====================================================================
        if os.path.exists(QUESTIONS_YAML_PATH):
            print(f"📖 正在导入面试题库: {QUESTIONS_YAML_PATH}")
            with open(QUESTIONS_YAML_PATH, 'r', encoding='utf-8') as f:
                questions_data = yaml.safe_load(f)

            for item in questions_data.get('items', []):
                title = item.get('question', '')
                # 将 key_points 拼接为文本段落
                content = "\n".join([f"- {kp}" for kp in item.get('key_points', [])])
                tags = item.get('tags', [])

                # 向量化题干+考点
                text_to_encode = f"问题: {title} 答案要点: {content}"
                embedding = model.encode(text_to_encode).tolist()

                ki = KnowledgeItem(
                    title=title,
                    content=content,
                    type='practice',  # 面试题类型
                    job_id=job_id,
                    tags=tags,
                    embedding=embedding
                )
                db.session.add(ki)
            db.session.commit()
            print("✅ 面试题库导入完成！")
        else:
            print(f"❌ 找不到面试题文件: {QUESTIONS_YAML_PATH}")

        # =====================================================================
        # 4. 导入知识点及学习资源 -> KnowledgeTag & Resource (用于学习中心推荐)
        # =====================================================================
        if os.path.exists(KNOWLEDGE_POINTS_YAML_PATH):
            print(f"📚 正在导入知识点及学习资源: {KNOWLEDGE_POINTS_YAML_PATH}")
            with open(KNOWLEDGE_POINTS_YAML_PATH, 'r', encoding='utf-8') as f:
                kp_data = yaml.safe_load(f)

            for module in kp_data.get('modules', []):
                category = module.get('name')

                for pt in module.get('points', []):
                    # 处理纯字符串知识点 或 包含资源的字典对象
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
                        db.session.flush()  # 获取 ID 供关联

                    # 遍历关联的学习资源
                    for res in resources:
                        res_title = res.get('name')
                        res_url = res.get('url')
                        yaml_type = res.get('type')

                        mapped_type = RESOURCE_TYPE_MAPPING.get(yaml_type, "article")
                        res_content = f"所属模块: {category} | 知识点: {point_name} | 来源: {yaml_type}"

                        # 资源向量化 (标题 + 知识点名称，为了实现基于弱项薄弱点的精准语义搜索)
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
                        # 绑定多对多关联
                        resource_obj.knowledge_tags.append(tag)
                        db.session.add(resource_obj)

            db.session.commit()
            print("✅ 知识点及学习资源导入完成！")
        else:
            print(f"❌ 找不到知识点文件: {KNOWLEDGE_POINTS_YAML_PATH}")

        print("\n🎉 知识库自动化构建全部完成！现在数据库已经拥有了富含向量的面试和学习数据。")


if __name__ == '__main__':
    import_knowledge_base()