from flask import Flask
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

    # 注册蓝图等（根据需要取消注释）
    # from app.api.v1.users import user_bp
    # app.register_blueprint(user_bp, url_prefix='/api/v1/users')

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app