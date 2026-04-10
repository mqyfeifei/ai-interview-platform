import re

_TTS_SENTENCE_BOUNDARY_PATTERN = re.compile(r'[。！？；!?;!？\n]')
_TTS_SOFT_BOUNDARY_PATTERN = re.compile(r'[，、,:：]')
_TTS_SPEAKABLE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')

_MIN_TTS_SPEAKABLE_CHARS = 2
_TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS = 12
_TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS = 70
_STREAM_DISPLAY_CHUNK_CHARS = 10

def _strip_stream_control_tokens(text):
    return text.replace("[INTERVIEW_OVER]", "").strip()

def _count_tts_speakable_chars(text):
    return len(_TTS_SPEAKABLE_CHAR_PATTERN.findall(text or ''))

def _is_valid_tts_segment(text, force=False):
    clean_text = _strip_stream_control_tokens(text)
    if not clean_text:
        return False
    min_chars = 1 if force else _MIN_TTS_SPEAKABLE_CHARS
    return _count_tts_speakable_chars(clean_text) >= min_chars

def _extract_ready_tts_segments(buffer_text):
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
        if not _is_valid_tts_segment(candidate, force=force_valid):
            return False

        segments.append(_strip_stream_control_tokens(candidate))
        segment_start = split_pos
        speakable_count = 0
        last_soft_boundary = -1
        return True

    for index, ch in enumerate(text):
        char_pos = index + 1
        if _TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
            speakable_count += 1

        if _TTS_SOFT_BOUNDARY_PATTERN.match(ch):
            last_soft_boundary = char_pos
            if speakable_count >= _TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS:
                append_segment_if_valid(char_pos, force_valid=False)
                continue

        if _TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
            append_segment_if_valid(char_pos, force_valid=True)
            continue

        if speakable_count >= _TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS:
            split_pos = last_soft_boundary if last_soft_boundary > segment_start else char_pos
            did_split = append_segment_if_valid(split_pos, force_valid=False)
            if did_split and split_pos < char_pos:
                speakable_count = _count_tts_speakable_chars(text[segment_start:char_pos])

    return segments, text[segment_start:]

text = "更具体地说： 1. 在“局部窗口注意力”中，自注意力计算被限制在不重叠的、固定的局部窗口内。这虽然降低了计算量，但导致了什么问题？ 2. “移位窗口注意力”是如何通过在下一层滑动窗口位置来解决上述问题的？请描述一下这个“滑动”或“移位”的具体操作（可以提到cyclic shift等关键词）。 3. 这种设计最终达成了什么核心目标？（提示：在计算效率和模型建模能力之间取得平衡）"
segments, rem = _extract_ready_tts_segments(text)
for i, s in enumerate(segments):
    print(f"[{i}] {s}")
print(f"rem: {rem}")

print("=== First part test ===")
t1 = "🤖\n非常好！有实际项目经验是最好的学习方式。既然你在项目中用过Swin Transformer，那我们来深入探讨一下这个核心机制。这能很好地体现你对模型设计动机的理解。 请你结合自己的项目经验，具体说明： 在你使用Swin Transformer时，它的“移位窗口注意力”机制是如何工作的？更具体地说： 1. 在“局部窗口注意力”中，自注意力计算被限制在不重叠的、固定的局部窗口内。这虽然降低了计算量，但导致了什么问题？"
s1, r1 = _extract_ready_tts_segments(t1)
for i, s in enumerate(s1):
    print(f"[{i}] {s}")
