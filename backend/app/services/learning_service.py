# backend/app/services/learning_service.py
from datetime import datetime
from sqlalchemy import asc
from app.extensions import db
from app.models.interview import Interview, InterviewScore, Dimension
from app.models.learning import UserKnowledgeMastery, KnowledgeTag, Resource, UserLearning
from sentence_transformers import SentenceTransformer

# 复用全局加载的模型
local_embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')


class LearningService:
    @staticmethod
    def get_growth_curve(user_id, dimension_id=None):
        """
        获取能力成长曲线数据
        :param user_id: 用户ID
        :param dimension_id: 可选，如果为空则返回总分的变化，否则返回指定维度的得分变化
        """
        query = Interview.query.filter_by(user_id=user_id, status='completed').order_by(Interview.start_time.asc())
        interviews = query.all()

        curve_data = []
        for interview in interviews:
            if dimension_id:
                # 获取特定维度的分数
                score_record = InterviewScore.query.filter_by(interview_id=interview.id,
                                                              dimension_id=dimension_id).first()
                score = score_record.score if score_record else 0
            else:
                # 获取总分
                score = interview.total_score

            curve_data.append({
                "date": interview.start_time.strftime("%Y-%m-%d"),
                "score": score
            })
        return curve_data

    @staticmethod
    def get_weaknesses(user_id, limit=5):
        """获取用户的技能短板（掌握度最低的标签）"""
        weak_masteries = UserKnowledgeMastery.query.filter_by(user_id=user_id) \
            .order_by(UserKnowledgeMastery.mastery_level.asc()).limit(limit).all()

        weaknesses = []
        for m in weak_masteries:
            tag = KnowledgeTag.query.get(m.tag_id)
            if tag:
                weaknesses.append({
                    "tag_id": tag.id,
                    "name": tag.name,
                    "mastery_level": m.mastery_level
                })
        return weaknesses

    @staticmethod
    def get_personalized_recommendations(user_id, limit=5):
        """基于技能短板的向量，在资源库中进行检索推荐"""
        # 1. 找出最薄弱的知识点文本
        weaknesses = LearningService.get_weaknesses(user_id, limit=3)
        if not weaknesses:
            return []  # 如果没有短板数据，可返回默认热门资源

        weak_text = " ".join([w['name'] for w in weaknesses])

        # 2. 将薄弱点转换为向量
        target_vector = local_embedding_model.encode(weak_text).tolist()

        # 3. 找出用户已经完成的资源ID，避免重复推荐
        completed_resources = UserLearning.query.filter_by(user_id=user_id, status='completed').all()
        completed_ids = [cr.resource_id for cr in completed_resources]

        # 4. 向量检索：利用 pgvector 的 l2_distance 找出最相关的 Resource
        query = Resource.query
        if completed_ids:
            query = query.filter(~Resource.id.in_(completed_ids))

        recommended_resources = query.order_by(Resource.embedding.l2_distance(target_vector)).limit(limit).all()

        results = []
        for r in recommended_resources:
            results.append({
                "id": r.id,
                "title": r.title,
                "type": r.type,  # article, video, book, example
                "url": r.url,
                "content": r.content,
                "source": r.source,
                "difficulty": r.difficulty,
                "tags": r.tags
            })
        return results

    @staticmethod
    def start_learning(user_id, resource_id):
        """开始学习：创建记录并记录开始时间"""
        record = UserLearning.query.filter_by(user_id=user_id, resource_id=resource_id).first()
        if not record:
            record = UserLearning(user_id=user_id, resource_id=resource_id)
            db.session.add(record)

        record.status = 'in_progress'
        record.start_time = datetime.now()
        db.session.commit()
        return {"msg": "Learning started"}

    @staticmethod
    def finish_learning(user_id, resource_id):
        """完成学习：计算耗时，标记完成"""
        record = UserLearning.query.filter_by(user_id=user_id, resource_id=resource_id).first()
        if not record or record.status == 'completed':
            return {"msg": "Record not found or already completed"}

        record.finish_time = datetime.now()
        record.status = 'completed'
        record.progress = 100

        # 计算学习总耗时（秒）
        time_spent = 0
        if record.start_time:
            time_spent = int((record.finish_time - record.start_time).total_seconds())

        # TODO: 这里可以通过抛出事件或直接调用方法，提升该资源对应标签的掌握度 (UserKnowledgeMastery)

        db.session.commit()
        return {"msg": "Learning finished", "time_spent_seconds": time_spent}