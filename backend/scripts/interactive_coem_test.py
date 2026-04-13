#!/usr/bin/env python
"""
Interactive CoEM streaming test script

用法：在 backend 目录下激活虚拟环境后直接运行此脚本。
脚本会：
- 启动 Flask app 的 test_client
- 创建一个临时用户与面试（如果需要）
- 你输入一句话作为用户回答，脚本会调用流式 Chat 接口
- 测量首个数据包到达时间与整个回复完成时间，并打印每个接收到的文本片段

注意：需要在 dev 环境下运行，并且数据库里有至少一个 job（岗位）和示例数据。
"""
import sys
import time
import json
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job


def ensure_test_user_and_job(app):
    with app.app_context():
        # user
        user = User.query.filter_by(username='coem_tester').first()
        if not user:
            user = User(username='coem_tester', email='coem@test.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

        job = Job.query.first()
        if not job:
            raise RuntimeError('No job found in DB. Please import job/knowledge data before testing CoEM.')

        # ensure the test user has a minimal resume to pass validation
        try:
            from app.services.resume_service import ResumeService
            # build a minimal resume content dict expected by ResumeService
            minimal_resume = {
                'content': {
                    'personal': {
                        'name': '测试 用户',
                        'phone': '13800000000',
                        'email': 'coem@test.com'
                    },
                    'education': [
                        {'school': '测试大学', 'degree': '本科', 'major': '计算机科学', 'start': '2016', 'end': '2020'}
                    ],
                    'skills': ['Python', '算法', '数据结构'],
                    'workExperiences': [
                        {
                            'company': '测试公司',
                            'position': '工程师',
                            'start': '2020-01',
                            'end': '2021-12',
                            'description': '参与测试项目',
                            'achievements': '主导模块性能优化，将响应时间降低30%'
                        }
                    ],
                }
            }
            # Save or upsert resume for the test user
            try:
                ResumeService.save_main_resume(user.id, minimal_resume['content'])
                print('[TEST] 已写入测试简历（临时）')
            except Exception:
                # rollback to clear any partial transaction state before fallback write
                try:
                    db.session.rollback()
                except Exception:
                    pass
                # fallback: try lower-level model write
                from app.models.resume import Resume
                r = Resume.query.filter_by(user_id=user.id).first()
                if not r:
                    r = Resume(user_id=user.id)
                    r.set_content(minimal_resume['content'])
                    db.session.add(r)
                else:
                    r.set_content(minimal_resume['content'])
                db.session.commit()
                print('[TEST] 已写入测试简历（通过模型保存）')
        except Exception as e:
            print(f"[TEST] 写入测试简历失败: {e}")

        return user.id, job.id


def run_interactive():
    app = create_app('development')
    client = app.test_client()

    user_id, job_id = ensure_test_user_and_job(app)

    # start interview
    res = client.post('/api/v1/interviews/start', json={'user_id': user_id, 'job_id': job_id})
    try:
        start_json = res.get_json()
    except Exception:
        start_json = None
    print(f"Start API status: {res.status_code}, response: {start_json}")

    if res.status_code != 200 or not start_json or 'data' not in start_json:
        print("Failed to start interview. See response above. Aborting test.")
        return

    start_data = start_json.get('data', {})
    interview_id = start_data.get('interview_id')
    print(f"Started interview {interview_id}.\n")

    print('输入你的问题/回答（输入 退出 以结束）：')
    while True:
        text = input('你: ').strip()
        if not text:
            continue
        if text in ('退出', 'quit', 'exit'):
            break

        payload = {'answer': text}
        start_time = time.time()
        res = client.post(f'/api/v1/interviews/{interview_id}/chat/stream', json=payload)

        first_chunk_time = None
        full_text = ''
        print('\nAI: ', end='', flush=True)

        for raw in res.response:
            part = raw.decode('utf-8')
            for line in part.split('\n'):
                if not line:
                    continue
                if line.startswith(':'):  # heartbeat or control
                    continue
                if line.startswith('data: '):
                    try:
                        obj = json.loads(line[6:])
                    except Exception:
                        continue
                    chunk_text = obj.get('chunk', '')
                    if chunk_text:
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                        print(chunk_text, end='', flush=True)
                        full_text += chunk_text
                    audio_b64 = obj.get('audio_b64')
                    done = obj.get('done')
                    if audio_b64:
                        print('\n[AUDIO PACKET RECEIVED]', end='', flush=True)
                    if done:
                        print('\n[DONE]')
        end_time = time.time()
        if first_chunk_time:
            print(f"首字节延迟: {first_chunk_time - start_time:.3f}s, 完成延迟: {end_time - start_time:.3f}s")
        else:
            print(f"没有接收到文本片段，完整时间: {end_time - start_time:.3f}s")

    # After interactive loop, cleanup created interview records
    with app.app_context():
        try:
            from app.models.interview import Interview, InterviewChat, InterviewSessionConfig
            # delete chats
            chats = InterviewChat.query.filter_by(interview_id=interview_id).all()
            for c in chats:
                db.session.delete(c)
            # delete session config
            cfgs = InterviewSessionConfig.query.filter_by(interview_id=interview_id).all()
            for cfg in cfgs:
                db.session.delete(cfg)
            # delete interview
            inv = Interview.query.get(interview_id)
            if inv:
                db.session.delete(inv)
            db.session.commit()
            print(f"[TEST] 已删除面试记录与相关聊天 (interview_id={interview_id})")
        except Exception as e:
            print(f"[TEST] 清理面试记录失败: {e}")


if __name__ == '__main__':
    run_interactive()
