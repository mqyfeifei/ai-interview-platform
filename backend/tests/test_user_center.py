import time
import unittest
import io

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job


class UserCenterIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.created_user_ids = []

    def tearDown(self):
        if self.created_user_ids:
            User.query.filter(User.id.in_(self.created_user_ids)).delete(synchronize_session=False)
            db.session.commit()
        self.app_context.pop()

    def _build_register_payload(self, with_phone=True):
        ts = int(time.time() * 1000)
        payload = {
            "username": f"uc_test_{ts}",
            "real_name": "个人中心测试",
            "school": "测试大学",
            "major": "软件工程",
            "grade": "大三",
            "email": f"uc_{ts}@example.com",
            "password": "Test@123456"
        }
        if with_phone:
            payload["phone"] = f"1{str(ts)[-10:]}"
        return payload

    def _register_and_login(self, with_phone=True):
        payload = self._build_register_payload(with_phone=with_phone)
        register_resp = self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(register_resp.status_code, 200)
        register_body = register_resp.get_json()
        user_id = register_body['data']['user']['id']
        self.created_user_ids.append(user_id)

        login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": payload['password']
        })
        self.assertEqual(login_resp.status_code, 200)
        login_body = login_resp.get_json()
        token = login_body['data']['token']
        return payload, user_id, token

    @staticmethod
    def _auth_header(token):
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _ensure_job(name='Java后端开发'):
        job = Job.query.filter_by(name=name).first()
        if not job:
            job = Job(name=name, description='测试岗位', tech_stack=['Java', 'Spring Boot'])
            db.session.add(job)
            db.session.commit()
        return job

    def test_get_and_update_profile(self):
        _, user_id, token = self._register_and_login()

        get_resp = self.client.get('/api/v1/users/me', headers=self._auth_header(token))
        self.assertEqual(get_resp.status_code, 200)
        get_body = get_resp.get_json()
        self.assertEqual(get_body['data']['id'], user_id)

        update_resp = self.client.put('/api/v1/users/me', headers=self._auth_header(token), json={
            "username": f"uc_profile_{user_id}",
            "nickname": "新昵称",
            "school": "新学校",
            "major": "人工智能",
            "grade": "研一",
            "avatar_url": "https://example.com/avatar.png"
        })
        self.assertEqual(update_resp.status_code, 200)
        update_body = update_resp.get_json()
        self.assertEqual(update_body['code'], 200)
        self.assertEqual(update_body['data']['school'], '新学校')

        user_in_db = db.session.get(User, user_id)
        self.assertEqual(user_in_db.username, f"uc_profile_{user_id}")
        self.assertEqual(user_in_db.real_name, '新昵称')
        self.assertEqual(user_in_db.major, '人工智能')

    def test_change_password(self):
        payload, _, token = self._register_and_login()

        change_resp = self.client.post('/api/v1/users/me/change-password', headers=self._auth_header(token), json={
            "oldPassword": payload['password'],
            "newPassword": "NewPass@123"
        })
        self.assertEqual(change_resp.status_code, 200)

        old_login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": payload['password']
        })
        self.assertEqual(old_login_resp.status_code, 400)

        new_login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": "NewPass@123"
        })
        self.assertEqual(new_login_resp.status_code, 200)

    def test_bind_phone(self):
        payload, user_id, token = self._register_and_login(with_phone=False)

        new_phone = f"1{str(int(time.time() * 1000))[-10:]}"
        bind_resp = self.client.post('/api/v1/users/me/bind-phone', headers=self._auth_header(token), json={
            "phone": new_phone
        })
        self.assertEqual(bind_resp.status_code, 200)
        bind_body = bind_resp.get_json()
        self.assertEqual(bind_body['code'], 200)
        self.assertEqual(bind_body['data']['phone'], new_phone)

        user_in_db = db.session.get(User, user_id)
        self.assertEqual(user_in_db.phone, new_phone)

        phone_login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": new_phone,
            "password": payload['password']
        })
        self.assertEqual(phone_login_resp.status_code, 200)

    def test_dashboard_and_default_job_preference(self):
        _, user_id, token = self._register_and_login(with_phone=True)
        self._ensure_job('Java后端开发')

        pref_resp = self.client.patch('/api/v1/users/me/preferences', headers=self._auth_header(token), json={
            "defaultJob": "java-backend"
        })
        self.assertEqual(pref_resp.status_code, 200)
        pref_body = pref_resp.get_json()
        self.assertEqual(pref_body['code'], 200)
        self.assertEqual(pref_body['data']['defaultJob'], 'java-backend')

        user_in_db = db.session.get(User, user_id)
        self.assertIsNotNone(user_in_db.default_job_id)

        me_resp = self.client.get('/api/v1/users/me', headers=self._auth_header(token))
        self.assertEqual(me_resp.status_code, 200)
        me_body = me_resp.get_json()
        self.assertEqual(me_body['data']['defaultJob'], 'java-backend')
        self.assertIn('createdAt', me_body['data'])

        dashboard_resp = self.client.get('/api/v1/users/me/dashboard', headers=self._auth_header(token))
        self.assertEqual(dashboard_resp.status_code, 200)
        dashboard_body = dashboard_resp.get_json()
        self.assertEqual(dashboard_body['code'], 200)
        self.assertIn('totalInterviews', dashboard_body['data'])
        self.assertIn('avgScore', dashboard_body['data'])
        self.assertIn('weeklyPractice', dashboard_body['data'])

    def test_list_jobs_should_return_all_rows(self):
        self._ensure_job('Java后端开发')
        self._ensure_job('前端开发')

        response = self.client.get('/api/v1/jobs')
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['code'], 200)
        self.assertIsInstance(body['data'], list)
        self.assertGreaterEqual(len(body['data']), 2)

    def test_upload_avatar_should_persist_avatar_url(self):
        _, user_id, token = self._register_and_login(with_phone=True)

        form_data = {
            'avatar': (io.BytesIO(b'fake-png-content'), 'avatar.png')
        }
        response = self.client.post(
            '/api/v1/users/me/avatar',
            headers=self._auth_header(token),
            data=form_data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['code'], 200)
        self.assertIn('avatarUrl', body['data'])
        self.assertTrue(body['data']['avatarUrl'].startswith('/uploads/avatars/'))

        user_in_db = db.session.get(User, user_id)
        self.assertIsNotNone(user_in_db.avatar_url)
        self.assertTrue(user_in_db.avatar_url.startswith('/uploads/avatars/'))


if __name__ == '__main__':
    unittest.main()
