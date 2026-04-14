#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 jobs 表的技术栈和图标地址
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.job import Job, DEFAULT_JOBS

def update_job_tech_stack_and_icon():
    """更新 jobs 表的技术栈和图标地址"""
    # 创建Flask应用
    app = create_app()
    
    # 使用应用上下文
    with app.app_context():
        from app.extensions import db
        try:
            # 遍历默认岗位
            for job_key, job_info in DEFAULT_JOBS.items():
                # 查找对应的岗位记录
                job = Job.query.filter_by(name=job_info['name']).first()
                if job:
                    # 更新技术栈和图标地址
                    job.tech_stack = job_info.get('tech_stack')
                    job.icon_url = job_info.get('icon_url')
                    print(f"更新岗位: {job.name} - 技术栈: {job.tech_stack}, 图标: {job.icon_url}")
                else:
                    print(f"未找到岗位: {job_info['name']}")
            
            # 提交事务
            db.session.commit()
            print("\n更新完成！")
        except Exception as e:
            print(f"更新失败: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    update_job_tech_stack_and_icon()