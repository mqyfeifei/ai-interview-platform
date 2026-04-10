import sys
sys.path.append('e:/ai-interview-platform/backend')
sys.stdout.reconfigure(encoding='utf-8')
from app.services.interview_service import InterviewService

def test():
    text = "你的回答触及了核心，但不够精确和完整。让我们更严谨地探讨一下。在ViT中，输入图像首先被分割成一系列扁平的图像块（patches）。每个patch经过线性投影后，会生成三个向量：Query (Q)、Key (K) 和 Value (V)。你所说的“互相作为对方的key和value”这个描述，更准确地说，是所有patches共享同一个生成Q、K、V的线性变换参数，但每个patch会生成自己独立的Q、K、V向量。接下来，请你详细描述一下： 1. 计算过程：给定所有patches的Q、K、V矩阵，Self-Attention的具体计算公式是什么？请写出公式并解释每一步（例如缩放点积、Softmax）的作用。 2. 多头机制：“多头”（Multi-Head）具体是如何实现的？它相比单头注意力有什么优势？ 3. 长距离依赖：基于上述计算过程，请解释为们什么MHSA能够天然地捕获任意两个patch之间的依赖关系，而不像CNN那样受限于卷积核的局部感受野。"

    segments, rem = InterviewService._extract_ready_tts_segments(text)
    for i, s in enumerate(segments):
        print(f"[{i}] {s}")

if __name__ == '__main__':
    test()
