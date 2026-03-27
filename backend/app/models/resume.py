# backend/app/models/resume.py
"""
Resume data model.

Design:
- Each user has exactly ONE "main resume" (is_main=True, job_id=None).
- Users can have multiple "job-customized resumes" (is_main=False, job_id=<int>).
- Resume content (sections, block order, config) is stored as JSON in the `content`
  column so the schema stays flexible while the editor evolves.
"""

from app.extensions import db
from datetime import datetime
import json


class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)

    # Owner
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Metadata
    title = db.Column(db.String(100), nullable=False, default='我的简历')
    is_main = db.Column(db.Boolean, nullable=False, default=False)

    # Optional link to a job type (NULL for the main resume)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True)

    # Full resume payload stored as JSON text.
    # Schema mirrors the Vue component's reactive state:
    # {
    #   personal:              {...},
    #   objective:             {...},
    #   education:             [...],
    #   skills:                [...],
    #   campusExperiences:     [...],
    #   internshipExperiences: [...],
    #   workExperiences:       [...],
    #   prices:                [...],
    #   blockOrder:            [...],
    #   config:                {...},
    # }
    content = db.Column(db.Text, nullable=False, default='{}')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    job = db.relationship('Job', backref=db.backref('resumes', lazy='dynamic'))

    # ------------------------------------------------------------------ helpers

    def get_content(self) -> dict:
        """Return the parsed content dict (never raises)."""
        try:
            return json.loads(self.content) if self.content else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_content(self, data: dict) -> None:
        """Serialize and store the content dict."""
        self.content = json.dumps(data, ensure_ascii=False)

    def to_dict(self, include_content: bool = True) -> dict:
        result = {
            'id': self.id,
            'title': self.title,
            'isMain': self.is_main,
            'jobId': self.job_id,
            'jobName': self.job.name if self.job else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            result['content'] = self.get_content()
        return result