# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
# 初始化 SocketIO（使用 eventlet/gevent）
socketio = SocketIO(async_mode='eventlet', cors_allowed_origins='*')
