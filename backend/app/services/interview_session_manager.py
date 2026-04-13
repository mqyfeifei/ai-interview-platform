# backend/app/services/interview_session_manager.py
"""
面试服务 - 会话管理模块
负责面试启动、配置管理、开场白生成等
"""

import random
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewSessionConfig
from app.models.job import Job
from app.models.prompt import AiPrompt
from app.services.tts_service import bytes_to_b64


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
        
        raw_style = (interview_style or '').strip()
        if raw_style:
            normalized = style_aliases.get(raw_style.lower()) or style_aliases.get(raw_style)
            if normalized:
                return normalized
        
        # 兼容旧前端：未传 style 时，仍可从 voice_role 兜底推断
        normalized_role = (voice_role or '').strip().lower()
        role_style_map = {
            'role_strict': 'pressure',
            'role_warm': 'confident',
            'role_calm': 'teaching',
        }
        if normalized_role in role_style_map:
            return role_style_map[normalized_role]
        
        return 'confident'
    
    @staticmethod
    def build_session_config_payload(voice_mode=False, interview_style=None, voice_role=None):
        """
        构建会话配置载荷
        
        Args:
            voice_mode: 是否语音模式
            interview_style: 面试风格
            voice_role: 语音角色
            
        Returns:
            dict: 会话配置字典
        """
        style = InterviewSessionManager.normalize_interview_style(
            voice_mode=voice_mode,
            interview_style=interview_style,
            voice_role=voice_role,
        )
        
        profile_map = {
            'confident': {
                'tech_ratio': 60.0,
                'scenario_ratio': 40.0,
                'difficulty_level': 2,
                'tone_descriptor': 'balanced_confident'
            },
            'teaching': {
                'tech_ratio': 80.0,
                'scenario_ratio': 20.0,
                'difficulty_level': 2,
                'tone_descriptor': 'teaching_guided'
            },
            'pressure': {
                'tech_ratio': 70.0,
                'scenario_ratio': 30.0,
                'difficulty_level': 3,
                'tone_descriptor': 'pressure_challenge'
            }
        }
        profile = profile_map.get(style, profile_map['confident'])
        
        return {
            'interview_style': style,
            'tech_ratio': profile['tech_ratio'],
            'scenario_ratio': profile['scenario_ratio'],
            'is_dynamic_adjust': True,
            'voice_id': voice_role or None,
            'speech_speed': 1.0,
            'tone_descriptor': profile['tone_descriptor'],
            'enabled_dimensions': ['knowledge', 'logic', 'communication'],
            'difficulty_level': profile['difficulty_level'],
        }
    
    @staticmethod
    def build_fallback_greeting(base_greeting, interview_id):
        """
        无简历场景下给开场白加入多样化,避免每次完全一致
        
        Args:
            base_greeting: 基础开场白
            interview_id: 面试ID
            
        Returns:
            str: 多样化的开场白
        """
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
                       voice_role=None, voice=None):
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
            voice_role: 语音角色
            voice: 音色名称
            
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
            voice_role=voice_role,
        )
        db.session.add(InterviewSessionConfig(interview_id=interview.id, **session_payload))
        
        # 4. 动态获取角色设定与提示词
        prompt_config = AiPrompt.query.filter_by(job_id=job_id, is_active=True).first()
        base_greeting = prompt_config.greeting_message if prompt_config else "你好，我们开始面试吧。"
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
                    f"你是一个专业的面试官。请根据候选人简历摘要，结合默认开场白："
                    f"【{base_greeting}】，生成一句自然、友好的个性化开场欢迎语"
                    f"（要求：绝对不要提问，只打招呼并简短提及对方的背景，字数控制在80字左右）。\n\n"
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
                "tech_ratio": session_payload['tech_ratio'],
                "scenario_ratio": session_payload['scenario_ratio'],
                "difficulty_level": session_payload['difficulty_level'],
            },
            "warning": "请先完善简历以获得更个性化的面试体验" if is_resume_empty else None,
        }
