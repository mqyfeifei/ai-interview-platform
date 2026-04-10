#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 分片逻辑单元测试（独立版本）
不依赖外部依赖，仅测试核心分片算法
"""

import re

class SimpleTTSTest:
    _TTS_SENTENCE_BOUNDARY_PATTERN = re.compile(r'[。！？；!?;!？\n]')
    _TTS_SOFT_BOUNDARY_PATTERN = re.compile(r'[，,:：]')
    _TTS_SPEAKABLE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')
    _MIN_TTS_SPEAKABLE_CHARS = 2
    _TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS = 12
    _TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS = 70
    
    @classmethod
    def _count_tts_speakable_chars(cls, text):
        return len(cls._TTS_SPEAKABLE_CHAR_PATTERN.findall(text or ''))
    
    @classmethod
    def _is_valid_tts_segment(cls, text, force=False):
        if not text:
            return False
        min_chars = 1 if force else cls._MIN_TTS_SPEAKABLE_CHARS
        return cls._count_tts_speakable_chars(text) >= min_chars
    
    @classmethod
    def _extract_ready_tts_segments(cls, buffer_text):
        """从累计缓冲中提取已闭合的可播报句子"""
        text = buffer_text or ''
        segments = []
        segment_start = 0
        speakable_count = 0
        last_soft_boundary = -1

        def append_segment_if_valid(split_pos, force_valid=False):
            nonlocal segment_start, speakable_count, last_soft_boundary
            if split_pos <= segment_start:
                return False

            candidate = text[segment_start:split_pos]
            if not cls._is_valid_tts_segment(candidate, force=force_valid):
                return False

            segments.append(candidate)
            segment_start = split_pos
            speakable_count = 0
            last_soft_boundary = -1
            return True

        for index, ch in enumerate(text):
            char_pos = index + 1
            if cls._TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
                speakable_count += 1

            if cls._TTS_SOFT_BOUNDARY_PATTERN.match(ch):
                last_soft_boundary = char_pos
                if speakable_count >= cls._TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS:
                    append_segment_if_valid(char_pos, force_valid=False)
                    continue

            if cls._TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
                append_segment_if_valid(char_pos, force_valid=True)
                continue

            if speakable_count >= cls._TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS:
                split_pos = last_soft_boundary if last_soft_boundary > segment_start else char_pos
                did_split = append_segment_if_valid(split_pos, force_valid=False)
                if did_split and split_pos < char_pos:
                    speakable_count = cls._count_tts_speakable_chars(text[segment_start:char_pos])

        return segments, text[segment_start:]
    
    @classmethod
    def _extract_tail_tts_segment(cls, buffer_text):
        """提取尾句（更严格的检查）"""
        if not buffer_text:
            return None
        
        candidate = buffer_text.strip()
        if cls._count_tts_speakable_chars(candidate) >= 1:
            return candidate
        return None


def test_tts_segmentation():
    """测试 TTS 分片逻辑"""
    print("=" * 70)
    print("TTS 分片逻辑测试（独立版本）")
    print("=" * 70)
    
    test_cases = [
        {
            'name': '多个问题（带追问）',
            'text': '请介绍一下你的工作经历。你最近做过什么项目？项目中遇到的最大挑战是什么？',
            'expected_segments': 3
        },
        {
            'name': '完整对话流程',
            'text': '好的。我来追问一下，你能详细讲讲那个系统架构吗？包括核心模块设计。另外，团队中还有其他人参与吗？',
            'expected_segments': 4
        },
        {
            'name': '短碎片处理',
            'text': '嗯。对。很好。那么你对这个技术栈有什么想补充的吗？',
            'expected_segments': 2
        },
        {
            'name': '长句子自动分割',
            'text': '这是一个非常长的句子，包含了很多信息，需要在逗号处进行分割以避免单个TTS片段过长导致延迟问题，你看这样是否合理呢？',
            'expected_segments': 2
        },
        {
            'name': '尾句测试',
            'text': '好的，我明白了',
            'expected_segments': 1
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n【测试 {idx}】{test_case['name']}")
        print(f"输入文本：{test_case['text']}")
        
        segments, remaining = SimpleTTSTest._extract_ready_tts_segments(test_case['text'])
        
        print(f"提取的分片数：{len(segments)}")
        if segments:
            for i, seg in enumerate(segments, 1):
                speakable = SimpleTTSTest._count_tts_speakable_chars(seg)
                print(f"  [{i}] ({speakable:2d} 字符) {repr(seg[:50])}")
        
        if remaining:
            print(f"剩余文本：{repr(remaining)}")
            tail = SimpleTTSTest._extract_tail_tts_segment(remaining)
            if tail:
                speakable = SimpleTTSTest._count_tts_speakable_chars(tail)
                print(f"  [尾] ({speakable:2d} 字符) {repr(tail[:50])}")
                total_segments = len(segments) + 1
            else:
                total_segments = len(segments)
        else:
            total_segments = len(segments)
        
        total_tests += 1
        if total_segments >= test_case['expected_segments']:
            print(f"✅ 通过（预期 {test_case['expected_segments']} 个分片，实际 {total_segments} 个）")
            passed_tests += 1
        else:
            print(f"❌ 失败（预期 {test_case['expected_segments']} 个分片，实际 {total_segments} 个）")
    
    print("\n" + "=" * 70)
    print("尾句处理测试")
    print("=" * 70)
    
    tail_cases = [
        ("这是一个尾句", True, "正常尾句"),
        ("。。。", False, "纯标点"),
        ("，，，", False, "纯标点"),
        ("", False, "空字符串"),
        ("a", True, "单字符"),
        ("好", True, "单中文字"),
        ("  ", False, "纯空白"),
        ("你好吗？", True, "带标点的正常文本"),
    ]
    
    for text, should_extract, desc in tail_cases:
        total_tests += 1
        tail = SimpleTTSTest._extract_tail_tts_segment(text)
        has_content = tail is not None
        status = "✅" if has_content == should_extract else "❌"
        result = "有内容" if tail else "无内容"
        print(f"{status} {desc:20s} {repr(text):15s} → {result}")
        if has_content == should_extract:
            passed_tests += 1
    
    print("\n" + "=" * 70)
    print(f"测试结果：{passed_tests}/{total_tests} 通过")
    print("=" * 70)
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = test_tts_segmentation()
    exit(0 if success else 1)
