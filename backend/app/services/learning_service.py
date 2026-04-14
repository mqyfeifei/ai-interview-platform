# backend/app/services/learning_service.py
from datetime import datetime
from sqlalchemy import asc
from app.extensions import db
from app.models.interview import Interview, InterviewScore, Dimension
from app.models.learning import UserKnowledgeMastery, KnowledgeTag, Resource, UserLearning
from app.models.example import Example
from app.models.job import Job
from app.models.user import User


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
        if not user_id:
            return []

        # === 新增逻辑：优先展示与用户最近一次面试（或预设岗位）相关联的短板 ===
        target_job_id = None
        last_interview = Interview.query.filter_by(user_id=user_id, status='completed').order_by(Interview.start_time.desc()).first()
        if last_interview:
            target_job_id = last_interview.job_id
        else:
            user = User.query.get(user_id)
            if user and user.default_job:
                target_job_id = user.default_job.id if hasattr(user.default_job, 'id') else user.default_job

        base_query = UserKnowledgeMastery.query.filter_by(user_id=user_id)
        query = base_query

        if target_job_id:
            # M2M 改造后基于 Job.knowledge_tags 过滤岗位知识点
            target_job = Job.query.get(target_job_id)
            if target_job:
                job_tag_ids = [t.id for t in target_job.knowledge_tags.all()]
                if job_tag_ids:
                    query = query.filter(UserKnowledgeMastery.tag_id.in_(job_tag_ids))

        weak_masteries = query.order_by(db.asc(UserKnowledgeMastery.mastery_level)).limit(limit).all()
        if not weak_masteries and query is not base_query:
            # 岗位范围为空时回退到全局短板，避免页面完全无数据
            weak_masteries = base_query.order_by(db.asc(UserKnowledgeMastery.mastery_level)).limit(limit).all()

        weaknesses = []
        for m in weak_masteries:
            tag = KnowledgeTag.query.get(m.tag_id)
            if tag:
                weaknesses.append({
                    "tag_id": tag.id,
                    "name": tag.name,
                    "mastery_level": m.mastery_level,
                    # 新增透传字段，用于前端展示预计耗时与难度徽章
                    "complexity": tag.complexity,
                    "estimated_hours": tag.estimated_hours
                })

        # === 兜底逻辑：如果目前用户尚无短板记录，动态从他的岗位找一些补充并初始化 ===
        if not weaknesses:
            user = User.query.get(user_id)
            if user and user.default_job:
                job = user.default_job
                # M2M 改造后直接从岗位知识点初始化短板
                job_tags = job.knowledge_tags.order_by(KnowledgeTag.id.asc()).all() if hasattr(job, 'knowledge_tags') else []
                added = 0
                for t in job_tags:
                    if not any(w['tag_id'] == t.id for w in weaknesses):
                        # 创建新的掌握度记录，并给个中等偏下的初始分
                        mastery = UserKnowledgeMastery(user_id=user_id, tag_id=t.id, mastery_level=45)
                        db.session.add(mastery)
                        weaknesses.append({
                            "tag_id": t.id,
                            "name": t.name,
                            "mastery_level": 45,
                            "complexity": t.complexity,
                            "estimated_hours": t.estimated_hours
                        })
                        added += 1
                    if added >= limit:
                        break
                db.session.commit()

        # 后续二次排序
        weaknesses.sort(key=lambda x: x['mastery_level'])
        return weaknesses

    @staticmethod
    def get_personalized_recommendations(user_id, limit=5):
        """基于技能短板精准推荐学习资源（优化版）"""
        weakness_limit = max(3, limit)
        weaknesses = LearningService.get_weaknesses(user_id, limit=weakness_limit)
        if not weaknesses:
            return []

        completed_resources = UserLearning.query.filter_by(user_id=user_id, status='completed').all()
        completed_ids = {cr.resource_id for cr in completed_resources}

        results = []
        recommended_ids = set()

        def get_target_difficulty(mastery_level):
            if mastery_level < 40:
                return ['beginner', 'easy', '入门', '初级', '简单']
            if mastery_level < 75:
                return ['intermediate', 'medium', '进阶', '中级', '中等']
            return ['advanced', 'hard', '高级', '困难']

        quotas = [limit // len(weaknesses) + (1 if i < limit % len(weaknesses) else 0) for i in range(len(weaknesses))]

        from app.models.learning import resource_tags
        from app.services.interview_service import InterviewService

        for i, weakness in enumerate(weaknesses):
            if len(results) >= limit:
                break

            quota = quotas[i]
            if quota <= 0:
                continue

            tag_id = weakness['tag_id']
            tag_name = weakness['name']
            target_diffs = get_target_difficulty(weakness.get('mastery_level', 0))

            query = Resource.query.join(resource_tags, Resource.id == resource_tags.c.resource_id).filter(
                resource_tags.c.tag_id == tag_id
            )

            exclude_ids = list(completed_ids | recommended_ids)
            if exclude_ids:
                query = query.filter(~Resource.id.in_(exclude_ids))

            exact_resources = query.filter(Resource.difficulty.in_(target_diffs)).limit(quota).all()

            if len(exact_resources) < quota:
                more_needed = quota - len(exact_resources)
                exclude_ids_now = exclude_ids + [r.id for r in exact_resources]
                fallback_query = Resource.query.join(resource_tags, Resource.id == resource_tags.c.resource_id).filter(
                    resource_tags.c.tag_id == tag_id
                )
                if exclude_ids_now:
                    fallback_query = fallback_query.filter(~Resource.id.in_(exclude_ids_now))
                exact_resources += fallback_query.limit(more_needed).all()

            for r in exact_resources:
                results.append({
                    "id": r.id,
                    "title": r.title,
                    "type": r.type,
                    "url": r.url,
                    "content": r.content,
                    "source": r.source,
                    "difficulty": r.difficulty,
                    "tags": [t.name for t in r.knowledge_tags] if hasattr(r, 'knowledge_tags') else [],
                    "completed": False,
                    "relatedWeakness": tag_name,
                })
                recommended_ids.add(r.id)

            current_count = len([res for res in results if res['relatedWeakness'] == tag_name])
            if current_count < quota:
                needed = quota - current_count
                try:
                    weak_vector = InterviewService.get_embedding(tag_name)
                    vec_query = Resource.query
                    exclude_vec_ids = list(completed_ids | recommended_ids)
                    if exclude_vec_ids:
                        vec_query = vec_query.filter(~Resource.id.in_(exclude_vec_ids))

                    vec_resources = vec_query.order_by(Resource.embedding.l2_distance(weak_vector)).limit(needed).all()
                    for r in vec_resources:
                        results.append({
                            "id": r.id,
                            "title": r.title,
                            "type": r.type,
                            "url": r.url,
                            "content": r.content,
                            "source": r.source,
                            "difficulty": r.difficulty,
                            "tags": [t.name for t in r.knowledge_tags] if hasattr(r, 'knowledge_tags') else [],
                            "completed": False,
                            "relatedWeakness": tag_name,
                        })
                        recommended_ids.add(r.id)
                except Exception as e:
                    print(f"[{tag_name}] 向量检索兜底失败: {e}")

        return results

    @staticmethod
    def get_completed_resource_ids(user_id):
        """返回指定用户所有已完成资源的 ID 列表"""
        if not user_id:
            return []
        records = UserLearning.query.filter_by(user_id=user_id, status='completed').all()
        return [rec.resource_id for rec in records]

    @staticmethod
    def get_daily_plan(user_id):
        """根据用户短板与推荐资源生成每日学习计划"""
        if not user_id:
            return {"tasks": [], "progress": 0}

        weaknesses = LearningService.get_weaknesses(user_id, limit=3)
        recommendations = LearningService.get_personalized_recommendations(user_id, limit=3)
        completed_ids = set(LearningService.get_completed_resource_ids(user_id))

        tasks = []
        for idx, resource in enumerate(recommendations):
            tasks.append({
                "id": f"res-{resource.get('id')}",
                "title": resource.get('title') or f"学习任务 {idx + 1}",
                "done": resource.get('id') in completed_ids,
                "type": "resource",
                "resource_id": resource.get('id')
            })

        for weakness in weaknesses:
            task_id = f"wk-{weakness['tag_id']}"
            if any(t['id'] == task_id for t in tasks):
                continue
            tasks.append({
                "id": task_id,
                "title": f"复习薄弱点：{weakness['name']}",
                "done": False,
                "type": "weakness",
                "tag_id": weakness['tag_id']
            })
            if len(tasks) >= 5:
                break

        progress = int((sum(1 for t in tasks if t['done']) / len(tasks)) * 100) if tasks else 0
        return {"tasks": tasks, "progress": progress}

    @staticmethod
    def update_task_status(user_id, task_id, done):
        """更新学习中心每日任务状态。"""
        if not task_id:
            return {"success": False, "message": "invalid task id"}

        if task_id.startswith('res-'):
            if not user_id:
                return {"success": False, "message": "missing user id"}

            try:
                resource_id = int(task_id.split('-', 1)[1])
            except (ValueError, IndexError):
                return {"success": False, "message": "invalid resource task id"}

            if done:
                LearningService.start_learning(user_id, resource_id)
                LearningService.finish_learning(user_id, resource_id)
                return {"success": True, "task_id": task_id, "done": True}

            record = UserLearning.query.filter_by(user_id=user_id, resource_id=resource_id).first()
            if record:
                record.status = 'in_progress'
                db.session.commit()
            return {"success": True, "task_id": task_id, "done": False}

        return {"success": True, "task_id": task_id, "done": bool(done)}

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

        time_spent = 0
        if record.start_time:
            time_spent = int((record.finish_time - record.start_time).total_seconds())

        resource = Resource.query.get(resource_id)
        if resource and resource.knowledge_tags:
            for tag in resource.knowledge_tags:
                mastery = UserKnowledgeMastery.query.filter_by(user_id=user_id, tag_id=tag.id).first()
                if mastery:
                    mastery.mastery_level = min(100, mastery.mastery_level + 5)
                else:
                    mastery = UserKnowledgeMastery(user_id=user_id, tag_id=tag.id, mastery_level=10)
                    db.session.add(mastery)

        db.session.commit()
        return {"msg": "Learning finished", "time_spent_seconds": time_spent}

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

        # 完成学习后提升关联知识点掌握度
        resource = Resource.query.get(resource_id)
        if resource and resource.knowledge_tags:
            for tag in resource.knowledge_tags:
                mastery = UserKnowledgeMastery.query.filter_by(
                    user_id=user_id, tag_id=tag.id).first()
                if mastery:
                    mastery.mastery_level = min(100, mastery.mastery_level + 5)
                else:
                    mastery = UserKnowledgeMastery(
                        user_id=user_id, tag_id=tag.id, mastery_level=10)
                    db.session.add(mastery)

        db.session.commit()
        return {"msg": "Learning finished", "time_spent_seconds": time_spent}
