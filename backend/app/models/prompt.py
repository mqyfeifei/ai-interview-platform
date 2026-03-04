# backend/app/models/prompt.py
from app.extensions import db
from datetime import datetime


class AiPrompt(db.Model):
    __tablename__ = 'ai_prompts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='SET NULL'))
    role_description = db.Column(db.Text)
    system_prompt = db.Column(db.Text)
    greeting_message = db.Column(db.Text)
    questioning_style = db.Column(db.String(50))
    temperature = db.Column(db.Numeric(2, 1), default=0.7)
    max_tokens = db.Column(db.Integer, default=500)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    scenes = db.relationship('InterviewScene', backref='prompt', lazy=True)


class InterviewScene(db.Model):
    __tablename__ = 'interview_scenes'

    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('ai_prompts.id'), nullable=False)
    scene_name = db.Column(db.String(50))  # opening, technical, stress, closing
    scene_prompt = db.Column(db.Text)