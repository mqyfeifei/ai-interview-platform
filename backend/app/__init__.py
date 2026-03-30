# app/__init__.py
from flask import Flask
from flask import send_from_directory
import os

# 强制 Hugging Face 离线模式（整个应用生效）
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from app.extensions import db, migrate
from app.config import config   # 导入配置字典，而不是单个类

from pgvector.sqlalchemy import Vector
def render_item(type_, obj, autogen_context):
    """
        自定义 Alembic 的渲染行为：
        只要对象类型或模块名字里包含 'pgvector'，就自动注入 import pgvector
        """
    # 方案：通过字符串模糊匹配，比 isinstance 更稳健
    if type_ == 'type' and 'pgvector' in str(type(obj)):
        autogen_context.imports.add("import pgvector")
        return False

    # （可选）其实你甚至可以直接无脑加一行：com
    # autogen_context.imports.add("import pgvector")
    # 因为集合会自动去重，哪怕普通迁移带上这句也没任何副作用。

    return False

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')  # 从环境变量获取
    app = Flask(__name__)
    # 从配置字典中获取配置类
    app.config.from_object(config[config_name])

    # 初始化插件
    db.init_app(app)
    migrate.init_app(app, db, render_item=render_item)
    # 注册蓝图
    from app.api.v1.auth import auth_bp
    from app.api.v1.interview import interview_bp
    from app.api.v1.job import job_bp
    from app.api.v1.report import report_bp
    from app.api.v1.user import user_bp
    from app.api.v1.learning import learning_bp
    from app.api.v1.resumes import bp as resumes_bp
    from app.api.v1.admin import admin_bp
    app.register_blueprint(learning_bp, url_prefix='/api/v1/learning')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(interview_bp, url_prefix='/api/v1/interviews')
    app.register_blueprint(job_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(report_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(resumes_bp, url_prefix='/api/v1/resumes')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    # app.register_blueprint(resumes_bp, url_prefix='/api/v1')
    upload_root = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_root, exist_ok=True)

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        return send_from_directory(upload_root, filename)

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app