# Interview Service 模块重构说明

## 📦 模块结构

原 `interview_service.py` (1559行) 已按功能拆分为以下专业模块:

```
backend/app/services/
├── interview_service.py              # 原始文件(保留备份)
├── interview_service_v2.py           # 新版门面类(推荐使用)
├── interview_session_manager.py      # 会话管理模块(346行)
├── interview_qa_handler.py           # 问答处理模块(428行)
├── interview_report_generator.py     # 报告生成模块(293行)
├── interview_graph_helper.py         # 知识图谱辅助模块(575行)
├── interview_tts_helper.py           # TTS辅助模块(265行)
└── emotion_service.py                # 情感分析服务(345行,预留云端API集成)
```

## 🎯 各模块职责

### 1. **InterviewSessionManager** (`interview_session_manager.py`)
**职责**: 面试会话生命周期管理

**核心功能**:
- ✅ 启动面试会话 (`start_interview`)
- ✅ 标准化面试风格 (pressure/confident/teaching)
- ✅ 构建会话配置载荷
- ✅ 生成多样化开场白
- ✅ 结合简历生成个性化欢迎语
- ✅ 异步TTS合成开场白音频
- ✅ 解析生成温度(带随机抖动)
- ✅ 选择多样化候选题目

**关键方法**:
```python
InterviewSessionManager.start_interview(user_id, job_id, ...)
InterviewSessionManager.normalize_interview_style(...)
InterviewSessionManager.build_session_config_payload(...)
InterviewSessionManager.build_fallback_greeting(...)
InterviewSessionManager.resolve_generation_temperature(...)
InterviewSessionManager.pick_diverse_questions(...)
```

---

### 2. **InterviewQAHandler** (`interview_qa_handler.py`)
**职责**: 实时问答处理与流式输出

**核心功能**:
- ✅ 处理用户回答并记录到数据库
- ✅ 检测无意义回答(如"嗯"、"好")
- ✅ 组装GraphRAG增强提示词
- ✅ 调用大模型流式输出
- ✅ 实时TTS音频合成与队列管理
- ✅ 流式推送文字+音频到前端(SSE)
- ✅ 处理尾句和超时逻辑
- ✅ 保存AI回复并关联题目ID

**关键方法**:
```python
InterviewQAHandler.process_chat_round_stream(interview_id, user_answer, ...)
InterviewQAHandler.is_meaningless_answer(text)
InterviewQAHandler.normalize_answer_text(text)
```

**技术亮点**:
- 异步TTS线程池 + 音频队列保证顺序
- 智能文本分割(强边界/软边界/强制切分)
- 覆盖率监控与日志记录
- 180秒超时保护机制

---

### 3. **InterviewReportGenerator** (`interview_report_generator.py`)
**职责**: 面试结束后的评估与打分

**核心功能**:
- ✅ 提取完整对话历史
- ✅ 获取岗位标准知识点库
- ✅ RAG检索优秀回答范例
- ✅ 调用大模型生成JSON格式报告
- ✅ JSON解析与严格验证
- ✅ 写入总表评价字段(highlights/improvements/suggestions)
- ✅ 写入维度评分表(5个维度)
- ✅ 更新用户知识图谱掌握度(级联传播)
- ✅ 计算图谱覆盖率与深度率
- ✅ 兜底机制(防止大模型幻觉)

**关键方法**:
```python
InterviewReportGenerator.finish_interview(interview_id)
InterviewReportGenerator._update_knowledge_mastery(...)
InterviewReportGenerator._update_node_score(...)  # 递归级联更新
InterviewReportGenerator._normalize_score(...)
```

**算法特点**:
- 指数平滑更新: `新分数 = int((老分数 * 0.6) + (本次得分 * 0.4))`
- 父节点衰减传播: `weight * 0.3`
- 严格标签校验(防大模型捏造)
- 自动兜底机制(至少2个标签及格分)

---

### 4. **InterviewGraphHelper** (`interview_graph_helper.py`)
**职责**: 知识图谱相关的所有辅助逻辑

