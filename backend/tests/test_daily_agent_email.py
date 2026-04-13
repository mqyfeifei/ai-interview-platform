import os
import sys
import argparse

# 确保能正确导入 backend/app 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.user import User
from app.services.daily_agent_service import DailyAgentService


def main():
    parser = argparse.ArgumentParser(description='测试每日任务提醒邮件发送功能')
    parser.add_argument('--email', type=str, default=None, help='指定接收提醒的用户邮箱（可选）')
    parser.add_argument('--env', type=str, default='development', help='Flask 运行环境，默认 development')
    args = parser.parse_args()

    app = create_app(args.env)

    with app.app_context():
        if args.email:
            user = User.query.filter_by(email=args.email).first()
            if not user:
                print(f'未找到邮箱为 {args.email} 的用户，请确认数据库中该邮箱对应用户存在。')
                return
        else:
            user = User.query.filter(User.email.isnot(None)).first()
            if not user:
                print('未找到任何配置了 email 的用户，请先在数据库中设置 user.email。')
                return

        print('将发送提醒邮箱给用户：', user.id, user.username, user.email)
        try:
            DailyAgentService._send_user_summary(user)
            print('发送逻辑已执行，请检查目标邮箱是否收到邮件。')
        except Exception as e:
            print('发送提醒邮件时发生异常：', e)


if __name__ == '__main__':
    main()
