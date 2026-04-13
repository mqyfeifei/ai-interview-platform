# 多模态情感分析服务使用指南

## 📋 概述

`MultimodalEmotionService` 是一个**后融合型多模态情感分析服务**，结合了：
- ✅ 腾讯云语音情感识别（通过ASR标签）
- ✅ 腾讯云文本情感分析API
- ✅ COEM检索增强上下文
- ✅ 动态权重分配机制
- ✅ 冲突仲裁规则
- ✅ LLM最终判决（可解释性）

---

## 🚀 快速开始

### 1. 基础用法

```python
from app.services.multimodal_emotion_service import MultimodalEmotionService

service = MultimodalEmotionService()

result = service.analyze(
    audio_tags="[pause][breath]",  # ASR返回的情感标签
    asr_text="我觉得这个方案还不错",  # ASR转写文本
    job_id=1,                       # 岗位ID（用于COEM检索）
    user_id=1,                      # 用户ID（用于COEM检索）
    use_coem=True                   # 是否启用COEM检索增强
)

print(f"主导情绪: {result.dominant_emotion}")
print(f"置信度: {result.fusion_confidence:.2%}")
print(f"LLM推理: {result.llm_reasoning}")
```

### 2. 便捷函数

```python
from app.services.multimodal_emotion_service import (
    analyze_multimodal_emotion,
    get_multimodal_emotion_prompt
)

# 获取字典格式结果
result_dict = analyze_multimodal_emotion(
    audio_tags="[laughter]",
    asr_text="我对这个项目很有信心",
    job_id=1,
    user_id=1
)

# 获取大模型提示词
prompt = get_multimodal_emotion_prompt(
    audio_tags="[sigh]",
    asr_text="这个问题有点难",
    job_id=1,
    user_id=1
)
```

---

## 🔧 在面试流程中集成

### 修改 `interview_qa_handler.py`

在现有的情感分析代码位置（约第204-230行），替换为新的多模态情感分析：

```python
# 旧代码（注释掉或删除）
# emotion_instruction = ""
# try:
#     from app.services.emotion_tag_parser import EmotionTagParser
#     if '[' in normalized_answer and ']' in normalized_answer:
#         emotion_analysis = EmotionTagParser.analyze_emotion_from_tags(normalized_answer)
#         ...

# 新代码：使用多模态情感分析
emotion_instruction = ""
try:
    from app.services.multimodal_emotion_service import get_multimodal_emotion_prompt
    
    # 提取音频标签（如果有）
    audio_tags = normalized_answer if '[' in normalized_answer else ""
    
    # 执行多模态情感分析
    emotion_prompt = get_multimodal_emotion_prompt(
        audio_tags=audio_tags,
        asr_text=normalized_answer,
        job_id=interview.job_id,
        user_id=interview.user_id,
        use_coem=current_app.config.get('USE_COEM_FOR_TEXT', False)
    )
    
    if emotion_prompt:
        emotion_instruction = f"\n\n💭 候选人情绪状态分析：\n{emotion_prompt}"
        print(f"[多模态情感分析] {emotion_prompt}")
        
except Exception as e:
    print(f"[多模态情感分析] 异常: {e}")
    # 降级到原有逻辑
    emotion_instruction = ""
```

---

## 📊 算法流程详解

### Step 1: 语音情感识别
- 输入：ASR情感标签（如 `[pause][breath]`）
- 处理：解析标签 → 映射到情感向量
- 输出：`EmotionVector(positive=0.1, negative=0.7, neutral=0.2)`

### Step 2: 文本情感识别
- 输入：ASR转写文本
- 处理：
  - 清理ASR标签
  - 调用腾讯云NLP情感API
  - （可选）COEM检索增强上下文
- 输出：`EmotionVector(positive=0.6, negative=0.2, neutral=0.2)`

### Step 3: 动态权重计算
- 评估语音模态质量（基于标签数量、置信度）
- 评估文本模态质量（基于文本长度、API置信度）
- 动态分配权重：`α = quality_audio / (quality_audio + quality_text)`

### Step 4: 加权融合
- 公式：`V_fused = α * V_audio + β * V_text`
- 归一化确保概率和为1

### Step 5: 冲突仲裁
检测以下冲突类型：
- **强冲突（语音优先）**：语音强烈负面 vs 文本正面 → 信任语音（语调更真实）
- **强冲突（保持融合）**：语音正面 vs 文本负面 → 保持融合结果（语义更可靠）
- **弱冲突**：双方都有明确情感但不一致 → 采用加权融合
- **无冲突**：直接输出融合结果

### Step 6: LLM最终判决
构建结构化Prompt，包含：
- 对话历史/检索上下文（COEM）
- 用户语音转录
- 多模态融合结果
- 权重分配信息
- 冲突仲裁说明

