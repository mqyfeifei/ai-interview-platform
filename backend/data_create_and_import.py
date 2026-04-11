import os
import sys
import yaml
from sentence_transformers import SentenceTransformer

# 确保能正确导入 app (根据你的项目结构可能需要调整路径)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.job import Job, DEFAULT_JOBS
from app.models.interview import Dimension
from app.models.prompt import AiPrompt
from app.models.learning import KnowledgeTag, Resource
from app.models.question import Question
from app.models.example import Example

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

JOB_PS = {
    'backend': {
        'name': 'Java后端开发',
        'prompt_name': '资深Java架构师',
        'role_description': '一位拥有10年大厂经验的Java架构师，侧重考察底层原理与高并发场景。',
        'system_prompt': '你是一位拥有10年阿里/腾讯经验的资深Java架构师。你面试不仅看重API的使用，更看重候选人对JVM、多线程、Redis底层结构及高并发场景架构设计的理解。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
        'questioning_style': '犀利、专业，喜欢连环追问底层原理。',
        'greeting_message': '你好，我是今天的面试官。我看你投递了Java后端开发岗位，咱们直接切入正题，先从你熟悉的Java基础或者中间件开始聊起吧？',
        'temperature': 0.7
    },
    'frontend': {
        'name': 'Web前端开发',
        'prompt_name': '前端技术专家',
        'role_description': '精通Vue/React源码与前端工程化的专家，关注性能优化与交互体验。',
        'system_prompt': '你是一位资深前端开发专家。你不仅关注页面实现，更关注候选人对JS闭包/原型链、Vue/React底层响应式原理、Webpack/Vite打包工程化以及前端性能优化的掌握。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
        'questioning_style': '注重细节，喜欢结合实际业务场景（如白屏优化、组件封装）进行提问。',
        'greeting_message': '你好，欢迎参加Web前端岗位的面试。前端技术日新月异，咱们今天就重点聊聊JS核心基础、框架原理以及你在前端工程化方面的实践吧。',
        'temperature': 0.7
    },
    'cv': {
        'name': '计算机视觉',
        'prompt_name': 'AI视觉科学家',
        'role_description': '深耕CV领域的科学家，关注模型结构、前沿算法及端侧部署落地能力。',
        'system_prompt': '你是一位计算机视觉（CV）领域的AI科学家。你需要考察候选人对CNN/Transformer架构的理解，以及目标检测/图像分割领域的经典算法。同时，要关注模型轻量化与工程部署（如TensorRT）的落地经验。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
        'questioning_style': '严谨、学术，注重数学推导与模型落地的平衡。',
        'greeting_message': '你好，很高兴和你聊聊计算机视觉方向。平时主要是做检测还是分割？我们可以从你最熟悉的经典模型架构或者你的模型部署经验开始聊起。',
        'temperature': 0.5  # 算法岗位调低 temperature，让大模型的回答更精确严谨
    },
    'network': {
        'name': '网络工程',
        'prompt_name': '资深网络架构师',
        'role_description': '精通网络协议栈与大型数据中心网络设计的架构师。',
        'system_prompt': '你是一位资深网络架构师。你需要考察候选人对TCP/IP协议栈、OSPF/BGP等动态路由协议的深度理解，以及在大型网络故障排查、SD-WAN或云计算网络方向的实战经验。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
        'questioning_style': '稳重、务实，侧重排障逻辑与网络拓扑设计。',
        'greeting_message': '你好。网络工程师需要极其扎实的底层基础，咱们今天就从最核心的TCP/IP协议栈和路由协议开始，聊聊你的网络架构和排障经验吧。',
        'temperature': 0.6
    },
    'qa': {
        'name': '测试开发',
        'prompt_name': '高级测试开发工程师',
        'role_description': '侧重自动化测试工具开发与全链路质量保障的测开专家。',
        'system_prompt': '你是一位高级测试开发专家。你不能只问手工测试，必须重点考察候选人的自动化测试能力（UI/接口）、白盒代码测试能力、CI/CD流水线集成经验以及发现深层Bug的思维逻辑。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
        'questioning_style': '细致、全面，极度注重边界条件与异常情况的考察。',
        'greeting_message': '你好，欢迎来到测开岗位的面试。对于测开来说，开发能力和质量保障思维同等重要。咱们今天重点聊聊你的接口自动化落地经验以及CI/CD实践。',
        'temperature': 0.7
    }
}


