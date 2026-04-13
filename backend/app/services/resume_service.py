# backend/app/services/resume_service.py
"""
简历业务逻辑层，供 resumes.py 视图层调用。
所有数据库操作、业务规则校验都在这里处理。
"""

from datetime import datetime
from app.extensions import db
from app.models.resume import Resume
from app.models.job import Job, get_job_front_key
from app.models.user import User
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
# 允许的头像格式


class ResumeService:

    # ------------------------------------------------------------------ #
    # 查询                                                                 #
    # ------------------------------------------------------------------ #
    ALLOWED_AVATAR_EXT = {"png", "jpg", "jpeg", "gif"}

    # ================= 新增：简历填写指导 =================
    @staticmethod
    def get_resume_guidance(job_id: int = None) -> dict:
        """
        获取简历填写的指导和必填项要求（供前端初始化或切换岗位时展示）
        """
        guidance = {
            "base_requirements": [
                {"field": "personal.name", "label": "姓名", "importance": "required", "desc": "请填写真实姓名，用于投递和沟通"},
                {"field": "personal.phone", "label": "联系电话", "importance": "required", "desc": "保持电话畅通，建议格式：138-xxxx-xxxx"},
                {"field": "personal.email", "label": "电子邮箱", "importance": "required", "desc": "建议使用专业邮箱，避免过于随意的昵称"},
                {"field": "education", "label": "教育经历", "importance": "required", "desc": "至少填写最高学历，包含就读院校和专业"}
            ],
            "job_specific_requirements": [],
            "general_tips": [
                "保持简历在一至两页纸，排版整洁，重点突出。",
                "经历按照时间倒序排列（最近的经历放在最前面）。"
            ]
        }

        if job_id:
            job = Job.query.get(job_id)
            job_key = get_job_front_key(job)

            if job_key in ['backend', 'frontend', 'cv', 'network', 'qa']:
                guidance["job_specific_requirements"] = [
                    {"field": "skills", "label": "专业技能", "importance": "required", "desc": f"请详细列出您的技术栈，突出在{job.name if job else '该技术'}领域的熟练度（如：熟练掌握、熟悉、了解）。"},
                    {"field": "achievements", "label": "量化产出", "importance": "required", "desc": "在工作或实习经历中，务必使用STAR法则描述，并包含具体的数据指标（如：QPS提升了xx%、耗时降低了xx%）。"}
                ]
                guidance["general_tips"].append(
                    "技术类简历极度看重项目落地经验和代码能力，请将包含复杂架构或难点攻克的核心项目置于显眼位置。"
                )

        return guidance


    # ================= 新增：简历填写指导与完成度计算 =================
    @staticmethod
    def calculate_completion(content: dict, job_id: int = None) -> dict:
        """
        实时分析简历内容，计算完成度百分比，并返回具体缺失项和建议
        """
        if not content:
            content = {}

        score = 0
        missing_items = []
        suggestions = []

        # 1. 基础信息 (占比 30%)
        personal = content.get('personal', {})
        if personal.get('name'): score += 10
        else: missing_items.append("个人信息：姓名")

        if personal.get('phone'): score += 10
        else: missing_items.append("个人信息：联系电话")

        if personal.get('email'): score += 10
        else: missing_items.append("个人信息：电子邮箱")

        # 2. 教育经历 (占比 20%)
        education = content.get('education', [])
        if education and len(education) > 0 and education[0].get('school'):
            score += 20
        else:
            missing_items.append("教育经历：就读院校")

        # 3. 岗位差异化校验与评分 (占比 50%)
        job_key = None
        if job_id:
            job = Job.query.get(job_id)
            job_key = get_job_front_key(job)

        if job_key in ['backend', 'frontend', 'cv', 'network', 'qa']:
            # 技术岗位逻辑：专业技能(25%) + 实习/工作产出(25%)
            skills = content.get('skills', [])
            if skills:
                score += 25
            else:
                missing_items.append("核心模块：专业技能")

            works = content.get('workExperiences', [])
            interns = content.get('internshipExperiences', [])
            all_exps = works + interns

            has_achievement = False
            if all_exps:
                for exp in all_exps:
                    if exp.get('achievements'):
                        has_achievement = True
                        break

            if has_achievement:
                score += 25
            else:
                missing_items.append("经历描述：具体的量化业绩(Achievements)")
                if not all_exps:
                    suggestions.append("建议添加实习、工作或开源项目经历来证明您的技术实力。")
                else:
                    suggestions.append("您的经历描述中缺少具体的成果展示，建议补充数据指标（如降低延迟、提升并发等）。")
        else:
            # 非技术岗位或未选择岗位：均分给工作/实习/校园经历
            works = content.get('workExperiences', [])
            interns = content.get('internshipExperiences', [])
            campus = content.get('campusExperiences', [])

            if works or interns:
                score += 35
            else:
                missing_items.append("核心模块：工作或实习经历")

            if campus:
                score += 15
            else:
                suggestions.append("补充校园经历（如社团、比赛）可进一步丰富您的背景。")

        return {
            "completion_rate": score,       # 0 - 100
            "missing_items": missing_items, # 明确指出缺了什么
            "suggestions": suggestions      # 给出软性优化建议
        }

    # ================= 新增：统一校验逻辑 =================
    @staticmethod
    def _validate_resume_content(content: dict, job_id: int = None, user_id: int = None):
        """
        校验简历内容的必填项与岗位差异化要求。
        校验失败时直接抛出友好的 ValueError，由外层 API 捕获并返回给前端 400。
        """
        # 漏洞修复 1：禁止保存空壳简历
        if not content:
            raise ValueError("简历内容不能为空")

        # 1. 最小通用必填校验 (个人信息)
        personal = content.get('personal', {})
        if not personal.get('name'):
            raise ValueError("简历基础信息缺失：姓名为必填项")
        if not personal.get('phone'):
            raise ValueError("简历基础信息缺失：联系电话为必填项")
        if not personal.get('email'):
            raise ValueError("简历基础信息缺失：电子邮箱为必填项")

        # 2. 最小通用必填校验 (教育经历)
        education = content.get('education', [])
        if not education or not isinstance(education, list):
            raise ValueError("至少需要填写一段教育经历")
        if not education[0].get('school'):
            raise ValueError("教育经历不完整：就读院校为必填项")

        # 漏洞修复 3：主简历无 job_id 时，兜底使用用户的 default_job_id 进行校验
        if not job_id and user_id:
            user = User.query.get(user_id)
            if user and user.default_job_id:
                job_id = user.default_job_id

        # 3. 岗位差异化校验
        if job_id:
            job = Job.query.get(job_id)
            job_key = get_job_front_key(job)

            # 技术类岗位：强校验技能栈与项目产出
            if job_key in ['backend', 'frontend', 'cv', 'network', 'qa']:
                skills = content.get('skills', [])
                if not skills:
                    raise ValueError("技术类简历必须填写「专业技能」模块")

                # 检查工作或实习经历是否填写了成绩
                works = content.get('workExperiences', [])
                interns = content.get('internshipExperiences', [])
                all_exps = works + interns
                if all_exps:
                    for exp in all_exps:
                        if not exp.get('achievements'):
                            raise ValueError(f"技术类简历要求量化产出，请完善经历【{exp.get('company', '未命名公司')}】中的「业绩/成就」字段")

            # # 产品/运营类岗位校验 (假设后续在 DEFAULT_JOBS 中增加了 product/operation)
            # elif job_key in ['product', 'operation']:
            #     works = content.get('workExperiences', [])
            #     interns = content.get('internshipExperiences', [])
            #     if not works and not interns:
            #         raise ValueError("产品/运营类简历高度看重项目经验，请至少填写一段实习或工作经历")
    # =======================================================


    @staticmethod
    def ensure_main_resume(user_id: int) -> Resume:
        """
        懒初始化主简历：若用户还没有主简历则自动创建一份空的，
        保证每个用户至少存在一份主简历。
        """
        main = Resume.query.filter_by(user_id=user_id, is_main=True).first()
        if not main:
            main = Resume(
                user_id=user_id,
                title='主简历',
                is_main=True,
                job_id=None,
            )
            main.set_content({})
            db.session.add(main)
            db.session.commit()
        return main

    @staticmethod
    def list_resumes(user_id: int) -> list:
        """
        返回该用户的所有简历（不含 content 大字段）。
        主简历排在最前，其余按创建时间升序。
        """
        ResumeService.ensure_main_resume(user_id)

        resumes = (
            Resume.query
            .filter_by(user_id=user_id)
            .order_by(Resume.is_main.desc(), Resume.created_at.asc())
            .all()
        )
        return [r.to_dict(include_content=False) for r in resumes]

    @staticmethod
    def get_resume(resume_id: int, user_id: int) -> dict:
        """
        获取单份简历（含 content）。
        若不存在或不属于该用户则抛出 ValueError。
        """
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not resume:
            raise ValueError('简历不存在')
        return resume.to_dict(include_content=True)

    @staticmethod
    def get_main_resume(user_id: int) -> dict:
        """返回主简历（含 content），不存在则先创建。"""
        main = ResumeService.ensure_main_resume(user_id)
        return main.to_dict(include_content=True)
    
    @staticmethod
    def get_resume(resume_id: int, user_id: int) -> dict:
        """根据resume_id获取指定的简历（含 content）。"""
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not resume:
            raise ValueError('简历不存在或不属于该用户')
        return resume.to_dict(include_content=True)

    # ------------------------------------------------------------------ #
    # 创建                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_resume(user_id: int, title: str, is_main: bool,
                      job_id=None, content: dict = None) -> dict:
        """
        创建新简历。
        - 主简历每人只能有一份，重复创建时抛出 ValueError。
        - 岗位定制简历数量不限。
        """
        title = (title or '新简历').strip()
        content = content or {}

        # 创建时不强制做全量校验，允许前端保存不完整简历（面试启动时再由后端做最终校验）
        # NOTE: 保留此注释用于审计历史变更

        if is_main:
            existing = Resume.query.filter_by(user_id=user_id, is_main=True).first()
            if existing:
                raise ValueError('主简历已存在，每位用户只能有一份主简历')

        resume = Resume(
            user_id=user_id,
            title=title,
            is_main=is_main,
            job_id=job_id,
        )
        resume.set_content(content)

        db.session.add(resume)
        db.session.commit()
        return resume.to_dict(include_content=True)

    # ------------------------------------------------------------------ #
    # 更新                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def update_resume(resume_id: int, user_id: int,
                      title: str = None, content: dict = None, job_id=None) -> dict:
        """
        更新简历标题、内容和/或关联岗位。
        若简历不存在或不属于该用户则抛出 ValueError。
        """
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not resume:
            raise ValueError('简历不存在')

        if title is not None:
            title = title.strip()
            if title:
                resume.title = title

        if content is not None:
            # 更新简历时不强制全量校验，允许前端保存不完整简历；最终校验将在面试启动阶段执行
            resume.set_content(content)

        if job_id is not None:
            resume.job_id = job_id

        resume.updated_at = datetime.utcnow()
        db.session.commit()
        return resume.to_dict(include_content=True)

    # ------------------------------------------------------------------ #
    # 删除                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def delete_resume(resume_id: int, user_id: int) -> None:
        """
        删除岗位定制简历。主简历不允许删除。
        若简历不存在或不属于该用户则抛出 ValueError。
        """
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not resume:
            raise ValueError('简历不存在')
        if resume.is_main:
            raise ValueError('主简历不可删除')

        db.session.delete(resume)
        db.session.commit()

    # ------------------------------------------------------------------ #
    # 从主简历复制                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def copy_from_main(resume_id: int, user_id: int) -> dict:
        """
        将主简历的 content 覆盖到指定简历。
        - 目标是主简历自身时抛出 ValueError。
        - 主简历不存在时抛出 ValueError（提示先填写主简历）。
        """
        target = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        if not target:
            raise ValueError('简历不存在')
        if target.is_main:
            raise ValueError('主简历无法从自身复制')

        main = Resume.query.filter_by(user_id=user_id, is_main=True).first()
        if not main:
            raise ValueError('主简历不存在，请先完善主简历')

        # 复制主简历到目标简历（允许覆盖，即便主简历不完善）
        main_content = main.get_content()
        target.set_content(main.get_content())
        target.updated_at = datetime.utcnow()
        db.session.commit()
        return target.to_dict(include_content=True)

    @staticmethod
    def upload_resume_avatar(user_id: int, file):
        # 1.基础校验
        if not file or file.filename == "":
            raise ValueError("未选择上传文件")

        # 2.取后缀+校验格式
        raw_name = secure_filename(file.filename)
        ext = raw_name.rsplit(".", 1)[-1].lower()
        if ext not in ResumeService.ALLOWED_AVATAR_EXT:
            raise ValueError("仅支持 png/jpg/jpeg/gif 图片")

        # 3.固定保存目录
        upload_dir = os.path.join(current_app.root_path, "uploads", "resume_avatars")
        os.makedirs(upload_dir, exist_ok=True)

        # 4.有意义的文件名（关键修改）
        new_filename = f"user_{user_id}_resume_avatar_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = os.path.join(upload_dir, new_filename)

        # 5.保存文件
        file.save(save_path)

        # 6.返回前端可访问URL
        return f"/uploads/resume_avatars/{new_filename}"