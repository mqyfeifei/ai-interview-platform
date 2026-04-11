import time
import unittest
from sqlalchemy import inspect

from app import create_app
from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewSessionConfig
from app.models.job import Job
from app.models.prompt import AiPrompt
from app.models.user import User


class TextInterviewStyleSelectionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        inspector = inspect(db.engine)
        interview_columns = {column['name'] for column in inspector.get_columns('interviews')}
        required_columns = {'graph_coverage_rate', 'graph_depth_rate'}
        if not required_columns.issubset(interview_columns):
            self.skipTest('数据库尚未执行最新迁移，请先运行 backend/scripts/upgrade_graph_db.py')

        ts = int(time.time() * 1000)
        self.username = f'style_test_user_{ts}'
        self.job_name = f'文字面试样式测试岗位_{ts}'

        self.user = User(
            username=self.username,
            email=f'{self.username}@example.com',
            password_hash='hash'
        )
        db.session.add(self.user)
        db.session.flush()
        self.user_id = self.user.id

        self.job = Job(
            name=self.job_name,
            description='文字面试样式测试岗位'
        )
        db.session.add(self.job)
        db.session.flush()
        self.job_id = self.job.id

        self.prompt = AiPrompt(
            name=f'{self.job_name}_Prompt',
            job_id=self.job_id,
            system_prompt='你是专业面试官，请按要求提问，当你认为评估充分时，在末尾输出[INTERVIEW_OVER]。',
            greeting_message='你好，我们开始今天的面试。',
            is_active=True,
        )
        db.session.add(self.prompt)
        db.session.commit()
        self.prompt_id = self.prompt.id

        self.created_interview_ids = []

    def tearDown(self):
        db.session.rollback()
        if self.created_interview_ids:
            InterviewChat.query.filter(InterviewChat.interview_id.in_(self.created_interview_ids)).delete(synchronize_session=False)
            InterviewSessionConfig.query.filter(InterviewSessionConfig.interview_id.in_(self.created_interview_ids)).delete(synchronize_session=False)
            Interview.query.filter(Interview.id.in_(self.created_interview_ids)).delete(synchronize_session=False)
            db.session.commit()

        User.query.filter_by(id=self.user_id).delete(synchronize_session=False)
        Job.query.filter_by(id=self.job_id).delete(synchronize_session=False)
        AiPrompt.query.filter_by(id=self.prompt_id).delete(synchronize_session=False)
        db.session.commit()
        self.app_context.pop()

    def _start_with_style(self, style_label):
        response = self.client.post('/api/v1/interviews/start', json={
            'user_id': self.user_id,
            'job_id': self.job_id,
            'voice_mode': False,
            'interview_style': style_label,
        })
        self.assertEqual(response.status_code, 200)

        body = response.get_json()
        self.assertEqual(body.get('code'), 200)
        data = body['data']
        interview_id = data['interview_id']
        self.created_interview_ids.append(interview_id)
        return data

    def _assert_style_case(self, style_label, expected_style, expected_tech_ratio, expected_scenario_ratio, expected_difficulty):
        data = self._start_with_style(style_label)

        self.assertIn('session_config', data)
        self.assertEqual(data['session_config']['interview_style'], expected_style)
        self.assertEqual(data['session_config']['tech_ratio'], expected_tech_ratio)
        self.assertEqual(data['session_config']['scenario_ratio'], expected_scenario_ratio)
        self.assertEqual(data['session_config']['difficulty_level'], expected_difficulty)

        interview_id = data['interview_id']
        session_config = InterviewSessionConfig.query.filter_by(interview_id=interview_id).first()
        self.assertIsNotNone(session_config)
        self.assertEqual(session_config.interview_style, expected_style)
        self.assertEqual(session_config.tech_ratio, expected_tech_ratio)
        self.assertEqual(session_config.scenario_ratio, expected_scenario_ratio)
        self.assertEqual(session_config.difficulty_level, expected_difficulty)

    def test_pressure_confident_teaching_styles(self):
        cases = [
            ('压力面', 'pressure', 70.0, 30.0, 3),
            ('自信面', 'confident', 60.0, 40.0, 2),
            ('教学面', 'teaching', 80.0, 20.0, 2),
        ]

        for style_label, expected_style, tech_ratio, scenario_ratio, difficulty in cases:
            with self.subTest(style=style_label):
                self._assert_style_case(style_label, expected_style, tech_ratio, scenario_ratio, difficulty)


if __name__ == '__main__':
    unittest.main()
