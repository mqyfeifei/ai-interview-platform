import time
import unittest
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension


class ReportApiIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.created_user_ids = []
        self.created_interview_ids = []

    def tearDown(self):
        if self.created_interview_ids:
            Interview.query.filter(Interview.id.in_(self.created_interview_ids)).delete(synchronize_session=False)
        if self.created_user_ids:
            User.query.filter(User.id.in_(self.created_user_ids)).delete(synchronize_session=False)
        db.session.commit()
        self.app_context.pop()

    @staticmethod
    def _ensure_job(name='Java后端开发'):
        job = Job.query.filter_by(name=name).first()
        if not job:
            job = Job(name=name, description='测试岗位', tech_stack=['Java', 'Spring Boot'])
            db.session.add(job)
            db.session.commit()
        return job

    @staticmethod
    def _ensure_dimensions():
        names = ['技术正确性', '逻辑严谨性', '岗位匹配度', '表达沟通', '应变能力']
        dim_map = {}
        for n in names:
            dim = Dimension.query.filter_by(name=n).first()
            if not dim:
                dim = Dimension(name=n, description=f'{n}维度')
                db.session.add(dim)
                db.session.flush()
            dim_map[n] = dim
        db.session.commit()
        return dim_map

    def _register_and_login(self):
        ts = int(time.time() * 1000)
        payload = {
            "username": f"report_user_{ts}",
            "real_name": "报告测试用户",
            "school": "测试大学",
            "major": "软件工程",
            "grade": "大三",
            "email": f"report_{ts}@example.com",
            "phone": f"1{str(ts)[-10:]}",
            "password": "Test@123456"
        }
        reg = self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(reg.status_code, 200)
        user_id = reg.get_json()['data']['user']['id']
        self.created_user_ids.append(user_id)

        login = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": payload['password']
        })
        self.assertEqual(login.status_code, 200)
        token = login.get_json()['data']['token']
        return user_id, token

    def _create_completed_interview(self, user_id, job_id):
        interview = Interview(
            user_id=user_id,
            job_id=job_id,
            status='completed',
            total_score=84,
            question_count=2,
            start_time=datetime.utcnow() - timedelta(minutes=10),
            end_time=datetime.utcnow(),
            used_time=600,
            evaluation_highlights='亮点A\n亮点B',
            evaluation_improvements='改进点A\n改进点B',
            evaluation_suggestions='建议A\n建议B'
        )
        db.session.add(interview)
        db.session.flush()

        db.session.add_all([
            InterviewChat(interview_id=interview.id, role='ai', content='请自我介绍。'),
            InterviewChat(interview_id=interview.id, role='user', content='我是后端开发。'),
            InterviewChat(interview_id=interview.id, role='ai', content='请说明JVM内存模型。'),
            InterviewChat(interview_id=interview.id, role='user', content='堆栈方法区。')
        ])

        dim_map = self._ensure_dimensions()
        db.session.add_all([
            InterviewScore(interview_id=interview.id, dimension_id=dim_map['技术正确性'].id, score=85, comment='较好'),
            InterviewScore(interview_id=interview.id, dimension_id=dim_map['逻辑严谨性'].id, score=80, comment='较好'),
            InterviewScore(interview_id=interview.id, dimension_id=dim_map['岗位匹配度'].id, score=88, comment='较好'),
            InterviewScore(interview_id=interview.id, dimension_id=dim_map['表达沟通'].id, score=82, comment='较好'),
            InterviewScore(interview_id=interview.id, dimension_id=dim_map['应变能力'].id, score=84, comment='较好')
        ])
        db.session.commit()
        self.created_interview_ids.append(interview.id)
        return interview.id

    def test_get_report_detail(self):
        user_id, token = self._register_and_login()
        job = self._ensure_job('Java后端开发')
        report_id = self._create_completed_interview(user_id, job.id)

        resp = self.client.get(f'/api/v1/reports/{report_id}', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['code'], 200)
        self.assertEqual(body['data']['id'], report_id)
        self.assertIn('dimensions', body['data'])
        self.assertIn('avgDimensions', body['data'])
        self.assertIn('suggestions', body['data'])
        self.assertEqual(body['data']['suggestions'], ['建议A', '建议B'])
        self.assertIn('questions', body['data'])

    def test_list_reports(self):
        user_id, token = self._register_and_login()
        job = self._ensure_job('Java后端开发')
        self._create_completed_interview(user_id, job.id)

        resp = self.client.get('/api/v1/reports?page=1&pageSize=10', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['code'], 200)
        self.assertGreaterEqual(body['data']['total'], 1)
        self.assertTrue(len(body['data']['list']) >= 1)


if __name__ == '__main__':
    unittest.main()