LLM输出JSON格式：
```json
{
  "emotion": "negative",
  "confidence": 0.75,
  "reasoning": "语音检测到紧张情绪（叹气+呼吸急促），虽然文本表达正面，但根据冲突仲裁规则，语音语调更真实反映候选人状态..."
}
```

---

## 🎯 关键参数配置

| 参数 | 默认值 | 说明 | 调整建议 |
|------|--------|------|---------|
| `DEFAULT_VOICE_WEIGHT` | 0.4 | 语音初始权重 | 语音质量好可提高 |
| `DEFAULT_TEXT_WEIGHT` | 0.6 | 文本初始权重 | 文本质量好可提高 |
| `STRONG_CONFLICT_THRESHOLD` | 0.7 | 强冲突阈值 | 越高越严格 |
| `temperature` (LLM) | 0.3 | LLM温度 | 越低越稳定 |

---

## 🧪 测试

运行测试脚本：

```bash
cd backend
python tests/test_multimodal_emotion.py
```

预期输出示例：

```
================================================================================
🧠 测试多模态情感分析服务
================================================================================

================================================================================
📝 测试用例1: 语音负面 + 文本正面（强冲突场景）
================================================================================

✅ 主导情绪: negative
✅ 融合置信度: 72.50%
✅ 冲突检测: True
   - 冲突类型: strong_voice
   - 仲裁原因: 语音显示强烈负面情绪，优先信任语音（语调更真实）
✅ 权重分配: 语音=0.55, 文本=0.45
✅ 语音情感向量: {'positive': 0.05, 'negative': 0.85, 'neutral': 0.1}
✅ 文本情感向量: {'positive': 0.72, 'negative': 0.18, 'neutral': 0.1}
✅ 融合情感向量: {'positive': 0.35, 'negative': 0.55, 'neutral': 0.1}

✅ LLM终判:
   - 情绪: negative
   - 置信度: 75.00%
   - 推理: 语音检测到强烈负面情绪（叹气+呼吸急促），虽然文本表达正面，但根据冲突仲裁规则，语音语调更真实反映候选人紧张状态...
```

---

## ⚠️ 注意事项

1. **腾讯云NLP API配额**
   - 需要在腾讯云控制台开通NLP服务
   - 注意监控API调用次数和费用

2. **性能优化**
   - LLM调用会增加延迟（约1-2秒）
   - 建议在异步线程中执行
   - 可以缓存相同文本的分析结果

3. **降级策略**
   - 如果腾讯云NLP API不可用，自动降级到简单关键词匹配
   - 如果LLM调用失败，使用加权融合结果

4. **COEM检索**
   - 需要确保数据库中有足够的题目和答案数据
   - 首次检索可能较慢（需要计算embedding）

---

## 📈 效果对比

| 特性 | 原有方案（仅ASR标签） | 新方案（多模态融合） |
|------|---------------------|-------------------|
| **情感维度** | 单一（基于标签） | 三维（正/负/中） |
| **准确性** | 中等 | 高（双通道验证） |
| **鲁棒性** | 低（依赖标签） | 高（动态权重） |
| **可解释性** | 弱 | 强（LLM推理） |
| **冲突处理** | 无 | 有（规则仲裁） |
| **知识库增强** | 无 | 有（COEM） |

---

## 🔗 相关文档

- [腾讯云NLP情感分析API](https://cloud.tencent.com/document/api/271/35552)
- [COEM检索增强架构](../app/services/coem.py)
- [ASR情感标签解析器](../app/services/emotion_tag_parser.py)

---

## 💡 最佳实践

1. **生产环境配置**
   ```python
   # .env
   USE_MULTIMODAL_EMOTION=1  # 启用多模态情感分析
   EMOTION_LLM_TEMPERATURE=0.3  # LLM温度
   EMOTION_USE_COEM=1  # 启用COEM检索
   ```

2. **性能监控**
   ```python
   result = service.analyze(...)
   print(f"处理时间: {result.processing_time_ms}ms")
   if result.processing_time_ms > 3000:
       print("⚠️ 情感分析耗时过长，考虑优化")
   ```

3. **日志记录**
   ```python
   import logging
   logger = logging.getLogger('emotion')
   logger.info(f"情感分析结果: {result.to_dict()}")
   ```

---

## 🎉 总结

多模态情感分析服务为你的AI面试平台带来了：
- ✅ **更准确的情感识别**（双通道验证）
- ✅ **更强的鲁棒性**（动态权重 + 降级策略）
- ✅ **更好的可解释性**（LLM推理）
- ✅ **更智能的冲突处理**（规则仲裁）
- ✅ **知识库增强**（COEM检索）

立即集成，提升你的AI面试官的情商！🚀
