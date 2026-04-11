#!/usr/bin/env python
"""Backfill Job-Question and Job-Tag many-to-many links after job_id removal."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.extensions import db
from app.models.job import Job
from app.models.question import Question


DOMAIN_RULES = {
    'backend': {
        'keywords': {
            'java', 'jvm', 'spring', 'springboot', 'mybatis', 'mysql', 'redis', 'mq', 'kafka',
            '并发', '线程', '后端', '数据库', '缓存', '微服务', '分布式', '事务'
        }
    },
    'frontend': {
        'keywords': {
            'vue', 'react', 'javascript', 'typescript', 'css', 'html', 'webpack', 'vite',
            '浏览器', '前端', 'dom', 'http缓存', '组件化', '工程化'
        }
    },
    'cv': {
        'keywords': {
            'cv', '视觉', '图像', 'opencv', 'cnn', 'rnn', 'transformer', 'yolo', 'resnet',
            '目标检测', '分割', '识别', '深度学习'
        }
    },
    'network': {
        'keywords': {
            'tcp', 'udp', 'ip', 'dns', 'http', 'https', 'bgp', 'ospf', 'vlan', '交换机', '路由',
            '网络', '协议', '子网', '广域网', 'sd-wan'
        }
    },
    'qa': {
        'keywords': {
            '测试', 'qa', 'pytest', 'junit', 'selenium', '接口测试', '自动化', '压测', '性能测试',
            '缺陷', '用例', 'mock'
        }
    },
}


def normalize_text(text: str) -> str:
    text = (text or '').lower()
    return re.sub(r'\s+', ' ', text)


def score_domain(corpus: str, domain: str) -> int:
    score = 0
    tokens = DOMAIN_RULES[domain]['keywords']
    for token in tokens:
        if token in corpus:
            score += 1
    return score


def find_target_jobs() -> dict[str, Job]:
    preferred_names = {
        'backend': 'Java后端开发',
        'frontend': 'Web前端开发',
        'cv': '计算机视觉',
        'network': '网络工程',
        'qa': '测试开发',
    }
    result = {}

    for domain, name in preferred_names.items():
        job = Job.query.filter_by(name=name).first()
        if not job and domain == 'backend':
            job = Job.query.filter(Job.name.ilike('%后端%')).order_by(Job.id.asc()).first()
        if not job and domain == 'frontend':
            job = Job.query.filter(Job.name.ilike('%前端%')).order_by(Job.id.asc()).first()
        if not job and domain == 'cv':
            job = Job.query.filter(Job.name.ilike('%视觉%')).order_by(Job.id.asc()).first()
        if not job and domain == 'network':
            job = Job.query.filter(Job.name.ilike('%网络%')).order_by(Job.id.asc()).first()
        if not job and domain == 'qa':
            job = Job.query.filter(Job.name.ilike('%测试%')).order_by(Job.id.asc()).first()
        if job:
            result[domain] = job

    return result


def build_question_corpus(question: Question) -> str:
    parts = [
        question.content or '',
        question.type or '',
        json.dumps(question.keywords, ensure_ascii=False) if question.keywords is not None else '',
        json.dumps(question.reference_answer, ensure_ascii=False) if question.reference_answer is not None else '',
    ]

    for tag in question.knowledge_tags or []:
        parts.append(tag.name or '')
        parts.append(tag.category or '')

    return normalize_text(' '.join(parts))


def backfill(reset: bool = False, dry_run: bool = False) -> dict:
    target_jobs = find_target_jobs()
    if len(target_jobs) < 5:
        raise RuntimeError(f'核心岗位不足，无法完成回填。当前岗位映射: { {k: v.name for k, v in target_jobs.items()} }')

    questions = Question.query.all()
    matched = []
    unmatched = []

    for question in questions:
        corpus = build_question_corpus(question)
        scores = {domain: score_domain(corpus, domain) for domain in target_jobs.keys()}
        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]

        if best_score <= 0:
            unmatched.append(question.id)
            continue

        matched.append((question, target_jobs[best_domain], scores))

    if dry_run:
        return {
            'total_questions': len(questions),
            'matched_questions': len(matched),
            'unmatched_questions': len(unmatched),
            'unmatched_ids_preview': unmatched[:30],
            'target_jobs': {k: v.id for k, v in target_jobs.items()},
        }

    if reset:
        db.session.execute(db.text('DELETE FROM job_tags'))
        db.session.execute(db.text('DELETE FROM job_questions'))

    for question, job, _ in matched:
        if question not in job.questions:
            job.questions.append(question)

    db.session.flush()

    # 由 job_questions + question_tags 反推 job_tags
    for job in Job.query.all():
        for question in job.questions:
            for tag in question.knowledge_tags:
                if tag not in job.knowledge_tags:
                    job.knowledge_tags.append(tag)

    db.session.commit()

    return {
        'total_questions': len(questions),
        'matched_questions': len(matched),
        'unmatched_questions': len(unmatched),
        'unmatched_ids_preview': unmatched[:30],
        'job_questions_count': db.session.execute(db.text('SELECT COUNT(*) FROM job_questions')).scalar(),
        'job_tags_count': db.session.execute(db.text('SELECT COUNT(*) FROM job_tags')).scalar(),
    }


def main():
    parser = argparse.ArgumentParser(description='Backfill job_questions and job_tags from existing graph signals')
    parser.add_argument('--reset', action='store_true', help='Clear existing job_questions/job_tags before backfill')
    parser.add_argument('--dry-run', action='store_true', help='Preview stats only, no writes')
    args = parser.parse_args()

    app = create_app('development')
    with app.app_context():
        result = backfill(reset=args.reset, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
