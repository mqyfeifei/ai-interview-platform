# backend/app/services/interview_graph_helper.py
"""
面试服务 - 知识图谱辅助模块
负责简历解析、知识点匹配、题目推荐、图谱覆盖率计算等
"""

import re
import math
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
    def _normalize_difficulty(raw_value):
        """标准化题目难度到 easy/medium/hard。"""
        if raw_value is None:
            return 'medium'
        key = str(raw_value).strip().lower()
        return InterviewGraphHelper._DIFFICULTY_ALIASES.get(key, 'medium')

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
            return resume_text.strip()[:max_chars]
        
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
    def assign_questions(job_id, user_id, limit=5, recent_tag_ids=None, interview_round='first_round', interview_style='confident', resume_profile=None):
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
        target_mix = dict(strategy.get('target_mix') or {})
        target_difficulty = dict(strategy.get('difficulty') or {})
        round_focus = strategy.get('focus', '')
        style = str(interview_style or 'confident').strip().lower() or 'confident'

        for level in InterviewGraphHelper._DIFFICULTY_LEVELS:
            target_difficulty.setdefault(level, 0.0)

        strategy_adjustments = []

        if not questions or limit <= 0:
            return {
                'interview_round': normalized_round,
                'interview_style': style,
                'job_role': job_role,
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

        skill_sparse = InterviewGraphHelper._is_skill_profile_sparse(
            user_id=user_id,
            resume_profile=resume_profile,
            resume_context_text=resume_context,
        )
        if skill_sparse:
            strategy_adjustments.append({
                'rule': 'skills_sparse',
                'reason': '技能字段稀疏，优先技术基础题（easy/medium）',
            })
        
        recent_tag_ids = set(recent_tag_ids or [])
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
        
        # 为每个题目计算综合得分并按类型分桶
        by_type = {k: [] for k in type_order}
        ranked = []
        preferred_questions = [q for q in questions if q.id not in recent_question_ids]
        # 若去重后候选过少，保留全量题池并施加强惩罚，避免无题可选
        question_pool = preferred_questions if len(preferred_questions) >= max(2, min(limit, 3)) else questions

        for question in question_pool:
            question_tags = list(question.knowledge_tags or [])
            tag_ids = [tag.id for tag in question_tags]
            mastery_values = [mastery_map.get(tag_id, 0) for tag_id in tag_ids]
            avg_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0
            difficulty_key = InterviewGraphHelper._normalize_difficulty(question.difficulty)
            
            target_depth = InterviewGraphHelper.estimate_target_depth(avg_mastery)
            depth = question.reference_answer_depth or 1
            depth_gap = abs(depth - target_depth)
            
            # 基础分: 深度匹配度
            score = (100 - depth_gap * 25) + avg_mastery * 0.35
            
            # 完美匹配加分
            if depth == target_depth:
                score += 20
            
            # 最近提问惩罚
            if recent_tag_ids and recent_tag_ids.intersection(tag_ids):
                score -= 35
            elif recent_tag_ids:
                score -= 8

            # 跨场次去重惩罚：同用户同岗位近期问过的题目大幅降权
            if question.id in recent_question_ids:
                score -= 55

            # 技能稀疏时优先技术基础题
            if skill_sparse and (question.type or '').strip() == 'technical' and difficulty_key in ('easy', 'medium'):
                score += 18
            
            item = {
                'question': question,
                'tag_ids': tag_ids,
                'tag_names': [tag.name for tag in question_tags],
                'avg_mastery': avg_mastery,
                'target_depth': target_depth,
                'difficulty_key': difficulty_key,
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
            })

        return {
            'interview_round': normalized_round,
            'interview_style': style,
            'job_role': job_role,
            'selected_questions': selected_final,
            'selected_questions_meta': selected_questions_meta,
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
