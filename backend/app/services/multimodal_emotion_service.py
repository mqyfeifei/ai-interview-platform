# backend/app/services/multimodal_emotion_service.py
"""
后融合型多模态情感分析服务

算法特点:
- 语音模态 + 文本模态双通道独立分析
- 动态权重分配（基于模态质量）
- 加权融合 + 冲突仲裁
- LLM最终判决（可解释性）

集成:
- 腾讯云语音情感识别（通过ASR标签）
- 腾讯云文本情感分析API
- COEM检索增强上下文
- DeepSeek LLM终判
"""

import os
import json
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict

from app.utils.llm_client import DeepSeekClient


@dataclass
class EmotionVector:
    """情感向量数据结构"""
    positive: float = 0.0   # 正面情感概率
    negative: float = 0.0   # 负面情感概率
    neutral: float = 0.0    # 中性情感概率
    
    def to_dict(self) -> Dict:
        return {
            'positive': self.positive,
            'negative': self.negative,
            'neutral': self.neutral
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionVector':
        return cls(
            positive=data.get('positive', 0.0),
            negative=data.get('negative', 0.0),
            neutral=data.get('neutral', 0.0)
        )


@dataclass
class ModalityQuality:
    """模态质量评估"""
    confidence: float = 0.0     # API置信度
    completeness: float = 0.0   # 完整性（0-1）
    
    @property
    def quality_score(self) -> float:
        """综合质量分数"""
        return self.confidence * self.completeness


@dataclass
class MultimodalEmotionResult:
    """多模态情感分析结果"""
    # 原始模态结果
    voice_emotion: Optional[EmotionVector] = None
    text_emotion: Optional[EmotionVector] = None
    
    # 模态质量
    voice_quality: Optional[ModalityQuality] = None
    text_quality: Optional[ModalityQuality] = None
    
    # 融合结果
    fused_emotion: Optional[EmotionVector] = None
    dominant_emotion: str = "neutral"
    fusion_confidence: float = 0.0
    
    # 权重信息
    voice_weight: float = 0.4
    text_weight: float = 0.6
    
    # 冲突仲裁
    conflict_detected: bool = False
    conflict_type: str = ""  # strong_voice/strong_text/weak/no_conflict
    arbitration_reason: str = ""
    
    # LLM终判
    llm_emotion: str = "neutral"
    llm_confidence: float = 0.0
    llm_reasoning: str = ""
    
    # 元数据
    retrieved_context: str = ""  # COEM检索上下文
    asr_text: str = ""           # ASR转写文本
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # 转换嵌套对象
        if self.voice_emotion:
            result['voice_emotion'] = self.voice_emotion.to_dict()
        if self.text_emotion:
            result['text_emotion'] = self.text_emotion.to_dict()
        if self.fused_emotion:
            result['fused_emotion'] = self.fused_emotion.to_dict()
        return result


class MultimodalEmotionService:
    """
    后融合型多模态情感分析服务
    
    使用示例:
        service = MultimodalEmotionService()
        result = service.analyze(
            audio_tags="[pause][breath]",
            asr_text="我觉得这个方案还不错",
            job_id=1,
            user_id=1
        )
    """
    
    # 默认权重配置
    DEFAULT_VOICE_WEIGHT = 0.4
    DEFAULT_TEXT_WEIGHT = 0.6
    
    # 强冲突阈值
    STRONG_CONFLICT_THRESHOLD = 0.7
    
    def __init__(self):
        self.llm_client = DeepSeekClient()
    
    def analyze(
        self,
        audio_tags: str = "",
        asr_text: str = "",
        job_id: int = None,
        user_id: int = None,
        use_coem: bool = True
    ) -> MultimodalEmotionResult:
        """
        执行多模态情感分析
        
        Args:
            audio_tags: 音频情感标签（如"[pause][breath]"）
            asr_text: ASR转写文本
            job_id: 岗位ID（用于COEM检索）
            user_id: 用户ID（用于COEM检索）
            use_coem: 是否启用COEM检索增强
            
        Returns:
            MultimodalEmotionResult: 多模态情感分析结果
        """
        start_time = time.time()
        
        result = MultimodalEmotionResult(
            asr_text=asr_text
        )
        
        try:
            # Step 1: 语音情感识别
            result.voice_emotion, result.voice_quality = self._analyze_voice_emotion(audio_tags)
            
            # Step 2: 文本情感识别（含COEM增强）
            if use_coem and job_id and user_id:
                retrieved_context = self._retrieve_coem_context(asr_text, job_id, user_id)
                result.retrieved_context = retrieved_context
            
            result.text_emotion, result.text_quality = self._analyze_text_emotion(asr_text)
            
            # Step 3: 模态质量评估与动态权重计算
            result.voice_weight, result.text_weight = self._calculate_dynamic_weights(
                result.voice_quality,
                result.text_quality
            )
            
            # Step 4: 加权融合
            result.fused_emotion = self._weighted_fusion(
                result.voice_emotion,
                result.text_emotion,
                result.voice_weight,
                result.text_weight
            )
            
            # Step 5: 冲突仲裁
            result.conflict_detected, result.conflict_type, result.arbitration_reason = \
                self._conflict_arbitration(
                    result.voice_emotion,
                    result.text_emotion,
                    result.fused_emotion
                )
            
            # Step 6: LLM终判
            llm_result = self._llm_final_judgment(result)
            result.llm_emotion = llm_result.get('emotion', 'neutral')
            result.llm_confidence = llm_result.get('confidence', 0.0)
            result.llm_reasoning = llm_result.get('reasoning', '')
            
            # 设置主导情绪和置信度
            result.dominant_emotion = result.llm_emotion
            result.fusion_confidence = result.llm_confidence
            
        except Exception as e:
            print(f"[多模态情感分析] 异常: {e}")
            import traceback
            traceback.print_exc()
            
            # 降级：使用简单的标签解析
            from app.services.emotion_tag_parser import EmotionTagParser
            if audio_tags:
                analysis = EmotionTagParser.analyze_emotion_from_tags(audio_tags)
                result.dominant_emotion = analysis.get('dominant_emotion', 'neutral')
                result.fusion_confidence = analysis.get('confidence', 0.0)
        
        # 计算处理时间
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _analyze_voice_emotion(
        self, 
        audio_tags: str
    ) -> Tuple[Optional[EmotionVector], Optional[ModalityQuality]]:
        """
        Step 1: 语音情感识别
        
        基于腾讯云ASR返回的情感标签进行分析
        """
        if not audio_tags or '[' not in audio_tags:
            return None, None
        
        try:
            from app.services.emotion_tag_parser import EmotionTagParser
            
            # 解析情感标签
            analysis = EmotionTagParser.analyze_emotion_from_tags(audio_tags)
            
            if not analysis['emotion_tags']:
                return None, None
            
            # 将标签映射转换为情感向量
            emotion_vector = self._tags_to_emotion_vector(analysis)
            
            # 计算语音模态质量
            quality = ModalityQuality(
                confidence=analysis.get('confidence', 0.5),
                completeness=min(1.0, len(analysis['emotion_tags']) / 5.0)  # 最多5个标签为完整
            )
            
            print(f"[语音情感] 标签: {analysis['emotion_tags']}, 向量: {emotion_vector.to_dict()}")
            
            return emotion_vector, quality
            
        except Exception as e:
            print(f"[语音情感分析] 异常: {e}")
            return None, None
    
    def _analyze_text_emotion(
        self, 
        asr_text: str
    ) -> Tuple[Optional[EmotionVector], Optional[ModalityQuality]]:
        """
        Step 2: 文本情感识别（使用 DeepSeek LLM）
        """
        if not asr_text or len(asr_text.strip()) < 2:
            return None, None
        
        try:
            # 清理ASR标签，获取纯文本
            from app.services.emotion_tag_parser import EmotionTagParser
            clean_text = EmotionTagParser.clean_emotion_tags(asr_text)
            
            if not clean_text:
                return None, None
            
            # 使用 DeepSeek LLM 进行文本情感分析
            emotion_vector = self._llm_analyze_text_emotion(clean_text)
            
            if not emotion_vector:
                # 降级：使用简单规则
                emotion_vector = self._simple_text_emotion(clean_text)
            
            # 计算文本模态质量
            quality = ModalityQuality(
                confidence=0.85,  # LLM通常较可靠
                completeness=min(1.0, len(clean_text) / 100.0)  # 100字以上为完整
            )
            
            print(f"[文本情感-LLM] 文本: {clean_text[:30]}..., 向量: {emotion_vector.to_dict()}")
            
            return emotion_vector, quality
            
        except Exception as e:
            print(f"[文本情感分析] 异常: {e}")
            return None, None
    
    def _llm_analyze_text_emotion(self, text: str) -> Optional[EmotionVector]:
        """
        使用 DeepSeek LLM 进行文本情感分析
        """
        try:
            prompt = f"""请分析以下文本的情感倾向，输出JSON格式：
{{
  "positive": 0.0-1.0,
  "negative": 0.0-1.0,
  "neutral": 0.0-1.0
}}

文本：{text}

要求：
1. positive/negative/neutral 三个值之和必须等于 1.0
2. 根据文本内容判断情感倾向
3. 只输出JSON，不要其他文字
"""
            
            messages = [
                {'role': 'user', 'content': prompt}
            ]
            
            response = self.llm_client.generate_reply(
                messages,
                stream=False,
                temperature=0.1  # 低温度保证稳定性
            )
            
            # 解析 JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return EmotionVector(
                    positive=float(data.get('positive', 0.33)),
                    negative=float(data.get('negative', 0.33)),
                    neutral=float(data.get('neutral', 0.34))
                )
            
        except Exception as e:
            print(f"[LLM文本情感] 异常: {e}")
        
        return None
    
    def _call_tencent_nlp_emotion(self, text: str) -> Optional[EmotionVector]:
        """
        调用腾讯云NLP文本情感分析API
        
        API文档: https://cloud.tencent.com/document/api/271/35552
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.nlp.v20190408 import nlp_client, models
            
            # 从环境变量获取密钥
            secret_id = os.getenv('TENCENT_SECRET_ID', '')
            secret_key = os.getenv('TENCENT_SECRET_KEY', '')
            
            if not secret_id or not secret_key:
                print("[腾讯云NLP] 未配置密钥，跳过API调用")
                return None
            
            # 初始化客户端
            cred = credential.Credential(secret_id, secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "nlp.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = nlp_client.NlpClient(cred, "ap-guangzhou", clientProfile)
            
            # 构造请求
            req = models.SentimentAnalysisRequest()
            req.Text = text
            req.Mode = "3class"  # 三分类：positive/negative/neutral
            
            # 调用API
            resp = client.SentimentAnalysis(req)
            
            # 解析响应
            positive = getattr(resp, 'Positive', 0) / 100.0
            negative = getattr(resp, 'Negative', 0) / 100.0
            neutral = 1.0 - positive - negative
            
            return EmotionVector(
                positive=positive,
                negative=negative,
                neutral=max(0.0, neutral)
            )
            
        except ImportError:
            print("[腾讯云NLP] 未安装SDK，跳过API调用")
            return None
        except Exception as e:
            print(f"[腾讯云NLP] API调用失败: {e}")
            return None
    
    def _simple_text_emotion(self, text: str) -> EmotionVector:
        """
        简单文本情感分析（降级方案）
        
        基于关键词匹配
        """
        positive_keywords = ['好', '不错', '喜欢', '擅长', '熟悉', '精通', '优秀', '积极']
        negative_keywords = ['不好', '困难', '不熟悉', '不会', '问题', '挑战', '负面']
        
        pos_count = sum(1 for kw in positive_keywords if kw in text)
        neg_count = sum(1 for kw in negative_keywords if kw in text)
        
        total = pos_count + neg_count
        if total == 0:
            return EmotionVector(positive=0.33, negative=0.33, neutral=0.34)
        
        return EmotionVector(
            positive=pos_count / total * 0.8,
            negative=neg_count / total * 0.8,
            neutral=0.2
        )
    
    def _tags_to_emotion_vector(self, analysis: Dict) -> EmotionVector:
        """
        将ASR标签分析结果转换为情感向量
        """
        tags = analysis.get('emotion_tags', [])
        dominant = analysis.get('dominant_emotion', 'neutral')
        
        # 简单映射
        emotion_map = {
            'happy': EmotionVector(positive=0.8, negative=0.1, neutral=0.1),
            'confident': EmotionVector(positive=0.75, negative=0.05, neutral=0.2),
            'nervous': EmotionVector(positive=0.1, negative=0.7, neutral=0.2),
            'hesitant': EmotionVector(positive=0.2, negative=0.3, neutral=0.5),
            'frustrated': EmotionVector(positive=0.05, negative=0.85, neutral=0.1),
            'uncomfortable': EmotionVector(positive=0.15, negative=0.6, neutral=0.25),
            'neutral': EmotionVector(positive=0.33, negative=0.33, neutral=0.34)
        }
        
        base_vector = emotion_map.get(dominant, emotion_map['neutral'])
        
        # 根据标签数量调整置信度
        tag_factor = min(1.0, len(tags) / 3.0)
        
        return EmotionVector(
            positive=base_vector.positive * tag_factor + 0.33 * (1 - tag_factor),
            negative=base_vector.negative * tag_factor + 0.33 * (1 - tag_factor),
            neutral=base_vector.neutral * tag_factor + 0.34 * (1 - tag_factor)
        )
    
    def _calculate_dynamic_weights(
        self,
        voice_quality: Optional[ModalityQuality],
        text_quality: Optional[ModalityQuality]
    ) -> Tuple[float, float]:
        """
        Step 3: 动态权重计算
        
        基于模态质量动态调整权重
        """
        if not voice_quality and not text_quality:
            return self.DEFAULT_VOICE_WEIGHT, self.DEFAULT_TEXT_WEIGHT
        
        voice_score = voice_quality.quality_score if voice_quality else 0.0
        text_score = text_quality.quality_score if text_quality else 0.0
        
        total_score = voice_score + text_score
        
        if total_score == 0:
            return self.DEFAULT_VOICE_WEIGHT, self.DEFAULT_TEXT_WEIGHT
        
        # 动态权重分配
        alpha = voice_score / total_score
        beta = text_score / total_score
        
        # 限制范围，避免极端权重
        alpha = max(0.2, min(0.8, alpha))
        beta = 1.0 - alpha
        
        print(f"[动态权重] 语音={alpha:.2f}, 文本={beta:.2f}")
        
        return alpha, beta
    
    def _weighted_fusion(
        self,
        voice_emotion: Optional[EmotionVector],
        text_emotion: Optional[EmotionVector],
        voice_weight: float,
        text_weight: float
    ) -> EmotionVector:
        """
        Step 4: 加权融合
        """
        if not voice_emotion and not text_emotion:
            return EmotionVector(positive=0.33, negative=0.33, neutral=0.34)
        
        if not voice_emotion:
            return text_emotion
        
        if not text_emotion:
            return voice_emotion
        
        # 加权平均
        fused = EmotionVector(
            positive=voice_weight * voice_emotion.positive + text_weight * text_emotion.positive,
            negative=voice_weight * voice_emotion.negative + text_weight * text_emotion.negative,
            neutral=voice_weight * voice_emotion.neutral + text_weight * text_emotion.neutral
        )
        
        # 归一化
        total = fused.positive + fused.negative + fused.neutral
        if total > 0:
            fused.positive /= total
            fused.negative /= total
            fused.neutral /= total
        
        print(f"[加权融合] 融合向量: {fused.to_dict()}")
        
        return fused
    
    def _conflict_arbitration(
        self,
        voice_emotion: Optional[EmotionVector],
        text_emotion: Optional[EmotionVector],
        fused_emotion: EmotionVector
    ) -> Tuple[bool, str, str]:
        """
        Step 5: 冲突仲裁
        """
        if not voice_emotion or not text_emotion:
            return False, "no_conflict", "单模态，无需仲裁"
        
        # 检测强冲突
        voice_dominant = max(voice_emotion.to_dict(), key=voice_emotion.to_dict().get)
        text_dominant = max(text_emotion.to_dict(), key=text_emotion.to_dict().get)
        
        voice_max_prob = voice_emotion.to_dict()[voice_dominant]
        text_max_prob = text_emotion.to_dict()[text_dominant]
        
        # 强冲突：一方强烈情感 vs 另一方相反情感
        if voice_max_prob > self.STRONG_CONFLICT_THRESHOLD and text_dominant != voice_dominant:
            if voice_dominant == 'negative' and text_dominant in ['positive', 'neutral']:
                return True, "strong_voice", "语音显示强烈负面情绪，优先信任语音（语调更真实）"
            elif voice_dominant == 'positive' and text_dominant == 'negative':
                return True, "strong_text", "语音正面但文本负面，保持融合结果（语义更可靠）"
        
        # 弱冲突：双方都有明确情感但不一致
        if voice_dominant != text_dominant and voice_max_prob > 0.5 and text_max_prob > 0.5:
            return True, "weak", f"语音({voice_dominant})与文本({text_dominant})存在分歧，采用加权融合"
        
        return False, "no_conflict", "无冲突或冲突不明显"
    
    def _retrieve_coem_context(self, text: str, job_id: int, user_id: int) -> str:
        """
        COEM检索增强上下文
        """
        try:
            from app.services.coem import retrieve_candidate_docs
            from app.services.interview_service import InterviewService
            
            # 检索相关文档
            docs = retrieve_candidate_docs(
                query=text,
                interview_service=InterviewService,
                job_id=job_id,
                limit=2
            )
            
            if docs:
                context = "\n".join([doc.get('text', '') for doc in docs[:2]])
                print(f"[COEM检索] 找到 {len(docs)} 个相关文档")
                return context
            
        except Exception as e:
            print(f"[COEM检索] 异常: {e}")
        
        return ""
    
    def _llm_final_judgment(self, result: MultimodalEmotionResult) -> Dict:
        """
        Step 6: LLM最终判决
        """
        try:
            # 构建结构化Prompt
            prompt = self._build_llm_prompt(result)
            
            messages = [
                {
                    'role': 'system',
                    'content': '你是一个专业的情感分析助手，擅长多模态情感融合分析。请根据提供的信息输出JSON格式结果。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # 调用LLM
            response = self.llm_client.generate_reply(
                messages,
                stream=False,
                temperature=0.3  # 低温度保证稳定性
            )
            
            # 解析JSON响应
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
                print(f"[LLM终判] 结果: {llm_result}")
                return llm_result
            
        except Exception as e:
            print(f"[LLM终判] 异常: {e}")
        
        # 降级：使用融合结果
        dominant = max(result.fused_emotion.to_dict(), key=result.fused_emotion.to_dict().get)
        return {
            'emotion': dominant,
            'confidence': result.fused_emotion.to_dict()[dominant],
            'reasoning': '基于加权融合结果的简单判断'
        }
    
    def _build_llm_prompt(self, result: MultimodalEmotionResult) -> str:
        """
        构建LLM Prompt
        """
        parts = []
        
        # 对话历史/检索上下文
        if result.retrieved_context:
            parts.append(f"【对话历史/检索上下文】\n{result.retrieved_context}\n")
        
        # 用户语音转录
        parts.append(f"【用户语音转录】\n{result.asr_text}\n")
        
        # 多模态融合结果
        parts.append("【多模态融合结果】")
        if result.voice_emotion:
            parts.append(f"- 语音倾向: {result.voice_emotion.to_dict()}")
        if result.text_emotion:
            parts.append(f"- 文本倾向: {result.text_emotion.to_dict()}")
        if result.fused_emotion:
            parts.append(f"- 综合判定: {result.fused_emotion.to_dict()}")
        
        parts.append(f"- 权重分配: 语音={result.voice_weight:.2f}, 文本={result.text_weight:.2f}\n")
        
        # 规则修正说明
        if result.conflict_detected:
            parts.append(f"【规则修正说明】\n冲突类型: {result.conflict_type}\n仲裁依据: {result.arbitration_reason}\n")
        
        # 输出要求
        parts.append("\n请输出JSON格式结果：")
        parts.append('{')
        parts.append('  "emotion": "positive/negative/neutral",')
        parts.append('  "confidence": 0.0-1.0,')
        parts.append('  "reasoning": "详细判断理由"')
        parts.append('}')
        
        return '\n'.join(parts)
    
    def format_for_llm(self, result: MultimodalEmotionResult) -> str:
        """
        将多模态情感分析结果格式化为大模型可读的提示词
        """
        if not result:
            return ""
        
        parts = []
        
        # 主导情绪
        parts.append(f"【情绪状态】{result.dominant_emotion}")
        
        # 多模态信息
        if result.voice_emotion:
            voice_str = f"语音({result.voice_weight:.0%}): {result.voice_emotion.to_dict()}"
            parts.append(f"【语音情感】{voice_str}")
        
        if result.text_emotion:
            text_str = f"文本({result.text_weight:.0%}): {result.text_emotion.to_dict()}"
            parts.append(f"【文本情感】{text_str}")
        
        # 冲突信息
        if result.conflict_detected:
            parts.append(f"【冲突仲裁】{result.arbitration_reason}")
        
        # LLM推理
        if result.llm_reasoning:
            parts.append(f"【AI推理】{result.llm_reasoning}")
        
        # 置信度
        parts.append(f"【置信度】{result.fusion_confidence:.0%}")
        
        return ' | '.join(parts)


# ==================== 便捷函数 ====================

def analyze_multimodal_emotion(
    audio_tags: str = "",
    asr_text: str = "",
    job_id: int = None,
    user_id: int = None,
    use_coem: bool = True
) -> Dict:
    """
    便捷函数：执行多模态情感分析并返回字典
    """
    service = MultimodalEmotionService()
    result = service.analyze(audio_tags, asr_text, job_id, user_id, use_coem)
    return result.to_dict()


def get_multimodal_emotion_prompt(
    audio_tags: str = "",
    asr_text: str = "",
    job_id: int = None,
    user_id: int = None,
    use_coem: bool = True
) -> str:
    """
    便捷函数：获取用于大模型的格式化情感提示词
    """
    service = MultimodalEmotionService()
    result = service.analyze(audio_tags, asr_text, job_id, user_id, use_coem)
    return service.format_for_llm(result)