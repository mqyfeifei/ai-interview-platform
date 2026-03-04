from app.extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    real_name = db.Column(db.String(50))
    school = db.Column(db.String(100))
    major = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    avatar_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键关联
    default_job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))

    # 关系属性 (方便查询)
    default_job = db.relationship('Job', backref='users')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'school': self.school,
            # ... 其他需要的字段
        }