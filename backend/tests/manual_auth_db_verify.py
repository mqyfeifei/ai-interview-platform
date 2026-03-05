import argparse
import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.extensions import db
from app.models.user import User


def build_payload():
    ts = int(time.time() * 1000)
    suffix = str(ts)[-10:]
    return {
        "username": f"manual_auth_{ts}",
        "real_name": "数据库联通测试",
        "school": "测试大学",
        "major": "软件工程",
        "grade": "大四",
        "email": f"manual_{ts}@example.com",
        "phone": f"1{suffix}",
        "password": "Test@123456"
    }


def print_latest_users(limit=5):
    users = User.query.order_by(User.id.desc()).limit(limit).all()
    print(f"\n最近 {limit} 条 users 记录：")
    for user in users:
        print(
            f"- id={user.id}, username={user.username}, email={user.email}, "
            f"phone={user.phone}, created_at={user.created_at}"
        )


def main(cleanup=False):
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        before_count = User.query.count()
        payload = build_payload()

        print("=== 开始验证注册写库 ===")
        print(f"写入前 users 总数: {before_count}")

        response = client.post('/api/v1/auth/register', json=payload)
        body = response.get_json() or {}
        print(f"注册接口 HTTP 状态: {response.status_code}")
        print(f"注册接口响应: {body}")

        if response.status_code != 200 or body.get('code') != 200:
            print("注册失败，未执行后续数据库变化检查。")
            return

        user_id = body['data']['user']['id']
        after_count = User.query.count()
        saved_user = db.session.get(User, user_id)

        print(f"写入后 users 总数: {after_count}")
        print(f"数量变化: {after_count - before_count}")
        print(
            f"新用户详情: id={saved_user.id}, username={saved_user.username}, "
            f"email={saved_user.email}, phone={saved_user.phone}, "
            f"real_name={saved_user.real_name}, school={saved_user.school}, "
            f"major={saved_user.major}, grade={saved_user.grade}"
        )

        print_latest_users(limit=5)

        if cleanup:
            db.session.delete(saved_user)
            db.session.commit()
            final_count = User.query.count()
            print("\n已清理本次测试数据。")
            print(f"清理后 users 总数: {final_count}")
        else:
            print("\n已保留测试数据，方便你直接在数据库里查看变化。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='手动验证登录注册数据是否写入数据库')
    parser.add_argument('--cleanup', action='store_true', help='验证后删除本次测试数据')
    args = parser.parse_args()
    main(cleanup=args.cleanup)
