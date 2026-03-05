from flask import Flask
from flask import send_from_directory
import os
from app.extensions import db, migrate
from app.config import config   # 导入配置字典，而不是单个类

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')  # 从环境变量获取
    app = Flask(__name__)
    # 从配置字典中获取配置类
    app.config.from_object(config[config_name])

    # 初始化插件
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from app.api.v1.auth import auth_bp
    from app.api.v1.interview import interview_bp
    from app.api.v1.job import job_bp
    from app.api.v1.user import user_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(interview_bp, url_prefix='/api/v1/interviews')
    app.register_blueprint(job_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')

    upload_root = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_root, exist_ok=True)

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        return send_from_directory(upload_root, filename)

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app