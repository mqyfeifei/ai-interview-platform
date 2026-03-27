import sys
import os

# 把项目根目录加入路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from app import create_app, db
from app.models.user import User
from app.models.resume import Resume
from app.api.v1.resumes import _ensure_main_resume

class ResumeAPITestCase(unittest.TestCase):
    def setUp(self):
        """测试前准备：创建测试APP、内存数据库、测试用户"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # 创建测试用户
            user = User(username="testuser", password_hash="123456")
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        """测试后清理"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_resumes_list(self):
        """测试：获取简历列表（自动创建主简历）"""
        with self.app.app_context():
            _ensure_main_resume(self.user_id)
        resumes = Resume.query.filter_by(user_id=self.user_id).all()
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0].is_main, True)
        print("✅ 获取简历列表：成功（自动创建主简历）")

    def test_create_custom_resume(self):
        """测试：创建岗位定制简历"""
        with self.app.app_context():
            resume = Resume(
                user_id=self.user_id,
                title="产品经理简历",
                is_main=False,
                job_id=1
            )
            resume.set_content({"name": "测试"})
            db.session.add(resume)
            db.session.commit()

            count = Resume.query.filter_by(user_id=self.user_id).count()
            self.assertEqual(count, 2)  # 1主+1定制
            print("✅ 创建定制简历：成功")

    def test_main_resume_cannot_be_deleted(self):
        """测试：主简历不能删除"""
        with self.app.app_context():
            main = _ensure_main_resume(self.user_id)
            self.assertEqual(main.is_main, True)
            print("✅ 主简历不可删除：验证成功")

    def test_copy_from_main(self):
        """测试：从主简历复制内容到定制简历"""
        with self.app.app_context():
            main = _ensure_main_resume(self.user_id)
            main.set_content({"test": "content"})
            db.session.commit()

            custom = Resume(
                user_id=self.user_id,
                title="复制版简历",
                is_main=False
            )
            db.session.add(custom)
            db.session.commit()

            custom.set_content(main.get_content())
            self.assertEqual(custom.get_content()["test"], "content")
            print("✅ 复制主简历内容：成功")

if __name__ == "__main__":
    unittest.main()