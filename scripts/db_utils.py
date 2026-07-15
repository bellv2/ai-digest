"""
Shared SQLite helper functions for the ai-digest pipeline.
All sourcing/scoring scripts import from here to keep database logic
in one place instead of duplicated across repos/videos/news scripts.
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ai_digest.db"


def get_connection():
    """Open a connection to the shared database. Callers are responsible for closing it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    """Current UTC timestamp as an ISO string, used consistently across all tables."""
    return datetime.now(timezone.utc).isoformat()


def item_exists(conn, table, url):
    """Check whether a URL is already tracked, per the dedup rule in the rubric."""
    cur = conn.execute(f"SELECT url FROM {table} WHERE url = ?", (url,))
    return cur.fetchone() is not None


def get_item(conn, table, url):
    cur = conn.execute(f"SELECT * FROM {table} WHERE url = ?", (url,))
    return cur.fetchone()


def log_snapshot(conn, url, content_type, metric_name, metric_value):
    """
    Record a daily metric snapshot (star count, view count, etc.) so velocity
    formulas have real deltas to compute against on future runs.
    """
    conn.execute(
        """INSERT INTO snapshots (url, content_type, snapshot_date, metric_name, metric_value)
           VALUES (?, ?, ?, ?, ?)""",
        (url, content_type, now_iso(), metric_name, metric_value),
    )


def get_snapshot_history(conn, url, metric_name):
    """Return all logged snapshots for a given item/metric, oldest first."""
    cur = conn.execute(
        """SELECT snapshot_date, metric_value FROM snapshots
           WHERE url = ? AND metric_name = ? ORDER BY snapshot_date ASC""",
        (url, metric_name),
    )
    return cur.fetchall()


def days_since_first_seen(conn, table, url):
    """Used to determine whether an item has crossed the 14-day settling window."""
    row = get_item(conn, table, url)
    if row is None:
        return 0
    first_seen = datetime.fromisoformat(row["date_first_seen"])
    delta = datetime.now(timezone.utc) - first_seen
    return delta.days


def is_settled(conn, table, url):
    """Per the rubric's Pipeline Operational Notes: items stop being re-polled after 14 days."""
    row = get_item(conn, table, url)
    if row is None:
        return False
    if row["settled"]:
        return True
    return days_since_first_seen(conn, table, url) >= 14


def mark_settled(conn, table, url):
    conn.execute(f"UPDATE {table} SET settled = 1 WHERE url = ?", (url,))


def append_digest_tag(conn, table, url, digest_date):
    """Track which digests an item appeared in, without overwriting prior history."""
    row = get_item(conn, table, url)
    if row is None:
        return
    tags = json.loads(row["included_in_digest"] or "[]")
    if digest_date not in tags:
        tags.append(digest_date)
    conn.execute(
        f"UPDATE {table} SET included_in_digest = ? WHERE url = ?",
        (json.dumps(tags), url),
    )
