from app import create_app, db
from app.models.user import User
from app.models.resume import Resume  # 请确保你的Resume模型路径正确
import json
from datetime import datetime

app = create_app()

with app.app_context():
    # ===================== 1. 插入10个脱敏用户（无学校信息）=====================
    test_users = [
        {"username": "user01", "password": "test123456", "phone": "13800138001", "email": "user01@test.com", "real_name": "学生01", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user02", "password": "test123456", "phone": "13800138002", "email": "user02@test.com", "real_name": "学生02", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user03", "password": "test123456", "phone": "13800138003", "email": "user03@test.com", "real_name": "学生03", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user04", "password": "test123456", "phone": "13800138004", "email": "user04@test.com", "real_name": "学生04", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user05", "password": "test123456", "phone": "13800138005", "email": "user05@test.com", "real_name": "学生05", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user06", "password": "test123456", "phone": "13800138006", "email": "user06@test.com", "real_name": "学生06", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user07", "password": "test123456", "phone": "13800138007", "email": "user07@test.com", "real_name": "学生07", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user08", "password": "test123456", "phone": "13800138008", "email": "user08@test.com", "real_name": "学生08", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "user09", "password": "test123456", "phone": "13800138009", "email": "user09@test.com", "real_name": "学生09", "school": "高校", "major": "计算机相关", "grade": "本科"},
        {"username": "admin01", "password": "admin123456", "phone": "13800138010", "email": "admin@test.com", "real_name": "管理员", "school": "系统内置", "major": "系统管理", "grade": None, "role": "admin"}
    ]

    user_list = []
    for user_data in test_users:
        payload = dict(user_data)
        role = payload.pop("role", "user")
        password = payload.pop("password")

        user = User.query.filter_by(username=payload["username"]).first()
        if user:
            user.phone = payload.get("phone")
            user.email = payload.get("email")
            user.real_name = payload.get("real_name")
            user.school = payload.get("school")
            user.major = payload.get("major")
            user.grade = payload.get("grade")
            user.role = role
            user.set_password(password)
        else:
            user = User(**payload, role=role)
            user.set_password(password)
            db.session.add(user)
        user_list.append(user)

    db.session.flush()  # 立即生成用户ID，确保简历能绑定

    # ===================== 2. 插入对应简历（与用户ID完全同步）=====================
    resume_contents = [
        # 1 Java后端
        '{"personal": {"name": "学生01", "gender": "男", "age": 0, "experience": 0, "email": "user01@test.com", "phone": "13800138001", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677706, "start": "2026-02-01", "end": "2026-04-30", "title": "校园小程序开发", "description": "参与校园服务类小程序开发，负责前端页面与接口联调", "achievements": "提升了校内服务查询效率，用户反馈良好"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 2 Java后端
        '{"personal": {"name": "学生02", "gender": "男", "age": 0, "experience": 0, "email": "user02@test.com", "phone": "13800138002", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677707, "start": "2026-02-01", "end": "2026-04-30", "title": "课程管理系统开发", "description": "参与课程管理系统后端接口开发，负责用户模块与权限控制", "achievements": "系统稳定运行，支持200+用户并发访问"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 3 Java后端
        '{"personal": {"name": "学生03", "gender": "男", "age": 0, "experience": 0, "email": "user03@test.com", "phone": "13800138003", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677708, "start": "2026-02-01", "end": "2026-04-30", "title": "数据可视化项目", "description": "参与校园数据可视化平台开发，负责数据清洗与图表展示", "achievements": "实现了校园数据的实时监控与报表生成"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 4 Java后端
        '{"personal": {"name": "学生04", "gender": "男", "age": 0, "experience": 0, "email": "user04@test.com", "phone": "13800138004", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677709, "start": "2026-02-01", "end": "2026-04-30", "title": "实验室管理系统开发", "description": "参与实验室预约管理系统开发，负责预约模块与消息通知", "achievements": "优化了预约流程，减少了管理工作量"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 5 Java后端
        '{"personal": {"name": "学生05", "gender": "男", "age": 0, "experience": 0, "email": "user05@test.com", "phone": "13800138005", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677710, "start": "2026-02-01", "end": "2026-04-30", "title": "校园论坛开发", "description": "参与校园论坛前后端开发，负责帖子模块与评论功能", "achievements": "支持用户发帖、评论与点赞，提升了校园交流效率"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 6 CV算法
        '{"personal": {"name": "学生06", "gender": "男", "age": 0, "experience": 0, "email": "user06@test.com", "phone": "13800138006", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "CV算法工程师", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Python"},{"id":2,"name":"PyTorch"},{"id":3,"name":"OpenCV"},{"id":4,"name":"深度学习"},{"id":5,"name":"模型部署"}], "campusExperiences": [{"id": 1776651677711, "start": "2026-02-01", "end": "2026-04-30", "title": "校园目标检测项目", "description": "参与校园场景目标检测模型训练与推理优化，负责数据标注与实验对比", "achievements": "模型在验证集上达到稳定效果，支持基础实时识别演示"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 7 Network
        '{"personal": {"name": "学生07", "gender": "男", "age": 0, "experience": 0, "email": "user07@test.com", "phone": "13800138007", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Network工程师", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"TCP/IP"},{"id":2,"name":"Linux网络"},{"id":3,"name":"Nginx"},{"id":4,"name":"Wireshark"},{"id":5,"name":"网络排障"}], "campusExperiences": [{"id": 1776651677712, "start": "2026-02-01", "end": "2026-04-30", "title": "校园网络监控系统", "description": "参与网络状态采集与异常告警模块开发，负责链路监控与日志分析", "achievements": "实现网络异常及时告警，提升了日常运维排障效率"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 8 测试开发
        '{"personal": {"name": "学生08", "gender": "男", "age": 0, "experience": 0, "email": "user08@test.com", "phone": "13800138008", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "测试开发工程师", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Python"},{"id":2,"name":"PyTest"},{"id":3,"name":"Selenium"},{"id":4,"name":"JMeter"},{"id":5,"name":"接口测试"}], "campusExperiences": [{"id": 1776651677713, "start": "2026-02-01", "end": "2026-04-30", "title": "在线考试系统测试平台", "description": "参与自动化测试脚本开发，负责接口回归与性能压测方案", "achievements": "关键功能回归效率提升，提前发现并定位多项稳定性问题"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 9 前端
        '{"personal": {"name": "学生09", "gender": "男", "age": 0, "experience": 0, "email": "user09@test.com", "phone": "13800138009", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "前端开发工程师", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "高校", "major": "计算机相关", "degree": "本科"}], "skills": [{"id":1,"name":"Vue"},{"id":2,"name":"JavaScript"},{"id":3,"name":"TypeScript"},{"id":4,"name":"Element Plus"},{"id":5,"name":"ECharts"}], "campusExperiences": [{"id": 1776651677714, "start": "2026-02-01", "end": "2026-04-30", "title": "校园地图导航前端项目", "description": "参与校园地图导航小程序前端开发，负责地图展示与交互优化", "achievements": "实现流畅的路径展示与信息弹窗，提升了用户使用体验"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}',
        # 10 管理员
        '{"personal": {"name": "管理员", "gender": "男", "age": 0, "experience": 0, "email": "admin@test.com", "phone": "13800138010", "avatar": "", "address": "", "summary": ""}, "objective": {"jobType": "实习", "position": "Java后端开发", "city": "", "salary": "", "status": ""}, "education": [{"id": 1, "start": "", "end": "", "school": "系统内置", "major": "系统管理", "degree": "本科"}], "skills": [{"id":1,"name":"Java"},{"id":2,"name":"Spring Boot"},{"id":3,"name":"MySQL"},{"id":4,"name":"Redis"},{"id":5,"name":"MyBatis"}], "campusExperiences": [{"id": 1776651677715, "start": "2026-02-01", "end": "2026-04-30", "title": "校园二手交易平台", "description": "参与校园二手交易平台开发，负责商品发布与交易模块", "achievements": "支持用户发布、浏览与交易二手物品，促进了资源循环利用"}], "internshipExperiences": [], "workExperiences": [], "projectExperiences": [], "prices": [{"id": 1, "award": "", "period": "", "level": ""}], "blockOrder": ["profile", "objective", "education", "campus", "internship", "work", "project", "prices", "skills"], "config": {"titleColor": "#2B2B2B", "bodyColor": "#4F4F4F", "fontSize": 14, "padding": 20}}'
    ]

    # 批量插入/更新简历，自动绑定对应用户ID
    for i, content in enumerate(resume_contents):
        resume = Resume.query.filter_by(user_id=user_list[i].id, is_main=True).first()
        if resume:
            resume.title = "主简历"
            resume.job_id = 1
            resume.content = content
            resume.updated_at = datetime.now()
        else:
            resume = Resume(
                user_id=user_list[i].id,
                title="主简历",
                is_main=True,
                job_id=1,
                content=content,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(resume)

    # 最终提交
    db.session.commit()
    print("✅ 10个用户 + 对应简历 已全部插入成功！")
