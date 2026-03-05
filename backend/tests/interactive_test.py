import json
import sys
import os

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.prompt import AiPrompt
from app.models.interview import Interview, InterviewChat, Dimension, InterviewScore


def setup_test_data():
    """初始化基础测试数据"""
    dimensions_names = ['技术正确性', '逻辑严谨性', '岗位匹配度', '表达沟通', '应变能力']
    for name in dimensions_names:
        if not Dimension.query.filter_by(name=name).first():
            db.session.add(Dimension(name=name, description=f'{name}维度'))

    user = User.query.filter_by(username="interactive_user").first()
    if not user:
        user = User(username="interactive_user", email="test@test.com", password_hash="hash")
        db.session.add(user)

    job = Job.query.filter_by(name="Java后端").first()
    if not job:
        job = Job(name="Java后端")
        db.session.add(job)
        db.session.commit()  # 先提交获取 job.id

        prompt = AiPrompt(
            name="Java标准Prompt",
            job_id=job.id,
            system_prompt="你是一个资深Java架构师面试官。请针对Java基础、并发、JVM进行提问。每次只问一个问题。当用户输入[结束]时，输出[INTERVIEW_OVER]。",
            greeting_message="你好，我是今天的面试官，请先做个简单的自我介绍。",
            is_active=True
        )
        db.session.add(prompt)

    db.session.commit()
    return user.id, job.id


def run_interactive_test():
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        user_id, job_id = setup_test_data()

        print("\n" + "=" * 50)
        print("🚀 AI 面试交互式测试启动")
        print("=" * 50)

        # 1. 启动面试
        res = client.post('/api/v1/interviews/start', json={"user_id": user_id, "job_id": job_id})
        res_json = res.get_json()

        # --- 新增：错误拦截与打印真实报错 ---
        if res_json.get('code') != 200:
            print(f"\n[致命错误] 面试启动失败！")
            print(f"后端真实报错信息: {res_json.get('msg')}")
            return  # 终止程序运行

        start_data = res_json['data']
        interview_id = start_data['interview_id']

        # 2. 循环对话
        while True:
            user_input = input("\n你: ")
            if user_input.strip() in ['退出', '结束', 'quit', 'exit']:
                break

            print("考官: ", end="", flush=True)

            # 请求流式接口
            response = client.post(f'/api/v1/interviews/{interview_id}/chat/stream', json={'answer': user_input})

            # --- 请将解析 SSE 的代码替换为以下内容 ---
            full_reply = ""
            for chunk_bytes in response.response:
                chunk_str = chunk_bytes.decode('utf-8')
                # SSE 格式可能有多个换行符，按行分割处理
                for line in chunk_str.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            chunk_text = data.get('chunk', '')
                            full_reply += chunk_text
                            # 剔除结束标记不显示
                            print(chunk_text.replace('[INTERVIEW_OVER]', ''), end="", flush=True)
                        except json.JSONDecodeError:
                            continue
            print()  # 换行
            # --- 替换结束 ---

            # 检测是否被考官主动结束
            if '[INTERVIEW_OVER]' in full_reply:
                print("\n[系统] 检测到考官发出结束指令。")
                break

        # 3. 生成报告
        print("\n[系统] 正在生成面试报告，请稍候...")
        client.post(f'/api/v1/interviews/{interview_id}/finish')

        # 4. 验证数据库变化
        print("\n" + "=" * 50)
        print("📊 数据库状态核查")
        print("=" * 50)

        # 查验对话记录
        chats = InterviewChat.query.filter_by(interview_id=interview_id).order_by(InterviewChat.timestamp).all()
        print(f"总对话轮数: {len(chats)}")

        # 查验总表与报告文本
        interview = Interview.query.get(interview_id)
        print(f"面试状态: {interview.status}")
        print(f"面试总分: {interview.total_score}")
        print(f"亮点分析: {interview.evaluation_highlights}")
        print(f"改进建议: {interview.evaluation_suggestions}")

        # 查验维度评分
        print("\n详细维度评分:")
        scores = InterviewScore.query.filter_by(interview_id=interview_id).all()
        for s in scores:
            dim_name = Dimension.query.get(s.dimension_id).name
            print(f" - {dim_name}: {s.score}分 (评语: {s.comment})")


if __name__ == '__main__':
    run_interactive_test()