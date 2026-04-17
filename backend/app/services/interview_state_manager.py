from dataclasses import dataclass
from enum import Enum

from app.services.interview_session_manager import InterviewSessionManager, ROUND_ALIASES


class InterviewPhase(str, Enum):
    INIT_OPENING = 'INIT_OPENING'
    TECH_BASIC = 'TECH_BASIC'
    PROJECT_DEEP_DIVE = 'PROJECT_DEEP_DIVE'
    SCENARIO = 'SCENARIO'
    BEHAVIORAL = 'BEHAVIORAL'
    CLOSING = 'CLOSING'


@dataclass
class InterviewTurnState:
    phase: InterviewPhase
    phase_targets: dict
    phase_progress: dict
    planned_questions: int
    min_questions: int
    max_questions: int
    max_questions_per_turn: int
    session_round: str
    session_style: str


class InterviewStateManager:
    _QUESTION_TYPE_TO_PHASE = {
        'technical': InterviewPhase.TECH_BASIC,
        'project_deep_dive': InterviewPhase.PROJECT_DEEP_DIVE,
        'scenario_design': InterviewPhase.SCENARIO,
        'behavioral': InterviewPhase.BEHAVIORAL,
    }

    _PHASE_ORDER = [
        InterviewPhase.TECH_BASIC,
        InterviewPhase.PROJECT_DEEP_DIVE,
        InterviewPhase.SCENARIO,
        InterviewPhase.BEHAVIORAL,
    ]

    @staticmethod
    def _safe_int(value, default):
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _compute_target_counts(limit, ratio_map, ordered_keys):
        safe_limit = max(0, int(limit or 0))
        if safe_limit <= 0:
            return {k: 0 for k in ordered_keys}

        raw_targets = {k: float(ratio_map.get(k, 0.0) or 0.0) * safe_limit for k in ordered_keys}
        counts = {k: int(raw_targets[k]) for k in ordered_keys}
        remained = safe_limit - sum(counts.values())
        if remained > 0:
            by_fraction = sorted(
                ordered_keys,
                key=lambda k: (raw_targets[k] - counts[k], raw_targets[k]),
                reverse=True,
            )
            idx = 0
            while remained > 0 and by_fraction:
                counts[by_fraction[idx % len(by_fraction)]] += 1
                remained -= 1
                idx += 1
        return counts

    @staticmethod
    def _get_ratio_map(session_config):
        cfg = session_config or {}
        tech = float(getattr(cfg, 'tech_ratio', 60.0) or 60.0) / 100.0
        project = float(getattr(cfg, 'project_deep_dive_percentage', 15.0) or 15.0) / 100.0
        scenario = float(getattr(cfg, 'scenario_ratio', 40.0) or 40.0) / 100.0
        behavioral = float(getattr(cfg, 'behavioral_percentage', 15.0) or 15.0) / 100.0
        raw = {
            'technical': max(0.0, tech),
            'project_deep_dive': max(0.0, project),
            'scenario_design': max(0.0, scenario),
            'behavioral': max(0.0, behavioral),
        }
        total = sum(raw.values()) or 1.0
        return {k: v / total for k, v in raw.items()}

    @staticmethod
    def _resolve_phase(asked_count, phase_targets):
        cumulative = 0
        for phase in InterviewStateManager._PHASE_ORDER:
            cumulative += int(phase_targets.get(phase.value, 0))
            if asked_count < cumulative:
                return phase
        return InterviewPhase.CLOSING

    @staticmethod
    def build_turn_state(interview, session_config, asked_count):
        round_raw = getattr(session_config, 'interview_round', None)
        session_round = ROUND_ALIASES.get(
            str(round_raw).strip().lower() if round_raw is not None else '',
            'first_round',
        )
        session_style = str(getattr(session_config, 'interview_style', 'confident') or 'confident').strip().lower() or 'confident'
        if session_style not in ('pressure', 'confident', 'teaching'):
            session_style = 'confident'

        plan = InterviewSessionManager.get_interview_question_plan(
            job_id=interview.job_id,
            interview_round=session_round,
            interview_style=session_style,
        )
        min_questions = InterviewStateManager._safe_int(plan.get('min_questions', 6), 6)
        max_questions = InterviewStateManager._safe_int(plan.get('max_questions', 10), 10)
        planned_questions = InterviewStateManager._safe_int(plan.get('planned_questions', max_questions), max_questions)

        ratios = InterviewStateManager._get_ratio_map(session_config)
        target_counts = InterviewStateManager._compute_target_counts(
            planned_questions,
            ratios,
            ['technical', 'project_deep_dive', 'scenario_design', 'behavioral'],
        )
        phase_targets = {
            InterviewPhase.TECH_BASIC.value: int(target_counts.get('technical', 0)),
            InterviewPhase.PROJECT_DEEP_DIVE.value: int(target_counts.get('project_deep_dive', 0)),
            InterviewPhase.SCENARIO.value: int(target_counts.get('scenario_design', 0)),
            InterviewPhase.BEHAVIORAL.value: int(target_counts.get('behavioral', 0)),
        }
        phase = InterviewStateManager._resolve_phase(max(0, int(asked_count or 0)), phase_targets)
        phase_progress = {
            'asked_count': max(0, int(asked_count or 0)),
            'remaining_to_min': max(0, int(min_questions) - max(0, int(asked_count or 0))),
            'remaining_to_max': max(0, int(max_questions) - max(0, int(asked_count or 0))),
        }
        max_per_turn = 2 if session_style == 'pressure' else 1
        return InterviewTurnState(
            phase=phase,
            phase_targets=phase_targets,
            phase_progress=phase_progress,
            planned_questions=planned_questions,
            min_questions=min_questions,
            max_questions=max_questions,
            max_questions_per_turn=max_per_turn,
            session_round=session_round,
            session_style=session_style,
        )
