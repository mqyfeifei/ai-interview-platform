# backend/app/services/emotion_tag_parser.py
"""
腾讯云ASR情感标签解析器
解析腾讯云服务返回的情绪标签，转换为大模型可读的提示词
"""

import re
from typing import Dict, List, Optional


class EmotionTagParser:
    """
    情感标签解析器
    
    腾讯云ASR返回的情感标签示例:
    - [pause]: 停顿
    - [laughter]: 笑声
    - [breath]: 呼吸声
    - [cough]: 咳嗽
    - [sigh]: 叹气
    
    这些标签可以反映用户的情绪状态和说话节奏
    """
    
    # 情感标签映射表
    EMOTION_TAG_MAP = {
        '[pause]': {'emotion': 'hesitant', 'description': '犹豫/思考', 'weight': 0.3},
        '[laughter]': {'emotion': 'happy', 'description': '轻松/自信', 'weight': 0.5},
        '[breath]': {'emotion': 'nervous', 'description': '紧张/急促', 'weight': 0.4},
        '[cough]': {'emotion': 'uncomfortable', 'description': '不适/尴尬', 'weight': 0.2},
        '[sigh]': {'emotion': 'frustrated', 'description': '沮丧/无奈', 'weight': 0.4},
    }
    
    @staticmethod
    def extract_emotion_tags(text: str) -> List[str]:
        """
        从文本中提取所有情感标签
        
        Args:
            text: 包含情感标签的文本
            
        Returns:
            list: 情感标签列表
        """
        if not text:
            return []
        
        # 匹配所有 [...] 格式的标签
        tags = re.findall(r'\[([a-zA-Z_]+)\]', text)
        return tags
    
    @staticmethod
    def analyze_emotion_from_tags(text: str) -> Dict:
        """
        根据情感标签分析用户情绪状态
        
        Args:
            text: 包含情感标签的文本
            
        Returns:
            dict: 情感分析结果
        """
        if not text:
            return {
                'dominant_emotion': 'neutral',
                'emotion_tags': [],
                'emotion_summary': '',
                'confidence': 0.0
            }
        
        # 提取所有标签
        tags = EmotionTagParser.extract_emotion_tags(text)
        
        if not tags:
            return {
                'dominant_emotion': 'neutral',
                'emotion_tags': [],
                'emotion_summary': '未检测到明显情绪特征',
                'confidence': 0.0
            }
        
        # 统计各情绪类型的权重
        emotion_weights = {}
        for tag in tags:
            tag_lower = f'[{tag.lower()}]'
            if tag_lower in EmotionTagParser.EMOTION_TAG_MAP:
                info = EmotionTagParser.EMOTION_TAG_MAP[tag_lower]
                emotion = info['emotion']
                emotion_weights[emotion] = emotion_weights.get(emotion, 0) + info['weight']
        
        # 找出主导情绪
        if emotion_weights:
            dominant_emotion = max(emotion_weights, key=emotion_weights.get)
            confidence = min(1.0, emotion_weights[dominant_emotion] / len(tags))
        else:
            dominant_emotion = 'neutral'
            confidence = 0.0
        
        # 生成情感摘要
        tag_descriptions = []
        for tag in tags:
            tag_lower = f'[{tag.lower()}]'
            if tag_lower in EmotionTagParser.EMOTION_TAG_MAP:
                desc = EmotionTagParser.EMOTION_TAG_MAP[tag_lower]['description']
                tag_descriptions.append(desc)
        
        emotion_summary = '、'.join(tag_descriptions) if tag_descriptions else '未检测到明显情绪特征'
        
        return {
            'dominant_emotion': dominant_emotion,
            'emotion_tags': tags,
            'emotion_summary': emotion_summary,
            'confidence': round(confidence, 2),
            'tag_count': len(tags)
        }
    
    @staticmethod
    def clean_emotion_tags(text: str) -> str:
        """
        清理文本中的情感标签，只保留纯文本
        
        Args:
            text: 包含情感标签的文本
            
        Returns:
            str: 清理后的纯文本
        """
        if not text:
            return ''
        
        # 移除所有 [...] 格式的标签
        cleaned = re.sub(r'\[[a-zA-Z_]+\]', '', text)
        # 清理多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    @staticmethod
    def format_for_llm(text_with_tags: str) -> str:
        """
        将带情感标签的文本格式化为大模型可读的提示词
        
        Args:
            text_with_tags: 包含情感标签的原始文本
            
        Returns:
            str: 格式化后的提示词
        """
        if not text_with_tags:
            return ''
        
        # 分析情感
        analysis = EmotionTagParser.analyze_emotion_from_tags(text_with_tags)
        
        # 清理标签得到纯文本
        clean_text = EmotionTagParser.clean_emotion_tags(text_with_tags)
        
        # 构建提示词
        parts = []
        
        if analysis['emotion_tags']:
            parts.append(f"【语音情感特征】检测到{analysis['tag_count']}个情绪标记：{analysis['emotion_summary']}")
            parts.append(f"【主导情绪】{analysis['dominant_emotion']}（置信度{analysis['confidence']:.0%}）")
        
        if clean_text:
            parts.append(f"【识别文本】{clean_text}")
        
        return ' | '.join(parts) if parts else ''


# ==================== 便捷函数 ====================

def parse_emotion_tags(text: str) -> Dict:
    """
    便捷函数：解析情感标签
    
    Args:
        text: 包含情感标签的文本
        
    Returns:
        dict: 情感分析结果
    """
    return EmotionTagParser.analyze_emotion_from_tags(text)


def get_emotion_prompt(text_with_tags: str) -> str:
    """
    便捷函数：获取大模型情感提示词
    
    Args:
        text_with_tags: 包含情感标签的文本
        
    Returns:
        str: 格式化后的提示词
    """
    return EmotionTagParser.format_for_llm(text_with_tags)


def clean_tags(text: str) -> str:
    """
    便捷函数：清理情感标签
    
    Args:
        text: 包含情感标签的文本
        
    Returns:
        str: 清理后的纯文本
    """
    return EmotionTagParser.clean_emotion_tags(text)
