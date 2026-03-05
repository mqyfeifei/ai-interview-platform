import sys
import os
import json

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.learning import UserKnowledgeMastery


def run_interactive_full_flow():
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        # 准备测试用户
        user = User.query.filter_by(username="interactive_tester").first()
        if not user:
            user = User(username="interactive_tester", email="it@test.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()

        # 清理旧掌握度，保证每次测试都是新的状态
        UserKnowledgeMastery.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # 寻找真实岗位
        job = Job.query.filter_by(name="Java后端开发").first()
        if not job:
            print("❌ 未找到Java后端开发岗位数据，请确认已运行过 import_kb.py 导入题库！")
            return

        user_id = user.id
        job_id = job.id

    print("\n" + "═" * 60)
    print("🚀 AI 面试交互式测试启动")
    print("💡 提示：你可以故意回答不会某些知识点。输入『结束』可立即终止面试并生成报告。")
    print("═" * 60)

    # 1. 创建面试
    res = client.post('/api/v1/interviews/start', json={'user_id': user_id, 'job_id': job_id})
    data = res.get_json().get('data', {})
    interview_id = data.get('interview_id')

    print(f"\n🤖 考官: {data.get('question')}")

    # 2. 交互式聊天循环
    while True:
        user_input = input("\n🧑 你: ")
        if not user_input.strip():
            continue

        if user_input.strip() in ['结束', 'quit', 'exit']:
            break

        # 流式请求 AI 回复
        res = client.post(f'/api/v1/interviews/{interview_id}/chat/stream', json={'answer': user_input})

        print("\n🤖 考官: ", end="")
        for chunk_bytes in res.response:
            chunk_str = chunk_bytes.decode('utf-8')
            for line in chunk_str.split('\n'):
                if line.startswith('data: '):
                    try:
                        chunk_data = json.loads(line[6:])
                        text = chunk_data.get('chunk', '')
                        text = text.replace('[INTERVIEW_OVER]', '')
                        print(text, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        print()  # 换行

    # 3. 生成报告与打分
    print("\n\n" + "═" * 60)
    print("📝 面试结束，正在向大模型请求评估报告 (约10-20秒)...")
    res = client.post(f'/api/v1/interviews/{interview_id}/finish')

    if res.status_code != 200:
        print(f"❌ 报告生成失败: {res.get_json()}")
        return

    report = res.get_json()['data']

    print("\n📊 【核心综合报告】")
    print(f"  👉 总分: {report.get('total_score')}")
    print(f"  👉 亮点: {report.get('evaluation_highlights', report.get('highlights'))}")
    print(f"  👉 不足: {report.get('evaluation_improvements', report.get('improvements'))}")

    print("\n🎯 【大模型从标准库中抓取并打分的知识点】")
    tags_eval = report.get('knowledge_tags_eval', {})
    if not tags_eval:
        print("  ⚠️ AI没有从本次对话中提取到具体的标准库知识点。")
    else:
        for tag, score in tags_eval.items():
            print(f"  - {tag} : {score}分")

    # 4. 获取短板
    print("\n" + "═" * 60)
    print("📉 【学习中心 - 生成的薄弱点列表】")
    res = client.get(f'/api/v1/learning/weaknesses?user_id={user_id}')
    weaknesses = res.get_json().get('data', [])
    if not weaknesses:
        print("  暂无薄弱点记录（可能由于得分不低或匹配失败）。")
    else:
        for w in weaknesses:
            print(f"  - 标签: 【{w['name']}】 (当前掌握度: {w['mastery_level']}分)")

    # 5. 智能推荐
    print("\n💡 【学习中心 - 智能资源推荐 (基于薄弱点的向量匹配)】")
    res = client.get(f'/api/v1/learning/recommendations?user_id={user_id}&limit=3')
    recs = res.get_json().get('data', [])
    if not recs:
        print("  未能推荐出学习资源 (请检查 Resource 表中是否有数据与向量)。")
    else:
        for i, r in enumerate(recs):
            print(f"  [{i + 1}] 《{r['title']}》")
            print(f"       资源类型: {r['type']} | 来源: {r.get('source')} | 难度: {r.get('difficulty')}")
    print("═" * 60 + "\n")


if __name__ == '__main__':
    run_interactive_full_flow()