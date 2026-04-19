#!/usr/bin/env python
"""Backward-compatible entrypoint for interview profile filling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from data_create_and_import import fill_interview_profiles


def main() -> None:
    parser = argparse.ArgumentParser(description='Fill interview_profiles for five jobs, 3 rounds × 3 styles.')
    parser.add_argument('--reset', action='store_true', help='Delete existing interview_profiles for the core jobs before inserting')
    parser.add_argument('--dry-run', action='store_true', help='Do not write data, only report planned inserts')
    args = parser.parse_args()

    app = create_app('development')
    with app.app_context():
        result = fill_interview_profiles(reset=args.reset, dry_run=args.dry_run)
        print(result)


if __name__ == '__main__':
    main()
