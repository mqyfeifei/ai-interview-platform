# backend/app/services/interview_tts_helper.py
"""
面试服务 - TTS(文本转语音)辅助模块
负责音频合成、流式分割、音频队列管理等
"""

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from app.services.tts_service import TTSService


class InterviewTTSHelper:
    """TTS 辅助工具类"""
    
    # === 线程池配置 ===
    _TTS_MAX_WORKERS = max(1, min(4, int(os.environ.get('TTS_MAX_WORKERS', '2'))))
    tts_executor = ThreadPoolExecutor(max_workers=_TTS_MAX_WORKERS)
    
    # === TTS 文本处理正则表达式 ===
    # 句末停顿符号(强边界)
    _TTS_SENTENCE_BOUNDARY_PATTERN = re.compile(r'[。！？；!?;!？\n]')
    # 句中停顿符号(软边界)
    _TTS_SOFT_BOUNDARY_PATTERN = re.compile(r'[，,:：]')
    # 可发音字符模式(中英文数字)
    _TTS_SPEAKABLE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')
    
    # === TTS 分段阈值配置 ===
    _MIN_TTS_SPEAKABLE_CHARS = 2  # 最小可发音字符数
    _TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS = int(
        os.environ.get('TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS', '16')
    )  # 提高阈值，减少过碎分段
    _TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS = int(
        os.environ.get('TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS', '120')
    )  # 放宽强制切分，减少请求次数
    _STREAM_DISPLAY_CHUNK_CHARS = 10  # 前端流式显示块大小
    _TTS_HEAD_BLOCK_TIMEOUT_SECONDS = float(
        os.environ.get('TTS_HEAD_BLOCK_TIMEOUT_SECONDS', '20.0')
    )  # 结束阶段按顺序等待每个片段完成，避免只播出首段
    
    @staticmethod
    def get_tts_voice(prompt_config=None, selected_voice=None):
        """
        获取TTS音色
        
        Args:
            prompt_config: AI提示词配置对象
            selected_voice: 用户选择的音色
            
        Returns:
            str: 音色名称
        """
        explicit_voice = (selected_voice or '').strip()
        if explicit_voice:
            return explicit_voice
        voice = getattr(prompt_config, 'preferred_voice', None) if prompt_config else None
        return voice or TTSService.get_default_speaker()
    
    @staticmethod
    def synthesize_audio_async(text, voice, fmt='mp3'):
        """
        异步 TTS 合成包装器
        在线程池中执行同步的 synthesize_bytes,避免阻塞主线程
        
        Args:
            text: 待合成文本
            voice: 音色名称
            fmt: 音频格式(mp3/wav)
            
        Returns:
            bytes: 音频数据,失败返回None
        """
        try:
            audio_bytes = TTSService.synthesize_bytes(text, voice=voice, fmt=fmt)
            return audio_bytes
        except Exception as e:
            print(f'异步 TTS 合成失败：{e}')
            return None
    
    @staticmethod
    def strip_stream_control_tokens(text):
        """
        清理流式控制标记和不可发音字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        t = (text or '').replace('[INTERVIEW_OVER]', '').strip()
        # 移除 markdown 符号
        t = re.sub(r'[*_~>#`]+', '', t)
        
        # 移除不可发音且非标点的特殊字符(如emoji)
        allowed_pattern = re.compile(
            r'[^\u4e00-\u9fffa-zA-Z0-9，。！？；、:""《》（）\.,!?;\'"()\[\]\-\+\s\n·—－￥]'
        )
        t = allowed_pattern.sub('', t)
        
        # 合并多余空格
        t = re.sub(r'\s+', ' ', t)
        return t.strip()
    
    @classmethod
    def count_tts_speakable_chars(cls, text):
        """统计可发音字符数量"""
        return len(cls._TTS_SPEAKABLE_CHAR_PATTERN.findall(text or ''))
    
    @classmethod
    def is_valid_tts_segment(cls, text, force=False):
        """
        检查文本是否为有效的TTS片段
        
        Args:
            text: 待检查文本
            force: 是否强制验证(忽略长度限制)
            
        Returns:
            bool: 是否有效
        """
        clean_text = cls.strip_stream_control_tokens(text)
        if not clean_text:
            return False
        
        min_chars = 1 if force else cls._MIN_TTS_SPEAKABLE_CHARS
        return cls.count_tts_speakable_chars(clean_text) >= min_chars
    
    @classmethod
    def extract_ready_tts_segments(cls, buffer_text):
        """
        从累计缓冲中提取已闭合的可播报句子
        
        策略:
        1. 优先在句末停顿(。！？)切分
        2. 若句子过长则在逗号等软停顿处切分
        3. 超长句子强制切分
        
        Args:
            buffer_text: 累积的文本缓冲区
            
        Returns:
            tuple: (segments列表, remaining_text剩余文本)
        """
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
            if not cls.is_valid_tts_segment(candidate, force=force_valid):
                return False
            
            segments.append(cls.strip_stream_control_tokens(candidate))
            segment_start = split_pos
            speakable_count = 0
            last_soft_boundary = -1
            return True
        
        for index, ch in enumerate(text):
            char_pos = index + 1
            if cls._TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
                speakable_count += 1
            
            # 检测软边界(逗号等)
            if cls._TTS_SOFT_BOUNDARY_PATTERN.match(ch):
                last_soft_boundary = char_pos
                if speakable_count >= cls._TTS_SOFT_SPLIT_MIN_SPEAKABLE_CHARS:
                    append_segment_if_valid(char_pos, force_valid=False)
                    continue
            
            # 检测强边界(句号等)
            if cls._TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
                # 强行断句,即使是1个字也直接送去播报
                append_segment_if_valid(char_pos, force_valid=True)
                continue
            
            # 超长句子强制切分
            if speakable_count >= cls._TTS_FORCE_SPLIT_MAX_SPEAKABLE_CHARS:
                split_pos = last_soft_boundary if last_soft_boundary > segment_start else char_pos
                did_split = append_segment_if_valid(split_pos, force_valid=False)
                if did_split and split_pos < char_pos:
                    # 重新统计当前段剩余可发音字符
                    speakable_count = cls.count_tts_speakable_chars(text[segment_start:char_pos])
        
        return segments, text[segment_start:]
    
    @classmethod
    def extract_tail_tts_segment(cls, buffer_text):
        """
        流式结束时提取剩余尾句
        
        Args:
            buffer_text: 剩余缓冲文本
            
        Returns:
            str or None: 尾句文本,无效则返回None
        """
        if not buffer_text:
            return None
        
        candidate = cls.strip_stream_control_tokens(buffer_text)
        
        # 如果整个候选文本为空(纯标点/空格),返回None
        if not candidate or not candidate.strip():
            return None
        
        # 尾句只要包含至少1个可发音字符,就应该被合成
        speakable_count = cls.count_tts_speakable_chars(candidate)
        if speakable_count >= 1:
            return candidate
        
        # 纯标点符号不需要额外合成
        return None
    
    @classmethod
    def split_stream_display_chunks(cls, content):
        """
        将单次模型大块输出拆成更细粒度文本事件,改善前端逐字体验
        
        Args:
            content: 模型输出的完整文本
            
        Returns:
            list: 拆分后的文本块列表
        """
        text = content or ''
        if not text:
            return []
        
        pieces = []
        current = []
        speakable_count = 0
        
        for ch in text:
            current.append(ch)
            if cls._TTS_SPEAKABLE_CHAR_PATTERN.match(ch):
                speakable_count += 1
            
            # 遇到强边界立即切分
            if cls._TTS_SENTENCE_BOUNDARY_PATTERN.match(ch):
                pieces.append(''.join(current))
                current = []
                speakable_count = 0
                continue
            
            # 遇到软边界且达到最小长度时切分
            if cls._TTS_SOFT_BOUNDARY_PATTERN.match(ch) and speakable_count >= 4:
                pieces.append(''.join(current))
                current = []
                speakable_count = 0
                continue
            
            # 达到显示块大小时切分
            if speakable_count >= cls._STREAM_DISPLAY_CHUNK_CHARS:
                pieces.append(''.join(current))
                current = []
                speakable_count = 0
        
        # 处理剩余文本
        if current:
            pieces.append(''.join(current))
        
        return pieces
