# backend/app/models/__init__.py

# 依次导入所有模型，这样 Migration 工具才能扫描到它们
from .job import Job
from .user import User
from .question import Question
from .interview import Interview, InterviewChat, Dimension, InterviewScore
from .learning import Resource