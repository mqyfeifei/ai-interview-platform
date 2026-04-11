"""
腾讯云ASR和情感分析测试脚本
用法: python tests/test_tencent_asr.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db


def test_tencent_asr():
    """测试腾讯云语音识别"""
    print("=" * 60)
    print("🚀 开始测试腾讯云语音识别")
    print("=" * 60)
    
    # 创建应用
    app = create_app('development')
    client = app.test_client()
    
    # 测试音频文件路径
    audio_path = os.path.join(os.path.dirname(__file__), '录音.m4a')
    
    if not os.path.exists(audio_path):
        print(f"❌ 找不到测试音频文件: {audio_path}")
        print("💡 提示: 请在 tests 目录下放置一个名为 '录音.m4a' 的音频文件")
        return
    
    print(f"📂 测试音频: {audio_path}")
    print(f"📏 文件大小: {os.path.getsize(audio_path) / 1024:.2f} KB")
    print()
    
    try:
        # 上传音频进行识别
        with open(audio_path, 'rb') as f:
            data = {
                'audio': (f, 'test.wav')
            }
            
            print("⏳ 正在调用腾讯云ASR API...")
            response = client.post(
                '/api/v1/interviews/upload-audio',
                data=data,
                content_type='multipart/form-data'
            )
        
        # 解析响应
        result = response.get_json()
        
        if response.status_code == 200 and result.get('code') == 200:
            text = result['data'].get('text', '')
            print("✅ 识别成功!")
            print(f"📝 识别结果: {text}")
            print(f"📊 响应数据: {result['data']}")
        else:
            print(f"❌ 识别失败!")
            print(f"状态码: {response.status_code}")
            print(f"响应: {result}")
    
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✨ 测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_tencent_asr()
