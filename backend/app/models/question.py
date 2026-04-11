# backend/app/models/question.py
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector  # 关键导入
from .associations import job_questions

# --- 新增：题目与知识点标签的多对多关联表 ---
question_tags = db.Table('question_tags',
                         db.Column('question_id', db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True),
                         db.Column('tag_id', db.Integer, db.ForeignKey('knowledge_tags.id', ondelete='CASCADE'), primary_key=True)
                         )

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    # 扩大长度限制以兼容 technical, behavioral, project_deep_dive, scenario_design
    type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(10))
    keywords = db.Column(JSONB)
    # 将类型从 Text 修改为 JSONB，以存储 YAML 中的数组
    reference_answer = db.Column(JSONB)

    # 图谱增强字段：参考答案深度、结构化追问模板、前置技能要求
    reference_answer_depth = db.Column(db.Integer, default=1)
    follow_up_templates = db.Column(JSONB)
    required_skills_meta = db.Column(JSONB)

    # --- 新增字段 ---
    source = db.Column(db.String(100))                 # 题目来源
    status = db.Column(db.String(20), default='draft') # 状态：draft/published
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    embedding = db.Column(Vector(512))

    # --- 新增字段：建立与 KnowledgeTag 的ORM关系 ---
    # 使用字符串 'KnowledgeTag' 避免和 learning.py 产生循环导入问题
    knowledge_tags = db.relationship('KnowledgeTag', secondary=question_tags, backref=db.backref('questions', lazy='dynamic'))

    # 与岗位多对多，支持题目跨岗位复用
    jobs = db.relationship('Job', secondary=job_questions, back_populates='questions', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'difficulty': self.difficulty,
            'source': self.source,
            'status': self.status,
            'reference_answer_depth': self.reference_answer_depth,
            'follow_up_templates': self.follow_up_templates,
            'required_skills_meta': self.required_skills_meta
        }