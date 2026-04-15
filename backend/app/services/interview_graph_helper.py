# backend/app/services/interview_graph_helper.py
"""
面试服务 - 知识图谱辅助模块
负责简历解析、知识点匹配、题目推荐、图谱覆盖率计算等
"""

import re
import math
import threading
from datetime import datetime
from difflib import SequenceMatcher

from app.extensions import db
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.models.question import Question
from app.models.job import Job
from app.models.interview import Interview, InterviewChat
from app.services.resume_service import ResumeService


class InterviewGraphHelper:
    """知识图谱辅助工具类"""

    _RESUME_CONTEXT_CACHE = {}
    _RESUME_CONTEXT_CACHE_LOCK = threading.Lock()

    _QUESTION_TYPES = ['technical', 'project_deep_dive', 'scenario_design', 'behavioral']
    _DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
    
    # === 技能别名映射表 ===
    _SKILL_ALIAS_MAP = {
        'vue3': 'vue',
        'vuejs': 'vue',
        'reactjs': 'react',
        'nodejs': 'node.js',
        'springboot': 'springboot',
        'typescript': 'ts',
    }
    
    # === 技能等级到分数映射 ===
    _SKILL_LEVEL_MAPPING = {
        '精通': 80,
        '熟悉': 60,
        '了解': 45,
        '入门': 30,
        'beginner': 30,
        'familiar': 60,
        'intermediate': 60,
        'proficient': 80,
        'expert': 90,
    }

    # 题型降级优先级（类型不足时按顺序回退）
    _TYPE_FALLBACK_CHAIN = {
        'technical': ['scenario_design', 'project_deep_dive', 'behavioral'],
        'project_deep_dive': ['scenario_design', 'technical', 'behavioral'],
        'scenario_design': ['technical', 'project_deep_dive', 'behavioral'],
        'behavioral': ['project_deep_dive', 'scenario_design', 'technical'],
    }

    _DIFFICULTY_ALIASES = {
        'easy': 'easy',
        'e': 'easy',
        'low': 'easy',
        'junior': 'easy',
        'medium': 'medium',
        'mid': 'medium',
        'm': 'medium',
        'normal': 'medium',
        'hard': 'hard',
        'high': 'hard',
        'h': 'hard',
        'senior': 'hard',
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
    def _is_project_experience_sparse(user_id, resume_context_text=''):
        """判断简历项目经历是否缺失或过于稀疏。"""
        try:
            resume_data = ResumeService.get_main_resume(user_id)
            content = resume_data.get('content', {}) or {}

            projects = content.get('projects', []) or content.get('projectExperiences', []) or []
            works = content.get('workExperiences', []) or []
            interns = content.get('internshipExperiences', []) or []

            # 显式项目优先
            if isinstance(projects, list) and projects:
                joined = ' '.join(
                    [
                        str(item.get('name', '')) + ' ' + str(item.get('description', ''))
                        if isinstance(item, dict) else str(item)
                        for item in projects
                    ]
                ).strip()
                return len(joined) < 30

            # 没有 projects 时，用工作/实习经历文本近似判断
            exp_text = []
            for exp in (works + interns):
                if isinstance(exp, dict):
                    exp_text.append(str(exp.get('description', '') or ''))
                    exp_text.append(str(exp.get('achievements', '') or ''))
                else:
                    exp_text.append(str(exp))
            joined_exp = ' '.join(exp_text).strip()
            if joined_exp:
                return len(joined_exp) < 40

            # 再兜底到摘要文本
            compact = (resume_context_text or '').strip()
            if not compact:
                return True
            if '近期经历' in compact and '未填写' in compact:
                return True
            return len(compact) < 80
        except Exception:
            # 读取简历失败时不做激进判定，避免误伤
            return False

    @staticmethod
    def _is_skill_profile_sparse(user_id, resume_profile=None, resume_context_text=''):
        """判断技能字段是否稀疏，用于基础题优先策略。"""
        try:
            if isinstance(resume_profile, dict):
                skills = resume_profile.get('skills') or []
                if isinstance(skills, list):
                    return len([s for s in skills if str(s).strip()]) <= 2

            resume_data = ResumeService.get_main_resume(user_id)
            content = resume_data.get('content', {}) or {}
            skills = content.get('skills', []) or []
            if isinstance(skills, list):
                meaningful = []
                for item in skills:
                    if isinstance(item, dict):
                        name = str(item.get('name', '')).strip()
                    else:
                        name = str(item).strip()
                    if name:
                        meaningful.append(name)
                return len(meaningful) <= 2

            text = (resume_context_text or '').strip()
            if not text:
                return True
            return '核心技能: 未填写' in text
        except Exception:
            return False

    @staticmethod
    def _is_skill_sparse(user_id, resume_context_text=''):
        """判断简历技能字段是否缺失或过于稀疏。"""
        return InterviewGraphHelper._is_skill_profile_sparse(
            user_id=user_id,
            resume_profile=None,
            resume_context_text=resume_context_text,
        )

    @staticmethod
    def _normalize_difficulty(raw_value):
        """标准化题目难度到 easy/medium/hard。"""
        if raw_value is None:
            return 'medium'
        key = str(raw_value).strip().lower()
        return InterviewGraphHelper._DIFFICULTY_ALIASES.get(key, 'medium')

    @staticmethod
    def _flatten_text_fragments(raw_value):
        """把字符串、列表、字典等值拍平成可读文本片段。"""
        fragments = []

        def _walk(value):
            if value is None:
                return
            if isinstance(value, dict):
                preferred_keys = ('name', 'skill', 'tag', 'title', 'label', 'value', 'keyword', 'text')
                for key in preferred_keys:
                    if value.get(key) is not None:
                        _walk(value.get(key))
                if value.get('skills') is not None:
                    _walk(value.get('skills'))
                if value.get('items') is not None:
                    _walk(value.get('items'))
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    _walk(item)
                return

            text = str(value).strip()
            if text:
                fragments.append(text)

        _walk(raw_value)
        return fragments

    @staticmethod
    def _extract_question_skill_names(question):
        """从题目标签/关键词中提取可用于 GraphRAG 的技能名。"""
        skill_names = []
        seen = set()

        def push(text):
            normalized = str(text or '').strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                skill_names.append(normalized)

        for tag in question.knowledge_tags or []:
            push(tag.name)

        for fragment in InterviewGraphHelper._flatten_text_fragments(question.keywords):
            push(fragment)

        if not skill_names and question.type:
            push(question.type)

        return skill_names[:6]

    @staticmethod
    def _extract_required_skill_names(required_skills_meta):
        """从 required_skills_meta 中抽取技能名列表。"""
        names = []
        seen = set()

        def push(text):
            normalized = str(text or '').strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                names.append(normalized)

        if isinstance(required_skills_meta, dict):
            for key in ('skills', 'items', 'required_skills', 'tags'):
                value = required_skills_meta.get(key)
                if value is not None:
                    for fragment in InterviewGraphHelper._flatten_text_fragments(value):
                        push(fragment)
            if not names:
                for key in ('primary_skill', 'secondary_skill', 'skill', 'name'):
                    if required_skills_meta.get(key) is not None:
                        push(required_skills_meta.get(key))
        else:
            for fragment in InterviewGraphHelper._flatten_text_fragments(required_skills_meta):
                push(fragment)

        return names[:8]

    @staticmethod
    def _infer_reference_answer_depth(question):
        """基于题面、答案要点和题型推断参考答案深度。"""
        reference_answer = question.reference_answer
        answer_fragments = InterviewGraphHelper._flatten_text_fragments(reference_answer)
        answer_text = ' '.join(answer_fragments)
        content_text = f"{question.content or ''} {question.type or ''} {answer_text}".lower()

        depth = 1
        if len(answer_fragments) >= 5 or len(answer_text) >= 260:
            depth = 3
        elif len(answer_fragments) >= 2 or len(answer_text) >= 120:
            depth = 2

        deep_terms = ('原理', '机制', '源码', '性能', '边界', '权衡', '优化', '对比', '复杂度', '架构', '事务', '并发', '一致性', '落地', '扩展')
        medium_terms = ('为什么', '如何', '怎么', '区别', '场景', '方案', '实现', '解释')

        if any(term in content_text for term in deep_terms):
            depth = max(depth, 3)
        elif any(term in content_text for term in medium_terms):
            depth = max(depth, 2)

        q_type = str(question.type or '').strip().lower()
        if q_type in ('project_deep_dive', 'scenario_design'):
            depth = max(depth, 2)
        if q_type == 'technical' and len(answer_fragments) >= 4:
            depth = max(depth, 3)

        return min(3, max(1, depth))

    @staticmethod
    def _infer_required_skills_meta(question, skill_names=None):
        """根据题目标签、关键词和题型生成 required_skills_meta。"""
        names = list(skill_names or [])
        if not names:
            names = InterviewGraphHelper._extract_question_skill_names(question)

        if not names:
            type_fallback = {
                'technical': ['技术原理'],
                'project_deep_dive': ['项目经验'],
                'scenario_design': ['场景分析'],
                'behavioral': ['行为面试'],
            }
            names = type_fallback.get(str(question.type or '').strip().lower(), ['综合能力'])

        weights = []
        total = max(1, len(names))
        for idx, name in enumerate(names[:6]):
            weight = max(0.35, round(1.0 - idx * 0.12, 2))
            weights.append({
                'name': name,
                'weight': weight,
            })

        q_type = str(question.type or '').strip().lower()
        if len(names) <= 2:
            complexity = 'basic'
        elif len(names) <= 4:
            complexity = 'intermediate'
        else:
            complexity = 'advanced'

        if q_type in ('project_deep_dive', 'scenario_design') and len(names) >= 3:
            complexity = 'advanced'
        elif q_type == 'behavioral' and len(names) <= 2:
            complexity = 'basic'

        return {
            'skills': weights,
            'count': len(weights),
            'complexity': complexity,
            'source': 'generated',
        }

    @staticmethod
    def _infer_follow_up_templates(question, reference_answer_depth=None, required_skills_meta=None):
        """根据题目元数据生成二轮/三轮追问链模板。"""
        depth = int(reference_answer_depth or InterviewGraphHelper._infer_reference_answer_depth(question) or 1)
        required_skill_names = InterviewGraphHelper._extract_required_skill_names(required_skills_meta)
        question_skill_names = InterviewGraphHelper._extract_question_skill_names(question)
        base_skill = required_skill_names[0] if required_skill_names else (question_skill_names[0] if question_skill_names else (question.content or '这个知识点'))
        secondary_skill = required_skill_names[1] if len(required_skill_names) > 1 else (question_skill_names[1] if len(question_skill_names) > 1 else '')

        templates = []

        templates.append({
            'step': 1,
            'rounds': ['first_round', 'second_round', 'third_round'],
            'focus': 'core_concept',
            'prompt': f'先说说{base_skill}的核心作用、基本原理和适用场景。',
        })

        if depth >= 2:
            templates.append({
                'step': 2,
                'rounds': ['second_round', 'third_round'],
                'focus': 'implementation',
                'prompt': f'如果把{base_skill}放到真实业务里，你会怎么落地实现，和{secondary_skill or "相关概念"}怎么配合？',
            })

        if depth >= 3:
            templates.append({
                'step': 3,
                'rounds': ['third_round'],
                'focus': 'boundary_and_tradeoff',
                'prompt': f'再往下追一层，{base_skill}在边界条件、性能瓶颈或并发场景下会遇到什么问题，你会怎么权衡和优化？',
            })

        if not templates:
            templates.append({
                'step': 1,
                'rounds': ['first_round', 'second_round', 'third_round'],
                'focus': 'core_concept',
                'prompt': f'请围绕{base_skill}说明你的理解。',
            })

        return templates

    @staticmethod
    def build_question_graph_meta(question):
        """为题目生成可复用的 GraphRAG 元数据。"""
        question_skill_names = InterviewGraphHelper._extract_question_skill_names(question)
        reference_answer_depth = question.reference_answer_depth or InterviewGraphHelper._infer_reference_answer_depth(question)
        required_skills_meta = question.required_skills_meta or InterviewGraphHelper._infer_required_skills_meta(question, question_skill_names)
        follow_up_templates = question.follow_up_templates or InterviewGraphHelper._infer_follow_up_templates(
            question,
            reference_answer_depth=reference_answer_depth,
            required_skills_meta=required_skills_meta,
        )

        return {
            'reference_answer_depth': int(reference_answer_depth or 1),
            'required_skills_meta': required_skills_meta,
            'follow_up_templates': follow_up_templates,
            'skill_names': question_skill_names,
        }

    @staticmethod
    def build_follow_up_chain_context(question, interview_round='first_round', interview_style='confident', max_items=3):
        """把题目的追问模板整理成可直接塞进提示词的文本。"""
        if not question:
            return ''

        meta = InterviewGraphHelper.build_question_graph_meta(question)
        templates = meta.get('follow_up_templates') or []
        round_key = str(interview_round).strip().lower() if interview_round is not None else 'first_round'

        formatted_lines = []
        for template in templates:
            if not isinstance(template, dict):
                prompt = str(template).strip()
                if prompt:
                    formatted_lines.append(prompt)
                continue

            rounds = template.get('rounds') or []
            if rounds and round_key not in rounds:
                continue

            prompt = str(template.get('prompt') or '').strip()
            if not prompt:
                continue

            focus = str(template.get('focus') or '').strip()
            if focus:
                formatted_lines.append(f"- {prompt}（{focus}）")
            else:
                formatted_lines.append(f"- {prompt}")

            if len(formatted_lines) >= max(1, int(max_items or 3)):
                break

        if not formatted_lines:
            return ''

        style_hint = {
            'pressure': '追问时更直接，少铺垫，优先追根究底。',
            'teaching': '追问时先解释半句，再一步步引导。',
            'confident': '追问时保持自然、均衡。',
        }.get(str(interview_style or '').strip().lower(), '追问时保持自然、均衡。')

        return f"追问链模板（{style_hint}）:\n" + '\n'.join(formatted_lines)

    @staticmethod
    def _compute_target_counts(limit, ratio_map, ordered_keys):
        """按比例计算目标数量，保证总和严格等于 limit。"""
        safe_limit = max(0, int(limit or 0))
        if safe_limit <= 0:
            return {k: 0 for k in ordered_keys}

        raw_targets = {k: float(ratio_map.get(k, 0.0) or 0.0) * safe_limit for k in ordered_keys}
        counts = {k: int(math.floor(raw_targets[k])) for k in ordered_keys}
        remained = safe_limit - sum(counts.values())
        if remained > 0:
            residues = sorted(
                ordered_keys,
                key=lambda key: (raw_targets[key] - counts[key], raw_targets[key]),
                reverse=True,
            )
            for idx in range(remained):
                counts[residues[idx % len(residues)]] += 1
        return counts

    @staticmethod
    def _resolve_job_role_key(job):
        """将岗位名称映射到策略岗位类型键，便于可观测输出。"""
        if not job:
            return 'default'

        name = str(getattr(job, 'name', '') or '').strip().lower()
        if not name:
            return 'default'

        if any(k in name for k in ('后端', 'backend', 'java', 'golang', 'python')):
            return 'backend'
        if any(k in name for k in ('前端', 'frontend', 'web', 'vue', 'react')):
            return 'frontend'
        if any(k in name for k in ('算法', 'algorithm', '机器学习', '视觉', 'cv')):
            return 'algorithm'
        if any(k in name for k in ('测试', 'qa', 'quality')):
            return 'qa'
        if any(k in name for k in ('网络', 'network', '运维', 'devops', 'sre')):
            return 'network'
        return 'default'

    @staticmethod
    def _get_tag_depth(tag):
        """计算知识点在图谱中的深度。"""
        depth = 1
        visited = set()
        current = tag
        while current and current.parent_id and current.parent_id not in visited:
            visited.add(current.id)
            current = KnowledgeTag.query.get(current.parent_id)
            if current:
                depth += 1
        return depth

    @staticmethod
    def _build_graph_rag_signals(tag_map, mastery_map, interview_round='first_round', interview_style='confident', recent_tag_ids=None, dynamic_adjust=True):
        """构建 GraphRAG 选题信号：弱节点、前沿节点与标签分数。"""
        normalized_round = interview_round
        round_key = str(interview_round).strip().lower() if interview_round is not None else ''
        if round_key not in ('first_round', 'second_round', 'third_round'):
            normalized_round = 'first_round'

        style_key = str(interview_style).strip().lower() if interview_style is not None else 'confident'
        if style_key not in ('pressure', 'confident', 'teaching'):
            style_key = 'confident'

        route_mode_map = {
            'first_round': 'root',
            'second_round': 'adjacent',
            'third_round': 'bridge',
        }
        route_mode = route_mode_map.get(normalized_round, 'root')

        if not dynamic_adjust or not tag_map:
            return {
                'round_key': normalized_round,
                'weak_tag_ids': set(),
                'frontier_tag_ids': set(),
                'strong_tag_ids': set(),
                'tag_depth_map': {},
                'tag_boost_map': {},
                'route_mode': route_mode,
                'route_tag_ids': set(),
                'adjustments': [],
            }

        weak_threshold_map = {
            'first_round': 55,
            'second_round': 60,
            'third_round': 65,
        }
        weak_bonus_map = {
            'first_round': 14.0,
            'second_round': 12.0,
            'third_round': 10.0,
        }
        frontier_bonus_map = {
            'first_round': 8.0,
            'second_round': 10.0,
            'third_round': 12.0,
        }
        bridge_bonus_map = {
            'first_round': 1.0,
            'second_round': 2.5,
            'third_round': 4.0,
        }

        weak_threshold = weak_threshold_map.get(normalized_round, 55)
        weak_bonus = weak_bonus_map.get(normalized_round, 12.0)
        frontier_bonus = frontier_bonus_map.get(normalized_round, 8.0)
        bridge_bonus = bridge_bonus_map.get(normalized_round, 1.0)

        style_bonus_map = {
            'pressure': {
                'weak_bonus_delta': 4.0,
                'frontier_bonus_delta': -1.0,
                'bridge_bonus_delta': 2.0,
            },
            'confident': {
                'weak_bonus_delta': 0.0,
                'frontier_bonus_delta': 0.0,
                'bridge_bonus_delta': 0.0,
            },
            'teaching': {
                'weak_bonus_delta': -2.0,
                'frontier_bonus_delta': 3.0,
                'bridge_bonus_delta': -1.5,
            },
        }
        style_bonus = style_bonus_map.get(style_key, style_bonus_map['confident'])

        weak_bonus += style_bonus['weak_bonus_delta']
        frontier_bonus += style_bonus['frontier_bonus_delta']
        bridge_bonus += style_bonus['bridge_bonus_delta']

        recent_tag_ids = set(recent_tag_ids or [])
        tag_depth_map = {}
        weak_tag_ids = set()
        frontier_tag_ids = set()
        strong_tag_ids = set()
        route_tag_ids = set()

        for tag_id, tag in tag_map.items():
            mastery = float(mastery_map.get(tag_id, 0) or 0)
            tag_depth_map[tag_id] = InterviewGraphHelper._get_tag_depth(tag)
            if mastery <= 0 or mastery < weak_threshold:
                weak_tag_ids.add(tag_id)
            elif mastery >= 75:
                strong_tag_ids.add(tag_id)

        for tag_id in list(weak_tag_ids):
            tag = tag_map.get(tag_id)
            if not tag:
                continue
            if tag.parent_id and tag.parent_id in tag_map:
                frontier_tag_ids.add(tag.parent_id)
            for child in tag.children or []:
                if child.id in tag_map:
                    frontier_tag_ids.add(child.id)

        if normalized_round in ('second_round', 'third_round'):
            for tag_id in strong_tag_ids:
                tag = tag_map.get(tag_id)
                if not tag:
                    continue
                for child in tag.children or []:
                    if child.id in tag_map:
                        frontier_tag_ids.add(child.id)

        if normalized_round == 'third_round':
            # 三面更适合跨节点综合判断：把弱节点的兄弟/下游节点也纳入前沿
            for tag_id, tag in tag_map.items():
                if tag.parent_id and tag.parent_id in weak_tag_ids:
                    frontier_tag_ids.add(tag_id)

        # 轮次推进路线：一面看根节点，二面看邻接节点，三面看桥接/组合节点
        for tag_id, tag in tag_map.items():
            depth = tag_depth_map.get(tag_id, 1)
            if route_mode == 'root' and depth <= 2:
                route_tag_ids.add(tag_id)
            elif route_mode == 'adjacent' and (tag_id in frontier_tag_ids or depth == 2):
                route_tag_ids.add(tag_id)
            elif route_mode == 'bridge' and (depth >= 2 or len(getattr(tag, 'children', []) or []) > 0):
                route_tag_ids.add(tag_id)

        if style_key == 'pressure':
            route_tag_ids.update(weak_tag_ids)
            route_tag_ids.update(frontier_tag_ids)
        elif style_key == 'teaching':
            route_tag_ids.update(frontier_tag_ids)
            route_tag_ids.update(tag_id for tag_id, depth in tag_depth_map.items() if depth <= 2)

        tag_boost_map = {}
        for tag_id, tag in tag_map.items():
            mastery = float(mastery_map.get(tag_id, 0) or 0)
            depth = tag_depth_map.get(tag_id, 1)
            boost = 0.0

            if tag_id in weak_tag_ids:
                boost += weak_bonus
                boost += max(0.0, (weak_threshold - mastery) * 0.25)

            if tag_id in frontier_tag_ids:
                boost += frontier_bonus

            if tag_id in route_tag_ids:
                boost += 3.0

            if style_key == 'pressure':
                if tag_id in weak_tag_ids:
                    boost += 3.0
                if depth >= 3:
                    boost += 2.0
            elif style_key == 'teaching':
                if depth <= 2:
                    boost += 3.0
                if tag_id in frontier_tag_ids:
                    boost += 1.5
                if depth >= 3:
                    boost -= 2.0
            else:
                if depth == 2:
                    boost += 1.0

            if normalized_round == 'third_round' and depth >= 3:
                boost += 2.0

            if normalized_round == 'second_round' and depth >= 2:
                boost += 1.0

            if tag_id in recent_tag_ids:
                boost -= 10.0

            tag_boost_map[tag_id] = boost

        adjustments = []
        if weak_tag_ids:
            adjustments.append({
                'rule': 'graph_weak_nodes',
                'count': len(weak_tag_ids),
                'reason': f'优先覆盖掌握度低于 {weak_threshold} 的图谱节点',
            })
        if frontier_tag_ids:
            adjustments.append({
                'rule': 'graph_frontier_nodes',
                'count': len(frontier_tag_ids),
                'reason': '优先沿弱节点的父子邻接边向外扩展',
            })
        if normalized_round == 'third_round':
            adjustments.append({
                'rule': 'graph_bridge_third_round',
                'reason': '三面偏向跨节点综合判断与深层追问',
            })
        adjustments.append({
            'rule': 'graph_style_route',
            'style': style_key,
            'reason': '风格会改变图谱检索偏好：pressure 偏弱点与组合题，teaching 偏基础与邻接，confident 保持均衡',
        })
        adjustments.append({
            'rule': 'graph_round_route',
            'route_mode': route_mode,
            'reason': '按轮次推进路线引导选题：一面根节点，二面邻接节点，三面桥接组合题',
        })

        return {
            'round_key': normalized_round,
            'style_key': style_key,
            'route_mode': route_mode,
            'weak_tag_ids': weak_tag_ids,
            'frontier_tag_ids': frontier_tag_ids,
            'strong_tag_ids': strong_tag_ids,
            'route_tag_ids': route_tag_ids,
            'tag_depth_map': tag_depth_map,
            'tag_boost_map': tag_boost_map,
            'adjustments': adjustments,
        }
    
    @staticmethod
    def normalize_tag_name(name):
        """
        标准化标签名称(去除空格、标点、大小写统一)
        
        Args:
            name: 原始标签名
            
        Returns:
            str: 标准化后的标签名
        """
        text = (name or '').strip().lower()
        text = re.sub(r'[\s\-_()（）\[\]【】,.，。/\\]+', '', text)
        return text
    
    @staticmethod
    def skill_level_to_score(skill_item):
        """
        将技能等级转换为分数
        
        Args:
            skill_item: 技能项(可以是字典或字符串)
            
        Returns:
            int: 对应的分数(0-100)
        """
        if isinstance(skill_item, dict):
            # 从字典中提取等级字段
            for key in ('mastery', 'mastery_level', 'score', 'level', 'proficiency'):
                if skill_item.get(key) is not None:
                    raw_value = skill_item.get(key)
                    break
            else:
                raw_value = None
            
            if isinstance(raw_value, (int, float)):
                return int(raw_value)
            
            text = str(raw_value or '').strip().lower()
        else:
            text = str(skill_item or '').strip().lower()
        
        return InterviewGraphHelper._SKILL_LEVEL_MAPPING.get(text, 60)
    
    @staticmethod
    def extract_resume_context(user_id, max_chars=800):
        """
        拉取并解析用户主简历,进行去敏与核心要点抽取
        
        Args:
            user_id: 用户ID
            max_chars: 最大字符数限制
            
        Returns:
            str: 简历摘要文本
        """
        try:
            resume_data = ResumeService.get_main_resume(user_id)
            resume_updated_at = (
                resume_data.get('updatedAt')
                or resume_data.get('updated_at')
                or resume_data.get('createdAt')
                or resume_data.get('created_at')
                or ''
            )
            cache_key = (int(user_id or 0), str(resume_updated_at))

            with InterviewGraphHelper._RESUME_CONTEXT_CACHE_LOCK:
                cached_summary = InterviewGraphHelper._RESUME_CONTEXT_CACHE.get(cache_key)
            if cached_summary is not None:
                return cached_summary[:max_chars]

            content = resume_data.get('content', {})
            if not content:
                return ""
            
            # 1. 基础信息去敏(禁止加入手机号和邮箱)
            personal = content.get('personal', {})
            name = personal.get('name', '候选人')
            
            # 2. 技能抽取(Top-10)
            skills_list = content.get('skills', [])
            skills_names = [s.get('name', '') for s in skills_list if s.get('name')]
            skills_str = "、".join(skills_names[:10])
            
            # 3. 合并工作、实习、校园经历
            works = content.get('workExperiences', [])
            interns = content.get('internshipExperiences', [])
            campus = content.get('campusExperiences', [])
            all_exps = []
            
            for w in works:
                all_exps.append({
                    'org': w.get('company', '某公司'),
                    'role': w.get('role', '某职位'),
                    'period': f"{w.get('startDate', '')} 至 {w.get('endDate', '')}",
                    'desc': w.get('description', '')
                })
            for i in interns:
                all_exps.append({
                    'org': i.get('company', '某公司'),
                    'role': i.get('role', '实习生'),
                    'period': f"{i.get('startDate', '')} 至 {i.get('endDate', '')}",
                    'desc': i.get('description', '')
                })
            for c in campus:
                org_name = c.get('school') or c.get('organization') or '某学校/组织'
                all_exps.append({
                    'org': org_name,
                    'role': c.get('role', '成员'),
                    'period': f"{c.get('startDate', '')} 至 {c.get('endDate', '')}",
                    'desc': c.get('description', '')
                })
            
            # 取最前面的3条经历
            work_context = ""
            for exp in all_exps[:3]:
                desc = exp['desc'].replace('\n', ' ')[:100] if exp['desc'] else ''
                work_context += f"- {exp['org']} | {exp['role']} ({exp['period']})\n  核心职责/成就: {desc}...\n"
            
            # 4. 组装简历摘要模块
            resume_text = f"""
            【候选人简历摘要】
            - 姓名: {name}
            - 核心技能: {skills_str if skills_str else '未填写'}
            - 近期经历:
            {work_context if work_context else '未填写'}
            """
            
            # 5. 安全硬截断
            resume_text = resume_text.strip()
            with InterviewGraphHelper._RESUME_CONTEXT_CACHE_LOCK:
                InterviewGraphHelper._RESUME_CONTEXT_CACHE[cache_key] = resume_text
            return resume_text[:max_chars]
        
        except Exception as e:
            print(f"简历摘要提取失败: {str(e)}")
            return ""
    
    @staticmethod
    def align_resume_entities(resume_skills_list):
        """
        根据简历技能对用户知识图谱进行实体对齐
        
        策略:
        1. 精确匹配
        2. 别名匹配
        3. 模糊匹配(SequenceMatcher)
        4. 向量相似度匹配(兜底)
        
        Args:
            resume_skills_list: 简历中的技能列表
            
        Returns:
            list: 对齐后的实体列表
        """
        if not resume_skills_list:
            return []
        
        all_tags = KnowledgeTag.query.all()
        if not all_tags:
            return []
        
        aligned = []
        for skill in resume_skills_list:
            if isinstance(skill, dict):
                raw_name_val = skill.get('name') or skill.get('skill') or skill.get('tag')
                raw_name = str(raw_name_val).strip() if raw_name_val is not None else ''
            else:
                raw_name = str(skill).strip()

            if not raw_name:
                continue
            
            normalized = InterviewGraphHelper.normalize_tag_name(raw_name)
            alias = InterviewGraphHelper._SKILL_ALIAS_MAP.get(normalized, normalized)
            
            matched_tag = None
            best_score = 0.0
            
            # 遍历所有标签进行匹配
            for tag in all_tags:
                candidate = InterviewGraphHelper.normalize_tag_name(tag.name)
                score = 0.0
                
                # 精确匹配
                if candidate == alias or candidate == normalized:
                    score = 1.0
                # 包含关系匹配
                elif alias and (alias in candidate or candidate in alias):
                    score = 0.9
                # 模糊匹配
                else:
                    score = SequenceMatcher(None, alias, candidate).ratio()
                
                if score > best_score:
                    best_score = score
                    matched_tag = tag
            
            # 如果模糊匹配失败,尝试向量匹配
            if not matched_tag or best_score < 0.35:
                try:
                    from app.services.interview_service import InterviewService
                    vec = InterviewService.get_embedding(raw_name)
                    matched_tag = KnowledgeTag.query.order_by(
                        KnowledgeTag.embedding.l2_distance(vec)
                    ).first()
                    best_score = max(best_score, 0.5 if matched_tag else 0.0)
                except Exception:
                    matched_tag = None
            
            if not matched_tag:
                continue
            
            aligned.append({
                'raw_name': raw_name,
                'tag': matched_tag,
                'matched_by': 'alias_or_fuzzy' if best_score < 1.0 else 'exact',
                'mastery_level': InterviewGraphHelper.skill_level_to_score(skill),
            })
        
        return aligned
    
    @staticmethod
    def initialize_user_graph_from_resume(user_id, resume_skills_list, base_score=60):
        """
        根据简历技能对用户知识图谱进行冷启动初始化
        
        Args:
            user_id: 用户ID
            resume_skills_list: 简历技能列表
            base_score: 基础分数(默认60)
        """
        if not resume_skills_list:
            return
        
        aligned_entities = InterviewGraphHelper.align_resume_entities(resume_skills_list)
        if not aligned_entities:
            return
        
        for entity in aligned_entities:
            tag = entity['tag']
            score = max(base_score, entity['mastery_level'])
            
            mastery = UserKnowledgeMastery.query.filter_by(
                user_id=user_id, tag_id=tag.id
            ).first()
            
            if not mastery:
                db.session.add(
                    UserKnowledgeMastery(
                        user_id=user_id,
                        tag_id=tag.id,
                        mastery_level=score,
                        last_updated=datetime.utcnow()
                    )
                )
            else:
                mastery.mastery_level = max(mastery.mastery_level or 0, score)
                mastery.last_updated = datetime.utcnow()
    
    @staticmethod
    def get_job_graph_snapshot(job_id):
        """
        获取岗位的知识图谱快照(题目+标签)
        
        Args:
            job_id: 岗位ID
            
        Returns:
            tuple: (questions列表, tag_map字典)
        """
        job = db.session.get(Job, int(job_id)) if job_id is not None else None
        if not job:
            return [], {}
        
        # 获取已发布的题目
        questions_rel = job.questions
        if hasattr(questions_rel, 'filter_by'):
            questions = questions_rel.filter_by(status='published').all()
            if not questions:
                questions = questions_rel.all()
        else:
            questions = list(questions_rel or [])
            published_questions = [q for q in questions if getattr(q, 'status', None) == 'published']
            if published_questions:
                questions = published_questions
        
        # 收集所有相关标签
        tags_rel = job.knowledge_tags
        if hasattr(tags_rel, 'all'):
            job_tags = tags_rel.all()
        else:
            job_tags = list(tags_rel or [])
        
        tag_map = {}
        for tag in job_tags:
            tag_map[tag.id] = tag
        for question in questions:
            for tag in question.knowledge_tags:
                tag_map[tag.id] = tag
        
        return questions, tag_map
    
    @staticmethod
    def estimate_target_depth(mastery_level):
        """
        根据掌握度估算目标深度
        
        Args:
            mastery_level: 掌握度分数(0-100)
            
        Returns:
            int: 目标深度(1-3)
        """
        if mastery_level >= 75:
            return 3
        if mastery_level >= 45:
            return 2
        return 1
    
    @staticmethod
    def assign_questions(job_id, user_id, limit=5, recent_tag_ids=None, interview_round='first_round', interview_style='confident', target_source='通用', resume_profile=None, is_dynamic_adjust=True):
        """
        为用户智能分配面试题目（轮次策略驱动）
        
        分发策略:
        1. 根据岗位与轮次加载 target_mix / focus
        2. 按类型分桶计算目标数量
        3. 在岗位图谱题池中按分数选题
        4. 某类型不足时按降级链路回退并记录明细
        
        Args:
            job_id: 岗位ID
            user_id: 用户ID
            limit: 返回题目数量
            recent_tag_ids: 最近提问的标签ID列表
            interview_round: 面试轮次(first_round/second_round/third_round)
            
        Returns:
            dict: {
                interview_round: str,
                interview_style: str,
                job_role: str,
                is_dynamic_adjust: bool,
                selected_questions: list,
                selected_questions_meta: list,
                fallback_applied: bool,
                fallback_detail: list,
                round_focus: str,
            }
        """
        from app.services.interview_session_manager import InterviewSessionManager, ROUND_ALIASES

        job = db.session.get(Job, int(job_id)) if job_id is not None else None
        job_role = InterviewGraphHelper._resolve_job_role_key(job)
        questions, tag_map = InterviewGraphHelper.get_job_graph_snapshot(job_id)

        strategy = InterviewSessionManager.get_round_strategy(job_id, interview_round)
        normalized_round = ROUND_ALIASES.get(
            str(interview_round).strip().lower() if interview_round is not None else '',
            'first_round',
        )
        normalized_source = InterviewGraphHelper.normalize_target_source(target_source)
        if questions:
            generic_sources = {'', '通用'}
            if normalized_source == '通用':
                generic_questions = [
                    q for q in questions
                    if InterviewGraphHelper.normalize_target_source(getattr(q, 'source', None)) in generic_sources
                ]
                if generic_questions:
                    questions = generic_questions
            else:
                company_questions = [
                    q for q in questions
                    if InterviewGraphHelper.normalize_target_source(getattr(q, 'source', None)) == normalized_source
                ]
                generic_questions = [
                    q for q in questions
                    if InterviewGraphHelper.normalize_target_source(getattr(q, 'source', None)) in generic_sources
                ]
                if company_questions:
                    seen_ids = set()
                    merged = []
                    for q in company_questions + generic_questions:
                        if q.id not in seen_ids:
                            seen_ids.add(q.id)
                            merged.append(q)
                    questions = merged
                elif generic_questions:
                    questions = generic_questions
        target_mix = dict(strategy.get('target_mix') or {})
        target_difficulty = dict(strategy.get('difficulty') or {})
        round_focus = strategy.get('focus', '')
        style = str(interview_style or 'confident').strip().lower() or 'confident'
        dynamic_adjust = bool(is_dynamic_adjust)

        for level in InterviewGraphHelper._DIFFICULTY_LEVELS:
            target_difficulty.setdefault(level, 0.0)

        strategy_adjustments = []

        if not questions or limit <= 0:
            return {
                'interview_round': normalized_round,
                'interview_style': style,
                'job_role': job_role,
                'is_dynamic_adjust': dynamic_adjust,
                'selected_questions': [],
                'selected_questions_meta': [],
                'question_mix': {
                    'target': {},
                    'actual': {},
                },
                'difficulty_mix': {
                    'target': {},
                    'actual': {},
                },
                'fallback_applied': False,
                'fallback_detail': [],
                'strategy_adjustments': strategy_adjustments,
                'round_focus': round_focus,
            }

        # 保障四类题型键存在
        type_order = list(InterviewGraphHelper._QUESTION_TYPES)
        for q_type in type_order:
            target_mix.setdefault(q_type, 0.0)

        resume_context = ''
        skill_sparse = False
        if dynamic_adjust:
            # 阶段三：简历感知前置拦截
            # 若项目经历缺失/稀疏，则将 project_deep_dive 权重按 6:4 分配给 scenario_design/technical。
            resume_context = InterviewGraphHelper.extract_resume_context(user_id)
            project_ratio = float(target_mix.get('project_deep_dive', 0.0) or 0.0)
            if project_ratio > 0 and InterviewGraphHelper._is_project_experience_sparse(user_id, resume_context):
                target_mix['project_deep_dive'] = 0.0
                target_mix['scenario_design'] = float(target_mix.get('scenario_design', 0.0)) + project_ratio * 0.6
                target_mix['technical'] = float(target_mix.get('technical', 0.0)) + project_ratio * 0.4
                strategy_adjustments.append({
                    'rule': 'project_experience_sparse',
                    'from': 'project_deep_dive',
                    'to': {'scenario_design': round(project_ratio * 0.6, 4), 'technical': round(project_ratio * 0.4, 4)},
                    'reason': '项目经历缺失/稀疏，按规则转移配比',
                })

                # 归一化，避免浮点叠加后总和偏离1
                total = sum(float(target_mix.get(k, 0.0) or 0.0) for k in type_order)
                if total > 0:
                    for k in type_order:
                        target_mix[k] = float(target_mix.get(k, 0.0) or 0.0) / total

            skill_sparse = InterviewGraphHelper._is_skill_sparse(user_id, resume_context)
            if skill_sparse:
                # 技能稀疏时：降低 hard 题配额，并将一部分权重转到 easy / medium
                hard_ratio = float(target_difficulty.get('hard', 0.0) or 0.0)
                if hard_ratio > 0:
                    target_difficulty['hard'] = 0.0
                    target_difficulty['easy'] = float(target_difficulty.get('easy', 0.0) or 0.0) + hard_ratio * 0.7
                    target_difficulty['medium'] = float(target_difficulty.get('medium', 0.0) or 0.0) + hard_ratio * 0.3

                # 同时压低场景题，补充基础技术题和行为题
                scenario_ratio = float(target_mix.get('scenario_design', 0.0) or 0.0)
                if scenario_ratio > 0.15:
                    transfer_amount = scenario_ratio - 0.15
                    target_mix['scenario_design'] = 0.15
                    target_mix['technical'] = float(target_mix.get('technical', 0.0) or 0.0) + transfer_amount * 0.7
                    target_mix['behavioral'] = float(target_mix.get('behavioral', 0.0) or 0.0) + transfer_amount * 0.3

                strategy_adjustments.append({
                    'rule': 'skills_sparse',
                    'reason': '技能字段稀疏，降低 hard 题并补强 technical / behavioral',
                })

            # 阶段 C：矩阵归一化（防止浮点溢出，确保权重加和严格为 1）
            total_target = sum(float(v or 0.0) for v in target_mix.values())
            if total_target > 0:
                target_mix = {k: float(v or 0.0) / total_target for k, v in target_mix.items()}

            total_diff = sum(float(v or 0.0) for v in target_difficulty.values())
            if total_diff > 0:
                target_difficulty = {k: float(v or 0.0) / total_diff for k, v in target_difficulty.items()}

            if not skill_sparse:
                # 保持与默认策略一致的行为，不做额外动态修正
                pass
        recent_tag_ids = set(recent_tag_ids or [])
        resume_skill_names = set()
        if dynamic_adjust:
            try:
                resume_data = ResumeService.get_main_resume(user_id)
                resume_content = resume_data.get('content', {}) or {}
                resume_skills = resume_content.get('skills', []) or []
                for skill_item in resume_skills:
                    if isinstance(skill_item, dict):
                        skill_name = skill_item.get('name') or skill_item.get('skill') or skill_item.get('tag')
                    else:
                        skill_name = skill_item
                    skill_name = str(skill_name or '').strip()
                    if skill_name:
                        resume_skill_names.add(InterviewGraphHelper.normalize_tag_name(skill_name))
            except Exception:
                resume_skill_names = set()

        recent_question_ids = set(
            InterviewGraphHelper.get_recent_asked_question_ids(
                user_id=user_id,
                job_id=job_id,
                lookback_limit=max(30, int(limit) * 8),
            )
        )

        # 获取用户对各标签的掌握度
        mastery_rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == user_id,
            UserKnowledgeMastery.tag_id.in_(list(tag_map.keys()) or [0])
        ).all() if tag_map else []
        mastery_map = {row.tag_id: row.mastery_level or 0 for row in mastery_rows}

        graph_signals = InterviewGraphHelper._build_graph_rag_signals(
            tag_map=tag_map,
            mastery_map=mastery_map,
            interview_round=interview_round,
            interview_style=style,
            recent_tag_ids=recent_tag_ids,
            dynamic_adjust=dynamic_adjust,
        )
        strategy_adjustments.extend(graph_signals.get('adjustments', []))
        
        # 为每个题目计算综合得分并按类型分桶
        by_type = {k: [] for k in type_order}
        ranked = []
        preferred_questions = [q for q in questions if q.id not in recent_question_ids]
        # 优先严格避开近期已问过的题目；只有完全没有新题时，才退回全量题池
        question_pool = preferred_questions if preferred_questions else questions

        for question in question_pool:
            question_tags = list(question.knowledge_tags or [])
            tag_ids = [tag.id for tag in question_tags]
            mastery_values = [mastery_map.get(tag_id, 0) for tag_id in tag_ids]
            avg_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0
            difficulty_key = InterviewGraphHelper._normalize_difficulty(question.difficulty)
            question_graph_meta = InterviewGraphHelper.build_question_graph_meta(question)
            inferred_depth = question_graph_meta.get('reference_answer_depth', 1)
            required_skills_meta = question.required_skills_meta or question_graph_meta.get('required_skills_meta') or {}
            follow_up_templates = question.follow_up_templates or question_graph_meta.get('follow_up_templates') or []
            required_skill_names = InterviewGraphHelper._extract_required_skill_names(required_skills_meta)
            required_skill_count = len(required_skill_names)
            required_skill_complexity = str((required_skills_meta or {}).get('complexity') or '').strip().lower()
            graph_boost = 0.0
            if dynamic_adjust and tag_ids:
                boost_map = graph_signals.get('tag_boost_map', {})
                graph_boost = sum(float(boost_map.get(tag_id, 0.0) or 0.0) for tag_id in tag_ids) / len(tag_ids)
                if len(tag_ids) > 1:
                    graph_boost += 2.0 * (len(tag_ids) - 1)
                if graph_signals.get('frontier_tag_ids') and set(tag_ids).intersection(graph_signals['frontier_tag_ids']):
                    graph_boost += 2.0
                if graph_signals.get('weak_tag_ids') and set(tag_ids).intersection(graph_signals['weak_tag_ids']):
                    graph_boost += 2.5
                route_mode = graph_signals.get('route_mode', 'root')
                route_tag_ids = graph_signals.get('route_tag_ids') or set()
                if route_tag_ids and set(tag_ids).intersection(route_tag_ids):
                    graph_boost += 4.0
                if route_mode == 'root' and any(graph_signals.get('tag_depth_map', {}).get(tag_id, 1) <= 2 for tag_id in tag_ids):
                    graph_boost += 1.5
                elif route_mode == 'adjacent' and any(graph_signals.get('tag_depth_map', {}).get(tag_id, 1) == 2 for tag_id in tag_ids):
                    graph_boost += 2.0
                elif route_mode == 'bridge' and len(tag_ids) > 1:
                    graph_boost += 3.0
                if graph_signals.get('strong_tag_ids') and graph_signals['round_key'] == 'third_round' and set(tag_ids).intersection(graph_signals['strong_tag_ids']):
                    graph_boost += 1.0

                style_key = graph_signals.get('style_key', 'confident')
                if style_key == 'pressure':
                    if difficulty_key == 'hard':
                        graph_boost += 5.0
                    elif difficulty_key == 'medium':
                        graph_boost += 2.0
                elif style_key == 'teaching':
                    if difficulty_key == 'easy':
                        graph_boost += 4.0
                    elif difficulty_key == 'medium':
                        graph_boost += 2.0
                    elif difficulty_key == 'hard':
                        graph_boost -= 2.0
                else:
                    if difficulty_key == 'medium':
                        graph_boost += 1.0
                    if difficulty_key == 'hard' and graph_signals.get('round_key') == 'third_round':
                        graph_boost += 1.5

                if required_skill_names:
                    matched_skills = resume_skill_names.intersection({InterviewGraphHelper.normalize_tag_name(name) for name in required_skill_names})
                    if matched_skills:
                        graph_boost += min(6.0, len(matched_skills) * 1.8)

                if style_key == 'pressure':
                    if required_skill_count >= 3:
                        graph_boost += 2.5
                    if required_skill_complexity == 'advanced':
                        graph_boost += 2.0
                elif style_key == 'teaching':
                    if required_skill_count <= 2:
                        graph_boost += 2.5
                    if required_skill_complexity == 'basic':
                        graph_boost += 1.5
                    if required_skill_complexity == 'advanced':
                        graph_boost -= 1.5
                else:
                    if required_skill_count == 2:
                        graph_boost += 1.0
                    if required_skill_count >= 3:
                        graph_boost += 1.5
            
            target_depth = InterviewGraphHelper.estimate_target_depth(avg_mastery)
            depth = inferred_depth or 1
            depth_gap = abs(depth - target_depth)
            
            # 基础分: 深度匹配度
            score = (100 - depth_gap * 25) + avg_mastery * 0.35
            
            # 完美匹配加分
            if depth == target_depth:
                score += 20

            # GraphRAG 加权：优先弱节点、前沿节点和跨节点题
            score += graph_boost
            
            # 最近提问惩罚
            if recent_tag_ids and recent_tag_ids.intersection(tag_ids):
                score -= 35
            elif recent_tag_ids:
                score -= 8

            # 跨场次去重惩罚：同用户同岗位近期问过的题目大幅降权
            if question.id in recent_question_ids:
                score -= 55

            # 技能稀疏时优先技术基础题
            if dynamic_adjust and skill_sparse and (question.type or '').strip() == 'technical' and difficulty_key in ('easy', 'medium'):
                score += 18
            
            item = {
                'question': question,
                'tag_ids': tag_ids,
                'tag_names': [tag.name for tag in question_tags],
                'avg_mastery': avg_mastery,
                'target_depth': target_depth,
                'reference_answer_depth': depth,
                'required_skills_meta': required_skills_meta,
                'required_skill_names': required_skill_names,
                'required_skill_count': required_skill_count,
                'follow_up_templates': follow_up_templates,
                'difficulty_key': difficulty_key,
                'graph_boost': graph_boost,
                'score': score,
            }

            ranked.append(item)
            q_type = (question.type or '').strip()
            if q_type in by_type:
                by_type[q_type].append(item)

        # 按得分降序排列
        ranked.sort(key=lambda item: (-item['score'], -item['avg_mastery'], item['question'].id))
        for q_type in by_type:
            by_type[q_type].sort(key=lambda item: (-item['score'], -item['avg_mastery'], item['question'].id))

        # 按 target_mix 计算每个题型目标数量（总和严格等于 limit）
        desired_counts = InterviewGraphHelper._compute_target_counts(limit, target_mix, type_order)
        desired_difficulty_counts = InterviewGraphHelper._compute_target_counts(
            limit,
            target_difficulty,
            InterviewGraphHelper._DIFFICULTY_LEVELS,
        )

        selected = []
        selected_question_ids = set()
        fallback_detail = []
        remaining_difficulty = dict(desired_difficulty_counts)

        def _pick_from_type(q_type, need_count):
            picked = []
            if need_count <= 0:
                return picked

            # 先满足当前仍缺口的难度
            for candidate in by_type.get(q_type, []):
                qid = candidate['question'].id
                if qid in selected_question_ids:
                    continue
                diff = candidate.get('difficulty_key', 'medium')
                if remaining_difficulty.get(diff, 0) <= 0:
                    continue
                picked.append(candidate)
                selected_question_ids.add(qid)
                remaining_difficulty[diff] = max(0, int(remaining_difficulty.get(diff, 0)) - 1)
                if len(picked) >= need_count:
                    break

            # 再放宽难度约束补齐
            if len(picked) < need_count:
                for candidate in by_type.get(q_type, []):
                    qid = candidate['question'].id
                    if qid in selected_question_ids:
                        continue
                    picked.append(candidate)
                    selected_question_ids.add(qid)
                    diff = candidate.get('difficulty_key', 'medium')
                    if remaining_difficulty.get(diff, 0) > 0:
                        remaining_difficulty[diff] -= 1
                    if len(picked) >= need_count:
                        break
            return picked

        # 第一轮：按当前轮次目标数量优先级选题（避免固定 technical 先出）
        dispatch_order = sorted(
            type_order,
            key=lambda t: (
                desired_counts.get(t, 0),
                float(target_mix.get(t, 0.0) or 0.0)
            ),
            reverse=True,
        )

        for q_type in dispatch_order:
            wanted = desired_counts[q_type]
            if wanted <= 0:
                continue

            picked = _pick_from_type(q_type, wanted)
            selected.extend(picked)

            short = wanted - len(picked)
            if short <= 0:
                continue

            # 第二轮：按降级链路补足缺口
            for fb_type in InterviewGraphHelper._TYPE_FALLBACK_CHAIN.get(q_type, []):
                if short <= 0:
                    break
                fb_picked = _pick_from_type(fb_type, short)
                if fb_picked:
                    selected.extend(fb_picked)
                    fallback_detail.append({
                        'from': q_type,
                        'to': fb_type,
                        'reason': f'{q_type} inventory不足',
                        'count': len(fb_picked),
                    })
                    short -= len(fb_picked)

        # 第三轮：若总数仍不足，直接从全局高分池补齐（避免中断）
        if len(selected) < limit:
            filled_by_global_pool = 0
            for candidate in ranked:
                qid = candidate['question'].id
                if qid in selected_question_ids:
                    continue
                selected.append(candidate)
                selected_question_ids.add(qid)
                filled_by_global_pool += 1
                diff = candidate.get('difficulty_key', 'medium')
                if remaining_difficulty.get(diff, 0) > 0:
                    remaining_difficulty[diff] -= 1
                if len(selected) >= limit:
                    break
            if filled_by_global_pool > 0:
                fallback_detail.append({
                    'from': 'global_gap',
                    'to': 'global_high_score_pool',
                    'reason': '类型池不足，按全局高分补齐',
                    'count': filled_by_global_pool,
                })

        fallback_applied = len(fallback_detail) > 0

        # 计算实际题型分布
        selected_final = selected[:limit]
        actual_counts = {q_type: 0 for q_type in type_order}
        for item in selected_final:
            q_type = (item['question'].type or '').strip()
            if q_type in actual_counts:
                actual_counts[q_type] += 1
        actual_mix = {
            q_type: round((actual_counts[q_type] / len(selected_final)), 4) if selected_final else 0.0
            for q_type in type_order
        }
        actual_difficulty_counts = {k: 0 for k in InterviewGraphHelper._DIFFICULTY_LEVELS}
        for item in selected_final:
            diff_key = item.get('difficulty_key', 'medium')
            if diff_key in actual_difficulty_counts:
                actual_difficulty_counts[diff_key] += 1
        actual_difficulty_mix = {
            k: round((actual_difficulty_counts[k] / len(selected_final)), 4) if selected_final else 0.0
            for k in InterviewGraphHelper._DIFFICULTY_LEVELS
        }
        target_mix_norm = {q_type: round(float(target_mix.get(q_type, 0.0) or 0.0), 4) for q_type in type_order}
        target_difficulty_norm = {
            k: round(float(target_difficulty.get(k, 0.0) or 0.0), 4)
            for k in InterviewGraphHelper._DIFFICULTY_LEVELS
        }

        selected_questions_meta = []
        for item in selected_final:
            q = item['question']
            selected_questions_meta.append({
                'question_id': q.id,
                'question_type': (q.type or '').strip(),
                'difficulty': item.get('difficulty_key', 'medium'),
                'source': q.source or '',
                'reference_answer_depth': item.get('reference_answer_depth', 1),
                'required_skill_count': item.get('required_skill_count', 0),
                'required_skills_meta': item.get('required_skills_meta', {}),
                'follow_up_templates': item.get('follow_up_templates', []),
            })

        return {
            'interview_round': normalized_round,
            'interview_style': style,
            'job_role': job_role,
            'selected_questions': selected_final,
            'selected_questions_meta': selected_questions_meta,
            'graph_rag_meta': {
                'weak_tag_count': len(graph_signals.get('weak_tag_ids', [])),
                'frontier_tag_count': len(graph_signals.get('frontier_tag_ids', [])),
                'strong_tag_count': len(graph_signals.get('strong_tag_ids', [])),
                'route_tag_count': len(graph_signals.get('route_tag_ids', [])),
                'route_mode': graph_signals.get('route_mode', 'root'),
                'round_key': graph_signals.get('round_key', normalized_round),
            },
            'question_mix': {
                'target': target_mix_norm,
                'actual': actual_mix,
            },
            'difficulty_mix': {
                'target': target_difficulty_norm,
                'actual': actual_difficulty_mix,
            },
            'fallback_applied': fallback_applied,
            'fallback_detail': fallback_detail,
            'strategy_adjustments': strategy_adjustments,
            'round_focus': round_focus,
        }
    
    @staticmethod
    def get_recent_asked_tag_ids(interview_id, limit=3):
        """
        获取最近提问过的标签ID列表
        
        Args:
            interview_id: 面试ID
            limit: 回溯的题目数量
            
        Returns:
            list: 标签ID列表
        """
        recent_ai_questions = (
            InterviewChat.query
            .filter_by(interview_id=interview_id, role='ai')
            .filter(InterviewChat.question_id.isnot(None))
            .order_by(InterviewChat.timestamp.desc(), InterviewChat.id.desc())
            .limit(limit)
            .all()
        )
        
        recent_tag_ids = []
        seen_tag_ids = set()
        for chat in recent_ai_questions:
            question = Question.query.get(chat.question_id)
            if not question:
                continue
            for tag in question.knowledge_tags or []:
                if tag.id not in seen_tag_ids:
                    seen_tag_ids.add(tag.id)
                    recent_tag_ids.append(tag.id)
        
        return recent_tag_ids

    @staticmethod
    def get_recent_asked_question_ids(user_id, job_id, lookback_limit=40):
        """获取同用户同岗位近期已问过的问题ID，用于跨场次去重。"""
        if not user_id or not job_id:
            return []

        rows = (
            db.session.query(InterviewChat.question_id)
            .join(Interview, Interview.id == InterviewChat.interview_id)
            .filter(Interview.user_id == user_id)
            .filter(Interview.job_id == job_id)
            .filter(InterviewChat.role == 'ai')
            .filter(InterviewChat.question_id.isnot(None))
            .order_by(InterviewChat.timestamp.desc(), InterviewChat.id.desc())
            .limit(lookback_limit)
            .all()
        )

        seen = set()
        result = []
        for (qid,) in rows:
            if qid and qid not in seen:
                seen.add(qid)
                result.append(qid)
        return result
    
    @staticmethod
    def build_adjacent_tag_context(tag_ids, interview_style='confident'):
        """
        构建相邻标签上下文(用于提示词扩展)
        
        Args:
            tag_ids: 当前标签ID列表
            interview_style: 面试风格(pressure/confident/teaching)
            
        Returns:
            str: 相邻标签名称字符串
        """
        if not tag_ids:
            return ''
        
        tags = KnowledgeTag.query.filter(KnowledgeTag.id.in_(list(set(tag_ids)))).all()
        if not tags:
            return ''
        
        related_names = []
        seen = set()
        
        def push(tag_name):
            if tag_name and tag_name not in seen:
                seen.add(tag_name)
                related_names.append(tag_name)
        
        for tag in tags:
            if interview_style == 'pressure':
                # 压力面: 追问子节点
                for child in tag.children or []:
                    push(child.name)
            elif interview_style == 'teaching':
                # 教学面: 展示父节点和兄弟节点
                if tag.parent:
                    push(tag.parent.name)
                    for sibling in tag.parent.children or []:
                        if sibling.id != tag.id:
                            push(sibling.name)
            else:
                # 自信面: 展示父节点和子节点
                if tag.parent:
                    push(tag.parent.name)
                for child in tag.children or []:
                    push(child.name)
        
        if not related_names:
            return ''
        
        return '、'.join(related_names[:12])
    
    @staticmethod
    def compute_graph_coverage(interview):
        """
        计算知识图谱覆盖率和深度率
        
        Args:
            interview: Interview对象
            
        Returns:
            dict: 覆盖率统计结果
        """
        questions, tag_map = InterviewGraphHelper.get_job_graph_snapshot(interview.job_id)
        core_tag_ids = list(tag_map.keys())
        
        if not core_tag_ids:
            return {
                'coverage_rate': 0.0,
                'depth_rate': 0.0,
                'meta': {
                    'core_nodes': [],
                    'touched_nodes': [],
                    'max_depth': 0,
                    'core_count': 0,
                    'touched_count': 0,
                }
            }
        
        # 获取用户已掌握的标签
        mastery_rows = UserKnowledgeMastery.query.filter(
            UserKnowledgeMastery.user_id == interview.user_id,
            UserKnowledgeMastery.tag_id.in_(core_tag_ids)
        ).all()
        
        touched_tag_ids = [row.tag_id for row in mastery_rows if (row.mastery_level or 0) > 0]
        touched_set = set(touched_tag_ids)
        
        # 计算最大深度
        def get_depth(tag):
            depth = 1
            visited = set()
            current = tag
            while current and current.parent_id and current.parent_id not in visited:
                visited.add(current.id)
                current = KnowledgeTag.query.get(current.parent_id)
                if current:
                    depth += 1
            return depth
        
        max_depth = 0
        for tag_id in touched_set:
            tag = tag_map.get(tag_id) or KnowledgeTag.query.get(tag_id)
            if tag:
                max_depth = max(max_depth, get_depth(tag))
        
        # 计算覆盖率
        core_count = len(core_tag_ids)
        touched_count = len(touched_set)
        coverage_rate = round((touched_count / core_count) * 100, 2) if core_count else 0.0
        depth_rate = round((min(max_depth, 3) / 3) * 100, 2) if max_depth else 0.0
        
        return {
            'coverage_rate': coverage_rate,
            'depth_rate': depth_rate,
            'meta': {
                'core_nodes': [tag_map[tag_id].name for tag_id in core_tag_ids if tag_id in tag_map],
                'touched_nodes': [tag_map[tag_id].name for tag_id in touched_set if tag_id in tag_map],
                'max_depth': max_depth,
                'core_count': core_count,
                'touched_count': touched_count,
            }
        }
