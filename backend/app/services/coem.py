# backend/app/services/coem.py
"""
CoEM：一个多阶段增强情感/知识处理管线（简化实现，供集成使用）

功能：
- chunk_text：将长文本切分为块
- initial_rank：使用 InterviewService.get_embedding 对块与查询做相似度排序
- coem_sage_enrich：使用 DeepSeekClient 对每个候选块做增强（返回结构化notes）
- rerank_enhanced_chunks：基于原始相似度与 Sage 提示进行重新排序
- coem_core_generate：把增强块注入到最终生成模型，得到最后回答

设计原则：保持简单、可测；所有外部调用有容错，出错时返回可接受的降级结果。
"""

import json
import hashlib
import math
from typing import List, Dict, Any

from flask import current_app


def _sha1_short(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    把长文本按字符（近似 token）切分为多个 chunk，返回每个 chunk 的字典：{id, text, meta}
    - max_chars: 每块最大字符数（粗略近似 token）
    - overlap: 邻接块之间的重叠字符数
    """
    if not text:
        return []
    text = text.strip()
    chunks = []
    start = 0
    length = len(text)
    idx = 0
    while start < length:
        end = min(start + max_chars, length)
        chunk_text = text[start:end].strip()
        if not chunk_text:
            break
        cid = f"c{idx}_" + _sha1_short(chunk_text)
        chunks.append({
            'id': cid,
            'text': chunk_text,
            'meta': {'offset': start, 'length': len(chunk_text)}
        })
        if end == length:
            break
        start = end - overlap if (end - overlap) > start else end
        idx += 1
    return chunks


def retrieve_candidate_docs(query: str, interview_service, job_id: int = None, limit: int = 8) -> List[Dict[str, Any]]:
    """
    使用数据库中已有的向量字段进行检索（优先 Example/Question/Resource），返回候选文档列表。
    每项为 {'id': '<model>:<pk>', 'text': '...', 'source': 'example/question/resource'}
    如果检索失败或数据库中无数据，返回空列表。
    """
    candidates = []
    try:
        vec = interview_service.get_embedding(query)
    except Exception as e:
        current_app.logger.exception("CoEM.retrieve_candidate_docs: failed to get embedding: %s", e)
        return candidates

    try:
        # 延迟导入模型，避免循环依赖
        from app.models.example import Example
        from app.models.question import Question
        try:
            from app.models.learning import Resource
        except Exception:
            Resource = None

        # Examples 优先（示例回答）
        try:
            examples = Example.query
            if job_id:
                examples = examples.filter(Example.job_id == job_id)
            examples = examples.order_by(Example.embedding.l2_distance(vec)).limit(limit).all()
            for ex in examples:
                text = (ex.answer or '')
                if text:
                    candidates.append({'id': f"example:{ex.id}", 'text': text, 'source': 'example'})
        except Exception:
            current_app.logger.debug('CoEM.retrieve_candidate_docs: example retrieval failed or empty')

        # Questions 作为补充
        try:
            qs = Question.query
            if job_id:
                qs = qs.filter(Question.job_id == job_id)
            qs = qs.order_by(Question.embedding.l2_distance(vec)).limit(limit).all()
            for q in qs:
                text = (q.reference_answer or q.content or '')
                if text:
                    candidates.append({'id': f"question:{q.id}", 'text': text, 'source': 'question'})
        except Exception:
            current_app.logger.debug('CoEM.retrieve_candidate_docs: question retrieval failed or empty')

        # Resource 表（学习资源）作为兜底
        if Resource is not None:
            try:
                rs = Resource.query
                # Resource 可能没有 job_id 关联，直接检索全表
                rs = rs.order_by(Resource.embedding.l2_distance(vec)).limit(limit).all()
                for r in rs:
                    text = (r.content or r.title or '')
                    if text:
                        candidates.append({'id': f"resource:{r.id}", 'text': text, 'source': 'resource'})
            except Exception:
                current_app.logger.debug('CoEM.retrieve_candidate_docs: resource retrieval failed or empty')

    except Exception as e:
        current_app.logger.exception("CoEM.retrieve_candidate_docs: DB retrieval failed: %s", e)

    # 去重并截取前 limit
    seen = set()
    out = []
    for c in candidates:
        if c['text'] and c['text'] not in seen:
            seen.add(c['text'])
            out.append(c)
        if len(out) >= limit:
            break

    return out


# 修改 initial_rank 签名以支持可选 job_id，并在 chunks 缺失时调用 DB 检索
def initial_rank(chunks: List[Dict[str, Any]], query: str, interview_service, top_k: int = 8, job_id: int = None) -> List[Dict[str, Any]]:
    """
    使用 InterviewService.get_embedding 获取向量, 对 chunks 与 query 做余弦相似度排序。
    如果 chunks 为空或数量少于 top_k, 会尝试调用数据库检索以补充候选文档。
    返回带 embedding 与 score 的 scored_chunks 列表。
    每个元素形如: {'chunk': chunk, 'embedding': [...], 'score': 0.8}
    """
    # 如果候选块不足，使用检索补齐
    if not chunks or len(chunks) < 1:
        try:
            retrieved = retrieve_candidate_docs(query, interview_service, job_id=job_id, limit=top_k)
            merged_text = '\n\n'.join([d['text'] for d in retrieved]) if retrieved else ''
            if merged_text:
                chunks = chunk_text(merged_text, max_chars=current_app.config.get('COEM_CHUNK_MAX_CHARS', 800), overlap=current_app.config.get('COEM_CHUNK_OVERLAP', 100))
        except Exception as e:
            current_app.logger.exception("CoEM.initial_rank: retrieval fallback failed: %s", e)

    if not chunks:
        return []

    try:
        # query embedding
        q_vec = interview_service.get_embedding(query)
    except Exception as e:
        current_app.logger.exception("CoEM.initial_rank: failed to get query embedding: %s", e)
        # 返回原始顺序的前 top_k
        return [{'chunk': c, 'embedding': None, 'score': 0.0} for c in chunks[:top_k]]

    scored = []
    for c in chunks:
        try:
            emb = interview_service.get_embedding(c['text'])
            score = _cosine(q_vec, emb)
        except Exception:
            emb = None
            score = 0.0
        scored.append({'chunk': c, 'embedding': emb, 'score': float(score)})

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:max(1, min(len(scored), top_k))]


def coem_sage_enrich(scored_chunks: List[Dict[str, Any]], query: str, deepseek_client, timeout: float = 5.0) -> List[Dict[str, Any]]:
    """
    对每个候选块调用小型 LLM（CoEM-Sage）做增强，期望返回 JSON 格式的增强笔记。
    返回 enhanced_chunks 列表，每项包含: {'scored': scored_chunk, 'sage_notes': {...}, 'raw_sage': str}
    若单个块增强失败, 将 sage_notes 置为空结构并继续。
    """
    enhanced = []
    if not scored_chunks:
        return enhanced

    system_prompt = (
        "你是 CoEM-Sage: 一个面向情感与知识增强的小型助手。\n"
        "任务：对给定文本块产生简短结构化的增强信息，用于下游检索与生成。\n"
        "请输出合法的 JSON，字段包括：summary(1-2句)，answers(可选的候选短答案数组)，emotion(情感标签或空字符串)，tags(关键词数组)，relevance(0.0-1.0 数值，表示与查询的相关性)。"
    )

    for item in scored_chunks:
        chunk = item['chunk']
        user_prompt = (
            f"CHUNK:\n{chunk['text']}\n\nQUERY:\n{query}\n\n"
            "请基于上面内容生成 JSON。"
        )
        raw = ''
        notes = {}
        try:
            # Use non-streaming call for simplicity
            resp = deepseek_client.generate_reply(
                [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                stream=False,
                temperature=0.0,
            )
            raw = resp if isinstance(resp, str) else str(resp)
            # 尝试解析 JSON
            try:
                parsed = json.loads(raw)
                # normalize fields
                notes = {
                    'summary': parsed.get('summary') if isinstance(parsed.get('summary'), str) else (parsed.get('summary', '') if isinstance(parsed.get('summary', ''), str) else ''),
                    'answers': parsed.get('answers') if isinstance(parsed.get('answers'), list) else [],
                    'emotion': parsed.get('emotion') if isinstance(parsed.get('emotion'), str) else '',
                    'tags': parsed.get('tags') if isinstance(parsed.get('tags'), list) else [],
                    'relevance': float(parsed.get('relevance')) if parsed.get('relevance') is not None else None,
                }
            except Exception:
                # 非严格 JSON 输出，放入 raw_text
                notes = {'summary': raw.strip()[:400], 'answers': [], 'emotion': '', 'tags': [], 'relevance': None}
        except Exception as e:
            current_app.logger.exception("CoEM.sage_enrich failed for chunk %s: %s", chunk.get('id'), e)
            raw = ''
            notes = {'summary': '', 'answers': [], 'emotion': '', 'tags': [], 'relevance': None}

        enhanced.append({'scored': item, 'sage_notes': notes, 'raw_sage': raw})

    return enhanced


def rerank_enhanced_chunks(enhanced_chunks: List[Dict[str, Any]], query: str, interview_service, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    基于 original score 和 sage_notes.relevance 做二次排序。返回排序后的 enhanced_chunks（截取前 top_k）。
    如果 sage_notes.relevance 可用，使用加权平均：new_score = 0.6*orig + 0.4*relevance
    否则保留原始 score。
    """
    if not enhanced_chunks:
        return []

    def _score(item):
        orig = float(item['scored'].get('score') or 0.0)
        rel = item['sage_notes'].get('relevance')
        if rel is None:
            return orig
        try:
            relf = float(rel)
        except Exception:
            relf = 0.0
        return 0.6 * orig + 0.4 * relf

    enhanced_chunks.sort(key=_score, reverse=True)
    return enhanced_chunks[:max(1, min(len(enhanced_chunks), top_k))]


def coem_core_generate(top_enhanced_chunks: List[Dict[str, Any]], query: str, conversation_messages: List[Dict[str, Any]], deepseek_client, streaming: bool = False):
    """
    把增强后的 top chunks 注入到最终生成器 (CoEM-Core)。
    - streaming=False: 返回字符串
    - streaming=True: 返回一个生成器，yield 原始增量内容字符串（与 LLM 流式 delta 内容一致的片段），
      调用方负责将这些片段拆分为显示块并进行 TTS 合成。
    """
    system_prompt = (
        "你是 CoEM-Core：结合提供的增强块（包含 Sage 注释）与会话历史，生成符合查询的最终答案。\n"
        "要求：基于块内的事实与情感信息回答，避免凭空添加事实；如果信息不足直言不知。"
    )

    # 构建 TOP_CHUNKS_BLOCK
    chunks_block_lines = []
    for idx, item in enumerate(top_enhanced_chunks):
        chunk = item['scored']['chunk']
        notes = item.get('sage_notes', {}) or {}
        chunks_block_lines.append(
            f"[CHUNK #{idx+1} id={chunk.get('id')}]:\n{chunk.get('text')}\nSAGE_SUMMARY: {notes.get('summary','')}\nSAGE_ANSWERS: {notes.get('answers',[])}\nSAGE_EMOTION: {notes.get('emotion','')}\nSAGE_TAGS: {notes.get('tags',[])}\n"
        )

    top_chunks_block = "\n\n".join(chunks_block_lines)

    user_prompt = (
        f"QUERY:\n{query}\n\nCONVERSATION_HISTORY:\n"
        + '\n'.join([m.get('content','') for m in (conversation_messages or [])][-8:])
        + "\n\nTOP_CHUNKS:\n"
        + top_chunks_block
        + "\n\n请基于上述信息直接回答查询："
    )

    if not streaming:
        try:
            reply = deepseek_client.generate_reply(
                [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                stream=False,
                temperature=current_app.config.get('COEM_CORE_TEMPERATURE', 0.0),
            )
            return reply if isinstance(reply, str) else str(reply)
        except Exception as e:
            current_app.logger.exception("CoEM.core_generate failed: %s", e)
            return ''

    # streaming == True: 返回一个 generator，逐步 yield 增量内容
    try:
        response = deepseek_client.generate_reply(
            [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
            stream=True,
            temperature=current_app.config.get('COEM_CORE_TEMPERATURE', 0.0),
        )
    except Exception as e:
        current_app.logger.exception("CoEM.core_generate(stream) failed to start: %s", e)
        # 返回一个空的生成器
        return iter(())

    def _iter_response():
        try:
            for chunk in response:
                # 尝试与现有 LLM 流式返回一致的解析路径
                content = None
                try:
                    content = getattr(chunk, 'choices', None) and chunk.choices[0].delta.content
                except Exception:
                    # 兼容不同客户端返回形式
                    try:
                        content = chunk.get('choices')[0].get('delta', {}).get('content') if isinstance(chunk, dict) else None
                    except Exception:
                        content = None
                # 直接支持 if chunk is raw string
                if not content and isinstance(chunk, str):
                    content = chunk
                if content:
                    yield content
        except Exception as e:
            current_app.logger.exception("CoEM.core_generate(stream) iteration failed: %s", e)
            return

    return _iter_response()