**核心功能**:
- ✅ 简历技能解析与去敏
- ✅ 实体对齐(精确/别名/模糊/向量匹配)
- ✅ 用户图谱冷启动初始化
- ✅ 岗位图谱快照获取
- ✅ 智能题目推荐(深度匹配+掌握度+去重)
- ✅ 相邻标签上下文构建
- ✅ 图谱覆盖率与深度率计算
- ✅ 最近提问标签追踪

**关键方法**:
```python
InterviewGraphHelper.extract_resume_context(user_id)
InterviewGraphHelper.align_resume_entities(resume_skills_list)
InterviewGraphHelper.initialize_user_graph_from_resume(...)
InterviewGraphHelper.assign_questions(job_id, user_id, limit, recent_tag_ids)
InterviewGraphHelper.get_recent_asked_tag_ids(interview_id)
InterviewGraphHelper.build_adjacent_tag_context(tag_ids, style)
InterviewGraphHelper.compute_graph_coverage(interview)
InterviewGraphHelper.get_job_graph_snapshot(job_id)
```

**匹配策略**:
1. 精确匹配 (score=1.0)
2. 别名映射 (vue3→vue, reactjs→react等)
3. 包含关系 (score=0.9)
4. SequenceMatcher模糊匹配
5. 向量相似度匹配(兜底)

---

### 5. **InterviewTTSHelper** (`interview_tts_helper.py`)
**职责**: TTS音频合成与流式处理

**核心功能**:
- ✅ 获取TTS音色(优先级: 用户选择 > 配置 > 默认)
- ✅ 异步音频合成(线程池)
- ✅ 清理流式控制标记([INTERVIEW_OVER]、markdown符号、emoji)
- ✅ 智能文本分割(三级边界策略)
- ✅ 可发音字符统计
- ✅ 流式显示块拆分(改善前端打字机体验)
- ✅ 尾句提取与过滤

**关键方法**:
```python
InterviewTTSHelper.synthesize_audio_async(text, voice, fmt)
InterviewTTSHelper.extract_ready_tts_segments(buffer_text)
InterviewTTSHelper.extract_tail_tts_segment(buffer_text)
InterviewTTSHelper.split_stream_display_chunks(content)
InterviewTTSHelper.strip_stream_control_tokens(text)
InterviewTTSHelper.is_valid_tts_segment(text, force)
```

**分割策略**:
- **强边界**: `。！？；!?;!？\n` → 立即切分(即使1个字)
- **软边界**: `，,:：` → 达到8个可发音字符时切分
- **强制切分**: 超过70个可发音字符时在最近软边界处切分

---

### 6. **EmotionService** (`emotion_service.py`) ⭐新增
**职责**: 多模态情感分析(预留云端API集成)

**核心功能**:
- ✅ 统一的情感分析接口
- ✅ 支持多服务商切换(aliyun/azure/tencent/local)
- ✅ 本地降级方案(基于语速推断)
- ✅ 格式化输出供大模型使用
- ✅ 预留阿里云/Azure/腾讯云API实现位置

**关键方法**:
```python
EmotionService.analyze_emotion(audio_file_path, text, provider)
EmotionService.format_for_llm(emotion_result)
analyze_audio_emotion(audio_path, text)  # 便捷函数
get_emotion_prompt(audio_path, text)     # 便捷函数
```

**数据结构**:
```python
@dataclass
class EmotionResult:
    dominant_emotion: str        # 主导情绪(nervous/confident/calm等)
    emotion_scores: Dict[str, float]  # 各情绪维度得分(0-1)
    acoustic_features: Dict[str, float]  # 声学特征(语速/时长等)
    confidence: float            # 置信度(0-1)
    raw_response: dict           # 原始响应数据
```

**扩展指南**:
每个云端API都有独立的私有方法,只需按注释步骤实现:
- `_analyze_with_aliyun()` - 阿里云实现位置
- `_analyze_with_azure()` - Azure实现位置
- `_analyze_with_tencent()` - 腾讯云实现位置

