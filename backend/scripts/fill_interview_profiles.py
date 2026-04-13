#!/usr/bin/env python
"""Populate interview_profiles for five core jobs with 3 rounds × 3 interviewer styles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.extensions import db
from app.models.job import Job, DEFAULT_JOBS
from app.models.interview import InterviewProfile

STYLE_CONFIGS = {
    'confident': {
        'technique_percentage': 60.0,
        'scenario_percentage': 10.0,
        'project_deep_dive_percentage': 10.0,
        'behavioral_percentage': 20.0,
        'difficulty_low_percentage': 35.0,
        'difficulty_medium_percentage': 55.0,
        'difficulty_high_percentage': 10.0,
    },
    'teaching': {
        'technique_percentage': 50.0,
        'scenario_percentage': 15.0,
        'project_deep_dive_percentage': 15.0,
        'behavioral_percentage': 20.0,
        'difficulty_low_percentage': 30.0,
        'difficulty_medium_percentage': 50.0,
        'difficulty_high_percentage': 20.0,
    },
    'pressure': {
        'technique_percentage': 70.0,
        'scenario_percentage': 10.0,
        'project_deep_dive_percentage': 10.0,
        'behavioral_percentage': 10.0,
        'difficulty_low_percentage': 20.0,
        'difficulty_medium_percentage': 50.0,
        'difficulty_high_percentage': 30.0,
    },
}

ROUND_ADJUSTMENTS = {
    1: {
        'technique_percentage': 5.0,
        'scenario_percentage': -5.0,
        'project_deep_dive_percentage': -2.0,
        'behavioral_percentage': 2.0,
        'difficulty_low_percentage': 5.0,
        'difficulty_medium_percentage': -3.0,
        'difficulty_high_percentage': -2.0,
    },
    2: {
        'technique_percentage': 0.0,
        'scenario_percentage': 0.0,
        'project_deep_dive_percentage': 5.0,
        'behavioral_percentage': -5.0,
        'difficulty_low_percentage': -5.0,
        'difficulty_medium_percentage': 5.0,
        'difficulty_high_percentage': 0.0,
    },
    3: {
        'technique_percentage': -3.0,
        'scenario_percentage': 10.0,
        'project_deep_dive_percentage': 2.0,
        'behavioral_percentage': -9.0,
        'difficulty_low_percentage': -10.0,
        'difficulty_medium_percentage': 5.0,
        'difficulty_high_percentage': 5.0,
    },
}

STYLE_LABELS = {
    'confident': '自信面',
    'teaching': '教学面',
    'pressure': '压力面',
}

ROUND_LABELS = {
    1: '一面',
    2: '二面',
    3: '三面',
}


def find_target_jobs() -> dict[str, Job]:
    """Return the five core jobs used for interview profile generation."""
    jobs: dict[str, Job] = {}
    for domain, info in DEFAULT_JOBS.items():
        job = Job.query.filter_by(name=info['name']).first()
        if job is None:
            job = Job.query.filter(Job.name.ilike(f"%{info['name']}%")) .order_by(Job.id.asc()).first()
        if job is not None:
            jobs[domain] = job
    return jobs


def build_profile_for_round_style(job_id: int, round_number: int, style: str) -> InterviewProfile:
    base = STYLE_CONFIGS[style].copy()
    adjust = ROUND_ADJUSTMENTS.get(round_number, {})
    for key, delta in adjust.items():
        base[key] = max(0.0, base.get(key, 0.0) + delta)

    # Ensure total ratios remain sensible if small drift occurs
    total_topic = base['technique_percentage'] + base['scenario_percentage'] + base['project_deep_dive_percentage'] + base['behavioral_percentage']
    if abs(total_topic - 100.0) > 0.1:
        scale = 100.0 / total_topic
        for field in ['technique_percentage', 'scenario_percentage', 'project_deep_dive_percentage', 'behavioral_percentage']:
            base[field] = round(base[field] * scale, 2)

    return InterviewProfile(
        job_id=job_id,
        round=round_number,
        interviewer_style=style,
        technique_percentage=base['technique_percentage'],
        scenario_percentage=base['scenario_percentage'],
        project_deep_dive_percentage=base['project_deep_dive_percentage'],
        behavioral_percentage=base['behavioral_percentage'],
        difficulty_low_percentage=base['difficulty_low_percentage'],
        difficulty_medium_percentage=base['difficulty_medium_percentage'],
        difficulty_high_percentage=base['difficulty_high_percentage'],
        is_dynamic_adjust=True,
        enabled_dimensions=['communication', 'problem_solving', 'technical'],
        difficulty_level=round_number,
        tone_descriptor=f"{ROUND_LABELS[round_number]} {STYLE_LABELS[style]}",
    )


def fill_profiles(reset: bool = False, dry_run: bool = False) -> dict:
    target_jobs = find_target_jobs()
    if len(target_jobs) < 5:
        raise RuntimeError(f'未找到 5 个核心岗位，请检查 jobs 表是否包含必要岗位。已匹配岗位: { {k: v.name for k, v in target_jobs.items()} }')

    if reset:
        deleted = db.session.query(InterviewProfile).filter(InterviewProfile.job_id.in_([job.id for job in target_jobs.values()])).delete(synchronize_session=False)
        db.session.commit()
        print(f'已删除 {deleted} 条已有 interview_profiles')

    profiles = []
    for domain, job in target_jobs.items():
        for round_number in (1, 2, 3):
            for style in ('confident', 'teaching', 'pressure'):
                exists = InterviewProfile.query.filter_by(job_id=job.id, round=round_number, interviewer_style=style).first()
                if exists:
                    continue
                profiles.append(build_profile_for_round_style(job.id, round_number, style))

    if dry_run:
        return {
            'target_jobs': {k: v.id for k, v in target_jobs.items()},
            'planned_inserts': len(profiles)
        }

    db.session.add_all(profiles)
    db.session.commit()

    return {
        'created_profiles': len(profiles),
        'jobs': {k: v.id for k, v in target_jobs.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Fill interview_profiles for five jobs, 3 rounds × 3 styles.')
    parser.add_argument('--reset', action='store_true', help='Delete existing interview_profiles for the core jobs before inserting')
    parser.add_argument('--dry-run', action='store_true', help='Do not write data, only report planned inserts')
    args = parser.parse_args()

    app = create_app('development')
    with app.app_context():
        result = fill_profiles(reset=args.reset, dry_run=args.dry_run)
        print(result)


if __name__ == '__main__':
    main()
