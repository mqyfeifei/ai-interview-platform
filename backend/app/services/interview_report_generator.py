# backend/app/services/interview_report_generator.py
"""
面试服务 - 报告生成模块
负责面试结束后的评估、打分、知识点掌握度更新等
"""

import re
import json
from datetime import datetime

from app.extensions import db
from app.models.interview import Interview, InterviewChat, InterviewScore, Dimension
from app.models.learning import KnowledgeTag, UserKnowledgeMastery
from app.models.example import Example
from app.utils.llm_client import DeepSeekClient


class InterviewReportGenerator:
    """面试报告生成器"""

    DIMENSION_ALIASES = {
        '表达沟通力': '表达沟通',
        '表达能力': '表达沟通',
        '沟通表达': '表达沟通',
    }

    @classmethod
    def _normalize_dimension_name(cls, dim_name):
        name = str(dim_name or '').strip()
        return cls.DIMENSION_ALIASES.get(name, name)
    
    @staticmethod
    def finish_interview(interview_id):
        """
        结束面试并生成详尽评价写入数据库
        
        流程:
        1. 提取所有对话记录
        2. 获取岗位标准知识点库
        3. 检索优秀回答范例(RAG)
        4. 调用大模型生成JSON格式报告
        5. 解析并验证JSON
        6. 写入总表详细评价字段
        7. 写入维度评分表
        8. 更新用户知识图谱掌握度
        9. 计算图谱覆盖率
        
        Args:
            interview_id: 面试ID
            
        Returns:
            dict: 包含报告ID、总分、各维度得分等的完整报告
        """
        from app.services.interview_graph_helper import InterviewGraphHelper
        
        interview = Interview.query.get(interview_id)
        if interview.status == 'completed':
            return {"msg": "面试已出具报告", "reportId": interview.id}
        
        # 1. 提取所有对话记录
        chats = InterviewChat.query.filter_by(
            interview_id=interview_id
        ).order_by(InterviewChat.timestamp).all()
        chat_history = "\n".join([f"{c.role}: {c.content}" for c in chats])
        
        # 2. 获取岗位标准知识点库
        questions, _ = InterviewGraphHelper.get_job_graph_snapshot(interview.job_id)
        tag_set = set()
        for q in questions:
            for tag in q.knowledge_tags:
                tag_set.add(tag.name)
        valid_tags_str = "、".join(list(tag_set))
        
        # 3. 检索优秀回答范例(RAG增强)
        combined_text = " ".join([c.content for c in chats if c.role == 'user'])
        example_context = ""
        
        if combined_text.strip():
            # 截取最后400字符避免Token溢出
            try:
                from app.services.interview_service import InterviewService
                chat_vector = InterviewService.get_embedding(combined_text[-400:])
                
                if chat_vector:
                    related_examples = Example.query.filter_by(job_id=interview.job_id) \
                        .order_by(Example.embedding.l2_distance(chat_vector)).limit(2).all()
                    
                    if related_examples:
                        example_context = "\n\n【优秀回答参考范例】：\n请对比候选人回答与以下范例，并在给出建议时适当参考：\n"
                        for ex in related_examples:
                            example_context += (
                                f"问题：{ex.question}\n"
                                f"回答框架：{ex.framework}\n"
                                f"范例回答：{ex.answer}\n---\n"
                            )
            except Exception as e:
                print(f"优秀范例检索失败: {str(e)}")
        
        # 4. 构建系统提示词,强制输出JSON格式
        system_prompt = f"""
            请作为资深面试官对以下面试记录进行综合评估：
            必须严格返回 JSON 格式，不要输出任何额外的 markdown 标记或解释说明。结构如下：
            {{
                "total_score": 85,
                "dimensions": {{
                    "技术正确性": {{"score": 80, "comment": "评价..."}},
                    "逻辑严谨性": {{"score": 90, "comment": "评价..."}},
                    "岗位匹配度": {{"score": 85, "comment": "评价..."}},
                    "表达沟通": {{"score": 80, "comment": "评价..."}},
                    "应变能力": {{"score": 75, "comment": "评价..."}}
                }},
                "highlights": "按【维度】输出至少3条亮点，每条都要结合本场具体回答内容，包含结论+证据+总结，不要写“表现稳定”等套话",
                "improvements": "按【知识短板标签】输出至少3条待提升项，要点明哪道题答得不足、具体缺口和改进方向",
                "suggestions": "针对不足给出3条具体、可操作的学习改进建议",
                "knowledge_tags_eval": {{
                    "这里填标准知识点名称，如'HTML5语义化'": 20
                }}
            }}
            
            【绝对指令】：对于 knowledge_tags_eval 字段，你**只能**从下面的"标准知识点库"中挑选你在对话中考察到的知识点进行 0-100 的打分。
            如果候选人回答完全错误或不会，打 0分以下。
            **禁止直接照抄模板里的文字，必须填写真实的标签名称！**
            **禁止自己捏造、改写或发明新的知识点名称！如果对话涉及的知识不在下表中，请忽略它！**
            highlights / improvements 字段必须是可换行的纯文本，每一条都以【xxx】开头，且必须出现具体面试内容（技术词、方案或回答细节），禁止空泛表述。
            
            标准知识点库：
            [{valid_tags_str}]
            {example_context}
        """
        
        # 5. 调用大模型生成报告
        llm = DeepSeekClient()
        response_text = llm.generate_reply([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"面试记录如下：\n{chat_history}"}
        ])
        
        # 6. 解析并验证JSON
        try:
            # 清理markdown标记
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # 提取首尾大括号之间的核心JSON块
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(0)
            else:
                raise ValueError("未在模型响应中匹配到有效的 JSON 结构")
            
            report_data = json.loads(cleaned_text)
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"解析报告 JSON 失败: {str(e)}。原始响应: {response_text}")
            db.session.rollback()
            raise ValueError("AI 报告生成异常，请稍后再试（大模型返回格式不合规）")
        
        # 7. 写入总表详细评价字段
        interview.total_score = report_data.get("total_score", 0)
        interview.evaluation_highlights = report_data.get("highlights", "")
        interview.evaluation_improvements = report_data.get("improvements", "")
        interview.evaluation_suggestions = report_data.get("suggestions", "")
        interview.status = 'completed'
        
        # 记录结束时间和计算用时
        interview.end_time = datetime.now()
        if interview.start_time:
            time_diff = interview.end_time - interview.start_time
            interview.used_time = int(time_diff.total_seconds())
        
        # 计算图谱覆盖率
        graph_coverage = InterviewGraphHelper.compute_graph_coverage(interview)
        interview.graph_coverage_rate = graph_coverage['coverage_rate']
        interview.graph_depth_rate = graph_coverage['depth_rate']
        interview.graph_coverage_meta = graph_coverage['meta']
        
        # 8. 写入维度评分表
        for dim_name, dim_data in report_data.get("dimensions", {}).items():
            dimension = Dimension.query.filter_by(name=InterviewReportGenerator._normalize_dimension_name(dim_name)).first()
            if dimension:
                score_record = InterviewScore(
                    interview_id=interview.id,
                    dimension_id=dimension.id,
                    score=dim_data.get("score", 0),
                    comment=dim_data.get("comment", "")
                )
                db.session.add(score_record)
        
        # 9. 更新用户知识图谱掌握度
        InterviewReportGenerator._update_knowledge_mastery(
            interview, report_data.get("knowledge_tags_eval", {}), questions
        )
        
        db.session.commit()
        
        result = {
            "reportId": interview.id,
            "jobName": interview.job.name if hasattr(interview, 'job') and interview.job else None
        }
        result.update(report_data)
        return result
    
    @staticmethod
    def _normalize_score(raw_score):
        """标准化分数到0-100范围"""
        try:
            score_value = int(float(raw_score))
        except (TypeError, ValueError):
            return None
        return max(0, min(100, score_value))
    
    @staticmethod
    def _update_node_score(user_id, target_tag, score, weight):
        """
        图谱级联更新：
        1) 先更新当前节点
        2) 再按衰减权重向父节点递归传播
        
        Args:
            user_id: 用户ID
            target_tag: 目标标签对象
            score: 原始分数
            weight: 权重系数
        """
        if not target_tag or weight <= 0:
            return
        
        weighted_score = int(max(0, min(100, round(score * weight))))
        
        mastery = UserKnowledgeMastery.query.filter_by(
            user_id=user_id,
            tag_id=target_tag.id
        ).first()
        
        if not mastery:
            mastery = UserKnowledgeMastery(
                user_id=user_id,
                tag_id=target_tag.id,
                mastery_level=weighted_score,
                last_updated=datetime.utcnow()
            )
            db.session.add(mastery)
        else:
            # 指数平滑：新分数 = int((老分数 * 0.6) + (本次得分 * 0.4))
            mastery.mastery_level = int((mastery.mastery_level * 0.6) + (weighted_score * 0.4))
            mastery.last_updated = datetime.utcnow()
        
        # 递归更新父节点
        if target_tag.parent_id:
            parent_tag = KnowledgeTag.query.get(target_tag.parent_id)
            if parent_tag:
                InterviewReportGenerator._update_node_score(
                    user_id, parent_tag, score, weight * 0.3
                )
    
    @staticmethod
    def _update_knowledge_mastery(interview, tags_eval, questions):
        """
        根据大模型评估结果更新用户知识掌握度
        
        Args:
            interview: Interview对象
            tags_eval: 知识点评估字典 {tag_name: score}
            questions: 岗位题目列表(用于兜底)
        """
        valid_tags_found = 0
        
        for tag_name, score in tags_eval.items():
            # 跳过大模型照抄的模板废话
            if not isinstance(tag_name, str):
                continue
            if "真实的" in tag_name or "这里填" in tag_name:
                continue
            
            normalized_score = InterviewReportGenerator._normalize_score(score)
            if normalized_score is None:
                continue
            
            # 严格去数据库匹配已有的标签，找不到就直接丢弃（防大模型幻觉）
            tag = KnowledgeTag.query.filter_by(name=tag_name).first()
            if tag:
                valid_tags_found += 1
                InterviewReportGenerator._update_node_score(
                    interview.user_id, tag, normalized_score, 1.0
                )
        
        # 兜底机制：如果大模型没有正确输出任何有效标签
        if valid_tags_found == 0 and len(questions) > 0:
            fallback_tags = []
            fallback_tag_ids = set()
            
            for q in questions:
                for t in q.knowledge_tags:
                    if t.id not in fallback_tag_ids:
                        fallback_tags.append(t)
                        fallback_tag_ids.add(t.id)
                        if len(fallback_tags) >= 2:
                            break
                if len(fallback_tags) >= 2:
                    break
            
            for t in fallback_tags:
                InterviewReportGenerator._update_node_score(
                    interview.user_id, t, 50, 1.0
                )  # 默认及格偏下分数
