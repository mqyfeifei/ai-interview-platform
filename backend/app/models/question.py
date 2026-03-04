# backend/app/models/question.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector  # 关键导入


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # basic, scenario, followup
    difficulty = db.Column(db.String(10))
    keywords = db.Column(JSONB)
    reference_answer = db.Column(db.Text)
    knowledge_points = db.Column(JSONB)

    # 向量字段：1536维（对应 OpenAI text-embedding-3-small）
    embedding = db.Column(Vector(1536))

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'difficulty': self.difficulty
        }