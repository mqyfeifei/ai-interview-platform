# backend/app/models/learning.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime

# 多对多关联表：资源 - 知识点标签
resource_tags = db.Table('resource_tags',
                         db.Column('resource_id', db.Integer, db.ForeignKey('resources.id', ondelete='CASCADE'),
                                   primary_key=True),
                         db.Column('tag_id', db.Integer, db.ForeignKey('knowledge_tags.id', ondelete='CASCADE'),
                                   primary_key=True)
                         )


class KnowledgeTag(db.Model):
    __tablename__ = 'knowledge_tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # article, video, course, example
    url = db.Column(db.Text)
    content = db.Column(db.Text)
    source = db.Column(db.String(100))
    thumbnail = db.Column(db.Text)
    difficulty = db.Column(db.String(10))  # easy, medium, hard
    tags = db.Column(JSONB)  # JSON 形式的标签备份或扩展
    embedding = db.Column(Vector(1536))

    # 关系
    knowledge_tags = db.relationship('KnowledgeTag', secondary=resource_tags, backref='resources')


class UserLearning(db.Model):
    __tablename__ = 'user_learning'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    progress = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint('user_id', 'resource_id'),)


class UserKnowledgeMastery(db.Model):
    __tablename__ = 'user_knowledge_mastery'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('knowledge_tags.id', ondelete='CASCADE'), nullable=False)
    mastery_level = db.Column(db.Integer, default=0)  # 0-100
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'tag_id'),)