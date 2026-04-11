"""
腾讯云ASR情感分析测试脚本
用法: python tests/test_tencent_emotion.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_emotion_tag_parser():
    """测试情感标签解析器"""
    print("=" * 60)
    print("🧠 测试情感标签解析器")
    print("=" * 60)
    
    from app.services.emotion_tag_parser import EmotionTagParser
    
    # 测试用例1: 包含多个情感标签
    test_text1 = "我觉得[pause]这个方案[laughter]还不错[breath]"
    print(f"\n📝 测试文本: {test_text1}")
    
    analysis = EmotionTagParser.analyze_emotion_from_tags(test_text1)
    print(f"✅ 主导情绪: {analysis['dominant_emotion']}")
    print(f"✅ 情绪标签: {analysis['emotion_tags']}")
    print(f"✅ 情绪摘要: {analysis['emotion_summary']}")
    print(f"✅ 置信度: {analysis['confidence']:.0%}")
    
    prompt = EmotionTagParser.format_for_llm(test_text1)
    print(f"✅ 大模型提示词:\n   {prompt}")
    
    clean = EmotionTagParser.clean_emotion_tags(test_text1)
    print(f"✅ 清理后文本: {clean}")
    
    # 测试用例2: 无情感标签
    test_text2 = "这是一个普通的回答，没有任何情绪标记"
    print(f"\n📝 测试文本: {test_text2}")
    
    analysis2 = EmotionTagParser.analyze_emotion_from_tags(test_text2)
    print(f"✅ 主导情绪: {analysis2['dominant_emotion']}")
    print(f"✅ 情绪标签: {analysis2['emotion_tags']}")
    print(f"✅ 情绪摘要: {analysis2['emotion_summary']}")
    
    print("\n" + "=" * 60)
    print("✨ 情感标签解析器测试完成")
    print("=" * 60)


def test_tencent_asr_with_emotion():
    """测试腾讯云ASR（含情感分析）"""
    print("\n" + "=" * 60)
    print("🚀 测试腾讯云ASR（含情感分析）")
    print("=" * 60)
    
    from app import create_app
    
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
            
            print("⏳ 正在调用腾讯云ASR API（含情感分析）...")
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
            print(f"📝 识别结果（可能包含情感标签）: {text}")
            
            # 检查是否包含情感标签
            if '[' in text and ']' in text:
                print("🎭 检测到情感标签!")
                
                from app.services.emotion_tag_parser import EmotionTagParser
                analysis = EmotionTagParser.analyze_emotion_from_tags(text)
                print(f"   主导情绪: {analysis['dominant_emotion']}")
                print(f"   情绪标签: {analysis['emotion_tags']}")
                print(f"   情绪摘要: {analysis['emotion_summary']}")
                
                prompt = EmotionTagParser.format_for_llm(text)
                print(f"   大模型提示词:\n   {prompt}")
            else:
                print("ℹ️  未检测到情感标签（可能是平静语调）")
            
            print(f"📊 完整响应数据: {result['data']}")
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
    print("✨ ASR情感分析测试完成")
    print("=" * 60)


if __name__ == '__main__':
    # 先测试情感标签解析器
    test_emotion_tag_parser()
    
    # 再测试完整的ASR流程
    test_tencent_asr_with_emotion()
