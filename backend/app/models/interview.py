# backend/app/models/interview.py
from app.extensions import db
from datetime import datetime


class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    # --- 新增报告详情字段 ---
    evaluation_highlights = db.Column(db.Text)  # 亮点分析
    evaluation_improvements = db.Column(db.Text)  # 待改进点
    evaluation_suggestions = db.Column(db.Text)  # 改进建议

    # --- 新增设计文档中要求的字段 ---
    question_count = db.Column(db.Integer, default=0)  # 总题数
    used_time = db.Column(db.Integer)  # 用时（秒）
    # ---------------------------

    # 关系
    chats = db.relationship('InterviewChat', backref='interview', lazy='dynamic', cascade='all, delete-orphan')
    scores = db.relationship('InterviewScore', backref='interview', lazy='dynamic')
    # 新增：关联成长记录
    growth_records = db.relationship('UserGrowth', backref='interview', lazy='dynamic')


class InterviewChat(db.Model):
    __tablename__ = 'interview_chats'

    id = db.Column(db.BigInteger, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    role = db.Column(db.String(10), nullable=False)  # 'ai' or 'user'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # --- 新增设计文档中要求的字段 ---
    duration = db.Column(db.Integer)  # 用户回答耗时
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))  # 关联题目
    # ---------------------------


class Dimension(db.Model):
    __tablename__ = 'dimensions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    # --- 修复报错的关键：添加描述字段 ---
    description = db.Column(db.Text)
    # --------------------------------


class InterviewScore(db.Model):
    __tablename__ = 'interview_scores'
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimensions.id'))
    score = db.Column(db.Integer)
    comment = db.Column(db.Text)


# 确保 UserGrowth 也在这个文件中（之前补充的）
class UserGrowth(db.Model):
    __tablename__ = 'user_growth'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimensions.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    record_time = db.Column(db.DateTime, default=datetime.utcnow)