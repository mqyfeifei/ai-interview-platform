import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Config:
    """基础配置，所有环境共享的配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-THIS')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL',
        'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/ai_interview_dev')
    SQLALCHEMY_ECHO = True  # 打印SQL语句

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL',
        'postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/ai_interview_test')
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # 必须从环境变量获取，不留默认值
    SQLALCHEMY_ECHO = False  # 关闭SQL打印

# 提供一个字典映射，方便根据环境名获取配置类
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig   # 默认使用开发环境
}