import json
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.prompt import AiPrompt
from app.models.interview import Interview, InterviewChat, InterviewSessionConfig


STYLE_OPTIONS = {
    '1': '压力面',
    '2': '自信面',
    '3': '教学面',
}


def get_existing_user():
    """获取数据库中已有的用户"""
    users = User.query.limit(5).all()
    if not users:
        print('数据库中没有用户，请先创建用户。')
        return None
    
    print('\n请选择用户:')
    for i, user in enumerate(users, 1):
        print(f'  {i}. {user.username} ({user.email})')
    
    while True:
        selected = input('输入编号(1-5): ').strip()
        try:
            idx = int(selected) - 1
            if 0 <= idx < len(users):
                return users[idx]
        except ValueError:
            pass
        print('输入无效，请重新输入。')


def get_existing_job():
    """获取数据库中已有的岗位"""
    jobs = Job.query.limit(5).all()
    if not jobs:
        print('数据库中没有岗位，请先创建岗位。')
        return None
    
    print('\n请选择岗位:')
    for i, job in enumerate(jobs, 1):
        print(f'  {i}. {job.name}')
    
    while True:
        selected = input('输入编号(1-5): ').strip()
        try:
            idx = int(selected) - 1
            if 0 <= idx < len(jobs):
                return jobs[idx]
        except ValueError:
            pass
        print('输入无效，请重新输入。')


def ensure_prompt(job_id):
    """确保岗位有默认的Prompt"""
    prompt = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
    if not prompt:
        prompt = AiPrompt(
            name=f'{Job.query.get(job_id).name}默认Prompt',
            job_id=job_id,
            system_prompt='你是专业面试官，每次问一个问题；当你认为评估充分时，在末尾输出[INTERVIEW_OVER]。',
            greeting_message='你好，我们开始今天的面试。',
            is_active=True,
        )
        db.session.add(prompt)
        db.session.commit()
    return prompt


def choose_style():
    print('\n请选择面试类型:')
    print('  1. 压力面')
    print('  2. 自信面')
    print('  3. 教学面')

    while True:
        selected = input('输入编号(1/2/3): ').strip()
        if selected in STYLE_OPTIONS:
            return STYLE_OPTIONS[selected]
        print('输入无效，请重新输入 1/2/3。')


def parse_sse_chunks(response):
    full_reply = ''
    for chunk_bytes in response.response:
        chunk_str = chunk_bytes.decode('utf-8', errors='ignore')
        for line in chunk_str.split('\n'):
            if not line.startswith('data: '):
                continue
            try:
                payload = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            chunk_text = payload.get('chunk', '')
            full_reply += chunk_text
            if chunk_text:
                print(chunk_text.replace('[INTERVIEW_OVER]', ''), end='', flush=True)
    print()
    return full_reply


def run_manual_console_test():
    app = create_app('development')
    client = app.test_client()

    with app.app_context():
        # 获取现有用户
        user = get_existing_user()
        if not user:
            return
        
        # 获取现有岗位
        job = get_existing_job()
        if not job:
            return
        
        # 确保岗位有Prompt
        ensure_prompt(job.id)
        
        # 选择面试类型
        style = choose_style()

        print('\n' + '=' * 60)
        print('AI文字面试控制台测试启动')
        print(f'用户: {user.username}')
        print(f'岗位: {job.name}')
        print(f'已选择面试类型: {style}')
        print('=' * 60)

        # 启动面试
        start_res = client.post(
            '/api/v1/interviews/start',
            json={
                'user_id': user.id,
                'job_id': job.id,
                'voice_mode': False,
                'interview_style': style,
            },
        )
        start_json = start_res.get_json() or {}

        if start_res.status_code != 200 or start_json.get('code') != 200:
            print('\n[错误] 启动失败')
            print(start_json)
            return

        data = start_json.get('data', {})
        interview_id = data.get('interview_id')
        print(f"\nInterview ID: {interview_id}")
        print('开场白:', data.get('question', ''))
        print('会话配置:', data.get('session_config', {}))

        # 面试过程
        while True:
            user_input = input('\n你: ').strip()
            if user_input.lower() in {'exit', 'quit', '退出', '结束'}:
                break
            if not user_input:
                continue

            print('考官: ', end='', flush=True)
            response = client.post(
                f'/api/v1/interviews/{interview_id}/chat/stream',
                json={'answer': user_input, 'voice_mode': False},
            )
            full_reply = parse_sse_chunks(response)
            if '[INTERVIEW_OVER]' in full_reply:
                print('[系统] 检测到面试官结束信号。')
                break

        # 结束面试并生成报告
        print('\n[系统] 正在生成报告...')
        finish_res = client.post(f'/api/v1/interviews/{interview_id}/finish')
        finish_json = finish_res.get_json() or {}
        print('[系统] 报告接口返回:', finish_json.get('msg', ''))

        # 数据库核验
        interview = Interview.query.get(interview_id)
        chat_count = InterviewChat.query.filter_by(interview_id=interview_id).count()
        session_cfg = InterviewSessionConfig.query.filter_by(interview_id=interview_id).first()

        print('\n' + '=' * 60)
        print('数据库核验结果')
        print('=' * 60)
        print('面试状态:', interview.status if interview else None)
        print('总得分:', interview.total_score if interview else None)
        print('对话条数:', chat_count)
        if session_cfg:
            print('interview_style:', session_cfg.interview_style)
            print('tech_ratio/scenario_ratio:', f'{session_cfg.tech_ratio}/{session_cfg.scenario_ratio}')
            print('difficulty_level:', session_cfg.difficulty_level)
        else:
            print('未找到 InterviewSessionConfig 记录')

        # 验证面试类型是否正确落库
        expected_style = 'teaching' if style == '教学面' else ('pressure' if style == '压力面' else 'confident')
        if session_cfg and session_cfg.interview_style != expected_style:
            print('[警告] 落库类型与选择不一致，请检查后端映射逻辑。')
        else:
            print('[通过] 面试类型选择与数据库落库一致。')

        # 显示图谱覆盖率
        if interview:
            print('\n图谱评估结果:')
            print('图谱覆盖率:', interview.graph_coverage_rate, '%')
            print('图谱深度率:', interview.graph_depth_rate, '%')


if __name__ == '__main__':
    run_manual_console_test()
