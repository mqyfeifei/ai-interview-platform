# backend/init_data.py
from app import create_app
from app.extensions import db
from app.models import Dimension, Job, AiPrompt

app = create_app()

def init_db():
    with app.app_context():
        # 1. 创建所有表（如果表已存在则忽略）
        print("正在检查并创建数据库表...")
        db.create_all()
        print("数据库表检查完成。")

        # 2. 初始化评分维度 (Dimensions)
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

        # 3. 初始化示例岗位 (Jobs) - 可选
        if Job.query.count() == 0:
            print("正在初始化示例岗位...")
            java_job = Job(
                name='Java后端开发',
                description='负责企业级后端系统开发',
                tech_stack=['Java', 'Spring Boot', 'MySQL', 'Redis']
            )
            frontend_job = Job(
                name='前端开发',
                description='负责Web端用户界面开发',
                tech_stack=['Vue', 'React', 'TypeScript', 'CSS']
            )
            db.session.add_all([java_job, frontend_job])
            db.session.commit()
            print("示例岗位初始化完成。")

        # 4. 初始化基础 Prompt (AiPrompt) - 可选
        if AiPrompt.query.count() == 0:
            print("正在初始化默认 Prompt...")
            default_prompt = AiPrompt(
                name='通用面试官',
                role_description='你是一位专业、客观的面试官。',
                system_prompt='请根据候选人的简历和回答进行专业面试。【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。',
                greeting_message='你好，我是你的面试官。请先做一个简单的自我介绍。',
                questioning_style='专业严谨'
            )
            db.session.add(default_prompt)
            db.session.commit()
            print("默认 Prompt 初始化完成。")

if __name__ == '__main__':
    init_db()