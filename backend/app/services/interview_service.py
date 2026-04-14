# backend/app/services/interview_service_v2.py
"""
面试服务 - 重构版主入口(门面模式)
整合各子模块,提供统一的对外接口

【架构说明】
本文件作为轻量级门面,委托给以下专业模块处理具体逻辑:
- InterviewSessionManager: 会话管理(启动、配置、开场白)
- InterviewQAHandler: 问答处理(流式对话、TTS合成)
- InterviewReportGenerator: 报告生成(评估、打分、掌握度更新)
- InterviewGraphHelper: 知识图谱辅助(简历解析、题目推荐、覆盖率计算)
- InterviewTTSHelper: TTS辅助(音频合成、流式分割、队列管理)
- EmotionService: 情感分析(多模态情绪识别,预留云端API集成)

【使用方式】
保持与原InterviewService完全兼容的API,无需修改调用方代码。
只需将导入语句从 `from app.services.interview_service import InterviewService` 
改为 `from app.services.interview_service_v2 import InterviewService` 即可。
"""

# ==================== 导入所有子模块 ====================
from app.services.interview_session_manager import InterviewSessionManager
from app.services.interview_qa_handler import InterviewQAHandler
from app.services.interview_report_generator import InterviewReportGenerator
from app.services.interview_graph_helper import InterviewGraphHelper
from app.services.interview_tts_helper import InterviewTTSHelper
from app.services.emotion_service import EmotionService

# 向量模型相关(保留原有实现)
import os
import threading
from sentence_transformers import SentenceTransformer

_EMBEDDING_MODEL_NAME = 'BAAI/bge-small-zh-v1.5'
_local_embedding_model = None
_embedding_model_lock = threading.Lock()


