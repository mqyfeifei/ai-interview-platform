"""
多模态情感分析在语音面试中的集成演示
展示AI面试官如何根据候选人情绪给予安抚
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 初始化 Flask 应用上下文
from app import create_app
app = create_app()


def demo_emotion_support_in_interview():
    """演示语音面试中的情绪安抚功能"""
    print("=" * 80)
    print("🎤 语音面试 - 多模态情感分析集成演示")
    print("=" * 80)
    
    from app.services.multimodal_emotion_service import MultimodalEmotionService
    
    service = MultimodalEmotionService()
    
    # ==================== 场景1: 候选人紧张 ====================
    print("\n" + "=" * 80)
    print("📝 场景1: 候选人紧张（叹气+呼吸急促）")
    print("=" * 80)
    
    result1 = service.analyze(
        audio_tags="[sigh][breath]",  # 叹气+呼吸急促
        asr_text="这个...我...我觉得可能有点难",
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 检测结果:")
    print(f"   主导情绪: {result1.dominant_emotion}")
    print(f"   置信度: {result1.fusion_confidence:.2%}")
    if result1.conflict_detected:
        print(f"   冲突类型: {result1.conflict_type}")
        print(f"   仲裁原因: {result1.arbitration_reason}")
    
    print(f"\n💬 AI面试官的安抚话术示例:")
    print(f"   \"听得出你有些紧张，没关系，我们慢慢来。这个问题确实需要思考...\"")
    print(f"\n📊 详细分析:")
    if result1.voice_emotion:
        print(f"   语音情感: {result1.voice_emotion.to_dict()}")
    if result1.text_emotion:
        print(f"   文本情感: {result1.text_emotion.to_dict()}")
    print(f"   LLM推理: {result1.llm_reasoning[:100]}...")
    
    # ==================== 场景2: 候选人自信 ====================
    print("\n" + "=" * 80)
    print("📝 场景2: 候选人自信（笑声+流畅回答）")
    print("=" * 80)
    
    result2 = service.analyze(
        audio_tags="[laughter]",  # 笑声
        asr_text="我对这个项目非常有信心，之前做过类似的系统架构设计",
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 检测结果:")
    print(f"   主导情绪: {result2.dominant_emotion}")
    print(f"   置信度: {result2.fusion_confidence:.2%}")
    
    print(f"\n💬 AI面试官的鼓励话术示例:")
    print(f"   \"感受到你的自信，很好！让我们继续深入探讨一下架构设计的细节...\"")
    print(f"\n📊 详细分析:")
    if result2.voice_emotion:
        print(f"   语音情感: {result2.voice_emotion.to_dict()}")
    if result2.text_emotion:
        print(f"   文本情感: {result2.text_emotion.to_dict()}")
    
    # ==================== 场景3: 候选人犹豫 ====================
    print("\n" + "=" * 80)
    print("📝 场景3: 候选人犹豫（停顿+语速慢）")
    print("=" * 80)
    
    result3 = service.analyze(
        audio_tags="[pause][pause]",  # 多次停顿
        asr_text="嗯...让我想想...这个概念我好像听说过，但不太确定",
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 检测结果:")
    print(f"   主导情绪: {result3.dominant_emotion}")
    print(f"   置信度: {result3.fusion_confidence:.2%}")
    
    print(f"\n💬 AI面试官的引导话术示例:")
    print(f"   \"这个问题确实需要思考，不用着急。我们可以先从基础概念开始...\"")
    print(f"\n📊 详细分析:")
    if result3.voice_emotion:
        print(f"   语音情感: {result3.voice_emotion.to_dict()}")
    if result3.text_emotion:
        print(f"   文本情感: {result3.text_emotion.to_dict()}")
    
    # ==================== 场景4: 强冲突（语音负面 vs 文本正面）====================
    print("\n" + "=" * 80)
    print("📝 场景4: 强冲突（语音紧张但文本回答正确）")
    print("=" * 80)
    
    result4 = service.analyze(
        audio_tags="[breath][sigh]",  # 呼吸急促+叹气
        asr_text="我认为应该使用Redis做缓存，因为它支持高并发读写",  # 正确答案
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"\n✅ 检测结果:")
    print(f"   主导情绪: {result4.dominant_emotion}")
    print(f"   置信度: {result4.fusion_confidence:.2%}")
    if result4.conflict_detected:
        print(f"   ⚠️ 检测到冲突!")
        print(f"   冲突类型: {result4.conflict_type}")
        print(f"   仲裁原因: {result4.arbitration_reason}")
    
    print(f"\n💬 AI面试官的理解话术示例:")
    print(f"   \"虽然听得出你有些紧张，但你的回答非常准确！继续保持...\"")
    print(f"\n📊 详细分析:")
    if result4.voice_emotion:
        print(f"   语音情感: {result4.voice_emotion.to_dict()}")
    if result4.text_emotion:
        print(f"   文本情感: {result4.text_emotion.to_dict()}")
    print(f"   权重分配: 语音={result4.voice_weight:.2f}, 文本={result4.text_weight:.2f}")
    
    print("\n" + "=" * 80)
    print("✨ 演示完成！")
    print("=" * 80)
    
    print("\n💡 关键特性总结:")
    print("   ✅ 实时检测候选人情绪状态")
    print("   ✅ 智能识别语音与文本的情感冲突")
    print("   ✅ 动态调整安抚策略（紧张/自信/犹豫）")
    print("   ✅ LLM生成自然、个性化的安抚话术")
    print("   ✅ 让AI面试官更有'情商'和'温度'")


if __name__ == '__main__':
    # 在 Flask 应用上下文中运行
    with app.app_context():
        demo_emotion_support_in_interview()
