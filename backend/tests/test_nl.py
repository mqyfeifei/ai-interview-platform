from test_tts_standalone import _extract_ready_tts_segments
text = """更具体地说：
1. 在“局部窗口注意力”中，自注意力计算被限制在不重叠的、固定的局部窗口内。这虽然降低了计算量，但导致了什么问题？
2. “移位窗口注意力”是如何通过在下一层滑动窗口位置来解决上述问题的？请描述一下这个“滑动”或“移位”的具体操作（可以提到cyclic shift等关键词）。
3. 这种设计最终达成了什么核心目标？（提示：在计算效率和模型建模能力之间取得平衡）"""
segments, rem = _extract_ready_tts_segments(text)
for i, s in enumerate(segments):
    print(f"[{i}] {s!r}")
print(f"rem: {rem!r}")