def create_prompts():
    """批量创建所有的目标岗位及对应的专属AI提示词"""

    print("👔 正在创建岗位及专属 AI 提示词配置...")
    for domain_key, info in JOB_PS.items():
        # 直接去数据库中寻找由 get_or_create_job 创建好的岗位
        job = Job.query.filter_by(name=info['name']).first()
        if not job:
            print(f"  ⚠️ 警告：未找到岗位【{info['name']}】，跳过其提示词创建。")
            continue

        # 写入岗位专属提示词
        prompt = AiPrompt(
            name=info['prompt_name'],
            job_id=job.id,
            role_description=info['role_description'],
            system_prompt=info['system_prompt'],
            greeting_message=info['greeting_message'],
            questioning_style=info['questioning_style'],
            temperature=float(info['temperature']),
            is_active=True
        )
        db.session.add(prompt)
        print(f"  👉 已为岗位 [{info['name']}] 绑定专属面试官: {info['prompt_name']}")
        db.session.commit()


def clear_existing_data():
    """级联清空知识库相关的表数据（兼容 PostgreSQL / MySQL / SQLite）。

    策略：
    - PostgreSQL: 使用 TRUNCATE ... RESTART IDENTITY CASCADE（速度最快，且会级联清理并重置序列）
    - MySQL: 暂时禁用外键检查，逐表 DELETE 并重置 AUTO_INCREMENT
    - SQLite: 逐表 DELETE 并清理 sqlite_sequence
    - 其他: 退回到逐表 DELETE

    为安全起见，会按 metadata.sorted_tables 的反序（子表先）清理，并跳过重要表（如 users、alembic_version）。
    """
    print("🧹 正在清空旧数据...")

    # 不要删除的表（按需扩展）
    SKIP_TABLES = {"users", "alembic_version"}

    try:
        dialect = db.engine.dialect.name
        print(f"当前数据库方言: {dialect}")

        # 按依赖关系反向排序：子表通常在前，父表在后，方便逐表删除
        all_tables = list(reversed(db.metadata.sorted_tables))
        tables_to_clear = [t for t in all_tables if t.name not in SKIP_TABLES]

        if not tables_to_clear:
            print("⚠️ 未发现需要清空的表（或全部表被跳过）。")
            return

        if dialect == 'postgresql':
            # 使用 TRUNCATE ... RESTART IDENTITY CASCADE，效率高且级联
            table_names = ', '.join([f'"{t.name}"' for t in tables_to_clear])
            sql = f'TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE;'
            db.session.execute(db.text(sql))
            db.session.commit()

        elif dialect in ('mysql', 'mariadb'):
            # MySQL: 暂时关闭外键检查，逐表删除并重置自增
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS=0;'))
            for t in tables_to_clear:
                db.session.execute(t.delete())
                # 重置自增（仅当表包含自增列时生效）
                try:
                    db.session.execute(db.text(f'ALTER TABLE `{t.name}` AUTO_INCREMENT = 1;'))
                except Exception:
                    # 某些表或引擎可能不支持，忽略错误
                    pass
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS=1;'))
            db.session.commit()

        elif dialect == 'sqlite':
            # SQLite: 逐表 DELETE，并重置 sqlite_sequence
            for t in tables_to_clear:
                db.session.execute(t.delete())
            # 清理 sqlite_sequence 中的对应记录以重置 AUTOINCREMENT
            seq_names = ','.join([f"'{t.name}'" for t in tables_to_clear])
            try:
                db.session.execute(db.text(f"DELETE FROM sqlite_sequence WHERE name IN ({seq_names});"))
            except Exception:
                # sqlite_sequence 在某些 SQLite 空数据库中可能不存在
                pass
            db.session.commit()

        else:
            # 兜底：逐表删除
            for t in tables_to_clear:
                db.session.execute(t.delete())
            db.session.commit()

        print("✅ 旧数据已清空。")

    except Exception as e:
        # 回滚并打印错误以便诊断
        db.session.rollback()
        print("❌ 清空旧数据时发生错误:", str(e))
        raise


