from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    tech_stack = db.Column(JSONB)  # 对应 SQL 的 JSONB
    icon_url = db.Column(db.Text)

    # 关系：一个岗位对应多个题目
    questions = db.relationship('Question', backref='job', lazy='dynamic')