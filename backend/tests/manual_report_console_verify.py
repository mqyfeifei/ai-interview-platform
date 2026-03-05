import json
import time
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension


def ensure_job(name='Java后端开发'):
    job = Job.query.filter_by(name=name).first()
    if not job:
        job = Job(name=name, description='测试岗位', tech_stack=['Java', 'Spring Boot'])
        db.session.add(job)
        db.session.flush()
    return job


def ensure_dimensions():
    names = ['技术正确性', '逻辑严谨性', '岗位匹配度', '表达沟通', '应变能力']
    result = {}
    for name in names:
        dim = Dimension.query.filter_by(name=name).first()
        if not dim:
            dim = Dimension(name=name, description=f'{name}维度')
            db.session.add(dim)
            db.session.flush()
        result[name] = dim
    return result


def create_user_and_token(client):
    ts = str(int(time.time() * 1000))
    payload = {
        'username': f'report_console_{ts}',
        'real_name': '报告控制台测试',
        'school': '测试大学',
        'major': '软件工程',
        'grade': '大三',
        'email': f'report_console_{ts}@example.com',
        'phone': '1' + ts[-10:],
        'password': 'Test@123456'
    }

    reg = client.post('/api/v1/auth/register', json=payload)
    if reg.status_code != 200:
        raise RuntimeError(f'注册失败: {reg.status_code} {reg.get_json()}')

    login = client.post('/api/v1/auth/login', json={
        'loginId': payload['email'],
        'password': payload['password']
    })
    if login.status_code != 200:
        raise RuntimeError(f'登录失败: {login.status_code} {login.get_json()}')

    token = (login.get_json() or {}).get('data', {}).get('token', '')
    user_id = (reg.get_json() or {}).get('data', {}).get('user', {}).get('id')
    return user_id, token


def create_completed_interview(user_id):
    job = ensure_job('Java后端开发')
    dim_map = ensure_dimensions()

    interview = Interview(
        user_id=user_id,
        job_id=job.id,
        status='completed',
        total_score=86,
        question_count=3,
        start_time=datetime.utcnow() - timedelta(minutes=12),
        end_time=datetime.utcnow(),
        used_time=720,
        evaluation_highlights='亮点1：回答结构清晰\n亮点2：技术点覆盖全面',
        evaluation_improvements='改进1：可补充更多项目量化指标\n改进2：系统设计深度可增强',
        evaluation_suggestions='建议1：每个项目补充2-3个可量化指标\n建议2：准备高并发场景的架构拆解模板\n建议3：复盘慢查询优化案例并形成话术'
    )
    db.session.add(interview)
    db.session.flush()

    db.session.add_all([
        InterviewChat(interview_id=interview.id, role='ai', content='请做自我介绍。'),
        InterviewChat(interview_id=interview.id, role='user', content='我有三年后端开发经验。'),
        InterviewChat(interview_id=interview.id, role='ai', content='请说明你如何优化慢查询。'),
        InterviewChat(interview_id=interview.id, role='user', content='我会从索引、SQL和执行计划入手。')
    ])

    db.session.add_all([
        InterviewScore(interview_id=interview.id, dimension_id=dim_map['技术正确性'].id, score=88, comment='技术点准确'),
        InterviewScore(interview_id=interview.id, dimension_id=dim_map['逻辑严谨性'].id, score=84, comment='结构清晰'),
        InterviewScore(interview_id=interview.id, dimension_id=dim_map['岗位匹配度'].id, score=90, comment='匹配度高'),
        InterviewScore(interview_id=interview.id, dimension_id=dim_map['表达沟通'].id, score=83, comment='表达流畅'),
        InterviewScore(interview_id=interview.id, dimension_id=dim_map['应变能力'].id, score=85, comment='应对较好')
    ])

    db.session.commit()
    return interview.id


def print_report_console_view(report):
    print('\n================ 当前报告界面返回（控制台） ================')
    print(f"报告ID: {report.get('id')}")
    print(f"岗位: {report.get('jobName')} ({report.get('jobId')})")
    print(f"总分: {report.get('totalScore')}  用时(秒): {report.get('duration')}  创建时间: {report.get('createdAt')}")

    print('\n[维度得分]')
    print(json.dumps(report.get('dimensions', {}), ensure_ascii=False, indent=2))

    print('\n[对比平均分]')
    print(json.dumps(report.get('avgDimensions', {}), ensure_ascii=False, indent=2))

    print('\n[亮点]')
    for item in report.get('highlights', []):
        print(f'- {item}')

    print('\n[待改进]')
    for item in report.get('improvements', []):
        print(f"- {item.get('point')}")

    print('\n[改进建议]')
    for item in report.get('suggestions', []):
        print(f'- {item}')

    print('\n[问答明细]')
    for q in report.get('questions', []):
        print(f"Q{q.get('index')}: {q.get('question')}")
        print(f"A : {q.get('answer')}")
        print(f"分数: {q.get('score')}  追问: {q.get('isFollowUp')}")
        print('-' * 56)


def main():
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        user_id, token = create_user_and_token(client)
        report_id = create_completed_interview(user_id)

        resp = client.get(
            f'/api/v1/reports/{report_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        print(f'HTTP: {resp.status_code}')
        body = resp.get_json() or {}
        print(f"code: {body.get('code')}  msg: {body.get('msg')}")

        if resp.status_code != 200:
            print(json.dumps(body, ensure_ascii=False, indent=2))
            return

        report_data = body.get('data', {})
        print_report_console_view(report_data)


if __name__ == '__main__':
    main()
