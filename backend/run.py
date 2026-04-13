# backend/run.py
import os
from app import create_app

# 1. 确定当前运行环境
config_name = os.environ.get('FLASK_ENV', 'development')

# 2. 使用工厂函数创建应用实例
app = create_app(config_name)

if __name__ == '__main__':
    # 使用 SocketIO 启动（支持 WebSocket）
    from app.extensions import socketio
    # debug=True 让代码修改后自动重启，use eventlet for async
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
