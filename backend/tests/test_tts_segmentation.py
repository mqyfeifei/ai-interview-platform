#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 分片逻辑测试脚本
测试 _extract_ready_tts_segments 和 _extract_tail_tts_segment 的改进效果
"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.interview_service import InterviewService

def test_tts_segmentation():
    """测试 TTS 分片逻辑"""
    print("=" * 60)
    print("TTS 分片逻辑测试")
    print("=" * 60)
    
    # 测试用例 1：多个问题组合
    test_cases = [
        {
            'name': '多个问题（带追问）',
            'text': '请介绍一下你的工作经历。你最近做过什么项目？项目中遇到的最大挑战是什么？',
            'expected_min_segments': 2
        },
        {
            'name': '完整对话流程',
            'text': '好的。我来追问一下，你能详细讲讲那个系统架构吗？包括核心模块设计。另外，团队中还有其他人参与吗？',
            'expected_min_segments': 3
        },
        {
            'name': '短碎片处理',
            'text': '嗯。对。很好。那么你对这个技术栈有什么想补充的吗？',
            'expected_min_segments': 1
        },
        {
            'name': '长句子自动分割',
            'text': '这是一个非常长的句子，包含了很多信息，需要在逗号处进行分割以避免单个TTS片段过长导致延迟问题，你看这样是否合理呢？',
            'expected_min_segments': 1
        }
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n【测试 {idx}】{test_case['name']}")
        print(f"输入文本：{test_case['text']}")
        
        # 测试 _extract_ready_tts_segments
        segments, remaining = InterviewService._extract_ready_tts_segments(test_case['text'])
        
        print(f"提取的分片数：{len(segments)}")
        if segments:
            for i, seg in enumerate(segments, 1):
                speakable = InterviewService._count_tts_speakable_chars(seg)
                print(f"  [{i}] ({speakable} 字符) {repr(seg[:60])}")
        
        if remaining:
            print(f"剩余文本：{repr(remaining)}")
            # 尝试提取尾句
            tail = InterviewService._extract_tail_tts_segment(remaining)
            if tail:
                speakable = InterviewService._count_tts_speakable_chars(tail)
                print(f"  [尾] ({speakable} 字符) {repr(tail[:60])}")
        
        # 检查是否满足预期
        total_segments = len(segments) + (1 if remaining and InterviewService._extract_tail_tts_segment(remaining) else 0)
        if total_segments >= test_case['expected_min_segments']:
            print(f"✅ 测试通过（预期至少 {test_case['expected_min_segments']} 个分片，实际 {total_segments} 个）")
        else:
            print(f"❌ 测试失败（预期至少 {test_case['expected_min_segments']} 个分片，实际 {total_segments} 个）")
    
    print("\n" + "=" * 60)
    print("TTS 分片测试完毕")
    print("=" * 60)
    
    # 测试尾句处理
    print("\n【尾句处理测试】")
    tail_cases = [
        ("这是一个尾句", True),
        ("。。。", False),
        ("，，，", False),
        ("", False),
        ("a", True),
        ("好", True),
        ("  ", False),
    ]
    
    for text, should_extract in tail_cases:
        tail = InterviewService._extract_tail_tts_segment(text)
        result = "有内容" if tail else "无内容"
        status = "✅" if (tail is not None) == should_extract else "❌"
        print(f"{status} 尾句 {repr(text)}: {result}")

if __name__ == '__main__':
    test_tts_segmentation()
