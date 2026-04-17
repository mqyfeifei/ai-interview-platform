from datetime import datetime, timedelta
from app.extensions import db
from app.models.interview import Interview, InterviewScore, InterviewChat, UserGrowth
from app.models.learning import (
    UserKnowledgeMastery,
    KnowledgeTag,
    Resource,
    UserLearning,
    UserLearningPreference,
)
from app.models.job import Job
from app.models.user import User
from app.models.question import question_tags


class LearningService:
    @staticmethod
    def _difficulty_factor(difficulty):
        diff = str(difficulty or '').strip().lower()
        if diff == 'hard':
            return 2.0
        if diff == 'medium':
            return 1.5
        return 1.0

    @staticmethod
    def _get_or_create_preference(user_id):
        pref = UserLearningPreference.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = UserLearningPreference(user_id=user_id, daily_hours=2.0, selected_day_index=1)
            db.session.add(pref)
            db.session.commit()
        return pref

    @staticmethod
    def get_learning_settings(user_id):
        if not user_id:
            return {"dailyHours": 2.0, "selectedDayIndex": 1}
        pref = LearningService._get_or_create_preference(user_id)
        return {
            "dailyHours": float(pref.daily_hours or 2.0),
            "selectedDayIndex": int(pref.selected_day_index or 1),
            "updatedAt": pref.updated_at.isoformat() if pref.updated_at else None
        }

    @staticmethod
    def update_learning_settings(user_id, daily_hours=None, selected_day_index=None):
        if not user_id:
            return {"success": False, "message": "missing user id"}
        pref = LearningService._get_or_create_preference(user_id)
        if daily_hours is not None:
            pref.daily_hours = max(0.5, float(daily_hours))
        if selected_day_index is not None:
            pref.selected_day_index = max(1, int(selected_day_index))
        db.session.commit()
        return {
            "success": True,
            "dailyHours": float(pref.daily_hours or 2.0),
            "selectedDayIndex": int(pref.selected_day_index or 1)
        }

    @staticmethod
    def _resolve_focus_tag_ids(user_id, report_id=None):
        if report_id:
            interview = Interview.query.filter_by(id=int(report_id), user_id=user_id).first()
            if interview:
                from app.services.report_service import ReportService
                weak_rows = ReportService._build_report_weaknesses(interview, limit=20)
                tag_ids = [row.get('tag_id') for row in weak_rows if row.get('tag_id')]
                if tag_ids:
                    return list(dict.fromkeys(tag_ids))
                return []
        return None

    @staticmethod
    def _build_weakness_frequency(user_id):
        interview_ids = [row.id for row in Interview.query.filter_by(user_id=user_id, status='completed').all()]
        if not interview_ids:
            return {}
        rows = (
            db.session.query(question_tags.c.tag_id, db.func.count(db.distinct(InterviewChat.id)))
            .join(InterviewChat, InterviewChat.question_id == question_tags.c.question_id)
            .filter(
                InterviewChat.interview_id.in_(interview_ids),
                InterviewChat.role == 'ai'
            )
            .group_by(question_tags.c.tag_id)
            .all()
        )
        return {int(tag_id): int(cnt or 0) for tag_id, cnt in rows}

    @staticmethod
    def get_growth_curve(user_id, dimension_id=None):
        if not user_id:
            return []
        if dimension_id:
            rows = (
                UserGrowth.query
                .filter_by(user_id=user_id, dimension_id=dimension_id)
                .order_by(UserGrowth.record_time.asc())
                .all()
            )
            if rows:
                return [{
                    "date": r.record_time.strftime("%Y-%m-%d"),
                    "score": int(r.score or 0)
                } for r in rows if r.record_time]

        interviews = Interview.query.filter_by(user_id=user_id, status='completed').order_by(Interview.start_time.asc()).all()
        curve_data = []
        for interview in interviews:
            if dimension_id:
                score_record = InterviewScore.query.filter_by(
                    interview_id=interview.id,
                    dimension_id=dimension_id
                ).first()
                score = score_record.score if score_record else 0
            else:
                score = interview.total_score
            curve_data.append({
                "date": interview.start_time.strftime("%Y-%m-%d"),
                "score": int(score or 0)
            })
        return curve_data

    @staticmethod
    def get_weaknesses(user_id, limit=5, report_id=None):
        if not user_id:
            return []

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

        report_focus_tag_ids = LearningService._resolve_focus_tag_ids(user_id, report_id=report_id)
        if report_focus_tag_ids is not None:
            if report_focus_tag_ids:
                query = query.filter(UserKnowledgeMastery.tag_id.in_(report_focus_tag_ids))
            else:
                query = query.filter(db.text('1=0'))
        elif target_job_id:
            target_job = Job.query.get(target_job_id)
            if target_job:
                job_tag_ids = [t.id for t in target_job.knowledge_tags.all()]
                if job_tag_ids:
                    query = query.filter(UserKnowledgeMastery.tag_id.in_(job_tag_ids))

        weak_masteries = query.order_by(db.asc(UserKnowledgeMastery.mastery_level)).limit(limit).all()
        if not weak_masteries and query is not base_query:
            weak_masteries = base_query.order_by(db.asc(UserKnowledgeMastery.mastery_level)).limit(limit).all()

        freq_map = LearningService._build_weakness_frequency(user_id)
        weaknesses = []
        for m in weak_masteries:
            tag = KnowledgeTag.query.get(m.tag_id)
            if tag:
                weaknesses.append({
                    "tag_id": tag.id,
                    "name": tag.name,
                    "mastery_level": int(m.mastery_level or 0),
                    "complexity": tag.complexity,
                    "estimated_hours": tag.estimated_hours,
                    "frequency": int(freq_map.get(tag.id, 0))
                })

        if not weaknesses:
            user = User.query.get(user_id)
            if user and user.default_job:
                job = user.default_job
                job_tags = job.knowledge_tags.order_by(KnowledgeTag.id.asc()).all() if hasattr(job, 'knowledge_tags') else []
                added = 0
                for t in job_tags:
                    if not any(w['tag_id'] == t.id for w in weaknesses):
                        mastery = UserKnowledgeMastery(user_id=user_id, tag_id=t.id, mastery_level=45)
                        db.session.add(mastery)
                        weaknesses.append({
                            "tag_id": t.id,
                            "name": t.name,
                            "mastery_level": 45,
                            "complexity": t.complexity,
                            "estimated_hours": t.estimated_hours,
                            "frequency": 0
                        })
                        added += 1
                    if added >= limit:
                        break
                db.session.commit()

        weaknesses.sort(key=lambda x: (x['mastery_level'], -(x.get('frequency') or 0)))
        return weaknesses

    @staticmethod
    def get_personalized_recommendations(user_id, limit=5, report_id=None):
        if not user_id:
            return []
        weakness_limit = max(3, limit)
        weaknesses = LearningService.get_weaknesses(user_id, limit=weakness_limit, report_id=report_id)
        if not weaknesses:
            return []

        records = UserLearning.query.filter_by(user_id=user_id).all()
        record_map = {r.resource_id: r for r in records}
        completed_ids = {r.resource_id for r in records if r.status == 'completed'}

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
                record = record_map.get(r.id)
                results.append({
                    "id": r.id,
                    "title": r.title,
                    "type": r.type,
                    "url": r.url,
                    "content": r.content,
                    "source": r.source,
                    "difficulty": r.difficulty,
                    "tags": [t.name for t in r.knowledge_tags] if hasattr(r, 'knowledge_tags') else [],
                    "completed": bool(record and record.status == 'completed'),
                    "bookmarked": bool(record and record.bookmarked),
                    "relatedWeakness": tag_name,
                    "estimated_hours": weakness.get('estimated_hours'),
                    "priority": int(100 - (weakness.get('mastery_level') or 0) + 5 * (weakness.get('frequency') or 0)),
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
                        record = record_map.get(r.id)
                        results.append({
                            "id": r.id,
                            "title": r.title,
                            "type": r.type,
                            "url": r.url,
                            "content": r.content,
                            "source": r.source,
                            "difficulty": r.difficulty,
                            "tags": [t.name for t in r.knowledge_tags] if hasattr(r, 'knowledge_tags') else [],
                            "completed": bool(record and record.status == 'completed'),
                            "bookmarked": bool(record and record.bookmarked),
                            "relatedWeakness": tag_name,
                            "estimated_hours": weakness.get('estimated_hours'),
                            "priority": int(100 - (weakness.get('mastery_level') or 0) + 5 * (weakness.get('frequency') or 0)),
                        })
                        recommended_ids.add(r.id)
                except Exception as e:
                    print(f"[{tag_name}] 向量检索兜底失败: {e}")

        results.sort(key=lambda x: int(x.get('priority') or 0), reverse=True)
        return results[:limit]

    @staticmethod
    def get_completed_resource_ids(user_id):
        if not user_id:
            return []
        records = UserLearning.query.filter_by(user_id=user_id, status='completed').all()
        return [rec.resource_id for rec in records]

    @staticmethod
    def toggle_bookmark(user_id, resource_id, bookmarked):
        if not user_id or not resource_id:
            return {"success": False}
        record = UserLearning.query.filter_by(user_id=user_id, resource_id=resource_id).first()
        if not record:
            record = UserLearning(user_id=user_id, resource_id=resource_id, status='pending', progress=0)
            db.session.add(record)
        record.bookmarked = bool(bookmarked)
        db.session.commit()
        return {"success": True, "resourceId": int(resource_id), "bookmarked": bool(bookmarked)}

    @staticmethod
    def _save_planned_day_to_records(user_id, plan_calendar):
        day_map = {}
        for day in plan_calendar or []:
            day_idx = int(day.get('dayIndex') or 0)
            for item in day.get('items') or []:
                rid = item.get('resourceId')
                if rid:
                    day_map[int(rid)] = (day_idx, float(item.get('hours') or 0))

        if not day_map:
            return
        rows = UserLearning.query.filter(UserLearning.user_id == user_id, UserLearning.resource_id.in_(list(day_map.keys()))).all()
        existing = {r.resource_id: r for r in rows}
        for rid, (day_idx, hours) in day_map.items():
            row = existing.get(rid)
            if not row:
                row = UserLearning(user_id=user_id, resource_id=rid, status='pending')
                db.session.add(row)
            row.planned_day_index = day_idx
            row.planned_hours = hours
        db.session.commit()

    @staticmethod
    def get_study_plan(user_id, daily_hours=None, report_id=None):
        if not user_id:
            return {
                "recommendedDailyHours": 2.0,
                "totalEstimatedHours": 0,
                "estimatedDays": 0,
                "targetFinishDate": None,
                "items": [],
                "calendar": [],
                "selectedDayIndex": 1
            }

        pref = LearningService._get_or_create_preference(user_id)
        if daily_hours is None:
            daily = max(0.5, float(pref.daily_hours or 2.0))
        else:
            daily = max(0.5, float(daily_hours or 2.0))
            pref.daily_hours = daily
            db.session.commit()

        weaknesses = LearningService.get_weaknesses(user_id, limit=20, report_id=report_id)
        resources = LearningService.get_personalized_recommendations(user_id, limit=40, report_id=report_id)
        if not resources:
            return {
                "recommendedDailyHours": daily,
                "totalEstimatedHours": 0,
                "estimatedDays": 0,
                "targetFinishDate": None,
                "items": [],
                "calendar": [],
                "selectedDayIndex": int(pref.selected_day_index or 1)
            }

        weighted = []
        for item in resources:
            base_hours = float(item.get('estimated_hours') or 1)
            hours = round(base_hours * LearningService._difficulty_factor(item.get('difficulty')), 1)
            priority = int(item.get('priority') or 0)
            weighted.append({**item, "estimatedHours": hours, "priority": priority})

        weighted.sort(key=lambda x: (x.get('priority') or 0, x.get('estimatedHours') or 0), reverse=True)
        total_hours = round(sum(float(x.get('estimatedHours') or 0) for x in weighted), 1)
        est_days = int(max(1, -(-total_hours // daily))) if total_hours > 0 else 0

        today = datetime.now().date()
        calendar = []
        items_cursor = 0
        for day_index in range(est_days):
            remaining = daily
            day_items = []
            while items_cursor < len(weighted) and remaining > 0:
                current = weighted[items_cursor]
                h = float(current.get('estimatedHours') or 0)
                if h <= 0:
                    items_cursor += 1
                    continue
                if h <= remaining + 1e-6:
                    day_items.append({
                        "resourceId": current.get('id'),
                        "title": current.get('title'),
                        "hours": h,
                        "priority": current.get('priority'),
                        "relatedWeakness": current.get('relatedWeakness'),
                        "url": current.get('url')
                    })
                    remaining -= h
                    items_cursor += 1
                else:
                    day_items.append({
                        "resourceId": current.get('id'),
                        "title": current.get('title'),
                        "hours": round(remaining, 1),
                        "priority": current.get('priority'),
                        "relatedWeakness": current.get('relatedWeakness'),
                        "url": current.get('url')
                    })
                    current['estimatedHours'] = round(h - remaining, 1)
                    remaining = 0
            calendar.append({
                "dayIndex": day_index + 1,
                "date": (today + timedelta(days=day_index)).isoformat(),
                "hours": round(daily - remaining, 1),
                "items": day_items
            })
            if items_cursor >= len(weighted):
                break

        LearningService._save_planned_day_to_records(user_id, calendar)

        target_finish = calendar[-1]['date'] if calendar else None
        return {
            "recommendedDailyHours": daily,
            "totalEstimatedHours": total_hours,
            "estimatedDays": len(calendar),
            "targetFinishDate": target_finish,
            "weaknesses": weaknesses,
            "items": weighted,
            "calendar": calendar,
            "selectedDayIndex": int(pref.selected_day_index or 1),
        }

    @staticmethod
    def get_daily_plan(user_id, daily_hours=None, report_id=None):
        if not user_id:
            return {"tasks": [], "progress": 0, "recommendedDailyHours": 2.0}

        study_plan = LearningService.get_study_plan(user_id, daily_hours=daily_hours, report_id=report_id)
        pref = LearningService._get_or_create_preference(user_id)
        total_days = int(study_plan.get("estimatedDays") or 0)
        selected_day = max(1, int(pref.selected_day_index or 1))
        if total_days > 0 and selected_day > total_days:
            selected_day = total_days
            pref.selected_day_index = selected_day
            db.session.commit()

        calendar = study_plan.get("calendar") or []
        selected_day_payload = next((d for d in calendar if int(d.get("dayIndex") or 0) == selected_day), None)

        completed_ids = set(LearningService.get_completed_resource_ids(user_id))
        tasks = []
        if selected_day_payload:
            for item in selected_day_payload.get("items") or []:
                rid = item.get("resourceId")
                tasks.append({
                    "id": f"res-{rid}",
                    "title": item.get("title") or "学习任务",
                    "done": rid in completed_ids,
                    "type": "resource",
                    "resource_id": rid,
                    "estimatedHours": float(item.get("hours") or 1),
                    "url": item.get("url"),
                    "relatedWeakness": item.get("relatedWeakness"),
                })
        progress = int((sum(1 for t in tasks if t['done']) / len(tasks)) * 100) if tasks else 0

        day_status_map = {}
        for day in calendar:
            day_items = day.get("items") or []
            if not day_items:
                day_status_map[int(day.get("dayIndex") or 0)] = "empty"
                continue
            done_count = sum(1 for it in day_items if (it.get("resourceId") in completed_ids))
            if done_count == len(day_items):
                day_status_map[int(day.get("dayIndex") or 0)] = "done"
            elif done_count > 0:
                day_status_map[int(day.get("dayIndex") or 0)] = "partial"
            else:
                day_status_map[int(day.get("dayIndex") or 0)] = "pending"

        return {
            "tasks": tasks,
            "progress": progress,
            "recommendedDailyHours": float(study_plan.get("recommendedDailyHours") or 2.0),
            "selectedDayIndex": selected_day,
            "planTotalDays": total_days,
            "dayStatusMap": day_status_map,
            "planCalendar": calendar,
            "planTotalProgress": f"{sum(1 for v in day_status_map.values() if v == 'done')}/{total_days}" if total_days else "0/0"
        }

    @staticmethod
    def update_task_status(user_id, task_id, done):
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
