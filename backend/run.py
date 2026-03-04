# backend/run.py
import os
from app import create_app

# 1. 确定当前运行环境
config_name = os.environ.get('FLASK_ENV', 'development')

# 2. 使用工厂函数创建应用实例
app = create_app(config_name)

if __name__ == '__main__':
    # 3. 启动应用
    # debug=True 让代码修改后自动重启，方便开发
    # host='0.0.0.0' 允许局域网访问（如果不加只能本机访问）
    app.run(host='0.0.0.0', port=5000, debug=True)