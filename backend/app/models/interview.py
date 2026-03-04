from app.extensions import db
from datetime import datetime

class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    question_count = db.Column(db.Integer, default=0)
    used_time = db.Column(db.Integer) # 秒

    # 关系
    chats = db.relationship('InterviewChat', backref='interview', lazy='dynamic', cascade='all, delete-orphan')

class InterviewChat(db.Model):
    __tablename__ = 'interview_chats'

    id = db.Column(db.BigInteger, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(10), nullable=False) # 'ai' or 'user'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    duration = db.Column(db.Integer) # 用户回答耗时
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id')) # 关联题库