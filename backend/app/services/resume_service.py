# backend/app/services/resume_service.py
"""
简历业务逻辑层，供 resumes.py 视图层调用。
所有数据库操作、业务规则校验都在这里处理。
"""

from datetime import datetime
from app.extensions import db
from app.models.resume import Resume
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
                      title: str = None, content: dict = None) -> dict:
        """
        更新简历标题和/或内容（全量替换 content）。
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
            resume.set_content(content)

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