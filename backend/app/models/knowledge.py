# backend/app/models/knowledge.py
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

class KnowledgeItem(db.Model):
    __tablename__ = 'knowledge_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False) # tip, mistake, model, practice
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    tags = db.Column(JSONB)
    embedding = db.Column(Vector(512))