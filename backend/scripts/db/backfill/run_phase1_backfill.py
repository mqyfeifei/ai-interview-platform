#!/usr/bin/env python
"""Execute Phase 1 backfill SQL in current Flask app DB context."""

from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.extensions import db


def main() -> None:
    sql_path = BACKEND_ROOT / 'scripts' / 'db' / 'sql' / 'backfill_phase1_columns.sql'
    sql_text = sql_path.read_text(encoding='utf-8')

    app = create_app()
    with app.app_context():
        conn = db.engine.raw_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql_text)
            conn.commit()
        finally:
            conn.close()

    print(f'Phase1 backfill executed: {sql_path}')


if __name__ == '__main__':
    main()
