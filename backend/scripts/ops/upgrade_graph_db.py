#!/usr/bin/env python
"""One-click graph database upgrade for the AI interview platform.

Default flow:
1. Run Alembic migration upgrade
2. Backfill knowledge_tags metadata from YAML and graph relations
3. Backfill Phase1 graph columns (questions/resources/session config)

Usage:
    python scripts/ops/upgrade_graph_db.py
    python scripts/ops/upgrade_graph_db.py --dry-run
    python scripts/ops/upgrade_graph_db.py --skip-backfill
    python scripts/ops/upgrade_graph_db.py --skip-phase1-backfill
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path, env: dict[str, str], title: str) -> None:
    print(f"\n=== {title} ===")
    print(" ".join(command))
    result = subprocess.run(command, cwd=str(cwd), env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description='One-click upgrade for graph schema and metadata')
    parser.add_argument('--dry-run', action='store_true', help='Run metadata backfill in dry-run mode')
    parser.add_argument('--skip-backfill', action='store_true', help='Only run DB migration upgrade')
    parser.add_argument('--skip-phase1-backfill', action='store_true', help='Skip Phase1 columns backfill script')
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.setdefault('FLASK_APP', 'run.py')
    env.setdefault('FLASK_ENV', 'development')

    run_command([sys.executable, '-m', 'flask', 'db', 'upgrade'], backend_root, env, 'Running Alembic upgrade')

    if not args.skip_backfill:
        backfill_script = backend_root / 'scripts' / 'db' / 'backfill' / 'backfill_knowledge_tags_metadata.py'
        backfill_command = [sys.executable, str(backfill_script)]
        if args.dry_run:
            backfill_command.append('--dry-run')
        run_command(backfill_command, backend_root, env, 'Backfilling knowledge tag metadata')

    if not args.skip_phase1_backfill and not args.dry_run:
        phase1_script = backend_root / 'scripts' / 'db' / 'backfill' / 'run_phase1_backfill.py'
        run_command([sys.executable, str(phase1_script)], backend_root, env, 'Backfilling Phase1 graph columns')

    print('\nAll done.')


if __name__ == '__main__':
    main()