def get_or_create_job(domain_key):
    """根据领域 key 获取或创建目标岗位"""
    job_info = DEFAULT_JOBS.get(domain_key, {'name': f'{domain_key}工程师', 'desc': '自动生成的岗位'})
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
        # 0. 创建所有表（如果表已存在则忽略）
        print("正在检查并创建数据库表...")
        db.create_all()
        print("数据库表检查完成。")
        # 0. 清空旧数据
        clear_existing_data()

        # 1. 初始化评分维度 (Dimensions)
        if Dimension.query.count() == 0:
            print("正在初始化评分维度...")
            dimensions = [
                Dimension(name='技术正确性', description='回答中技术概念的准确程度'),
                Dimension(name='逻辑严谨性', description='回答结构是否清晰，逻辑是否自洽'),
                Dimension(name='岗位匹配度', description='回答是否符合目标岗位的要求'),
                Dimension(name='表达沟通', description='语言表达是否流畅、自信'),
                Dimension(name='应变能力', description='面对追问或未知问题的处理能力')
            ]
            db.session.add_all(dimensions)
            db.session.commit()
            print("评分维度初始化完成。")
        else:
            print("评分维度已存在，跳过。")

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
                            complexity, estimated_hours, resources = "Medium", 1, []
                        else:
                            point_name = pt.get('point')
                            complexity = pt.get('complexity', 'Medium')
                            estimated_hours = pt.get('estimated_hours', 1)
                            resources = pt.get('resources', [])

                        # 创建知识点标签
                        tag = KnowledgeTag.query.filter_by(name=point_name).first()
                        if not tag:
                            # 将模块名和知识点名结合，提升语义丰富度
                            tag_text_to_encode = f"模块: {category} 知识点: {point_name}"
                            tag_embedding = model.encode(tag_text_to_encode).tolist()

                            tag = KnowledgeTag(
                                name=point_name,
                                category=category,
                                complexity=complexity,            # 新增
                                estimated_hours=estimated_hours,  # 新增
                                embedding=tag_embedding           # 新增，存入向量
                            )
                            db.session.add(tag)
                            db.session.flush()
                        else:
                            updated = False
                            if not tag.category:
                                tag.category = category
                                updated = True
                            if not tag.complexity:
                                tag.complexity = complexity
                                updated = True
                            if not tag.estimated_hours:
                                tag.estimated_hours = estimated_hours
                                updated = True
                            if not tag.embedding:
                                tag.embedding = model.encode(f"模块: {category} 知识点: {point_name}").tolist()
                                updated = True
                            if updated:
                                db.session.add(tag)

                        # 遍历关联的学习资源
                        for res in resources:
                            res_title = res.get('name')
                            res_url = res.get('url')
                            yaml_type = res.get('type')

                            mapped_type = RESOURCE_TYPE_MAPPING.get(yaml_type, "article")
                            res_content = f"领域: {domain.upper()} | 所属模块: {category} | 知识点: {point_name} | 来源: {yaml_type}"
                            res_difficulty = res.get('complexity', complexity).lower()
                            res_embedding = model.encode(f"{res_title} {point_name} {category}").tolist()

                            resource_obj = Resource(
                                title=res_title,
                                type=mapped_type,
                                url=res_url,
                                content=res_content,
                                source=yaml_type,
                                difficulty=res_difficulty,
                                embedding=res_embedding
                            )
                            resource_obj.knowledge_tags.append(tag)
                            db.session.add(resource_obj)

                db.session.commit()

            # =====================================================================
            # 分支 B: 导入面试题库
            # =====================================================================
            elif 'questions' in ds_type:
                for item in data.get('items', []):
                    title = item.get('question', '')
                    tags = item.get('tags', [])
                    ki_type = item.get('type', 'technical')
                    difficulty = item.get('difficulty', 'medium')
                    key_points = item.get('key_points', [])
                    source = item.get('source', '')
                    status = item.get('status', 'draft')

                    # 组合用于向量化的文本
                    text_to_encode = f"问题: {title} 答案要点: {', '.join(key_points)}"
                    embedding = model.encode(text_to_encode).tolist()

                    # 写入 Question 表
                    q = Question(
                        job_id=job_id,
                        content=title,
                        type=ki_type,
                        difficulty=difficulty,
                        keywords=tags,
                        reference_answer=key_points, # 数据库已支持 JSONB 存储数组
                        source=source,               # 映射新增字段
                        status=status,               # 映射新增字段
                        embedding=embedding
                    )

                    # --- 自动语义匹配并绑定知识点 ---
                    # 利用 pgvector 的 cosine_distance 寻找最接近的 1 个或 2 个知识点
                    # 距离越小越相似 (要求 pgvector 安装正确且支持此语法)
                    similar_tags = KnowledgeTag.query.order_by(
                        KnowledgeTag.embedding.cosine_distance(embedding)
                    ).limit(1).all()
                    for stag in similar_tags:
                        q.knowledge_tags.append(stag)

                    db.session.add(q)
                db.session.commit()

            # =====================================================================
            # 分支 C: 导入优秀回答范例
            # =====================================================================
            elif 'examples' in ds_type or 'excellent_answer' in ds_type:
                for item in data.get('items', []):
                    title = item.get('question', '')
                    framework = item.get('framework', '无')
                    answer = item.get('answer', '')

                    # 组合用于向量化的文本（包含框架和具体回答）
                    text_to_encode = f"问题: {title} 框架: {framework} 回答内容: {answer}"
                    embedding = model.encode(text_to_encode).tolist()

                    # 写入 Example 表
                    example_obj = Example(
                        job_id=job_id,
                        question=title,
                        framework=framework,
                        answer=answer,
                        embedding=embedding
                    )
                    db.session.add(example_obj)
                db.session.commit()

            else:
                print(f"⚠️ 遇到未知的数据集类型: {ds_type}，跳过导入。")

        #5.导入提示词
        create_prompts()

        print("\n🎉 知识库自动化构建全部完成！所有领域的面试题、知识点和资源均已入库！")


if __name__ == '__main__':
    import_knowledge_base()