# backend/app/services/emotion_service.py
"""
语音情感分析服务
支持多模态情感识别（音频声学特征 + 文本语义）
预留云端API集成接口，支持灵活切换不同服务商
"""

import os
import json
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class EmotionResult:
    """情感分析结果数据结构"""
    # 主导情绪
    dominant_emotion: str = "neutral"  # nervous/confident/neutral/anxious/calm等
    
    # 各情绪维度得分 (0-1)
    emotion_scores: Dict[str, float] = None
    
    # 声学特征
    acoustic_features: Dict[str, float] = None
    
    # 置信度 (0-1)
    confidence: float = 0.0
    
    # 原始响应数据（用于调试）
    raw_response: dict = None
    
    def __post_init__(self):
        if self.emotion_scores is None:
            self.emotion_scores = {}
        if self.acoustic_features is None:
            self.acoustic_features = {}


class EmotionService:
    """
    情感分析服务类
    
    使用示例:
        result = EmotionService.analyze_emotion(audio_file_path, text="用户回答文本")
        print(result.dominant_emotion)
        print(result.emotion_scores)
    """
    
    # ==================== 配置区域 ====================
    # 当前使用的服务商: 'aliyun', 'azure', 'tencent', 'local'
    PROVIDER = os.getenv('EMOTION_PROVIDER', 'local')
    
    # API密钥配置（从环境变量读取）
    ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
    ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
    ALIYUN_APP_KEY = os.getenv('ALIYUN_APP_KEY', '')
    
    AZURE_SUBSCRIPTION_KEY = os.getenv('AZURE_SPEECH_KEY', '')
    AZURE_REGION = os.getenv('AZURE_REGION', 'eastus')
    
    TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', '')
    TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', '')
    TENCENT_APP_ID = os.getenv('TENCENT_APP_ID', '')
    # ==================================================
    
    @staticmethod
    def analyze_emotion(
        audio_file_path: str,
        text: str = "",
        provider: str = None
    ) -> EmotionResult:
        """
        分析音频文件的情感
        
        Args:
            audio_file_path: 音频文件路径 (WAV/MP3格式)
            text: 对应的文本内容（可选，用于多模态融合）
            provider: 指定服务商，默认使用配置的PROVIDER
            
        Returns:
            EmotionResult: 情感分析结果
        """
        provider = provider or EmotionService.PROVIDER
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
        
        # 根据服务商路由到不同的实现
        if provider == 'aliyun':
            return EmotionService._analyze_with_aliyun(audio_file_path, text)
        elif provider == 'azure':
            return EmotionService._analyze_with_azure(audio_file_path, text)
        elif provider == 'tencent':
            return EmotionService._analyze_with_tencent(audio_file_path, text)
        else:
            # 默认使用本地简化版（基于语速推断）
            return EmotionService._analyze_local(audio_file_path, text)
    
    @staticmethod
    def _analyze_with_aliyun(audio_file_path: str, text: str = "") -> EmotionResult:
        """
        使用阿里云语音情感识别API
        
        TODO: 实现阿里云API调用
        参考文档: https://help.aliyun.com/document_detail/xxx.html
        
        需要安装: pip install aliyun-python-sdk-core nls-sdk
        """
        print("[EmotionService] 使用阿里云情感分析（待实现）")
        
        # ===== 在这里实现阿里云API调用 =====
        # 
        # 步骤:
        # 1. 初始化阿里云客户端
        # 2. 上传音频文件或提供URL
        # 3. 调用情感识别接口
        # 4. 解析返回结果
        #
        # 示例伪代码:
        # from aliyunsdkcore.client import AcsClient
        # from aliyunsdknls.request import SpeechEmotionRecognitionRequest
        #
        # client = AcsClient(
        #     EmotionService.ALIYUN_ACCESS_KEY_ID,
        #     EmotionService.ALIYUN_ACCESS_KEY_SECRET,
        #     "cn-shanghai"
        # )
        # request = SpeechEmotionRecognitionRequest()
        # request.set_app_key(EmotionService.ALIYUN_APP_KEY)
        # request.set_file_link(audio_url)
        # response = client.do_action_with_exception(request)
        # result = json.loads(response)
        
        raise NotImplementedError("阿里云情感分析功能尚未实现")
    
    @staticmethod
    def _analyze_with_azure(audio_file_path: str, text: str = "") -> EmotionResult:
        """
        使用Azure Speech Service情感识别API
        
        TODO: 实现Azure API调用
        参考文档: https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/
        
        需要安装: pip install azure-cognitiveservices-speech
        """
        print("[EmotionService] 使用Azure情感分析（待实现）")
        
        # ===== 在这里实现Azure API调用 =====
        #
        # 步骤:
        # 1. 创建SpeechConfig
        # 2. 创建AudioConfig
        # 3. 启动情感识别
        # 4. 订阅事件获取结果
        #
        # 示例伪代码:
        # import azure.cognitiveservices.speech as speechsdk
        #
        # speech_config = speechsdk.SpeechConfig(
        #     subscription=EmotionService.AZURE_SUBSCRIPTION_KEY,
        #     region=EmotionService.AZURE_REGION
        # )
        # audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        # recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
        # result = recognizer.recognize_once()
        
        raise NotImplementedError("Azure情感分析功能尚未实现")
    
    @staticmethod
    def _analyze_with_tencent(audio_file_path: str, text: str = "") -> EmotionResult:
        """
        使用腾讯云语音情感分析API
        
        TODO: 实现腾讯云API调用
        参考文档: https://cloud.tencent.com/document/product/1093
        
        需要安装: pip install tencentcloud-sdk-python
        """
        print("[EmotionService] 使用腾讯云情感分析（待实现）")
        
        # ===== 在这里实现腾讯云API调用 =====
        #
        # 步骤:
        # 1. 创建认证对象
        # 2. 创建客户端
        # 3. 构造请求参数
        # 4. 发送请求并解析结果
        #
        # 示例伪代码:
        # from tencentcloud.common import credential
        # from tencentcloud.aai.v20180522 import aai_client, models
        #
        # cred = credential.Credential(
        #     EmotionService.TENCENT_SECRET_ID,
        #     EmotionService.TENCENT_SECRET_KEY
        # )
        # client = aai_client.AaiClient(cred, "ap-guangzhou")
        # req = models.SentenceRecognitionRequest()
        # req.ProjectId = int(EmotionService.TENCENT_APP_ID)
        # req.Data = base64_encoded_audio
        # resp = client.SentenceRecognition(req)
        
        raise NotImplementedError("腾讯云情感分析功能尚未实现")
    
    @staticmethod
    def _analyze_local(audio_file_path: str, text: str = "") -> EmotionResult:
        """
        本地简化版情感分析（降级方案）
        
        当前实现：基于语速的简单推断
        未来可扩展：使用本地模型提取声学特征（如openSMILE、librosa）
        """
        print("[EmotionService] 使用本地简化版情感分析")
        
        # 尝试从ASR缓存中获取语速信息
        from app.services.asr_service import global_speed_cache
        
        # 读取音频文件获取基本统计信息
        try:
            import wave
            with wave.open(audio_file_path, 'rb') as wf:
                duration = wf.getnframes() / wf.getframerate()
        except Exception:
            duration = 0
        
        # 计算语速
        char_count = len(text) if text else 0
        speech_speed = char_count / duration if duration > 0 else 0
        
        # 从缓存中获取更准确的语速（如果存在）
        if text in global_speed_cache:
            speech_speed = global_speed_cache[text]
        
        # 基于语速的简单情绪推断规则
        emotion_scores = {
            'nervous': 0.0,
            'confident': 0.0,
            'calm': 0.0,
            'hesitant': 0.0
        }
        
        if speech_speed > 5.0:
            # 语速快 -> 可能紧张或激动
            emotion_scores['nervous'] = min(0.8, (speech_speed - 5.0) / 5.0 + 0.3)
            emotion_scores['confident'] = 0.1
        elif speech_speed < 3.0:
            # 语速慢 -> 可能犹豫或思考
            emotion_scores['hesitant'] = min(0.8, (3.0 - speech_speed) / 3.0 + 0.3)
            emotion_scores['calm'] = 0.2
        else:
            # 正常语速 -> 相对自信和平静
            emotion_scores['confident'] = 0.5
            emotion_scores['calm'] = 0.4
            emotion_scores['nervous'] = 0.1
        
        # 确定主导情绪
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[dominant_emotion]
        
        return EmotionResult(
            dominant_emotion=dominant_emotion,
            emotion_scores=emotion_scores,
            acoustic_features={
                'speech_speed': round(speech_speed, 2),
                'duration': round(duration, 2),
                'char_count': char_count
            },
            confidence=round(confidence, 2),
            raw_response={'method': 'local_speed_based'}
        )
    
    @staticmethod
    def format_for_llm(emotion_result: EmotionResult) -> str:
        """
        将情感分析结果格式化为大模型可读的提示词
        
        Args:
            emotion_result: 情感分析结果
            
        Returns:
            str: 格式化后的提示词字符串
        """
        if not emotion_result:
            return ""
        
        parts = []
        
        # 主导情绪
        parts.append(f"【情绪状态】{emotion_result.dominant_emotion}")
        
        # 详细得分
        scores_str = ", ".join([
            f"{k}:{v:.2f}" for k, v in emotion_result.emotion_scores.items()
        ])
        parts.append(f"【情绪分布】{scores_str}")
        
        # 声学特征
        features = emotion_result.acoustic_features
        if features:
            feature_strs = []
            if 'speech_speed' in features:
                feature_strs.append(f"语速{features['speech_speed']}字/秒")
            if 'duration' in features:
                feature_strs.append(f"时长{features['duration']}秒")
            if feature_strs:
                parts.append(f"【声学特征】{', '.join(feature_strs)}")
        
        # 置信度
        parts.append(f"【置信度】{emotion_result.confidence:.0%}")
        
        return " | ".join(parts)


# ==================== 便捷函数 ====================

def analyze_audio_emotion(audio_path: str, text: str = "") -> Dict:
    """
    便捷函数：分析音频情感并返回字典格式
    
    Args:
        audio_path: 音频文件路径
        text: 对应文本
        
    Returns:
        dict: 情感分析结果（字典格式）
    """
    result = EmotionService.analyze_emotion(audio_path, text)
    return asdict(result)


def get_emotion_prompt(audio_path: str, text: str = "") -> str:
    """
    便捷函数：获取用于大模型的格式化情感提示词
    
    Args:
        audio_path: 音频文件路径
        text: 对应文本
        
    Returns:
        str: 格式化后的提示词
    """
    result = EmotionService.analyze_emotion(audio_path, text)
    return EmotionService.format_for_llm(result)
