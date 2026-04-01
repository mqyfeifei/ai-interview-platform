# backend/app/models/user.py
from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键：默认岗位
    default_job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    default_job = db.relationship('Job', backref='users')

    # 将密码逻辑封装在 Model 层，避免 Controller 变胖
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'school': self.school,
            'major': self.major,
            'grade': self.grade,
            'avatar_url': self.avatar_url,
            'default_job': self.default_job.name if self.default_job else None,
            'default_job_id': self.default_job_id,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }