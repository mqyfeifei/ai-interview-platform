import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.prompt import AiPrompt
from app.models.interview import Interview, InterviewChat, Dimension, InterviewScore


class RealInterviewTestCase(unittest.TestCase):
    def setUp(self):
        """测试前置准备：直接连接开发数据库"""
        self.app = create_app('development')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # 1. 确保评分维度数据存在
        dimensions_names = ['技术正确性', '逻辑严谨性', '岗位匹配度', '表达沟通', '应变能力']
        for name in dimensions_names:
            if not Dimension.query.filter_by(name=name).first():
                db.session.add(Dimension(name=name, description=f'{name}测试维度'))
        db.session.commit()

        # 2. 准备测试用户
        self.user = User.query.filter_by(username="real_test_user").first()
        if not self.user:
            # 【修改点在此】：增加了 password_hash="test_hash"
            self.user = User(
                username="real_test_user",
                email="real@test.com",
                password_hash="test_hash"
            )
            db.session.add(self.user)
            db.session.commit()

        # 3. 准备测试岗位
        self.job = Job.query.filter_by(name="Java后端开发_RealTest").first()
        if not self.job:
            self.job = Job(name="Java后端开发_RealTest")
            db.session.add(self.job)
            db.session.commit()

        # 4. 准备测试 Prompt
        self.prompt = AiPrompt.query.filter_by(job_id=self.job.id).first()
        if not self.prompt:
            # 【修改点】：增加了 name="自动测试Prompt"
            self.prompt = AiPrompt(
                name="自动测试Prompt",
                job_id=self.job.id,
                system_prompt="你是严厉的面试官，请严格打分",
                greeting_message="测试开始",
                is_active=True
            )
            db.session.add(self.prompt)
            db.session.commit()
    def tearDown(self):
        """清理应用上下文，保留数据库数据以便查看"""
        self.app_context.pop()

    def test_real_interview_flow(self):
        """真实测试流程：启动 -> 模拟对话 -> 调用真实大模型打分 -> 查验数据库"""
        print("\n--- 开始真实集成测试 ---")

        # 步骤 1：启动面试
        response = self.client.post('/api/v1/interviews/start', json={
            "user_id": self.user.id,
            "job_id": self.job.id
        })
        start_data = response.get_json()
        self.assertEqual(response.status_code, 200)
        interview_id = start_data['data']['interview_id']
        print(f"1. 面试创建成功，数据库已写入，Interview ID: {interview_id}")

        # 步骤 2：向数据库直接插入模拟的对话记录，为大模型提供评分素材
        chat1 = InterviewChat(interview_id=interview_id, role='ai', content='请介绍一下 Java 中的 HashMap 原理。')
        chat2 = InterviewChat(interview_id=interview_id, role='user',
                              content='HashMap 基于数组加链表实现，Java 8 之后加入了红黑树来优化冲突。线程不安全。')
        db.session.add_all([chat1, chat2])
        db.session.commit()
        print("2. 模拟对话记录已写入数据库。")

        # 步骤 3：真实调用接口生成报告 (此步将消耗 Token 并需要网络等待)
        print("3. 正在请求 DeepSeek API 生成报告，请稍候...")
        finish_response = self.client.post(f'/api/v1/interviews/{interview_id}/finish')
        finish_data = finish_response.get_json()

        # 验证接口响应
        self.assertEqual(finish_response.status_code, 200)
        self.assertIn('total_score', finish_data['data'])
        print(f"4. API 返回成功！大模型给出的总分为: {finish_data['data']['total_score']}")

        # 步骤 4：查验数据库变化
        # 验证面试主表状态和分数
        updated_interview = Interview.query.get(interview_id)
        self.assertEqual(updated_interview.status, 'completed')
        self.assertIsNotNone(updated_interview.total_score)

        # 验证维度评分表是否写入
        scores = InterviewScore.query.filter_by(interview_id=interview_id).all()
        self.assertTrue(len(scores) > 0)

        print("5. 数据库验证通过：")
        print(f"   - 面试状态更新为: {updated_interview.status}")
        print(f"   - 面试总分写入为: {updated_interview.total_score}")
        print(f"   - 共写入 {len(scores)} 条维度评分记录。")
        for s in scores:
            dimension_name = Dimension.query.get(s.dimension_id).name
            print(f"     * {dimension_name}: {s.score}分 - 评语: {s.comment}")

        print("--- 测试完成，可前往数据库查看具体数据 ---")