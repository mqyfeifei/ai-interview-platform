# backend/app/models/interview.py
from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    # Use local server time consistently with interview end_time writes.
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    # --- 新增报告详情字段 ---
    evaluation_highlights = db.Column(db.Text)  # 亮点分析
    evaluation_improvements = db.Column(db.Text)  # 待改进点
    evaluation_suggestions = db.Column(db.Text)  # 改进建议

    # --- 新增设计文档中要求的字段 ---
    question_count = db.Column(db.Integer, default=0)  # 总题数
    used_time = db.Column(db.Integer)  # 用时（秒）
    graph_coverage_rate = db.Column(db.Float)
    graph_depth_rate = db.Column(db.Float)
    graph_coverage_meta = db.Column(JSONB)
    # ---------------------------

    # 关系
    chats = db.relationship('InterviewChat', backref='interview', lazy='dynamic', cascade='all, delete-orphan')
    scores = db.relationship('InterviewScore', backref='interview', lazy='dynamic')
    # 新增：关联成长记录
    growth_records = db.relationship('UserGrowth', backref='interview', lazy='dynamic')
    session_config = db.relationship('InterviewSessionConfig', backref='interview', uselist=False, cascade='all, delete-orphan')


class InterviewChat(db.Model):
    __tablename__ = 'interview_chats'

    id = db.Column(db.BigInteger, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    role = db.Column(db.String(10), nullable=False)  # 'ai' or 'user'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # --- 新增设计文档中要求的字段 ---
    duration = db.Column(db.Integer)  # 用户回答耗时
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))  # 关联题目
    # ---------------------------

    # === 新增语音合成字段 ===
    tts_audio_id = db.Column(db.Integer, db.ForeignKey('tts_audios.id', ondelete='SET NULL'), nullable=True)

class TTSAudio(db.Model):
    __tablename__ = 'tts_audios'

    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, nullable=True) # 记录使用的是哪个配置
    file_path = db.Column(db.String(255), nullable=False) # 相对路径
    format = db.Column(db.String(20), default='mp3')
    voice = db.Column(db.String(50)) # 记录当时使用的音色
    duration = db.Column(db.Float, nullable=True) # 时长(秒)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 建立反向关系，方便从音频查聊天记录
    chat_record = db.relationship('InterviewChat', backref='tts_audio', lazy='dynamic')

class Dimension(db.Model):
    __tablename__ = 'dimensions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    # --- 修复报错的关键：添加描述字段 ---
    description = db.Column(db.Text)
    # --------------------------------


class InterviewScore(db.Model):
    __tablename__ = 'interview_scores'
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'))
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimensions.id'))
    score = db.Column(db.Integer)
    comment = db.Column(db.Text)


class InterviewSessionConfig(db.Model):
    __tablename__ = 'interview_session_configs'

    id = db.Column(db.BigInteger, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), unique=True, nullable=False)
    profile_id = db.Column(db.BigInteger, db.ForeignKey('interview_profiles.id', ondelete='SET NULL'), nullable=True)

    interview_style = db.Column(db.String(20), nullable=False, default='confident')
    tech_ratio = db.Column(db.Float, nullable=False, default=60.0)
    scenario_ratio = db.Column(db.Float, nullable=False, default=40.0)
    project_deep_dive_percentage = db.Column(db.Float, nullable=False, default=15.0)
    behavioral_percentage = db.Column(db.Float, nullable=False, default=15.0)
    difficulty_low_percentage = db.Column(db.Float, nullable=False, default=30.0)
    difficulty_medium_percentage = db.Column(db.Float, nullable=False, default=50.0)
    difficulty_high_percentage = db.Column(db.Float, nullable=False, default=20.0)

    is_dynamic_adjust = db.Column(db.Boolean, nullable=False, default=True)
    voice_id = db.Column(db.String(100))
    speech_speed = db.Column(db.Float, default=1.0)
    tone_descriptor = db.Column(db.Text)
    enabled_dimensions = db.Column(JSONB)
    difficulty_level = db.Column(db.Integer, default=2)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = db.relationship('InterviewProfile', backref='session_configs')


class InterviewProfile(db.Model):
    __tablename__ = 'interview_profiles'

    id = db.Column(db.BigInteger, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    round = db.Column(db.Integer)

    technique_percentage = db.Column(db.Float, nullable=False, default=60.0)
    scenario_percentage = db.Column(db.Float, nullable=False, default=40.0)
    project_deep_dive_percentage = db.Column(db.Float, nullable=False, default=15.0)
    behavioral_percentage = db.Column(db.Float, nullable=False, default=15.0)
    difficulty_low_percentage = db.Column(db.Float, nullable=False, default=30.0)
    difficulty_medium_percentage = db.Column(db.Float, nullable=False, default=50.0)
    difficulty_high_percentage = db.Column(db.Float, nullable=False, default=20.0)
    is_dynamic_adjust = db.Column(db.Boolean, nullable=False, default=True)

    interviewer_style = db.Column(db.String(20), nullable=False)
    custom_personality_json = db.Column(JSONB)

    voice_id = db.Column(db.String(100))
    speech_speed = db.Column(db.Float, default=1.0)
    tone_descriptor = db.Column(db.Text)

    enabled_dimensions = db.Column(ARRAY(db.String()))
    difficulty_level = db.Column(db.Integer, default=2)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = db.relationship('Job', backref='interview_profiles')


# 确保 UserGrowth 也在这个文件中（之前补充的）
class UserGrowth(db.Model):
    __tablename__ = 'user_growth'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'), nullable=False)
    dimension_id = db.Column(db.Integer, db.ForeignKey('dimensions.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    record_time = db.Column(db.DateTime, default=datetime.utcnow)