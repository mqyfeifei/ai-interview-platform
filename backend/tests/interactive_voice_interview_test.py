"""
交互式语音面试测试脚本
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
    print(f"\n📋 大模型提示词:\n   {prompt[:200]}...\n")
    
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
    print(f"\n📋 大模型提示词:\n   {prompt2[:200]}...\n")
    
    return result1, result2


def test_interview_chat_with_emotion(interview_id, user_answer, voice_mode=True):
    """测试面试对话（包含情感分析）"""
    from app.services.interview_service import InterviewService
    
    print_section(f"🎤 测试2: 面试对话 - 情感感知回复 (Interview ID: {interview_id})")
    
    print(f"📝 用户回答: {user_answer}")
    print(f"🔊 语音模式: {voice_mode}")
    print(f"\n⏳ 正在处理...\n")
    
    try:
        # 收集所有SSE事件
        events = []
        for item in InterviewService.process_chat_round_stream(
            interview_id,
            user_answer,
            voice_mode=voice_mode
        ):
            events.append(item)
            # 实时打印
            if item.startswith('data: '):
                data_str = item[6:].strip()
                if data_str and data_str != '[DONE]':
                    try:
                        data = json.loads(data_str)
                        chunk = data.get('chunk', '')
                        if chunk:
                            print(chunk, end='', flush=True)
                    except:
                        pass
        
        print("\n\n✅ 回复生成完成！")
        print(f"📊 总共接收 {len(events)} 个SSE事件")
        
        return events
        
    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def interactive_test():
    """交互式测试"""
    from app.services.interview_service import InterviewService
    
    print_section("🚀 语音面试交互式测试工具", char='*')
    print("说明:")
    print("  1. 首先启动一个面试会话")
    print("  2. 然后可以多次输入回答进行测试")
    print("  3. 输入 'quit' 或 'exit' 退出")
    print("  4. 输入 'help' 查看帮助")
    print()
    
    # Step 1: 启动面试
    print_section("Step 1: 启动面试会话")
    
    user_id = input("请输入用户ID [默认: 1]: ").strip() or "1"
    job_id = input("请输入岗位ID [默认: 1]: ").strip() or "1"
    
    try:
        user_id = int(user_id)
        job_id = int(job_id)
    except ValueError:
        print("❌ 无效的ID，必须是数字")
        return
    
    print(f"\n⏳ 正在启动面试 (user_id={user_id}, job_id={job_id})...")
    
    try:
        result = InterviewService.start_interview(
            user_id=user_id,
            job_id=job_id,
            voice_mode=True,  # 启用语音模式
            interview_style=None,
            voice_role=None,
            voice=None
        )
        
        interview_id = result['interview_id']
        first_question = result.get('first_question', '')
        
        print(f"✅ 面试启动成功！")
        print(f"   - Interview ID: {interview_id}")
        print(f"   - 第一个问题: {first_question[:100]}...")
        
    except Exception as e:
        print(f"❌ 启动面试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: 测试多模态情感分析
    print_section("Step 2: 测试多模态情感分析")
    test_multimodal_emotion()
    
    # Step 3: 交互式对话测试
    print_section("Step 3: 开始交互式对话测试", char='-')
    print("💡 提示:")
    print("  - 直接输入文本回答（会自动进行情感分析）")
    print("  - 输入带标签的文本模拟语音特征，例如: '[sigh][pause]这个有点难'")
    print("  - 输入 'new' 重新开始一轮对话")
    print("  - 输入 'finish' 结束面试并生成报告")
    print()
    
    round_count = 0
    
    while True:
        try:
            user_input = input(f"\n[第{round_count + 1}轮] 请输入回答: ").strip()
            
            if not user_input:
                continue
            
            # 命令处理
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 测试结束")
                break
            
            if user_input.lower() == 'help':
                print("\n📖 帮助:")
                print("  - 直接输入文本: 正常回答")
                print("  - 带标签格式: [sigh][pause]文本回答")
                print("  - new: 获取新问题")
                print("  - finish: 结束面试")
                print("  - quit/exit/q: 退出测试")
                continue
            
            if user_input.lower() == 'new':
                print("\n⏳ 获取新问题...")
                # 这里可以调用API获取新问题
                print("💡 提示: 当前实现中，新问题由LLM自动生成")
                continue
            
            if user_input.lower() == 'finish':
                print(f"\n⏳ 正在结束面试 (ID: {interview_id})...")
                try:
                    report = InterviewService.finish_interview(interview_id)
                    print("✅ 面试已结束！")
                    print(f"📊 总分: {report.get('total_score', 'N/A')}")
                    print(f"📝 亮点: {report.get('evaluation_highlights', 'N/A')[:100]}...")
                except Exception as e:
                    print(f"❌ 结束面试失败: {e}")
                break
            
            # 正常对话
            round_count += 1
            print(f"\n{'=' * 80}")
            print(f"🔄 第{round_count}轮对话处理中...")
            print(f"{'=' * 80}\n")
            
            # 提取音频标签（如果有）
            has_audio_tags = '[' in user_input and ']' in user_input
            if has_audio_tags:
                print(f"🔍 检测到音频标签，将进行多模态情感分析")
            
            # 调用流式接口
            events = test_interview_chat_with_emotion(
                interview_id=interview_id,
                user_answer=user_input,
                voice_mode=True
            )
            
            if events:
                print(f"\n✅ 第{round_count}轮完成！")
            else:
                print(f"\n❌ 第{round_count}轮失败！")
        
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，测试结束")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    with app.app_context():
        interactive_test()