class InterviewService:
    """
    面试服务主类(门面模式)
    
    职责:
    1. 提供与原版完全兼容的静态方法接口
    2. 委托给专业子模块处理具体业务逻辑
    3. 保留全局共享资源(线程池、向量模型等)
    """
    
    # === 全局线程池(用于异步TTS合成) ===
    tts_executor = InterviewTTSHelper.tts_executor
    
    # === 语速缓存锁 ===
    _speed_cache_lock = threading.Lock()
    
    # ==================== 向量模型相关(保留原有实现) ====================
    @staticmethod
    def _get_local_embedding_model():
        """获取本地嵌入模型(单例模式)"""
        global _local_embedding_model
        if _local_embedding_model is not None:
            return _local_embedding_model
        
        with _embedding_model_lock:
            if _local_embedding_model is not None:
                return _local_embedding_model
            try:
                model = SentenceTransformer(_EMBEDDING_MODEL_NAME, local_files_only=False)
            except ValueError as e:
                raise RuntimeError(
                    "本地向量模型加载失败：当前 sentence-transformers/transformers 与 "
                    f"{_EMBEDDING_MODEL_NAME} 不兼容。请升级/降级依赖后重试。原始错误: {e}"
                ) from e
            model.max_seq_length = 512
            _local_embedding_model = model
            return _local_embedding_model
    
    @staticmethod
    def get_embedding(text):
        """
        调用本地开源模型获取文本向量
        
        Args:
            text: 输入文本
            
        Returns:
            list: 512维向量列表
        """
        embeddings = InterviewService._get_local_embedding_model().encode(text)
        return embeddings.tolist()
    
    # ==================== 委托给子模块的方法 ====================
    
    @staticmethod
    def start_interview(user_id, job_id, voice_mode=False, interview_style=None, 
                       interview_round=None, voice_role=None, voice=None, profile_id=None, session_config=None):
        """
        启动一场新的面试会话
        
        委托给: InterviewSessionManager.start_interview()
        
        Args:
            user_id: 用户ID
            job_id: 岗位ID
            voice_mode: 是否语音模式
            interview_style: 面试风格(pressure/confident/teaching)
            interview_round: 面试轮次(first_round/second_round/third_round)
            voice_role: 语音角色
            voice: 音色名称
            profile_id: InterviewProfile ID
            session_config: 会话配置
            
        Returns:
            dict: 包含interview_id、开场白、音频等的初始化数据
        """
        return InterviewSessionManager.start_interview(
            user_id=user_id,
            job_id=job_id,
            voice_mode=voice_mode,
            interview_style=interview_style,
            interview_round=interview_round,
            voice_role=voice_role,
            voice=voice,
            profile_id=profile_id,
            session_config=session_config,
        )
    
    @staticmethod
    def process_chat_round_stream(interview_id, user_answer, voice_mode=False, voice=None):
        """
        处理对话轮次并返回流式生成器
        
        委托给: InterviewQAHandler.process_chat_round_stream()
        
        Args:
            interview_id: 面试ID
            user_answer: 用户回答文本
            voice_mode: 是否语音模式
            voice: 音色名称
            
        Yields:
            str: SSE格式的数据流
        """
        yield from InterviewQAHandler.process_chat_round_stream(
            interview_id=interview_id,
            user_answer=user_answer,
            voice_mode=voice_mode,
            voice=voice,
        )
    
    @staticmethod
    def finish_interview(interview_id):
        """
        结束面试并生成详尽评价写入数据库
        
        委托给: InterviewReportGenerator.finish_interview()
        
        Args:
            interview_id: 面试ID
            
        Returns:
            dict: 包含报告ID、总分、各维度得分等的完整报告
        """
        return InterviewReportGenerator.finish_interview(interview_id)
    
    # ==================== 兼容性代理方法(供内部调用) ====================
    # 这些方法主要为了保持与原有代码的兼容性,实际逻辑已迁移到子模块
    
    @staticmethod
    def _normalize_interview_style(voice_mode=False, interview_style=None, voice_role=None):
        """标准化面试风格(代理方法)"""
        return InterviewSessionManager.normalize_interview_style(
            voice_mode, interview_style, voice_role
        )
    
    @staticmethod
    def _build_session_config_payload(voice_mode=False, interview_style=None, voice_role=None):
        """构建会话配置载荷(代理方法)"""
        return InterviewSessionManager.build_session_config_payload(
            voice_mode, interview_style, voice_role
        )
    
    @staticmethod
    def _build_fallback_greeting(base_greeting, interview_id):
        """构建回退开场白(代理方法)"""
        return InterviewSessionManager.build_fallback_greeting(base_greeting, interview_id)
    
    @staticmethod
    def _resolve_generation_temperature(prompt_config=None, default_temp=0.85, seed=None):
        """解析生成温度(代理方法)"""
        return InterviewSessionManager.resolve_generation_temperature(
            prompt_config, default_temp, seed
        )
    
    @staticmethod
    def _pick_diverse_questions(assigned_questions, interview_id, round_index, pick_count=2):
        """选择多样化问题(代理方法)"""
        return InterviewSessionManager.pick_diverse_questions(
            assigned_questions, interview_id, round_index, pick_count
        )
    
    @staticmethod
    def _extract_resume_context(user_id, max_chars=800):
        """提取简历上下文(代理方法)"""
        return InterviewGraphHelper.extract_resume_context(user_id, max_chars)
    
    @staticmethod
    def _initialize_user_graph_from_resume(user_id, resume_skills_list, base_score=60):
        """初始化用户图谱(代理方法)"""
        return InterviewGraphHelper.initialize_user_graph_from_resume(
            user_id, resume_skills_list, base_score
        )
    
    @staticmethod
    def _get_job_graph_snapshot(job_id):
        """获取岗位图谱快照(代理方法)"""
        return InterviewGraphHelper.get_job_graph_snapshot(job_id)
    
    @staticmethod
    def _estimate_target_depth(mastery_level):
        """估算目标深度(代理方法)"""
        return InterviewGraphHelper.estimate_target_depth(mastery_level)
    
    @staticmethod
    def _assign_questions(job_id, user_id, limit=5, recent_tag_ids=None):
        """分配问题(代理方法)"""
        return InterviewGraphHelper.assign_questions(job_id, user_id, limit, recent_tag_ids)
    
    @staticmethod
    def _get_recent_asked_tag_ids(interview_id, limit=3):
        """获取最近提问标签ID(代理方法)"""
        return InterviewGraphHelper.get_recent_asked_tag_ids(interview_id, limit)
    
    @staticmethod
    def _build_adjacent_tag_context(tag_ids, interview_style='confident'):
        """构建相邻标签上下文(代理方法)"""
        return InterviewGraphHelper.build_adjacent_tag_context(tag_ids, interview_style)
    
    @staticmethod
    def _compute_graph_coverage(interview):
        """计算图谱覆盖率(代理方法)"""
        return InterviewGraphHelper.compute_graph_coverage(interview)
    
    @staticmethod
    def _get_tts_voice(prompt_config=None, selected_voice=None):
        """获取TTS音色(代理方法)"""
        return InterviewTTSHelper.get_tts_voice(prompt_config, selected_voice)
    
    @staticmethod
    def _synthesize_audio_async(text, voice, fmt='mp3'):
        """异步合成音频(代理方法)"""
        return InterviewTTSHelper.synthesize_audio_async(text, voice, fmt)
    
    @staticmethod
    def _strip_stream_control_tokens(text):
        """清理流式控制标记(代理方法)"""
        return InterviewTTSHelper.strip_stream_control_tokens(text)
    
    @staticmethod
    def _count_tts_speakable_chars(text):
        """统计可发音字符数(代理方法)"""
        return InterviewTTSHelper.count_tts_speakable_chars(text)
    
    @staticmethod
    def _is_valid_tts_segment(text, force=False):
        """验证TTS片段有效性(代理方法)"""
        return InterviewTTSHelper.is_valid_tts_segment(text, force)
    
    @staticmethod
    def _extract_ready_tts_segments(buffer_text):
        """提取就绪TTS片段(代理方法)"""
        return InterviewTTSHelper.extract_ready_tts_segments(buffer_text)
    
    @staticmethod
    def _extract_tail_tts_segment(buffer_text):
        """提取尾部TTS片段(代理方法)"""
        return InterviewTTSHelper.extract_tail_tts_segment(buffer_text)
    
    @staticmethod
    def _split_stream_display_chunks(content):
        """拆分流式显示块(代理方法)"""
        return InterviewTTSHelper.split_stream_display_chunks(content)
    
    @staticmethod
    def _normalize_answer_text(text):
        """标准化回答文本(代理方法)"""
        return InterviewQAHandler.normalize_answer_text(text)
    
    @staticmethod
    def _is_meaningless_answer(text):
        """检测无意义回答(代理方法)"""
        return InterviewQAHandler.is_meaningless_answer(text)


# ==================== 导出便捷别名 ====================
# 保持与原模块完全兼容
__all__ = ['InterviewService']
