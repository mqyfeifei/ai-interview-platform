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

    # 关系
    chats = db.relationship('InterviewChat', backref='interview', lazy='dynamic', cascade='all, delete-orphan')
    scores = db.relationship('InterviewScore', backref='interview', lazy='dynamic')


class InterviewChat(db.Model):
    __tablename__ = 'interview_chats'

    id = db.Column(db.BigInteger, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    role = db.Column(db.String(10), nullable=False)  # 'ai' or 'user'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Dimension(db.Model):
    __tablename__ = 'dimensions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # 技术正确性, 逻辑严谨性...


class InterviewScore(db.Model):
    __tablename__ = 'interview_scores'
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimensions.id'))
    score = db.Column(db.Integer)
    comment = db.Column(db.Text)