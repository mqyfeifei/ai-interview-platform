# backend/app/models/learning.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))  # article, video
    url = db.Column(db.Text)
    content = db.Column(db.Text)  # 用于向量化的内容
    embedding = db.Column(Vector(1536))

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'url': self.url}