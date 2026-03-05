import os
import sys
import json
import time
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.user import User


def build_register_payload():
    ts = int(time.time() * 1000)
    suffix = str(ts)[-10:]
    return {
        "username": f"avatar_test_{ts}",
        "real_name": "头像上传测试",
        "school": "测试大学",
        "major": "软件工程",
        "grade": "大三",
        "email": f"avatar_{ts}@example.com",
        "phone": f"1{suffix}",
        "password": "Test@123456"
    }


def resolve_upload_root(app):
    upload_root = app.config.get('UPLOAD_ROOT')
    if not upload_root:
        upload_root = os.path.join(app.root_path, 'uploads')
    return upload_root


def main(file_path, cleanup=False):
    app = create_app('development')
    client = app.test_client()

    input_path = Path(file_path).expanduser().resolve()
    if not input_path.exists() or not input_path.is_file():
        print(f"错误：文件不存在 -> {input_path}")
        return

    with app.app_context():
        payload = build_register_payload()

        reg_resp = client.post('/api/v1/auth/register', json=payload)
        reg_body = reg_resp.get_json() or {}
        print(f"注册接口状态码: {reg_resp.status_code}")
        if reg_resp.status_code != 200:
            print(json.dumps(reg_body, ensure_ascii=False, indent=2))
            return

        user_id = reg_body['data']['user']['id']
        login_resp = client.post('/api/v1/auth/login', json={
            "loginId": payload['email'],
            "password": payload['password']
        })
        login_body = login_resp.get_json() or {}
        print(f"登录接口状态码: {login_resp.status_code}")
        if login_resp.status_code != 200:
            print(json.dumps(login_body, ensure_ascii=False, indent=2))
            return

        token = login_body['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        before_user = db.session.get(User, user_id)
        before_avatar = before_user.avatar_url
        print(f"上传前数据库 avatar_url: {before_avatar}")

        with open(input_path, 'rb') as stream:
            upload_resp = client.post(
                '/api/v1/users/me/avatar',
                headers=headers,
                data={'avatar': (stream, input_path.name)},
                content_type='multipart/form-data'
            )

        upload_body = upload_resp.get_json() or {}
        print(f"上传接口状态码: {upload_resp.status_code}")
        print("上传接口返回:")
        print(json.dumps(upload_body, ensure_ascii=False, indent=2))

        after_user = db.session.get(User, user_id)
        after_avatar = after_user.avatar_url
        print(f"上传后数据库 avatar_url: {after_avatar}")

        upload_root = resolve_upload_root(app)
        file_exists = False
        if after_avatar and after_avatar.startswith('/uploads/'):
            relative_path = after_avatar.replace('/uploads/', '').replace('/', os.sep)
            physical_path = os.path.join(upload_root, relative_path)
            file_exists = os.path.exists(physical_path)
            print(f"头像文件物理路径: {physical_path}")
            print(f"头像文件是否存在: {file_exists}")

        if cleanup:
            if after_avatar and after_avatar.startswith('/uploads/'):
                relative_path = after_avatar.replace('/uploads/', '').replace('/', os.sep)
                physical_path = os.path.join(upload_root, relative_path)
                if os.path.exists(physical_path):
                    os.remove(physical_path)
            db.session.delete(after_user)
            db.session.commit()
            print("已清理测试用户及上传文件。")
        else:
            print("已保留测试用户和上传文件，便于你继续查看数据库变化。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='手动验证头像上传并观察数据库 avatar_url 字段变化')
    parser.add_argument('--file', type=str, default='', help='头像文件路径（不传则运行时输入）')
    parser.add_argument('--cleanup', action='store_true', help='验证后删除测试用户和上传文件')
    args = parser.parse_args()

    file_path = args.file.strip()
    if not file_path:
        file_path = input('请输入要上传的头像文件路径: ').strip().strip('"')

    main(file_path=file_path, cleanup=args.cleanup)
