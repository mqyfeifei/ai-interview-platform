import os
import sys

# 确保能正确导入 app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


def test_audio_recognition():
    # 创建开发环境下的应用实例
    app = create_app('development')
    client = app.test_client()

    # 获取当前目录下的 test.wav
    current_dir = os.path.dirname(__file__)
    audio_path = os.path.join(current_dir, '录音.m4a')

    if not os.path.exists(audio_path):
        print(f"[错误] 找不到音频文件: {audio_path}")
        print("请先录制一段音频并命名为 test.wav 放入 tests 目录下。")
        return

    print("========================================")
    print(f"🚀 开始测试语音转文字接口")
    print(f"📂 正在读取文件: {audio_path}")
    print("⏳ 模型正在解析中，请稍候（首次加载模型可能需要几十秒）...")
    print("========================================")

    # 模拟前端通过 FormData 上传文件
    with open(audio_path, 'rb') as f:
        data = {
            'audio': (f, 'test.wav')
        }

        # 发起 POST 请求
        response = client.post(
            '/api/v1/interviews/upload-audio',
            data=data,
            content_type='multipart/form-data'
        )

    # 解析返回结果
    res_json = response.get_json()

    if response.status_code == 200:
        print("\n✅ 测试通过！成功解析出以下文本：")
        print(f"💬 \"{res_json.get('data', {}).get('text')}\"")
    else:
        print("\n❌ 测试失败！")
        print(f"后端报错信息: {res_json.get('msg')}")


if __name__ == '__main__':
    test_audio_recognition()