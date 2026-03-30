# backend/app/models/example.py
from app.extensions import db
from pgvector.sqlalchemy import Vector

class Example(db.Model):
    __tablename__ = 'examples'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True) # 关联岗位
    question = db.Column(db.Text, nullable=False)                           # 题目内容
    framework = db.Column(db.Text)                                          # 回答框架
    answer = db.Column(db.Text, nullable=False)                             # 详细回答
    embedding = db.Column(Vector(512))                                      # 向量存储