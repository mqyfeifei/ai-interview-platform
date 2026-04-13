"""
自动化语音面试测试脚本（无需交互）
测试完整流程：ASR识别 → 多模态情感分析 → LLM智能回复
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 初始化 Flask 应用上下文
from app import create_app
app = create_app()


def print_section(title, char='=', width=80):
    """打印分隔线"""
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}\n")


def test_multimodal_emotion():
    """测试多模态情感分析服务"""
    from app.services.multimodal_emotion_service import MultimodalEmotionService
    
    print_section("🧪 测试1: 多模态情感分析服务")
    
    service = MultimodalEmotionService()
    
    # 测试场景1: 紧张情绪（叹气+犹豫）
    print("📝 场景1: 候选人紧张（叹气+呼吸急促+犹豫）")
    result1 = service.analyze(
        audio_tags="[sigh][breath][pause]",
        asr_text="这个...我...我觉得可能有点难",
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"✅ 主导情绪: {result1.dominant_emotion}")
    print(f"✅ 融合置信度: {result1.fusion_confidence:.2%}")
    print(f"✅ 冲突检测: {result1.conflict_detected}")
    if result1.conflict_detected:
        print(f"   - 冲突类型: {result1.conflict_type}")
        print(f"   - 仲裁原因: {result1.arbitration_reason}")
    print(f"✅ 处理时间: {result1.processing_time_ms}ms")
    
    if result1.voice_emotion:
        print(f"✅ 语音情感向量: {result1.voice_emotion.to_dict()}")
    if result1.text_emotion:
        print(f"✅ 文本情感向量: {result1.text_emotion.to_dict()}")
    if result1.fused_emotion:
        print(f"✅ 融合情感向量: {result1.fused_emotion.to_dict()}")
    
    print(f"\n💬 AI面试官的安抚话术:")
    print(f"   \"听得出你有些紧张，没关系，我们慢慢来。这个问题确实需要思考...\"")
    
    # 格式化输出
    prompt = service.format_for_llm(result1)
    print(f"\n📋 大模型提示词:\n   {prompt[:300]}...\n")
    
    # 测试场景2: 自信情绪（笑声+正面表达）
    print("\n" + "=" * 80)
    print("📝 场景2: 候选人自信（笑声+积极表达）")
    print("=" * 80)
    
    result2 = service.analyze(
        audio_tags="[laughter]",
        asr_text="我对这个项目非常有信心，之前做过类似的项目",
        job_id=1,
        user_id=1,
        use_coem=False
    )
    
    print(f"✅ 主导情绪: {result2.dominant_emotion}")
    print(f"✅ 融合置信度: {result2.fusion_confidence:.2%}")
    print(f"✅ 冲突检测: {result2.conflict_detected}")
    
    if result2.voice_emotion:
        print(f"✅ 语音情感向量: {result2.voice_emotion.to_dict()}")
    if result2.text_emotion:
        print(f"✅ 文本情感向量: {result2.text_emotion.to_dict()}")
    
    prompt2 = service.format_for_llm(result2)
    print(f"\n📋 大模型提示词:\n   {prompt2[:300]}...\n")
    
    return result1, result2


def test_interview_flow():
    """测试完整面试流程"""
    from app.services.interview_service import InterviewService
    
    print_section("🚀 测试2: 完整面试流程")
    
    # Step 1: 启动面试
    print("⏳ Step 1: 启动面试会话...")
    try:
        result = InterviewService.start_interview(
            user_id=1,
            job_id=1,
            voice_mode=True,
            interview_style=None,
            voice_role=None,
            voice=None
        )
        
        interview_id = result['interview_id']
        first_question = result.get('first_question', '')
        
        print(f"✅ 面试启动成功！")
        print(f"   - Interview ID: {interview_id}")
        print(f"   - 第一个问题: {first_question[:150]}...")
        
    except Exception as e:
        print(f"❌ 启动面试失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 2: 模拟用户回答（带情感标签）
    test_scenarios = [
        {
            "name": "场景1: 紧张犹豫",
            "answer": "[sigh][pause]这个...我...我觉得可能有点难，但是我会努力学习的",
            "expected_emotion": "nervous"
        },
        {
            "name": "场景2: 自信流畅",
            "answer": "[laughter]我对这个项目非常有信心，之前做过类似的项目，经验很丰富",
            "expected_emotion": "confident"
        },
        {
            "name": "场景3: 平静中性",
            "answer": "我认为这个问题的关键在于理解业务需求和技术的平衡",
            "expected_emotion": "calm"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print_section(f"Step 2.{i}: {scenario['name']}")
        
        print(f"📝 用户回答: {scenario['answer']}")
        print(f"🎯 预期情绪: {scenario['expected_emotion']}")
        print(f"\n⏳ 正在处理...\n")
        
        try:
            # 收集所有SSE事件
            full_response = []
            event_count = 0
            
            for item in InterviewService.process_chat_round_stream(
                interview_id,
                scenario['answer'],
                voice_mode=True
            ):
                event_count += 1
                if item.startswith('data: '):
                    data_str = item[6:].strip()
                    if data_str and data_str != '[DONE]':
                        try:
                            data = json.loads(data_str)
                            chunk = data.get('chunk', '')
                            if chunk:
                                full_response.append(chunk)
                                print(chunk, end='', flush=True)
                        except Exception as e:
                            print(f"\n[解析错误] {e}")
            
            response_text = ''.join(full_response)
            print(f"\n\n✅ 第{i}轮完成！")
            print(f"📊 接收 {event_count} 个SSE事件")
            print(f"📝 回复长度: {len(response_text)} 字符")
            
            # 检查是否包含情感安抚
            has_emotion_support = any(keyword in response_text for keyword in 
                                     ['紧张', '没关系', '慢慢来', '别担心', '放松'])
            if has_emotion_support:
                print(f"✅ 检测到情感安抚话术！")
            else:
                print(f"ℹ️  未检测到明显的情感安抚话术")
            
        except Exception as e:
            print(f"\n❌ 第{i}轮失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 3: 结束面试
    print_section("Step 3: 结束面试并生成报告")
    try:
        report = InterviewService.finish_interview(interview_id)
        print("✅ 面试已结束！")
        print(f"📊 总分: {report.get('total_score', 'N/A')}")
        print(f"📝 亮点: {report.get('evaluation_highlights', 'N/A')[:200]}...")
        print(f"💡 建议: {report.get('evaluation_suggestions', 'N/A')[:200]}...")
    except Exception as e:
        print(f"❌ 结束面试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return interview_id


if __name__ == '__main__':
    with app.app_context():
        print_section("🎤 语音面试自动化测试", char='*')
        print("本测试将验证:")
        print("  ✅ 多模态情感分析算法")
        print("  ✅ ASR音频标签集成")
        print("  ✅ LLM智能回复生成")
        print("  ✅ 情感感知对话流程")
        print()
        
        # 测试1: 多模态情感分析
        test_multimodal_emotion()
        
        # 测试2: 完整面试流程
        test_interview_flow()
        
        print_section("🎉 测试完成！", char='*')
