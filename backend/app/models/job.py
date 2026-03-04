
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 如 "Java后端开发"
    description = db.Column(db.Text)
    tech_stack = db.Column(JSONB)  # JSON数组存储技术栈
    icon_url = db.Column(db.Text)

    # 关系：反向关联题目（字符串引用避免循环导入）
    questions = db.relationship('Question', backref='job', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tech_stack': self.tech_stack,
            'icon_url': self.icon_url
        }