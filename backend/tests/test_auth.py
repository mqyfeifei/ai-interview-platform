import time
import unittest

from app import create_app
from app.extensions import db
from app.models.user import User


class AuthIntegrationTestCase(unittest.TestCase):
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

    def _build_register_payload(self):
        ts = int(time.time() * 1000)
        phone_tail = str(ts)[-10:]
        return {
            "username": f"auth_test_{ts}",
            "real_name": "测试用户",
            "school": "测试大学",
            "major": "软件工程",
            "grade": "大三",
            "email": f"auth_{ts}@example.com",
            "phone": f"1{phone_tail}",
            "password": "Test@123456"
        }

    def test_register_persist_to_database(self):
        payload = self._build_register_payload()
        response = self.client.post('/api/v1/auth/register', json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body.get('code'), 200)
        self.assertIn('data', body)
        self.assertIn('token', body['data'])

        user_id = body['data']['user']['id']
        self.created_user_ids.append(user_id)

        user_in_db = User.query.get(user_id)
        self.assertIsNotNone(user_in_db)
        self.assertEqual(user_in_db.email, payload['email'])
        self.assertEqual(user_in_db.phone, payload['phone'])
        self.assertEqual(user_in_db.real_name, payload['real_name'])

    def test_login_with_password(self):
        payload = self._build_register_payload()
        register_resp = self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(register_resp.status_code, 200)

        user_id = register_resp.get_json()['data']['user']['id']
        self.created_user_ids.append(user_id)

        login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": payload['password']
        })
        self.assertEqual(login_resp.status_code, 200)
        login_body = login_resp.get_json()
        self.assertEqual(login_body.get('code'), 200)
        self.assertTrue(login_body['data']['token'])
        self.assertEqual(login_body['data']['user']['id'], user_id)

    def test_login_with_wrong_password_should_fail(self):
        payload = self._build_register_payload()
        register_resp = self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(register_resp.status_code, 200)

        user_id = register_resp.get_json()['data']['user']['id']
        self.created_user_ids.append(user_id)

        login_resp = self.client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": "WrongPass@123"
        })
        self.assertEqual(login_resp.status_code, 400)
        login_body = login_resp.get_json()
        self.assertEqual(login_body.get('code'), 400)
        self.assertIn('账号或密码错误', login_body.get('msg', ''))

if __name__ == '__main__':
    unittest.main()
