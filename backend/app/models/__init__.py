# backend/app/models/__init__.py
from .job import Job
from .user import User
from .question import Question
from .interview import Interview, InterviewChat, Dimension, InterviewScore, UserGrowth
from .learning import Resource, KnowledgeTag, UserLearning, UserKnowledgeMastery
from .prompt import AiPrompt, InterviewScene
from .knowledge import KnowledgeItem