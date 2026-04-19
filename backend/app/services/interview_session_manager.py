# backend/app/services/interview_session_manager.py
"""
面试服务 - 会话管理模块
负责面试启动、配置管理、开场白生成等
"""

import random
import os
import re
from pathlib import Path
from difflib import SequenceMatcher
from copy import deepcopy
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import yaml

from flask import current_app

from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewSessionConfig, InterviewProfile
from app.models.job import Job, get_job_front_key
from app.models.prompt import AiPrompt
from app.services.tts_service import bytes_to_b64


# 轮次策略配置：岗位类型 -> 面试轮次 -> 题型/难度权重
ROUND_STRATEGY_CONFIG = {
    'default': {
        'first_round': {
            'label': '一面',
            'focus': '基础能力与表达清晰度',
            'target_mix': {
                'technical': 0.55,
                'project_deep_dive': 0.05,
                'scenario_design': 0.15,
                'behavioral': 0.25,
            },
            'difficulty': {'easy': 0.35, 'medium': 0.55, 'hard': 0.10},
        },
        'second_round': {
            'label': '二面',
            'focus': '项目真实性、系统设计与权衡能力',
            'target_mix': {
                'technical': 0.20,
                'project_deep_dive': 0.40,
                'scenario_design': 0.30,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.10, 'medium': 0.55, 'hard': 0.35},
        },
        'third_round': {
            'label': '三面',
            'focus': '复杂问题拆解、边界条件与高压决策',
            'target_mix': {
                'technical': 0.30,
                'project_deep_dive': 0.20,
                'scenario_design': 0.35,
                'behavioral': 0.15,
            },
            'difficulty': {'easy': 0.05, 'medium': 0.45, 'hard': 0.50},
        },
    },
    'backend': {
        'first_round': {
            'label': '一面',
            'focus': '语言基础、框架能力与工程规范',
            'target_mix': {
                'technical': 0.60,
                'project_deep_dive': 0.10,
                'scenario_design': 0.10,
                'behavioral': 0.20,
            },
            'difficulty': {'easy': 0.40, 'medium': 0.50, 'hard': 0.10},
        },
        'second_round': {
            'label': '二面',
            'focus': '系统设计、项目取舍与故障定位',
            'target_mix': {
                'technical': 0.20,
                'project_deep_dive': 0.40,
                'scenario_design': 0.30,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.10, 'medium': 0.50, 'hard': 0.40},
        },
        'third_round': {
            'label': '三面',
            'focus': '复杂场景决策、风险控制与技术领导力',
            'target_mix': {
                'technical': 0.25,
                'project_deep_dive': 0.35,
                'scenario_design': 0.25,
                'behavioral': 0.15,
            },
            'difficulty': {'easy': 0.05, 'medium': 0.40, 'hard': 0.55},
        },
    },
    'frontend': {
        'first_round': {
            'label': '一面',
            'focus': '前端基础、浏览器原理与组件化能力',
            'target_mix': {
                'technical': 0.70,
                'project_deep_dive': 0.10,
                'scenario_design': 0.10,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.50, 'medium': 0.40, 'hard': 0.10},
        },
        'second_round': {
            'label': '二面',
            'focus': '大型前端工程实践、性能与可维护性',
            'target_mix': {
                'technical': 0.25,
                'project_deep_dive': 0.35,
                'scenario_design': 0.30,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.10, 'medium': 0.55, 'hard': 0.35},
        },
        'third_round': {
            'label': '三面',
            'focus': '跨端架构权衡、复杂交互决策与团队协同',
            'target_mix': {
                'technical': 0.25,
                'project_deep_dive': 0.25,
                'scenario_design': 0.35,
                'behavioral': 0.15,
            },
            'difficulty': {'easy': 0.05, 'medium': 0.45, 'hard': 0.50},
        },
    },
    'algorithm': {
        'first_round': {
            'label': '一面',
            'focus': '算法基础、数学直觉与问题建模能力',
            'target_mix': {
                'technical': 0.40,
                'project_deep_dive': 0.10,
                'scenario_design': 0.40,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.30, 'medium': 0.40, 'hard': 0.30},
        },
        'second_round': {
            'label': '二面',
            'focus': '算法方案落地、实验设计与性能优化',
            'target_mix': {
                'technical': 0.20,
                'project_deep_dive': 0.35,
                'scenario_design': 0.35,
                'behavioral': 0.10,
            },
            'difficulty': {'easy': 0.10, 'medium': 0.45, 'hard': 0.45},
        },
        'third_round': {
            'label': '三面',
            'focus': '复杂开放问题、边界条件与研究判断力',
            'target_mix': {
                'technical': 0.25,
                'project_deep_dive': 0.20,
                'scenario_design': 0.40,
                'behavioral': 0.15,
            },
            'difficulty': {'easy': 0.05, 'medium': 0.35, 'hard': 0.60},
        },
    },
}


def _resolve_job_strategy_key(job):
    """将岗位名称归一化到策略配置键。"""
    if not job:
        return 'default'

    name = (job.name or '').strip().lower()
    if not name:
        return 'default'

    if any(k in name for k in ('后端', 'backend', 'java', 'golang', 'python')):
        return 'backend'
    if any(k in name for k in ('前端', 'frontend', 'web', 'vue', 'react')):
        return 'frontend'
    if any(k in name for k in ('算法', 'algorithm', '机器学习', '视觉', 'cv')):
        return 'algorithm'

    return 'default'


# 面试轮次别名映射：支持多种格式（字符串、整数）
ROUND_ALIASES = {
    # 字符串格式
    'first_round': 'first_round',
    'second_round': 'second_round',
    'third_round': 'third_round',
    '1': 'first_round',
    '2': 'second_round',
    '3': 'third_round',
    '一面': 'first_round',
    '二面': 'second_round',
    '三面': 'third_round',
    # 整数格式会被转换为字符串后匹配
}


