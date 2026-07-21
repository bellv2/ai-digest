"""
Idempotent schema migration — ensures all tables have every column the
pipeline scripts expect, regardless of what's in the committed .db file.

This exists because a schema mismatch (columns added during development but
never pushed to the committed database) caused a real production failure —
see digests/FAILED_RUN_2026-07-15.md. Running this first, every time, means
schema drift between local testing and the committed database can't cause
silent write failures again.

Safe to run any number of times — only adds missing columns, never removes
or modifies existing data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from db_utils import get_connection

# table_name -> list of (column_name, column_type) that must exist
REQUIRED_COLUMNS = {
    "repos": [
        ("cited_arxiv_ids", "TEXT"),
        ("raw_excerpt", "TEXT"),
        ("writeup", "TEXT"),
    ],
    "videos": [
        ("title_sketchiness_score", "INTEGER"),
        ("description_sketchiness_score", "INTEGER"),
        ("resource_link_count", "INTEGER"),
        ("promo_link_count", "INTEGER"),
        ("neutral_link_count", "INTEGER"),
        ("comment_check_performed", "INTEGER DEFAULT 0"),
        ("comment_check_result", "TEXT"),
        ("raw_excerpt", "TEXT"),
        ("writeup", "TEXT"),
    ],
    "news": [
        ("raw_excerpt", "TEXT"),
        ("writeup", "TEXT"),
    ],
}


def ensure_schema():
    conn = get_connection()
    cur = conn.cursor()
    changes = []

    for table, required_cols in REQUIRED_COLUMNS.items():
        existing_cols = {row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_name, col_type in required_cols:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                changes.append(f"{table}.{col_name}")

    conn.commit()
    conn.close()

    if changes:
        print(f"[schema] Added missing columns: {', '.join(changes)}")
    else:
        print("[schema] All required columns already present, no changes needed.")


if __name__ == "__main__":
    ensure_schema()
