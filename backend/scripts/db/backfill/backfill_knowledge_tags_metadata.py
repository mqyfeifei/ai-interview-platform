#!/usr/bin/env python
"""Backfill missing knowledge_tags metadata from YAML catalog and existing graph.

This script fills blank fields for historical knowledge_tags rows:
- category
- complexity
- estimated_hours
- embedding

It prefers exact matches from FuChuangTiKu knowledge_points YAML files.
If a tag is not found there, it inherits metadata from its parent tag.

Usage:
    python scripts/db/backfill/backfill_knowledge_tags_metadata.py
    python scripts/db/backfill/backfill_knowledge_tags_metadata.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import os
from difflib import SequenceMatcher
from pathlib import Path

import psycopg2
import yaml

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


MODEL = None


def get_db_dsn() -> str:
    return os.environ.get(
        'DEV_DATABASE_URL',
        'postgresql://postgres:mysecretpassword@localhost:5432/ai_interview_db'
    )


def get_backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_catalog() -> dict:
    backend_root = get_backend_root()
    knowledge_dir = backend_root / 'FuChuangTiKu' / 'data' / 'knowledge_points'
    catalog = {}

    if not knowledge_dir.exists():
        return catalog

    for yaml_path in sorted(knowledge_dir.glob('*.yaml')):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as fp:
                payload = yaml.safe_load(fp) or {}
        except Exception:
            continue

        for module in payload.get('modules', []) or []:
            category = (module.get('name') or '').strip()
            for point in module.get('points', []) or []:
                if isinstance(point, str):
                    point_name = point.strip()
                    complexity = 'Medium'
                    estimated_hours = 1
                else:
                    point_name = (point.get('point') or '').strip()
                    complexity = point.get('complexity', 'Medium')
                    estimated_hours = point.get('estimated_hours', 1)

                if not point_name:
                    continue

                catalog[point_name.lower()] = {
                    'name': point_name,
                    'category': category or None,
                    'complexity': complexity or 'Medium',
                    'estimated_hours': int(estimated_hours or 1),
                }

    return catalog


def get_model():
    global MODEL
    if MODEL is not None:
        return MODEL

    if SentenceTransformer is None:
        MODEL = False
        return MODEL

    try:
        MODEL = SentenceTransformer('BAAI/bge-small-zh-v1.5', local_files_only=False)
    except Exception:
        MODEL = False
    return MODEL


def embed_text(text: str):
    normalized = (text or '').strip() or 'knowledge_tag'
    model = get_model()
    if model:
        return model.encode(normalized).tolist()

    digest = hashlib.sha256(normalized.encode('utf-8')).digest()
    return [(digest[i % len(digest)] / 255.0) for i in range(512)]


def vector_literal(vec) -> str:
    return '[' + ','.join(f'{float(v):.6f}' for v in vec[:512]) + ']'


def best_root_parent(name: str, root_rows: list[dict]):
    target = (name or '').strip().lower()
    if not target or not root_rows:
        return None

    best = None
    best_score = 0.0
    for row in root_rows:
        candidate = (row['name'] or '').strip().lower()
        if not candidate:
            continue
        score = SequenceMatcher(None, target, candidate).ratio()
        if target in candidate or candidate in target:
            score += 0.2
        if score > best_score:
            best_score = score
            best = row
    return best if best_score >= 0.2 else None


def main():
    parser = argparse.ArgumentParser(description='Backfill knowledge_tags metadata')
    parser.add_argument('--dry-run', action='store_true', help='Print changes without writing to the database')
    args = parser.parse_args()

    catalog = load_catalog()
    dsn = get_db_dsn()

    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, category, complexity, estimated_hours, parent_id
                FROM knowledge_tags
                ORDER BY id
                """
            )
            rows = cur.fetchall()

            cur.execute(
                """
                SELECT id, name, category, complexity, estimated_hours
                FROM knowledge_tags
                WHERE category IS NOT NULL AND category <> ''
                ORDER BY id
                """
            )
            root_rows = [
                {
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'complexity': row[3],
                    'estimated_hours': row[4]
                }
                for row in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT id, name, category, complexity, estimated_hours
                FROM knowledge_tags
                ORDER BY id
                """
            )
            id_to_root = {}
            all_rows = cur.fetchall()
            for row in all_rows:
                if row[2]:
                    id_to_root[row[0]] = {
                        'id': row[0],
                        'name': row[1],
                        'category': row[2],
                        'complexity': row[3],
                        'estimated_hours': row[4]
                    }

            updates = []
            for row in rows:
                tag_id, name, category, complexity, estimated_hours, parent_id = row
                normalized_name = (name or '').strip()
                if not normalized_name:
                    continue

                catalog_item = catalog.get(normalized_name.lower())
                parent = id_to_root.get(parent_id)

                new_category = category
                new_complexity = complexity
                new_hours = estimated_hours
                embed_source = None

                if catalog_item:
                    if not new_category:
                        new_category = catalog_item.get('category')
                    if not new_complexity:
                        new_complexity = catalog_item.get('complexity') or 'Medium'
                    if not new_hours:
                        new_hours = catalog_item.get('estimated_hours') or 1
                    embed_source = f"模块: {new_category or ''} 知识点: {normalized_name}"
                elif parent:
                    if not new_category:
                        new_category = parent.get('category') or parent.get('name')
                    if not new_complexity:
                        new_complexity = parent.get('complexity') or 'Medium'
                    if not new_hours:
                        parent_hours = parent.get('estimated_hours') or 1
                        new_hours = max(1, int(round(float(parent_hours) * 0.5)))
                    embed_source = f"{normalized_name} {new_category or ''} {parent.get('name') or ''}"
                else:
                    best_parent = best_root_parent(normalized_name, root_rows)
                    if best_parent:
                        if not new_category:
                            new_category = best_parent.get('category') or best_parent.get('name')
                        if not new_complexity:
                            new_complexity = best_parent.get('complexity') or 'Medium'
                        if not new_hours:
                            parent_hours = best_parent.get('estimated_hours') or 1
                            new_hours = max(1, int(round(float(parent_hours) * 0.5)))
                        embed_source = f"{normalized_name} {new_category or ''} {best_parent.get('name') or ''}"
                    else:
                        if not new_category:
                            new_category = '未分类'
                        if not new_complexity:
                            new_complexity = 'Medium'
                        if not new_hours:
                            new_hours = 1
                        embed_source = f"{normalized_name} {new_category}"

                embedding_literal = vector_literal(embed_text(embed_source))

                changed = False
                if new_category != category and new_category is not None:
                    changed = True
                if new_complexity != complexity and new_complexity is not None:
                    changed = True
                if new_hours != estimated_hours and new_hours is not None:
                    changed = True

                if changed or not embedding_literal:
                    updates.append((new_category, new_complexity, int(new_hours or 1), embedding_literal, tag_id))

            print(f'Prepared {len(updates)} tag updates')

            if args.dry_run:
                for preview in updates[:20]:
                    print(preview)
                conn.rollback()
                return

            if updates:
                cur.executemany(
                    """
                    UPDATE knowledge_tags
                    SET category = %s,
                        complexity = %s,
                        estimated_hours = %s,
                        embedding = %s::vector
                    WHERE id = %s
                    """,
                    updates
                )

            conn.commit()
            print(f'Backfilled {len(updates)} knowledge_tags rows successfully.')

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
