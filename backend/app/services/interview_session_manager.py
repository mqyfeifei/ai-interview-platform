# backend/app/services/interview_session_manager.py
"""
面试服务 - 会话管理模块
负责面试启动、配置管理、开场白生成等
"""

import random
import os
from difflib import SequenceMatcher
from copy import deepcopy
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewSessionConfig, InterviewProfile
from app.models.job import Job
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
    _OPENING_TTS_WAIT_TIMEOUT_SECONDS = float(
        os.environ.get('OPENING_TTS_WAIT_TIMEOUT_SECONDS', '20.0')
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
            '欢迎来到一面，我们先从基础能力热身，逐步进入核心点。',
            '这一轮是一面，我会先看你的基础理解和表达清晰度。',
        ],
        'second_round': [
            '欢迎来到二面，这一轮会更关注项目真实性与系统权衡。',
            '本轮是二面，我会围绕项目决策与方案取舍继续深入。',
        ],
        'third_round': [
            '来到三面了，本轮更看重复杂问题拆解和高压决策。',
            '这一轮是三面，我会重点考察边界条件与综合判断。',
        ],
    }

    _STYLE_OPENING_SUFFIXES = {
        'pressure': '我会追问得更快更深，请你尽量给出结构化且可落地的回答。',
        'confident': '我们保持真实面试节奏，你可以先说结论，再补充关键依据。',
        'teaching': '如果你卡住我会适度引导，但仍会坚持考察核心能力。',
    }

    _FOCUS_OPENING_TEMPLATES = [
        '本轮重点会放在：{focus}。',
        '这一轮我们主要观察：{focus}。',
        '今天这轮我会重点考察：{focus}。',
    ]

    _BRIDGE_OPENING_TEMPLATES = [
        '先从一个短问题热身，再逐步深入。',
        '我们会先看核心思路，再追问落地细节。',
        '先做快速开题，然后进入场景化追问。',
    ]

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
                    'interview_style': profile.interviewer_style or style,
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
            }
        
        # 合并前端传来的 session_config 覆盖值
        if session_config and isinstance(session_config, dict):
            override_keys = [
                'interview_style', 'interview_round', 'tech_ratio', 'scenario_ratio', 
                'project_deep_dive_percentage', 'behavioral_percentage', 
                'difficulty_low_percentage', 'difficulty_medium_percentage',
                'difficulty_high_percentage', 'is_dynamic_adjust', 'voice_id', 'speech_speed',
                'tone_descriptor', 'enabled_dimensions', 'difficulty_level'
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
        
        # 最后，如果明确传入了 voice 参数，优先使用
        if voice:
            payload['voice_id'] = voice
        elif voice_role and not payload.get('voice_id'):
            payload['voice_id'] = voice_role
        
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

        for text in pool:
            if not InterviewSessionManager._is_opening_similar(text, recent_texts):
                return text

        # 如果都相似，退化为选择相似度最低的一条
        best_text = pool[0]
        best_score = 1.0
        for text in pool:
            max_ratio = 0.0
            for old in recent_texts or []:
                ratio = SequenceMatcher(None, text, (old or '')).ratio()
                if ratio > max_ratio:
                    max_ratio = ratio
            if max_ratio < best_score:
                best_score = max_ratio
                best_text = text

        return best_text
    
    @staticmethod
    def build_fallback_greeting(base_greeting, interview_id, interview_round='first_round', interview_style='confident', round_focus='', user_id=None, job_id=None):
        """无简历场景下给开场白加入多样化，避免每次完全一致。"""
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
        fallback_pool = [base_greeting] + InterviewSessionManager._DIVERSE_GREETING_FALLBACKS
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
        
        # 过滤掉不属于 InterviewSessionConfig 模型的字段
        valid_fields = {
            'profile_id', 'interview_round', 'tech_ratio', 'scenario_ratio',
            'project_deep_dive_percentage', 'behavioral_percentage',
            'difficulty_low_percentage', 'difficulty_medium_percentage',
            'difficulty_high_percentage', 'is_dynamic_adjust', 'voice_id',
            'speech_speed', 'tone_descriptor', 'enabled_dimensions', 'difficulty_level'
        }
        config_data = {k: v for k, v in session_payload.items() if k in valid_fields}
        config_data['interview_id'] = interview.id
        
        db.session.add(InterviewSessionConfig(**config_data))

        # 4. 动态获取角色设定与提示词
        prompt_config = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
        base_greeting = prompt_config.greeting_message if prompt_config else "你好，我们开始面试吧。"
        round_strategy = InterviewSessionManager.get_round_strategy(
            job_id,
            session_payload.get('interview_round', 'first_round'),
        )
        round_focus = round_strategy.get('focus', '')
        greeting = InterviewSessionManager.build_fallback_greeting(
            base_greeting,
            interview.id,
            interview_round=session_payload.get('interview_round', 'first_round'),
            interview_style=session_payload.get('interview_style', 'confident'),
            round_focus=round_focus,
            user_id=user_id,
            job_id=job_id,
        )

        recent_openings = InterviewSessionManager._get_recent_opening_texts(
            user_id=user_id,
            job_id=job_id,
            interview_round=session_payload.get('interview_round', 'first_round'),
            limit=8,
        )
        greeting = InterviewSessionManager.build_fallback_greeting(base_greeting, interview.id)
        
        # 5. 结合简历生成个性化开场白
        tts_voice = InterviewTTSHelper.get_tts_voice(prompt_config, voice)
        greeting_audio_b64 = None
        
        if not is_resume_empty:
            try:
                resume_context = InterviewGraphHelper.extract_resume_context(user_id)
                from app.utils.llm_client import DeepSeekClient
                
                llm = DeepSeekClient()
                sys_msg = (
                    f"你是一个专业的面试官。请根据候选人简历摘要，优化开场欢迎语。"
                    f"注意：必须保留轮次和风格导语，不要删除，不要改写核心含义。"
                    f"请在导语后补充一句与候选人背景相关的欢迎语。"
                    f"（要求：绝对不要提问，只打招呼并简短提及对方的背景，字数控制在80字左右）。"
                    f"当前轮次是【{session_payload.get('interview_round', 'first_round')}】，"
                    f"风格是【{session_payload.get('interview_style', 'confident')}】，"
                    f"轮次重点是【{round_focus or '基础能力与表达清晰度'}】。\n\n"
                    f"请基于以下导语进行补充（导语必须原样保留在结果里）：\n"
                    f"【{greeting}】\n\n"
                    f"{resume_context}"
                )
                
                greeting_temp = InterviewSessionManager.resolve_generation_temperature(
                    prompt_config=prompt_config,
                    default_temp=0.9,
                    seed=interview.id,
                )
                
                response = llm.generate_reply([
                    {'role': 'system', 'content': sys_msg},
                ], temperature=greeting_temp)
                
                personalized_greeting = response.strip()
                if personalized_greeting and len(personalized_greeting) > 10:
                    if InterviewSessionManager._is_opening_similar(personalized_greeting, recent_openings):
                        greeting = InterviewSessionManager.build_fallback_greeting(
                            base_greeting,
                            interview.id + 997,
                            interview_round=session_payload.get('interview_round', 'first_round'),
                            interview_style=session_payload.get('interview_style', 'confident'),
                            round_focus=round_focus,
                            user_id=user_id,
                            job_id=job_id,
                        )
                    else:
                        greeting = personalized_greeting
                    greeting = personalized_greeting
            except Exception as e:
                print(f"个性化开场白生成失败，使用默认开场白: {str(e)}")
        
        # 6. 异步TTS合成开场白音频
        speak_text = InterviewTTSHelper.strip_stream_control_tokens(greeting)
        if speak_text:
            def async_tts_task():
                return InterviewTTSHelper.synthesize_audio_async(
                    speak_text,
                    tts_voice,
                    'mp3'
                )

            timeout_seconds = max(0.5, InterviewSessionManager._OPENING_TTS_WAIT_TIMEOUT_SECONDS)
            try:
                # 开场白与流式回答共用全局队列会互相阻塞，这里使用独立执行器避免排队导致“先超时后成功”。
                with ThreadPoolExecutor(max_workers=1) as opening_tts_executor:
                    future = opening_tts_executor.submit(async_tts_task)
                    audio_bytes = future.result(timeout=timeout_seconds)
                if audio_bytes:
                    greeting_audio_b64 = bytes_to_b64(audio_bytes)
                    print(
                        f"[开场白 TTS] {timeout_seconds:.1f}秒内合成成功，"
                        f"音频大小={len(audio_bytes)} bytes"
                    )
                else:
                    print(f"[开场白 TTS] 合成返回空数据")
            except FutureTimeoutError:
                print(
                    f"[开场白 TTS] 等待超时（{timeout_seconds:.1f}s），"
                    "本次响应不携带开场白音频。"
                )
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
            },
            "warning": "请先完善简历以获得更个性化的面试体验" if is_resume_empty else None,
        }
