"""
多模态情感分析服务测试脚本
用法: python tests/test_multimodal_emotion.py
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 初始化 Flask 应用上下文
from app import create_app
app = create_app()


def test_basic_multimodal_emotion():
    """测试基础多模态情感分析"""
    print("=" * 80)
    print("🧠 测试多模态情感分析服务")
    print("=" * 80)
    
    from app.services.multimodal_emotion_service import MultimodalEmotionService
    
    service = MultimodalEmotionService()
    
    # 测试用例1: 语音负面 + 文本正面（强冲突）
    print("\n" + "=" * 80)
    print("📝 测试用例1: 语音负面 + 文本正面（强冲突场景）")
    print("=" * 80)
    
    result = service.analyze(
        audio_tags="[sigh][breath]",  # 叹气+呼吸急促 → 紧张/沮丧
        asr_text="我觉得这个方案还不错，挺有创意的",  # 文本正面
        job_id=1,
        user_id=1,
        use_coem=False  # 简化测试，不使用COEM
    )
    
    print(f"\n✅ 主导情绪: {result.dominant_emotion}")
    print(f"✅ 融合置信度: {result.fusion_confidence:.2%}")
    print(f"✅ 冲突检测: {result.conflict_detected}")
    if result.conflict_detected:
        print(f"   - 冲突类型: {result.conflict_type}")
        print(f"   - 仲裁原因: {result.arbitration_reason}")
    print(f"✅ 权重分配: 语音={result.voice_weight:.2f}, 文本={result.text_weight:.2f}")
    
    if result.voice_emotion:
        print(f"✅ 语音情感向量: {result.voice_emotion.to_dict()}")
    if result.text_emotion:
        print(f"✅ 文本情感向量: {result.text_emotion.to_dict()}")
    if result.fused_emotion:
        print(f"✅ 融合情感向量: {result.fused_emotion.to_dict()}")
    
    print(f"\n✅ LLM终判:")
    print(f"   - 情绪: {result.llm_emotion}")
    print(f"   - 置信度: {result.llm_confidence:.2%}")
    print(f"   - 推理: {result.llm_reasoning}")
    
    # 格式化输出
    prompt = service.format_for_llm(result)
    print(f"\n✅ 大模型提示词:\n   {prompt}")
    
    # 测试用例2: 语音正面 + 文本正面（无冲突）
    print("\n" + "=" * 80)
    print("📝 测试用例2: 语音正面 + 文本正面（一致场景）")
    print("=" * 80)
    
    result2 = service.analyze(
        audio_tags="[laughter]",  # 笑声 → 轻松/自信
        asr_text="我对这个项目非常有信心，之前做过类似的项目",  # 文本正面
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 主导情绪: {result2.dominant_emotion}")
    print(f"✅ 融合置信度: {result2.fusion_confidence:.2%}")
    print(f"✅ 冲突检测: {result2.conflict_detected}")
    
    if result2.voice_emotion:
        print(f"✅ 语音情感向量: {result2.voice_emotion.to_dict()}")
    if result2.text_emotion:
        print(f"✅ 文本情感向量: {result2.text_emotion.to_dict()}")
    
    print(f"\n✅ LLM推理: {result2.llm_reasoning}")
    
    # 测试用例3: 仅文本（单模态）
    print("\n" + "=" * 80)
    print("📝 测试用例3: 仅文本模态（降级场景）")
    print("=" * 80)
    
    result3 = service.analyze(
        audio_tags="",  # 无语音标签
        asr_text="这个问题有点困难，我需要再想想",  # 文本略带负面
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 主导情绪: {result3.dominant_emotion}")
    print(f"✅ 融合置信度: {result3.fusion_confidence:.2%}")
    print(f"✅ 权重分配: 语音={result3.voice_weight:.2f}, 文本={result3.text_weight:.2f}")
    
    if result3.text_emotion:
        print(f"✅ 文本情感向量: {result3.text_emotion.to_dict()}")
    
    print("\n" + "=" * 80)
    print("✨ 多模态情感分析测试完成")
    print("=" * 80)


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 80)
    print("🔧 测试便捷函数")
    print("=" * 80)
    
    from app.services.multimodal_emotion_service import (
        analyze_multimodal_emotion,
        get_multimodal_emotion_prompt
    )
    
    # 测试字典格式输出
    result_dict = analyze_multimodal_emotion(
        audio_tags="[pause]",
        asr_text="我觉得还可以吧",
        use_coem=False
    )
    
    print(f"\n✅ 字典格式结果:")
    print(json.dumps(result_dict, indent=2, ensure_ascii=False))
    
    # 测试提示词格式输出
    prompt = get_multimodal_emotion_prompt(
        audio_tags="[breath]",
        asr_text="我有点紧张，但我会尽力回答",
        use_coem=False
    )
    
    print(f"\n✅ 提示词格式:")
    print(f"   {prompt}")
    
    print("\n" + "=" * 80)
    print("✨ 便捷函数测试完成")
    print("=" * 80)


if __name__ == '__main__':
    # 在 Flask 应用上下文中运行
    with app.app_context():
        # 测试基础功能
        test_basic_multimodal_emotion()
        
        # 测试便捷函数
        test_convenience_functions()
        
        print("\n🎉 所有测试完成！")
