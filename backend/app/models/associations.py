from app.extensions import db


# 岗位 <-> 知识点（岗位知识大纲）
job_tags = db.Table(
    'job_tags',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('knowledge_tags.id', ondelete='CASCADE'), primary_key=True),
)


# 岗位 <-> 题目（跨岗位复用题目）
job_questions = db.Table(
    'job_questions',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True),
)
