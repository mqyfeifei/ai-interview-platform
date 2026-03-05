import sys
import os
import json
import time
from sentence_transformers import SentenceTransformer

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.learning import KnowledgeTag, Resource, UserKnowledgeMastery, UserLearning

# 提前加载向量模型，用于生成假资源的 512 维向量
print("⏳ 正在加载向量模型，请稍候...")
local_embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')


def setup_mock_data(app):
    """向数据库中塞入假的测试数据"""
    with app.app_context():
        # 1. 创建测试用户
        user = User.query.filter_by(username="learning_tester").first()
        if not user:
            user = User(username="learning_tester", email="learn@test.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()

        # 2. 创建知识点标签 (如果有就不重复创建)
        tags_data = [
            {"name": "Redis持久化", "category": "数据库"},
            {"name": "算法复杂度", "category": "算法"},
            {"name": "Spring Boot事务", "category": "后端"}
        ]
        for td in tags_data:
            if not KnowledgeTag.query.filter_by(name=td["name"]).first():
                db.session.add(KnowledgeTag(**td))
        db.session.commit()

        tag_redis = KnowledgeTag.query.filter_by(name="Redis持久化").first()
        tag_algo = KnowledgeTag.query.filter_by(name="算法复杂度").first()
        tag_spring = KnowledgeTag.query.filter_by(name="Spring Boot事务").first()

        # 3. 创建用户掌握度 (制造短板：Redis仅10分，算法20分，Spring则高达80分)
        mastery_data = [
            {"tag_id": tag_redis.id, "mastery_level": 10},
            {"tag_id": tag_algo.id, "mastery_level": 20},
            {"tag_id": tag_spring.id, "mastery_level": 80}
        ]
        for md in mastery_data:
            m = UserKnowledgeMastery.query.filter_by(user_id=user.id, tag_id=md["tag_id"]).first()
            if not m:
                db.session.add(UserKnowledgeMastery(user_id=user.id, **md))
            else:
                m.mastery_level = md["mastery_level"]
        db.session.commit()

        # 4. 创建带向量的假学习资源 (用于向量距离匹配)
        resources_data = [
            {
                "title": "深入理解Redis持久化：RDB与AOF",
                "type": "article",
                "content": "Redis持久化分为RDB和AOF两种方式，本文将带你详细解读它们的原理...",
                "difficulty": "medium",
                # 用模型将文本转成 512维 向量并存入数据库
                "embedding": local_embedding_model.encode("Redis持久化 深入理解Redis持久化：RDB与AOF").tolist()
            },
            {
                "title": "十分钟搞懂时间复杂度与空间复杂度",
                "type": "video",
                "content": "什么是O(n)？什么是O(logn)？大厂面试必问的算法复杂度基础...",
                "difficulty": "easy",
                "embedding": local_embedding_model.encode("算法复杂度 十分钟搞懂时间复杂度与空间复杂度").tolist()
            },
            {
                "title": "Vue3响应式原理深度剖析",
                "type": "article",
                "content": "Vue3中Proxy替代了Vue2的Object.defineProperty...",
                "difficulty": "hard",
                "embedding": local_embedding_model.encode("前端框架 Vue3响应式原理深度剖析").tolist()
            }
        ]

        for rd in resources_data:
            if not Resource.query.filter_by(title=rd["title"]).first():
                r = Resource(**rd)
                db.session.add(r)
        db.session.commit()

        # 清理该用户之前的学习记录（为了每次运行测试都能看到完整流程）
        UserLearning.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return user.id


def run_learning_test():
    app = create_app('development')
    client = app.test_client()
    user_id = setup_mock_data(app)

    print("\n" + "=" * 50)
    print("🚀 学习中心 / 向量推荐流程 测试启动")
    print("=" * 50)

    # 1. 测试：发现短板
    print("\n[1] 正在调用接口，获取用户技能短板...")
    res = client.get(f'/api/v1/learning/weaknesses?user_id={user_id}')
    weaknesses = res.get_json().get('data', [])
    for w in weaknesses:
        print(f"  - 发现短板知识点: 【{w['name']}】 | 掌握度: {w['mastery_level']}分")

    # 2. 测试：向量推荐
    print("\n[2] 正在基于短板动态生成向量，并在数据库中检索最相关的推荐资源...")
    res = client.get(f'/api/v1/learning/recommendations?user_id={user_id}&limit=3')
    recs = res.get_json().get('data', [])
    for i, r in enumerate(recs):
        print(f"  ⭐ 推荐结果 {i + 1}: 《{r['title']}》 (类型: {r['type']})")

    if not recs:
        print("未匹配到推荐资源。")
        return

    target_resource_id = recs[0]['id']

    # 3. 测试：开始学习
    print(f"\n[3] 模拟用户点击卡片，开始学习第一个推荐资源 (Resource ID: {target_resource_id})...")
    client.post('/api/v1/learning/records/start', json={"user_id": user_id, "resource_id": target_resource_id})

    with app.app_context():
        record = UserLearning.query.filter_by(user_id=user_id, resource_id=target_resource_id).first()
        print(f"  ✅ 数据库已记录: status='{record.status}', start_time={record.start_time}")

    # 模拟真实世界中用户看文章/看视频看了一会儿
    print("  ⏳ 模拟用户正在认真学习 (等待 2 秒钟)...")
    time.sleep(2)

    # 4. 测试：完成学习并计算用时
    print(f"\n[4] 模拟用户点击【标记完成】...")
    res = client.post('/api/v1/learning/records/finish', json={"user_id": user_id, "resource_id": target_resource_id})
    finish_data = res.get_json().get('data', {})
    print(f"  ✅ 接口返回结算信息: {finish_data['msg']}, 本次学习真实耗时: {finish_data.get('time_spent_seconds')} 秒")

    with app.app_context():
        record = UserLearning.query.filter_by(user_id=user_id, resource_id=target_resource_id).first()
        print(
            f"  ✅ 数据库已更新: status='{record.status}', progress={record.progress}%, finish_time={record.finish_time}")

    # 5. 测试：推荐列表过滤机制
    print("\n[5] 再次请求推荐资源列表，验证【已学完的资源】是否被自动过滤...")
    res = client.get(f'/api/v1/learning/recommendations?user_id={user_id}&limit=3')
    new_recs = res.get_json().get('data', [])
    for i, r in enumerate(new_recs):
        print(f"  ⭐ 最新推荐 {i + 1}: 《{r['title']}》")
        if r['id'] == target_resource_id:
            print("  ❌ 错误！已学完的资源不该再次出现！")

    print("\n🎉 测试圆满完成！你可以打开 DBeaver 查看表的数据变化。")


if __name__ == '__main__':
    run_learning_test()