---

## 🔄 迁移指南

### 方式1: 直接替换导入(推荐)
```python
# 旧代码
from app.services.interview_service import InterviewService

# 新代码
from app.services.interview_service_v2 import InterviewService
```

### 方式2: 逐步迁移
保持原 `interview_service.py` 不变,在新功能中使用 v2 版本。

### API兼容性
✅ **完全兼容**! 所有公开方法签名保持不变:
- `InterviewService.start_interview(...)`
- `InterviewService.process_chat_round_stream(...)`
- `InterviewService.finish_interview(...)`

---

## 📊 代码统计

| 模块 | 行数 | 复杂度 | 测试状态 |
|------|------|--------|----------|
| interview_session_manager.py | 346 | 中 | ⏳待测试 |
| interview_qa_handler.py | 428 | 高 | ⏳待测试 |
| interview_report_generator.py | 293 | 中 | ⏳待测试 |
| interview_graph_helper.py | 575 | 高 | ⏳待测试 |
| interview_tts_helper.py | 265 | 中 | ⏳待测试 |
| emotion_service.py | 345 | 低 | ⏳待测试 |
| **总计** | **2252** | - | - |
| 原文件 | 1559 | 极高 | ✅已验证 |

**优势**:
- ✅ 单一职责原则(每个模块专注一个领域)
- ✅ 可维护性提升(修改某个功能不影响其他模块)
- ✅ 可测试性提升(可单独单元测试每个模块)
- ✅ 可扩展性提升(新增功能只需添加新模块)
- ✅ 可读性提升(文件名即功能说明)

---

## 🚀 下一步工作

### 1. 集成情感分析
在 `interview_qa_handler.py` 中调用 `EmotionService`:
```python
# 在 process_chat_round_stream 中
if voice_mode and actual_speed is not None:
    from app.services.emotion_service import EmotionService
    emotion_result = EmotionService.analyze_emotion(
        audio_file_path, 
        text=normalized_answer
    )
    emotion_prompt = EmotionService.format_for_llm(emotion_result)
    # 将 emotion_prompt 注入到系统提示词中
```

### 2. 实现云端情感API
在 `emotion_service.py` 的三个方法中填入实际API调用代码:
- `_analyze_with_aliyun()`
- `_analyze_with_azure()`
- `_analyze_with_tencent()`

### 3. 单元测试
为每个模块编写独立的单元测试:
```python
# tests/test_interview_session_manager.py
# tests/test_interview_qa_handler.py
# tests/test_interview_report_generator.py
# tests/test_interview_graph_helper.py
# tests/test_interview_tts_helper.py
# tests/test_emotion_service.py
```

### 4. 性能优化
- 向量模型懒加载(已实现)
- TTS线程池调优(当前max_workers=1)
- 数据库查询优化(N+1问题检查)
- 缓存策略(最近提问标签、图谱快照等)

---

## 📝 注意事项

1. **循环导入问题**: 部分模块间存在相互引用,通过延迟导入解决
2. **全局状态**: `tts_executor` 和 `_local_embedding_model` 为全局共享资源
3. **线程安全**: 使用锁保护共享状态(`_speed_cache_lock`, `_embedding_model_lock`)
4. **异常处理**: 关键路径都有try-except保护,避免单点故障影响整体流程
5. **日志记录**: 关键操作都有print日志,建议后续接入logging模块

---

## 🎓 架构设计原则

1. **门面模式(Facade)**: `InterviewService` 作为统一入口,隐藏内部复杂性
2. **单一职责(SRP)**: 每个模块只负责一个领域的功能
3. **依赖倒置(DIP)**: 高层模块不依赖低层模块细节,都依赖抽象接口
4. **开闭原则(OCP)**: 对扩展开放(新增服务商),对修改关闭(不改已有代码)
5. **组合优于继承**: 通过组合多个专业模块实现复杂功能

---

**最后更新**: 2026-04-11  
**作者**: AI Assistant  
**版本**: v2.0 (模块化重构版)
