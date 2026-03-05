import sys
import os
import json

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.interview import InterviewChat


def print_db_records(app, interview_id):
    """辅助函数：从数据库中查询并打印聊天记录"""
    with app.app_context():
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
        print("\n" + "┌" + "─" * 50 + "┐")
        print("│ 🗄️ 当前数据库 interview_chats 表真实记录:")
        for c in chats:
            # 截断过长的文本方便查看
            content_preview = c.content if len(c.content) < 40 else c.content[:37] + "..."
            print(f"│ ID:{c.id} | 角色:{c.role.ljust(5)} | 内容: {content_preview}")
        print("└" + "─" * 50 + "┘")


def run_chat_db_verify():
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        # 1. 准备测试用户和岗位
        user = User.query.filter_by(username="db_tester").first()
        if not user:
            user = User(username="db_tester", email="db@test.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()

        job = Job.query.filter_by(name="Java后端开发").first()
        if not job:
            print("❌ 未找到Java后端开发岗位数据，请先导入知识库！")
            return

        user_id = user.id
        job_id = job.id

    print("\n" + "=" * 60)
    print("🚀 接口与数据库落表 实时验证测试启动")
    print("=" * 60)

    # 步骤 1：调用 /start 接口
    print("\n[1] 正在调用 POST /api/v1/interviews/start 接口创建面试...")
    res = client.post('/api/v1/interviews/start', json={'user_id': user_id, 'job_id': job_id})
    data = res.get_json().get('data', {})
    interview_id = data.get('interview_id')
    greeting = data.get('question')

    print(f"  ✅ 接口成功返回 Interview ID: {interview_id}")
    print(f"  ✅ 接口成功返回 开场白: {greeting}")

    # 马上查数据库，验证开场白是否已落表
    print_db_records(app, interview_id)

    # 步骤 2：循环交互
    print("\n💡 提示：输入你想说的话与AI对话。输入『结束』退出测试。")
    while True:
        user_input = input("\n🧑 你: ")
        if not user_input.strip():
            continue

        if user_input.strip() in ['结束', 'quit', 'exit']:
            print("测试主动结束。")
            break

        # 调用流式对话接口
        print("🤖 考官: ", end="")
        res = client.post(f'/api/v1/interviews/{interview_id}/chat/stream', json={'answer': user_input})

        full_ai_reply = ""
        for chunk_bytes in res.response:
            chunk_str = chunk_bytes.decode('utf-8')
            for line in chunk_str.split('\n'):
                if line.startswith('data: '):
                    try:
                        chunk_data = json.loads(line[6:])
                        text = chunk_data.get('chunk', '')
                        full_ai_reply += text
                        print(text.replace('[INTERVIEW_OVER]', ''), end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        print()  # 换行

        # 再次查数据库，验证你刚才说的话，以及AI回复的话是否都已经保存！
        print_db_records(app, interview_id)

        if '[INTERVIEW_OVER]' in full_ai_reply:
            print("\n🔔 检测到面试结束标志，测试终止。")
            break


if __name__ == '__main__':
    run_chat_db_verify()