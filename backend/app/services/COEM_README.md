CoEM 多阶段增强管线（集成说明）

简介
---
CoEM（Chunk → Enrich → Rank → Core）是一个面向长上下文情感智能任务的多阶段增强框架。它的目标是在面试/情感任务中提升 LLM 在情感识别、知识应用与共情生成三类任务的表现。

本实现为该仓库的轻量集成版本，设计原则为“最小侵入、可选启用、容错回退”。它将 CoEM 集成到 `InterviewQAHandler` 的“纯文本”对话路径（voice_mode=False）。

架构与阶段
---
- 阶段 1：分块（chunk_text）
  - 把候选文档（当前实现为：参考题目参考答案 + 简历摘要，合并成一个文本）按字符近似 token 切分成若干块。

- 阶段 2：初始排序（initial_rank）
  - 使用现有的 `InterviewService.get_embedding` 获得 query 与每个 chunk 的 embedding，按余弦相似度排序并取 Top-K。

- 阶段 3：多智能体丰富（coem_sage_enrich）
  - 对 Top-K 每个 chunk 调用 CoEM-Sage（使用现有 DeepSeekClient），期待返回结构化 JSON（summary、answers、emotion、tags、relevance）。
  - 若模型不返回合法 JSON，会把原始输出放到 `summary` 字段；单块失败不会中断流程。

- 阶段 4：重新排序（rerank_enhanced_chunks）
  - 如果 Sage 返回 `relevance` 字段，则按 `0.6 * orig_score + 0.4 * relevance` 做加权重排并取最终 top chunks。

- 阶段 5：情感集成生成（coem_core_generate）
  - 将 top enhanced chunks 注入 CoEM-Core prompt。Core 负责生成最终回复。
  - 本实现支持两种工作模式：
    - 非流式（stream=False）：一次性返回完整文本。
    - 流式（stream=True）：将 LLM 的流式输出包装成一个 generator，逐片段 yield 文本；主处理器使用同一套拆分与 TTS 流程逐句合成并发送音频。

如何配置（代码配置）
---
在 `backend/app/config.py` 中添加或设置以下环境变量来控制 CoEM：

- USE_COEM_FOR_TEXT (默认 0)
  - 说明：是否在纯文本对话路径启用 CoEM（设置为 1 表示启用）。

- COEM_MAX_CHUNKS (默认 4)
  - 说明：初始排序后选择的 Top-K 大小。

- COEM_CHUNK_MAX_CHARS (默认 800)
  - 说明：切分块时每块的最大字符数（字符数近似 token，按需调整）。

- COEM_CHUNK_OVERLAP (默认 100)
  - 说明：相邻块之间的重叠字符数，用以保留跨段信息。

- COEM_SAGE_TIMEOUT (默认 5.0)
  - 说明：Sage 阶段每个 chunk 的超时（秒）。

- COEM_CORE_TEMPERATURE (默认 0.0)
  - 说明：CoEM-Core 调用的采样温度。

快速启用示例（在 .env 或系统环境中）：

```
USE_COEM_FOR_TEXT=1
COEM_MAX_CHUNKS=4
COEM_CHUNK_MAX_CHARS=800
COEM_CHUNK_OVERLAP=100
COEM_SAGE_TIMEOUT=5.0
COEM_CORE_TEMPERATURE=0.0
```

运行时行为
---
- 若 `USE_COEM_FOR_TEXT` 为 True 且当前是文本模式（voice_mode=False）：
  - Handler 会先做 chunk + initial_rank + Sage enrich + rerank，然后使用 CoEM-Core 的 streaming 接口（stream=True）或非流式接口（stream=False）来获取最终回答。
  - 在 streaming=True 时，CoEM-Core 的流式输出会被 `interview_qa_handler` 的现有流式处理逻辑消费：
    - 输出文本被分片（split_stream_display_chunks），句子完成时会提交 TTS 异步合成，完成的音频与文本一起通过 SSE 发送给前端，从而与语音路径兼容。

容错与回退
---
- CoEM 是可选的（默认关闭）。
- 每个阶段都有 try/except 包裹；若任何阶段失败，系统会记录日志并回退到原始 LLM 流式生成 + 现有 TTS 流程，不会中断会话。

文件变更一览
---
- 新增：`backend/app/services/coem.py`（CoEM 实现）
- 修改：`backend/app/services/interview_qa_handler.py`（在文本路径集成 CoEM；支持 CoEM-Core 流式输出并与现有 TTS 流程兼容）
- 修改：`backend/app/config.py`（新增 CoEM 配置项）

注意事项与建议
---
- 性能：CoEM 会增加对 LLM 的调用（Sage 对每个 chunk 的调用 + Core），会提高延迟。建议先在 dev 环境尝试较低的 COEM_MAX_CHUNKS（如 2-4）并设置适当超时时间。
- 检索范围：当前实现仅使用参考答案与简历摘要作为候选文档。若要更高召回率，请将候选文档来源扩展为题库、历史对话、或接入向量检索（例如 Milvus / PGVector）。
- 并行化：可将 Sage 对 chunk 的调用并行化以降低总延迟（需做线程池/异步调用与整体超时控制）。

开发者说明
---
- LLM 客户端：使用现有的 `app.utils.llm_client.DeepSeekClient`；如果你使用其他 LLM 服务，确保其支持流式接口并返回结构类似的增量 chunk（或调整 `coem.coem_core_generate` 中对 chunk 的解析）。
- 日志：CoEM 的异常会写入 `current_app.logger`，你可以通过配置 Flask 的日志记录级别来观察这些信息。

后续迭代想法（非必须）
---
1. 将 chunk embedding 缓存到 Redis/DB 以减少重复计算。  
2. 把初始排序改为向量索引（更大 candidate pool）。  
3. 对 Sage 调用做并行化与总体超时预算管理。  
4. 在 Core 输出中返回 provenance（每段回答关联的 chunk id），用于可解释性与审核。

结束语
---
如果你想让我继续：
- 我可以把 CoEM-Core 的流式输出改为更小的显示片段（例如按句或按逗号切分）以优化 TTS 体验；
- 或者并行化 Sage 调用并在代码中加入整体超时预算；
- 也可以把配置追加到项目的 README 或示例 .env 文件中。

欢迎告诉我下一步要做哪项，我会继续实现并测试。
