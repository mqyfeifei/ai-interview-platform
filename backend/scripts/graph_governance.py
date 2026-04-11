#!/usr/bin/env python
"""Graph governance checks for relational knowledge graph health."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.extensions import db
from app.models.learning import KnowledgeTag, resource_tags
from app.models.question import question_tags


def normalize_name(name: str) -> str:
    text = (name or '').strip().lower()
    return re.sub(r'[\s\-_()（）\[\]【】,.，。/\\]+', '', text)


def detect_islands():
    rows = db.session.query(KnowledgeTag).all()
    islands = []
    for tag in rows:
        child_count = len(tag.children or [])
        question_bind_count = db.session.query(question_tags.c.question_id).filter(question_tags.c.tag_id == tag.id).count()
        resource_bind_count = db.session.query(resource_tags.c.resource_id).filter(resource_tags.c.tag_id == tag.id).count()
        if not tag.parent_id and child_count == 0 and question_bind_count == 0 and resource_bind_count == 0:
            islands.append(tag)
    return islands


def detect_duplicates(tags):
    duplicates = []
    tags = list(tags)
    for idx, left in enumerate(tags):
        left_norm = normalize_name(left.name)
        for right in tags[idx + 1:]:
            right_norm = normalize_name(right.name)
            if not left_norm or not right_norm:
                continue
            ratio = SequenceMatcher(None, left_norm, right_norm).ratio()
            if left_norm == right_norm or ratio >= 0.88:
                duplicates.append((left, right, ratio))
    return duplicates


def main():
    app = create_app('development')
    with app.app_context():
        tags = KnowledgeTag.query.order_by(KnowledgeTag.id.asc()).all()
        islands = detect_islands()
        duplicates = detect_duplicates(tags)

        print('=== Graph Governance Report ===')
        print(f'Total tags: {len(tags)}')
        print(f'Island tags: {len(islands)}')
        for tag in islands[:50]:
            print(f'  - [{tag.id}] {tag.name}')

        print(f'Duplicate candidates: {len(duplicates)}')
        for left, right, ratio in duplicates[:50]:
            print(f'  - [{left.id}] {left.name} <-> [{right.id}] {right.name} (similarity={ratio:.2f})')

        if not islands and not duplicates:
            print('No governance issues found.')


if __name__ == '__main__':
    main()