class InterviewSessionManager:
    """面试会话管理器"""
    _OPENING_GREETING_WAIT_TIMEOUT_SECONDS = float(
        os.environ.get('OPENING_GREETING_WAIT_TIMEOUT_SECONDS', '8.0')
    )
    _OPENING_TTS_WAIT_TIMEOUT_SECONDS = float(
        os.environ.get('OPENING_TTS_WAIT_TIMEOUT_SECONDS', '10.0')
    )
    
    # === 多样化开场白池 ===
    _DIVERSE_GREETING_FALLBACKS = [
        "你好，欢迎来到模拟面试。今天我们会从一个你熟悉的场景开始，逐步深入。",
        "欢迎你，先放轻松。我们先从一个基础问题热身，再进入进阶环节。",
        "你好，接下来我会以真实面试节奏和你交流，我们从你最擅长的方向切入。",
        "欢迎参加本轮面试。你可以把这当成一次实战演练，我们边问边优化。",
    ]

    _ROUND_OPENING_PREFIXES = {
        'first_round': [
            '欢迎来到一面，咱们先从基础概念和主干逻辑聊起。',
            '这一轮我先看你最基础的部分，咱们慢慢展开。',
        ],
        'second_round': [
            '欢迎来到二面，这一轮我会围绕关联概念和实际项目细聊。',
            '这一轮会往相邻知识点和方案取舍上多问一点。',
        ],
        'third_round': [
            '来到三面了，这一轮我会把几个知识点串起来一起问。',
            '这一轮会更像业务评审，我们重点看你怎么综合判断。',
        ],
    }

    _STYLE_OPENING_SUFFIXES = {
        'pressure': '我会追问得快一点、直接一点，你尽量把思路讲清楚。',
        'confident': '咱们按正常面试来，你先说结论，我再顺着问。',
        'teaching': '你要是卡住，我会稍微带一下，再继续往下问。',
    }

    _FOCUS_OPENING_TEMPLATES = [
        '这一轮重点我会放在 {focus}。',
        '今天主要看你在 {focus} 这块的表现。',
        '这轮我们就围绕 {focus} 来聊。',
    ]

    _BRIDGE_OPENING_TEMPLATES = [
        '我先问个小问题，咱们慢慢展开。',
        '先看你的思路，再往细里聊。',
        '我先热个身，然后再继续往下追问。',
    ]

    _ROUND_LABELS = {
        'first_round': '一面',
        'second_round': '二面',
        'third_round': '三面',
    }

    _ROUND_GREETING_ALIASES = {
        'first_round': ['一面', '第一轮', '第1轮', 'round 1', 'round1', '1面', 'first_round'],
        'second_round': ['二面', '第二轮', '第2轮', 'round 2', 'round2', '2面', 'second_round'],
        'third_round': ['三面', '第三轮', '第3轮', 'round 3', 'round3', '3面', 'third_round'],
    }

    @staticmethod
    def normalize_target_source(raw_source):
        source = str(raw_source or '').strip()
        if not source:
            return '通用'
        if re.fullmatch(r'[\u4e00-\u9fff·（）()、\s]+', source):
            return source
        return '通用'

    @staticmethod
    def get_job_source_options(job_id):
        """返回岗位可用来源列表（通用 + 公司来源）。"""
        try:
            job = Job.query.get(job_id) if job_id else None
            if not job:
                return ['通用']

            job_key = get_job_front_key(job)
            if not job_key:
                return ['通用']

            backend_root = Path(__file__).resolve().parents[2]
            question_dir = backend_root / 'FuChuangTiKu' / 'data' / 'questions'
            if not question_dir.exists():
                return ['通用']

            sources = set()
            for yaml_path in sorted(question_dir.glob(f'{job_key}_*_questions.yaml')):
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as fp:
                        payload = yaml.safe_load(fp) or {}
                except Exception:
                    continue
                for item in (payload.get('items') or []):
                    normalized = InterviewSessionManager.normalize_target_source(item.get('source'))
                    sources.add(normalized)

            return ['通用'] + sorted([s for s in sources if s != '通用'])
        except Exception:
            return ['通用']

    @staticmethod
    def get_round_strategy(job_id, round_name):
        """
        获取指定岗位与轮次的策略配置。

        Args:
            job_id: 岗位ID
            round_name: 轮次名(first_round/second_round/third_round 或中文别名)

        Returns:
            dict: 轮次策略配置（label/focus/target_mix/difficulty）
        """
        normalized_round = ROUND_ALIASES.get(str(round_name).strip().lower() if round_name is not None else '')
        if not normalized_round:
            normalized_round = 'first_round'

        job = Job.query.get(job_id) if job_id else None
        strategy_key = _resolve_job_strategy_key(job)

        strategy_group = ROUND_STRATEGY_CONFIG.get(strategy_key) or ROUND_STRATEGY_CONFIG['default']
        strategy = strategy_group.get(normalized_round) or ROUND_STRATEGY_CONFIG['default'][normalized_round]

        return deepcopy(strategy)

    @staticmethod
    def get_interview_question_plan(job_id, interview_round='first_round', interview_style='confident'):
        """
        基于轮次、风格与岗位知识库规模，动态规划题量范围。
        """
        normalized_round = ROUND_ALIASES.get(
            str(interview_round).strip().lower() if interview_round is not None else '',
            'first_round',
        )
        style_key = str(interview_style or 'confident').strip().lower() or 'confident'
        style_key = style_key if style_key in ('pressure', 'confident', 'teaching') else 'confident'

        round_base_map = {
            'first_round': 8,
            'second_round': 10,
            'third_round': 12,
        }
        style_bonus_map = {
            'pressure': 1,
            'confident': 0,
            'teaching': 1,
        }

        question_count = 0
        tag_count = 0
        try:
            from app.services.interview_graph_helper import InterviewGraphHelper
            questions, tag_map = InterviewGraphHelper.get_job_graph_snapshot(job_id)
            question_count = len(questions or [])
            tag_count = len(tag_map or {})
        except Exception:
            question_count = 0
            tag_count = 0

        base_total = int(round_base_map.get(normalized_round, 8) + style_bonus_map.get(style_key, 0))
        tag_bonus = min(3, int(tag_count / 8))
        bank_bonus = min(2, int(question_count / 30))
        planned = base_total + tag_bonus + bank_bonus

        max_questions = max(8, min(16, int(planned)))
        if question_count > 0:
            inventory_cap = max(8, min(16, int(max(8, question_count * 0.35))))
            max_questions = min(max_questions, inventory_cap)
            max_questions = max(8, max_questions)

        min_questions = max(6, min(max_questions - 1, max_questions - 3))

        return {
            'min_questions': int(min_questions),
            'max_questions': int(max_questions),
            'planned_questions': int(max_questions),
        }

    @staticmethod
    def align_round_greeting(base_greeting, interview_round):
        """将开场白中的轮次文案对齐到当前轮次，避免模板沿用上一轮称呼。"""
        text = str(base_greeting or '').strip()
        if not text:
            return text

        normalized_round = ROUND_ALIASES.get(
            str(interview_round).strip().lower() if interview_round is not None else '',
            'first_round',
        )
        target_label = InterviewSessionManager._ROUND_LABELS.get(normalized_round, '一面')

        if normalized_round == 'first_round':
            return text

        for round_key, aliases in InterviewSessionManager._ROUND_GREETING_ALIASES.items():
            if round_key == normalized_round:
                continue
            for alias in sorted(aliases, key=len, reverse=True):
                text = text.replace(alias, target_label)

        return text

    @staticmethod
    def apply_conversational_tone(text, interview_style='confident', voice_mode=False):
        """将开场/提问文本收敛到更口语化的表达。"""
        content = str(text or '').strip()
        if not content:
            return content

        replacements = [
            ('我会', '我这边会'),
            ('请你', '你可以'),
            ('首先', '先'),
            ('另外', '再就是'),
            ('因此', '所以'),
            ('此外', '还有'),
            ('我们先从一个短问题热身，再逐步深入。', '我先问个小问题，咱们慢慢展开。'),
        ]
        for old, new in replacements:
            content = content.replace(old, new)

        if voice_mode:
            content = content.replace('。', '，')
            content = content.replace('，，', '，')

        return content
    
    @staticmethod
    def normalize_interview_style(voice_mode=False, interview_style=None, voice_role=None):
        """
        标准化面试风格
        
        Args:
            voice_mode: 是否语音模式
            interview_style: 面试风格字符串
            voice_role: 语音角色
            
        Returns:
            str: 标准化后的风格(pressure/confident/teaching)
        """
        style_aliases = {
            '压力面': 'pressure',
            'pressure': 'pressure',
            'strict': 'pressure',
            '自信面': 'confident',
            'confident': 'confident',
            'balanced': 'confident',
            '教学面': 'teaching',
            'teaching': 'teaching',
            'technical': 'teaching',  # 兼容旧值
            'coach': 'teaching',
        }
        
        raw_style = str(interview_style).strip() if interview_style is not None else ''
        if raw_style:
            normalized = style_aliases.get(raw_style.lower()) or style_aliases.get(raw_style)
            if normalized:
                return normalized
        
        # 兼容旧前端：未传 style 时，仍可从 voice_role 兜底推断
        normalized_role = str(voice_role).strip().lower() if voice_role is not None else ''

        role_style_map = {
            'role_strict': 'pressure',
            'role_warm': 'confident',
            'role_calm': 'teaching',
        }
        if normalized_role in role_style_map:
            return role_style_map[normalized_role]
        
        return 'confident'
    
    @staticmethod
    def build_session_config_payload(voice_mode=False, interview_style=None, voice_role=None, interview_round=None, profile_id=None, voice=None, session_config=None):
        """
        构建会话配置载荷
        
        Args:
            voice_mode: 是否语音模式
            interview_style: 面试风格
            interview_round: 面试轮次
            voice_role: 语音角色
            profile_id: InterviewProfile ID
            voice: 语音音色名称
            session_config: 前端传入的会话配置覆盖字段
            
        Returns:
            dict: 会话配置字典
        """
        # 如果前端把风格放在 session_config 里，也一并兼容读取
        target_source = '通用'
        if isinstance(session_config, dict):
            interview_style = interview_style or session_config.get('interview_style') or session_config.get('interviewer_style')
            target_source = session_config.get('target_source') or session_config.get('source') or '通用'

        # 标准化面试风格
        style = InterviewSessionManager.normalize_interview_style(
            voice_mode=voice_mode,
            interview_style=interview_style,
            voice_role=voice_role,
        )
        
        # 标准化面试轮次
        # 先将 interview_round 转换为字符串，避免整数调用 strip() 报错
        round_str = str(interview_round).strip().lower() if interview_round is not None else ''
        normalized_round = ROUND_ALIASES.get(round_str) or 'first_round'
        
        # 初始化 payload
        payload = {}
        
        # 如果提供了 profile_id，从数据库读取配置
        if profile_id:
            profile = InterviewProfile.query.get(profile_id)
            if profile:
                tech_ratio = float(profile.technique_percentage or 60.0)
                scenario_ratio = float(profile.scenario_percentage or 40.0)
                project_deep_dive_percentage = float(profile.project_deep_dive_percentage if profile.project_deep_dive_percentage is not None else 15.0)
                behavioral_percentage = float(profile.behavioral_percentage if profile.behavioral_percentage is not None else 15.0)
                difficulty_low_percentage = float(profile.difficulty_low_percentage if profile.difficulty_low_percentage is not None else 30.0)
                difficulty_medium_percentage = float(profile.difficulty_medium_percentage if profile.difficulty_medium_percentage is not None else 50.0)
                difficulty_high_percentage = float(profile.difficulty_high_percentage if profile.difficulty_high_percentage is not None else 20.0)
                
                payload = {
                    'profile_id': profile.id,
                    # 用户显式选择的风格优先，其次才使用套餐默认风格
                    'interview_style': style,
                    'interview_round': normalized_round,
                    'tech_ratio': tech_ratio,
                    'scenario_ratio': scenario_ratio,
                    'project_deep_dive_percentage': project_deep_dive_percentage,
                    'behavioral_percentage': behavioral_percentage,
                    'difficulty_low_percentage': difficulty_low_percentage,
                    'difficulty_medium_percentage': difficulty_medium_percentage,
                    'difficulty_high_percentage': difficulty_high_percentage,
                    'is_dynamic_adjust': bool(profile.is_dynamic_adjust),
                    'voice_id': voice or profile.voice_id or voice_role or None,
                    'speech_speed': float(profile.speech_speed or 1.0),
                    'tone_descriptor': profile.tone_descriptor or '',
                    'enabled_dimensions': profile.enabled_dimensions or ['technical', 'project_deep_dive', 'scenario_design', 'behavioral'],
                    'difficulty_level': int(profile.difficulty_level or 2),
                    'target_source': InterviewSessionManager.normalize_target_source(
                        target_source if target_source != '通用' else profile.target_source
                    ),
                }
        
        # 如果没有 profile 或 profile 不存在，使用默认配置
        if not payload:
            profile_map = {
                'confident': {
                    'tech_ratio': 60.0,
                    'scenario_ratio': 40.0,
                    'project_deep_dive_percentage': 15.0,
                    'behavioral_percentage': 15.0,
                    'difficulty_low_percentage': 30.0,
                    'difficulty_medium_percentage': 50.0,
                    'difficulty_high_percentage': 20.0,
                    'difficulty_level': 2,
                    'tone_descriptor': 'balanced_confident'
                },
                'teaching': {
                    'tech_ratio': 80.0,
                    'scenario_ratio': 20.0,
                    'project_deep_dive_percentage': 15.0,
                    'behavioral_percentage': 15.0,
                    'difficulty_low_percentage': 35.0,
                    'difficulty_medium_percentage': 45.0,
                    'difficulty_high_percentage': 20.0,
                    'difficulty_level': 2,
                    'tone_descriptor': 'teaching_guided'
                },
                'pressure': {
                    'tech_ratio': 70.0,
                    'scenario_ratio': 30.0,
                    'project_deep_dive_percentage': 15.0,
                    'behavioral_percentage': 15.0,
                    'difficulty_low_percentage': 20.0,
                    'difficulty_medium_percentage': 50.0,
                    'difficulty_high_percentage': 30.0,
                    'difficulty_level': 3,
                    'tone_descriptor': 'pressure_challenge'
                }
            }
            profile = profile_map.get(style, profile_map['confident'])
            payload = {
                'interview_style': style,
                'interview_round': normalized_round,
                'tech_ratio': profile['tech_ratio'],
                'scenario_ratio': profile['scenario_ratio'],
                'project_deep_dive_percentage': profile.get('project_deep_dive_percentage', 15.0),
                'behavioral_percentage': profile.get('behavioral_percentage', 15.0),
                'difficulty_low_percentage': profile['difficulty_low_percentage'],
                'difficulty_medium_percentage': profile['difficulty_medium_percentage'],
                'difficulty_high_percentage': profile['difficulty_high_percentage'],
                'is_dynamic_adjust': True,
                'voice_id': voice or voice_role or None,
                'speech_speed': 1.0,
                'tone_descriptor': profile['tone_descriptor'],
                'enabled_dimensions': ['technical', 'project_deep_dive', 'scenario_design', 'behavioral'],
                'difficulty_level': profile['difficulty_level'],
                'target_source': InterviewSessionManager.normalize_target_source(target_source),
            }
        
        # 合并前端传来的 session_config 覆盖值
        if session_config and isinstance(session_config, dict):
            override_keys = [
                'interview_style', 'interview_round', 'tech_ratio', 'scenario_ratio', 
                'project_deep_dive_percentage', 'behavioral_percentage', 
                'difficulty_low_percentage', 'difficulty_medium_percentage',
                'difficulty_high_percentage', 'is_dynamic_adjust', 'voice_id', 'speech_speed',
                'tone_descriptor', 'enabled_dimensions', 'difficulty_level', 'target_source'
            ]
            for key in override_keys:
                if key in session_config and session_config[key] is not None:
                    payload[key] = session_config[key]
            
            # 特殊处理 enabled_dimensions（如果是字符串则转换为列表）
            if 'enabled_dimensions' in session_config and session_config['enabled_dimensions'] is not None:
                if not isinstance(session_config['enabled_dimensions'], list):
                    payload['enabled_dimensions'] = [
                        item.strip() for item in str(session_config['enabled_dimensions']).split(',') 
                        if item.strip()
                    ]
            
            # 特殊处理 speech_speed（确保是浮点数）
            if 'speech_speed' in session_config and session_config['speech_speed'] is not None:
                payload['speech_speed'] = float(session_config['speech_speed'])

            if 'source' in session_config and session_config['source'] is not None and 'target_source' not in session_config:
                payload['target_source'] = session_config['source']
        
        # 最后，如果明确传入了 voice 参数，优先使用
        if voice:
            payload['voice_id'] = voice
        elif voice_role and not payload.get('voice_id'):
            payload['voice_id'] = voice_role

        payload['target_source'] = InterviewSessionManager.normalize_target_source(payload.get('target_source'))
        
        return payload

    @staticmethod
    def _is_opening_similar(candidate_text, recent_texts, threshold=0.86):
        """判断候选开场白是否与最近开场过于相似。"""
        candidate = (candidate_text or '').strip()
        if not candidate:
            return False

        for old in recent_texts or []:
            old_text = (old or '').strip()
            if not old_text:
                continue
            if candidate == old_text:
                return True

            ratio = SequenceMatcher(None, candidate, old_text).ratio()
            if ratio >= threshold:
                return True

        return False

    @staticmethod
    def _extract_opening_question_text(candidate):
        """从候选题对象/字典中提取可展示的题干文本，避免 `<Question 123>` 这类对象repr泄漏。"""
        if candidate is None:
            return ''

        if isinstance(candidate, str):
            text = candidate.strip()
            return '' if re.fullmatch(r'<[^>]+>', text) else text

        if isinstance(candidate, (int, float, bool)):
            return str(candidate).strip()

        if isinstance(candidate, dict):
            for key in ('content', 'question', 'text', 'title'):
                text = InterviewSessionManager._extract_opening_question_text(candidate.get(key))
                if text:
                    return text
            return ''

        for attr in ('content', 'question', 'text', 'title'):
            if hasattr(candidate, attr):
                text = InterviewSessionManager._extract_opening_question_text(getattr(candidate, attr))
                if text:
                    return text

        fallback = str(candidate).strip()
        return '' if re.fullmatch(r'<[^>]+>', fallback) else fallback

    @staticmethod
    def _is_opening_question_domain_match(job, candidate):
        """开场首问做岗位域校验，避免明显错岗题进入开场。"""
        text = InterviewSessionManager._extract_opening_question_text(candidate)
        if not text:
            return False

        normalized_text = text.lower()
        job_name = (getattr(job, 'name', '') or '').lower()

        # 计算机视觉岗位：显式排除典型网络协议题
        is_cv_job = any(k in job_name for k in ('视觉', 'cv', 'image', 'computer vision'))
        if is_cv_job:
            network_keywords = (
                'arp', 'proxy arp', 'gratuitous arp', 'dhcp', 'dns', 'tcp', 'udp', 'icmp',
                'ip', 'vlan', '子网', '掩码', '网关', '路由', '交换机', 'mac地址', 'osi',
                '证书链', 'root ca', 'ca', 'ssl', 'tls', 'https', 'x.509', 'x509'
            )
            cv_keywords = (
                'opencv', 'cnn', 'yolo', '图像', '视觉', '检测', '分割', '跟踪',
                '特征提取', '标注', 'mAP', 'iou', '推理', '模型'
            )
            has_network = any(k in normalized_text for k in network_keywords)
            has_cv = any(k in normalized_text for k in cv_keywords)
            if has_network and not has_cv:
                return False

        return True

    @staticmethod
    def _pick_opening_seed_question(job, target_source='通用', seed=None):
        """快速挑选岗位匹配的开场首问，避免走重型选题链路。"""
        if not job:
            return ''

        questions_rel = job.questions
        if hasattr(questions_rel, 'filter_by'):
            base_query = questions_rel.filter_by(status='published')
            questions = base_query.limit(240).all()
            if not questions:
                questions = questions_rel.limit(240).all()
        else:
            questions = list(questions_rel or [])
            published = [q for q in questions if getattr(q, 'status', None) == 'published']
            if published:
                questions = published

        if not questions:
            return ''

        normalized_source = InterviewSessionManager.normalize_target_source(target_source)
        generic_sources = {'', '通用'}
        if normalized_source == '通用':
            source_filtered = [
                q for q in questions
                if InterviewSessionManager.normalize_target_source(getattr(q, 'source', None)) in generic_sources
            ]
            if source_filtered:
                questions = source_filtered
        else:
            company = [
                q for q in questions
                if InterviewSessionManager.normalize_target_source(getattr(q, 'source', None)) == normalized_source
            ]
            generic = [
                q for q in questions
                if InterviewSessionManager.normalize_target_source(getattr(q, 'source', None)) in generic_sources
            ]
            if company:
                questions = company + generic
            elif generic:
                questions = generic

        domain_matched = [q for q in questions if InterviewSessionManager._is_opening_question_domain_match(job, q)]
        if domain_matched:
            questions = domain_matched

        type_order = {'technical': 0, 'project_deep_dive': 1, 'scenario_design': 2, 'behavioral': 3}
        questions.sort(key=lambda q: (type_order.get(str(getattr(q, 'type', '')).strip(), 9), int(getattr(q, 'id', 0) or 0)))

        rng = random.Random(int(seed or 0))
        top_window = questions[:24] if len(questions) > 24 else questions
        pool = list(top_window)
        rng.shuffle(pool)
        for q in pool:
            text = InterviewSessionManager._extract_opening_question_text(q)
            if text:
                return text
        return ''

    @staticmethod
    def _default_opening_seed_by_job(job):
        """按岗位给出保底首问，避免错岗和过泛化。"""
        job_name = (getattr(job, 'name', '') or '').lower()
        if any(k in job_name for k in ('视觉', 'cv', 'image', 'computer vision')):
            return "请你挑一个最有代表性的视觉项目，讲讲从数据处理到模型评估你是怎么落地的。"
        if any(k in job_name for k in ('后端', 'backend', 'java', 'golang', 'python')):
            return "请你结合一个后端项目，说明你如何做接口设计、性能优化和异常处理。"
        if any(k in job_name for k in ('前端', 'frontend', 'web', 'vue', 'react')):
            return "请你结合一个前端项目，讲讲你如何做性能优化、状态管理和问题排查。"
        if any(k in job_name for k in ('算法', 'algorithm')):
            return "请你结合一个算法题或算法项目，说明你的建模思路、复杂度分析和优化过程。"
        return "请你结合一个最有代表性的项目，说明你如何完成问题建模、方案选择和效果评估。"

    @staticmethod
    def _build_resume_personalized_opening(resume_data, opening_seed_question, round_focus=''):
        """在大模型超时时，基于简历结构化数据快速生成个性化开场。"""
        content = (resume_data or {}).get('content', {}) if isinstance(resume_data, dict) else {}

        skills = []
        for item in (content.get('skills') or []):
            if isinstance(item, dict):
                name = str(item.get('name', '')).strip()
            else:
                name = str(item or '').strip()
            if name:
                skills.append(name)

        experiences = []
        for exp in (content.get('workExperiences') or []):
            if isinstance(exp, dict):
                org = str(exp.get('company', '')).strip()
                role = str(exp.get('role', '')).strip()
                if org or role:
                    experiences.append((org or '你的团队', role or '相关岗位'))
        for exp in (content.get('internshipExperiences') or []):
            if isinstance(exp, dict):
                org = str(exp.get('company', '')).strip()
                role = str(exp.get('role', '')).strip()
                if org or role:
                    experiences.append((org or '实习团队', role or '实习岗位'))
        for exp in (content.get('campusExperiences') or []):
            if isinstance(exp, dict):
                org = str(exp.get('organization') or exp.get('school') or '').strip()
                role = str(exp.get('role', '')).strip()
                if org or role:
                    experiences.append((org or '校园项目', role or '成员角色'))

        if experiences:
            org, role = experiences[0]
            first_sentence = f"我看你在{org}做过{role}，先从这个项目里你最关键的一次技术决策聊起。"
        elif skills:
            top_skills = '、'.join(skills[:2])
            first_sentence = f"我看过你的简历，先从你写到的{top_skills}里挑一个你做得最深入的项目说起。"
        else:
            first_sentence = "我们直接开始，你先用一个最能代表你水平的项目来展开。"

        seed_question = str(opening_seed_question or '').strip()
        if not seed_question:
            seed_question = "请你结合一个最有代表性的项目，说明你如何完成问题建模、方案选择和效果评估。"
        if not seed_question.rstrip().endswith(('？', '?', '。', '！', '!')):
            seed_question = f"{seed_question}？"

        return f"{first_sentence}{seed_question}"

    @staticmethod
    def _build_opening_candidates(base_greeting, interview_round='first_round', interview_style='confident', round_focus=''):
        """构建多组开场候选，用于去重后挑选。"""
        base_pool = [base_greeting] + InterviewSessionManager._DIVERSE_GREETING_FALLBACKS
        round_key = ROUND_ALIASES.get(str(interview_round).strip().lower() if interview_round is not None else '', 'first_round')
        round_prefix_pool = (
            InterviewSessionManager._ROUND_OPENING_PREFIXES.get(round_key)
            or InterviewSessionManager._ROUND_OPENING_PREFIXES['first_round']
        )
        style = str(interview_style).strip().lower() if interview_style is not None else 'confident'

        style_suffix = InterviewSessionManager._STYLE_OPENING_SUFFIXES.get(
            style, InterviewSessionManager._STYLE_OPENING_SUFFIXES['confident']
        )

        focus_lines = ['']
        if round_focus:
            focus_lines = [
                template.format(focus=round_focus)
                for template in InterviewSessionManager._FOCUS_OPENING_TEMPLATES
            ]

        candidates = []
        for prefix in round_prefix_pool:
            for base_line in base_pool:
                for focus_line in focus_lines:
                    for bridge in InterviewSessionManager._BRIDGE_OPENING_TEMPLATES:
                        candidates.append(f"{prefix}{focus_line}{style_suffix}{bridge}{base_line}")

        return candidates

    @staticmethod
    def _get_recent_opening_texts(user_id, job_id=None, interview_round='first_round', limit=8):
        """读取同用户最近几场开场白，优先同岗位同轮次。"""
        if not user_id:
            return []

        round_key = ROUND_ALIASES.get(str(interview_round).strip().lower() if interview_round is not None else '', 'first_round')

        query = (
            db.session.query(InterviewChat.content)
            .join(Interview, Interview.id == InterviewChat.interview_id)
            .outerjoin(InterviewSessionConfig, InterviewSessionConfig.interview_id == Interview.id)
            .filter(Interview.user_id == user_id)
            .filter(InterviewChat.role == 'ai')
        )
        if job_id:
            query = query.filter(Interview.job_id == job_id)
        if round_key:
            query = query.filter(InterviewSessionConfig.interview_round == round_key)

        rows = (
            query.order_by(InterviewChat.timestamp.desc())
            .limit(max(1, int(limit or 8)))
            .all()
        )
        return [row[0] for row in rows if row and row[0]]

    @staticmethod
    def _pick_non_repetitive_opening(candidates, recent_texts, seed):
        """从候选池选择与历史最不相似的开场。"""
        pool = list(candidates or [])
        if not pool:
            return ''

        random.Random(int(seed or 0)).shuffle(pool)

        best_candidates = []
        best_score = -1.0
        for text in pool:
            max_ratio = 0.0
            for old in recent_texts or []:
                ratio = SequenceMatcher(None, text, (old or '')).ratio()
                if ratio > max_ratio:
                    max_ratio = ratio

            if max_ratio < 0.86:
                best_candidates.append(text)
                continue

            if max_ratio > best_score:
                best_score = max_ratio
                best_candidates = [text]
            elif max_ratio == best_score:
                best_candidates.append(text)

        if best_candidates:
            return random.SystemRandom().choice(best_candidates)

        return random.SystemRandom().choice(pool)
    
    @staticmethod
    def build_fallback_greeting(base_greeting, interview_id, interview_round='first_round', interview_style='confident', round_focus='', user_id=None, job_id=None):
        """无简历场景下给开场白加入多样化，避免每次完全一致。"""
        base_greeting = InterviewSessionManager.align_round_greeting(base_greeting, interview_round)
        base_greeting = InterviewSessionManager.apply_conversational_tone(
            base_greeting,
            interview_style=interview_style,
            voice_mode=True,
        )
        candidates = InterviewSessionManager._build_opening_candidates(
            base_greeting=base_greeting,
            interview_round=interview_round,
            interview_style=interview_style,
            round_focus=round_focus,
        )
        recent_texts = InterviewSessionManager._get_recent_opening_texts(
            user_id=user_id,
            job_id=job_id,
            interview_round=interview_round,
            limit=8,
        )
        picked = InterviewSessionManager._pick_non_repetitive_opening(
            candidates,
            recent_texts,
            seed=interview_id,
        )
        if picked:
            return picked
        fallback_pool = [base_greeting] if base_greeting else []
        fallback_pool.extend(InterviewSessionManager._DIVERSE_GREETING_FALLBACKS)
        idx = int(interview_id or 0) % len(fallback_pool)
        return fallback_pool[idx]
    
    @staticmethod
    def resolve_generation_temperature(prompt_config=None, default_temp=0.85, seed=None):
        """
        基于配置和会话种子计算温度,增加小幅抖动以降低重复问法
        
        Args:
            prompt_config: AI提示词配置
            default_temp: 默认温度值
            seed: 随机种子
            
        Returns:
            float: 最终温度值(0.2-1.2)
        """
        try:
            raw_temp = getattr(prompt_config, 'temperature', None) if prompt_config else None
            base_temp = float(raw_temp) if raw_temp is not None else float(default_temp)
        except Exception:
            base_temp = float(default_temp)
        
        # 限制范围
        base_temp = max(0.2, min(1.2, base_temp))
        
        if seed is None:
            return base_temp
        
        # 添加小幅抖动
        rng = random.Random(int(seed))
        jitter = rng.uniform(-0.08, 0.08)
        return max(0.2, min(1.2, base_temp + jitter))
    
    @staticmethod
    def pick_diverse_questions(assigned_questions, interview_id, round_index, pick_count=2):
        """
        从高分候选题中做受控随机抽样,避免每轮都锁死同一题
        
        Args:
            assigned_questions: 候选题目列表
            interview_id: 面试ID
            round_index: 当前轮次
            pick_count: 抽取数量
            
        Returns:
            list: 抽取的题目列表
        """
        if not assigned_questions:
            return []
        
        top_window = min(len(assigned_questions), max(pick_count + 2, 3))
        pool = list(assigned_questions[:top_window])
        
        # 基于面试ID和轮次的确定性随机
        seed = (int(interview_id or 0) * 131) + (int(round_index or 1) * 17)
        random.Random(seed).shuffle(pool)
        
        return pool[:max(1, pick_count)]
    
    @staticmethod
    def start_interview(user_id, job_id, voice_mode=False, interview_style=None, 
                       voice_role=None, interview_round=None,voice=None, profile_id=None, session_config=None):
        """
        启动一场新的面试会话
        
        流程:
        1. 创建Interview记录
        2. 保存会话配置
        3. 获取提示词配置
        4. 结合简历生成个性化开场白
        5. 异步TTS合成开场白音频
        6. 返回初始化数据
        
        Args:
            user_id: 用户ID
            job_id: 岗位ID
            voice_mode: 是否语音模式
            interview_style: 面试风格
            interview_round: 面试轮次
            voice_role: 语音角色
            voice: 音色名称
            profile_id: 面试套餐ID
            
        Returns:
            dict: 包含interview_id、开场白、音频等的初始化数据
        """
        from app.services.interview_graph_helper import InterviewGraphHelper
        from app.services.interview_tts_helper import InterviewTTSHelper
        
        # 1. 检查简历是否为空
        resume_data = None
        is_resume_empty = True
        try:
            from app.services.resume_service import ResumeService
            resume_data = ResumeService.get_main_resume(user_id)
            content = resume_data.get('content', {})
            skills = content.get('skills', []) if content else []
            if skills:
                is_resume_empty = False
                # 冷启动知识图谱
                InterviewGraphHelper.initialize_user_graph_from_resume(user_id, skills)
        except Exception as e:
            print(f"简历检查失败: {str(e)}")
        
        # 2. 创建面试记录
        interview = Interview(
            user_id=user_id,
            job_id=job_id,
            status='in_progress',
            start_time=datetime.now(),
            question_count=0,
        )
        db.session.add(interview)
        db.session.flush()
        
        # 3. 保存会话配置
        session_payload = InterviewSessionManager.build_session_config_payload(
            voice_mode=voice_mode,
            interview_style=interview_style,
            interview_round=interview_round,
            voice_role=voice_role,
            profile_id=profile_id,
            voice=voice,
            session_config=session_config,
        )
        print('[InterviewDebug][session] session_payload =', session_payload)
        
        # 过滤掉不属于 InterviewSessionConfig 模型的字段
        valid_fields = {
            'profile_id', 'interview_round', 'interview_style', 'tech_ratio', 'scenario_ratio',
            'project_deep_dive_percentage', 'behavioral_percentage',
            'difficulty_low_percentage', 'difficulty_medium_percentage',
            'difficulty_high_percentage', 'is_dynamic_adjust', 'voice_id',
            'speech_speed', 'tone_descriptor', 'enabled_dimensions', 'difficulty_level',
            'target_source'
        }
        config_data = {k: v for k, v in session_payload.items() if k in valid_fields}
        config_data['interview_id'] = interview.id
        print('[InterviewDebug][session] config_data_before_commit =', config_data)
        
        db.session.add(InterviewSessionConfig(**config_data))

        question_plan = InterviewSessionManager.get_interview_question_plan(
            job_id=job_id,
            interview_round=session_payload.get('interview_round', 'first_round'),
            interview_style=session_payload.get('interview_style', 'confident'),
        )

        # 4. 动态获取角色设定与提示词
        prompt_config = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
        round_strategy = InterviewSessionManager.get_round_strategy(
            job_id,
            session_payload.get('interview_round', 'first_round'),
        )
        round_focus = round_strategy.get('focus', '')

        source_options = InterviewSessionManager.get_job_source_options(job_id)
        selected_source = InterviewSessionManager.normalize_target_source(
            session_payload.get('target_source', '通用')
        )
        active_source = selected_source if selected_source in source_options else '通用'

        job = Job.query.get(job_id) if job_id else None
        opening_seed_question = InterviewSessionManager._pick_opening_seed_question(
            job=job,
            target_source=active_source,
            seed=interview.id,
        )

        if not opening_seed_question:
            opening_seed_question = InterviewSessionManager._default_opening_seed_by_job(job)

        round_label_map = {
            'first_round': '一面',
            'second_round': '二面',
            'third_round': '三面',
        }
        round_key = ROUND_ALIASES.get(
            str(session_payload.get('interview_round', 'first_round')).strip().lower(),
            'first_round',
        )
        round_label = round_label_map.get(round_key, '一面')
        job_name = (job.name if job else '目标岗位')
        company_prefix = f"{active_source}·" if active_source != '通用' else ''
        opening_prefix = f"【{company_prefix}{job_name}{round_label}】"
        greeting = (
            f"{opening_prefix}我们开始吧。"
            f"先聊你最有代表性的项目：{opening_seed_question}"
        )
        if not greeting.rstrip().endswith(('？', '?', '。', '！', '!')):
            greeting = f"{greeting}？"

        recent_openings = InterviewSessionManager._get_recent_opening_texts(
            user_id=user_id,
            job_id=job_id,
            interview_round=session_payload.get('interview_round', 'first_round'),
            limit=8,
        )
        deterministic_personalized_greeting = InterviewSessionManager._build_resume_personalized_opening(
            resume_data=resume_data,
            opening_seed_question=opening_seed_question,
            round_focus=round_focus,
        )
        
        # 5. 结合简历生成个性化开场问题（直接提问，不做风格说明）
        tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, voice) if voice_mode else None
        greeting_audio_b64 = None
        opening_generation_timed_out = False
        opening_from_llm = False

        try:
            try:
                resume_context = InterviewGraphHelper.extract_resume_context(user_id, max_chars=420)
                from app.utils.llm_client import DeepSeekClient

                llm = DeepSeekClient()
                company_desc = active_source if active_source != '通用' else '通用题库'
                sys_msg = (
                    f"你是{company_desc}的{job_name}面试官。"
                    f"请输出两句话：第一句自然破冰并提到候选人简历里的真实经历；"
                    f"第二句只提一个首问，并以这道题为准：{opening_seed_question}。"
                    "禁止解释流程、禁止“这轮我会重点看…/最熟悉的实战场景”等模板化表达。"
                    "语气像真人面试官，简洁直接。只输出最终话术。"
                )
                app_obj = current_app._get_current_object()

                greeting_temp = InterviewSessionManager.resolve_generation_temperature(
                    prompt_config=prompt_config,
                    default_temp=0.75,
                    seed=interview.id,
                )

                personalized_greeting = None
                def _generate_opening_question():
                    with app_obj.app_context():
                        return llm.generate_reply(
                            [
                                {'role': 'system', 'content': sys_msg},
                                {'role': 'user', 'content': resume_context or '候选人暂无可用简历摘要。'},
                            ],
                            temperature=greeting_temp,
                            request_timeout=max(
                                2.5,
                                InterviewSessionManager._OPENING_GREETING_WAIT_TIMEOUT_SECONDS - 0.2
                            ),
                            max_retries=1,
                            retry_backoff_seconds=0.0,
                            max_tokens=120,
                        )
                timed_out = False
                response = None
                greeting_executor = ThreadPoolExecutor(max_workers=1)
                future = greeting_executor.submit(_generate_opening_question)
                try:
                    response = future.result(
                        timeout=InterviewSessionManager._OPENING_GREETING_WAIT_TIMEOUT_SECONDS
                    )
                except FutureTimeoutError:
                    timed_out = True
                    opening_generation_timed_out = True
                    future.cancel()
                    print(
                        f"[开场问题生成] 等待超时（{InterviewSessionManager._OPENING_GREETING_WAIT_TIMEOUT_SECONDS:.1f}s），"
                        "直接使用题库兜底问题。"
                    )
                finally:
                    greeting_executor.shutdown(wait=not timed_out, cancel_futures=timed_out)
                personalized_greeting = (response or '').strip()

                if personalized_greeting and len(personalized_greeting) > 8:
                    personalized_greeting = personalized_greeting.replace('[INTERVIEW_OVER]', '').strip()
                    if not personalized_greeting.rstrip().endswith(('？', '?', '。', '！', '!')):
                        personalized_greeting = f"{personalized_greeting}？"
                    if InterviewSessionManager._is_opening_similar(personalized_greeting, recent_openings):
                        if deterministic_personalized_greeting:
                            greeting = f"{opening_prefix}{deterministic_personalized_greeting}"
                        else:
                            greeting = f"{opening_prefix}我们直接进入正题。{opening_seed_question}"
                    else:
                        greeting = f"{opening_prefix}{personalized_greeting}"
                        opening_from_llm = True
            except Exception as e:
                print(f"个性化开场问题生成失败，使用默认问题: {str(e)}")
        except Exception as e:
            print(f"开场问题链路异常，使用默认问题: {str(e)}")

        if not opening_from_llm and deterministic_personalized_greeting:
            greeting = f"{opening_prefix}{deterministic_personalized_greeting}"

        # 6. 仅在语音面试时合成开场白音频
        if voice_mode:
            speak_text = InterviewTTSHelper.strip_stream_control_tokens(greeting)
            if speak_text:
                if opening_generation_timed_out:
                    print("[开场白 TTS] 跳过同步等待：开场问题已超时回退，本次响应不携带开场白音频。")
                    speak_text = ''

            if speak_text:
                def async_tts_task():
                    return InterviewTTSHelper.synthesize_audio_async(
                        speak_text,
                        tts_voice,
                        'mp3'
                    )

                timeout_seconds = max(
                    0.5,
                    max(
                        InterviewSessionManager._OPENING_TTS_WAIT_TIMEOUT_SECONDS,
                        min(20.0, 3.0 + (len(speak_text) * 0.08)),
                    ),
                )
                try:
                    # 开场白与流式回答共用全局队列会互相阻塞，这里使用独立执行器避免排队导致“先超时后成功”。
                    tts_timed_out = False
                    audio_bytes = None
                    opening_tts_executor = ThreadPoolExecutor(max_workers=1)
                    future = opening_tts_executor.submit(async_tts_task)
                    try:
                        audio_bytes = future.result(timeout=timeout_seconds)
                    except FutureTimeoutError:
                        tts_timed_out = True
                        future.cancel()
                        print(
                            f"[开场白 TTS] 等待超时（{timeout_seconds:.1f}s），"
                            "本次响应不携带开场白音频。"
                        )
                    finally:
                        opening_tts_executor.shutdown(wait=not tts_timed_out, cancel_futures=tts_timed_out)
                    if audio_bytes:
                        greeting_audio_b64 = bytes_to_b64(audio_bytes)
                        print(
                            f"[开场白 TTS] {timeout_seconds:.1f}秒内合成成功，"
                            f"音频大小={len(audio_bytes)} bytes"
                        )
                    elif not tts_timed_out:
                        print(f"[开场白 TTS] 合成返回空数据")
                except Exception as e:
                    print(f"[开场白 TTS] 异步合成异常: {type(e).__name__}: {e}")
        
        # 7. 保存开场白到聊天记录
        ai_chat = InterviewChat(
            interview_id=interview.id,
            role='ai',
            content=greeting,
            timestamp=datetime.utcnow(),
        )
        db.session.add(ai_chat)
        db.session.commit()
        
        # 8. 返回初始化数据
        return {
            "interview_id": interview.id,
            "question": greeting,
            "audio_b64": greeting_audio_b64,
            "total_questions": question_plan.get('planned_questions', 10),
            "min_questions": question_plan.get('min_questions', 6),
            "max_questions": question_plan.get('max_questions', 10),
            "session_config": {
                "interview_style": session_payload['interview_style'],
                "interview_round": session_payload['interview_round'],
                "tech_ratio": session_payload['tech_ratio'],
                "scenario_ratio": session_payload['scenario_ratio'],
                "tech_ratio": session_payload['tech_ratio'],
                "scenario_ratio": session_payload['scenario_ratio'],
                "project_deep_dive_percentage": session_payload.get('project_deep_dive_percentage'),
                "behavioral_percentage": session_payload.get('behavioral_percentage'),
                "difficulty_low_percentage": session_payload.get('difficulty_low_percentage'),
                "difficulty_medium_percentage": session_payload.get('difficulty_medium_percentage'),
                "difficulty_high_percentage": session_payload.get('difficulty_high_percentage'),
                "difficulty_level": session_payload['difficulty_level'],
                "target_source": session_payload.get('target_source', '通用'),
            },
            "warning": "请先完善简历以获得更个性化的面试体验" if is_resume_empty else None,
        }
