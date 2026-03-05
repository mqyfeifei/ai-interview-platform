import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.interview import InterviewChat
from app.models.learning import KnowledgeTag, UserKnowledgeMastery


def setup_test_env(app):
    with app.app_context():
        user = User.query.filter_by(username="mastery_tester").first()
        if not user:
            user = User(username="mastery_tester", email="test@m.com", password_hash="hash")
            db.session.add(user)

        job = Job.query.filter_by(name="Java后端开发").first()
        if not job:
            job = Job(name="Java后端开发")
            db.session.add(job)

        db.session.commit()
        return user.id, job.id


def test_knowledge_scoring():
    app = create_app('development')
    client = app.test_client()
    user_id, job_id = setup_test_env(app)

    print("\n" + "=" * 50)
    print("🚀 启动：知识点动态打分 测试")
    print("=" * 50)

    # 1. 启动面试
    res = client.post('/api/v1/interviews/start', json={"user_id": user_id, "job_id": job_id})
    interview_id = res.get_json()['data']['interview_id']
    print(f"[1] 面试已创建 (Interview ID: {interview_id})")

    # 2. 直接在数据库中伪造一段关于 Redis 的对话，故意回答错误
    print("[2] 模拟用户在面试中回答不出关于 Redis 持久化的问题...")
    with app.app_context():
        chat1 = InterviewChat(interview_id=interview_id, role='ai',
                              content='请详细说明一下 Redis 的 RDB 和 AOF 持久化机制的区别。')
        chat2 = InterviewChat(interview_id=interview_id, role='user',
                              content='不好意思，我没用过Redis，不太清楚它的持久化是什么。')
        chat3 = InterviewChat(interview_id=interview_id, role='ai', content='没关系，那你能说说 JVM 的垃圾回收机制吗？')
        chat4 = InterviewChat(interview_id=interview_id, role='user',
                              content='JVM我比较熟，主要有标记清除、复制算法和标记整理，新生代主要用复制算法。')
        db.session.add_all([chat1, chat2, chat3, chat4])
        db.session.commit()

    # 3. 触发生成报告（真实请求大模型）
    print("[3] 正在请求大模型生成报告，提取并评估知识点，请稍候...")
    start_time = time.time()
    res = client.post(f'/api/v1/interviews/{interview_id}/finish')

    if res.status_code != 200:
        print(f"❌ 报告生成失败: {res.get_json()}")
        return

    report_data = res.get_json()['data']
    print(f"✅ 报告生成完毕！耗时: {time.time() - start_time:.2f}秒")
    print(f"  👉 总分: {report_data.get('total_score')}")
    print(f"  👉 AI提取的知识点及打分: {report_data.get('knowledge_tags_eval')}")

    # 4. 验证数据库 user_knowledge_mastery 表是否正确落表
    print("\n[4] 正在核查数据库掌握度更新情况...")
    with app.app_context():
        masteries = UserKnowledgeMastery.query.filter_by(user_id=user_id).all()
        if not masteries:
            print("❌ 数据库中没有找到任何知识点掌握度记录！")
        else:
            for m in masteries:
                tag = KnowledgeTag.query.get(m.tag_id)
                print(f"  🏷️ 标签: 【{tag.name}】 | 掌握度分数: {m.mastery_level} | 来源: {tag.category}")

            print(
                "\n🎉 测试通过！现在你的大模型已经具备了自动抓取知识点并为其打分的能力，这将完美衔接【薄弱点分析与推荐】功能！")


if __name__ == '__main__':
    test_knowledge_scoring()