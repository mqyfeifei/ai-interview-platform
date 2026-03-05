import json
import time

from sqlalchemy import func

from app import create_app
from app.extensions import db
from app.models.job import Job
from app.models.user import User


def seed_data(prefix):
    jobs = []
    counts = [12, 10, 8, 6, 4, 2]

    for index, count in enumerate(counts, start=1):
        job = Job(
            name=f"热门岗位验证_{prefix}_{index}",
            description="热门岗位接口验证数据",
            tech_stack=["Python", "Flask"]
        )
        db.session.add(job)
        db.session.flush()
        jobs.append((job, count))

    created_user_ids = []
    for job, count in jobs:
        for user_index in range(count):
            user = User(
                username=f"popular_user_{prefix}_{job.id}_{user_index}",
                email=f"popular_{prefix}_{job.id}_{user_index}@example.com",
                phone=f"1{str(job.id).zfill(4)}{str(user_index).zfill(6)}"[-11:],
                default_job_id=job.id
            )
            user.set_password("Test@123456")
            db.session.add(user)
            db.session.flush()
            created_user_ids.append(user.id)

    db.session.commit()
    created_job_ids = [job.id for job, _ in jobs]
    return created_job_ids, created_user_ids


def fetch_expected_top5():
    rows = db.session.query(
        Job.id,
        Job.name,
        func.count(User.id).label("selected_count")
    ).join(
        User, User.default_job_id == Job.id
    ).group_by(
        Job.id, Job.name
    ).order_by(
        func.count(User.id).desc(),
        Job.id.asc()
    ).limit(5).all()

    return [
        {
            "id": row.id,
            "name": row.name,
            "selected_count": int(row.selected_count or 0)
        }
        for row in rows
    ]


def cleanup_data(job_ids, user_ids):
    if user_ids:
        User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    if job_ids:
        Job.query.filter(Job.id.in_(job_ids)).delete(synchronize_session=False)
    db.session.commit()


def main():
    app = create_app("development")
    client = app.test_client()

    prefix = str(int(time.time() * 1000))

    with app.app_context():
        created_job_ids = []
        created_user_ids = []
        try:
            created_job_ids, created_user_ids = seed_data(prefix)

            expected = fetch_expected_top5()
            response = client.get("/api/v1/jobs/popular")
            body = response.get_json() or {}
            actual_raw = body.get("data") or []
            actual = [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "selected_count": int(item.get("selected_count") or 0)
                }
                for item in actual_raw
            ]

            print("HTTP:", response.status_code)
            print("code:", body.get("code"), "msg:", body.get("msg"))
            print("\n==== 预期 Top5（数据库统计）====")
            print(json.dumps(expected, ensure_ascii=False, indent=2))
            print("\n==== 实际 Top5（接口返回）====")
            print(json.dumps(actual, ensure_ascii=False, indent=2))

            is_correct = response.status_code == 200 and expected == actual
            print("\n校验结果:", "通过 ✅" if is_correct else "不通过 ❌")
        finally:
            cleanup_data(created_job_ids, created_user_ids)


if __name__ == "__main__":
    main()
