"""
Generates a short narrative writeup for each item selected into tonight's
digest, using the raw content already stored at sourcing time (README
excerpt, transcript excerpt, or article summary) plus its scores.

Runs AFTER generate_digest.py, using its selections, so writeups are only
generated for the ~15-20 items that actually make the digest — not all
sourced items — keeping Gemini API usage proportional to what's actually
delivered rather than everything scored.
"""

import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(__file__))
from db_utils import get_connection

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

WRITEUP_PROMPT = """You are writing a brief, plain-English explanation for a personal AI news digest. Given the item below, write a 3-4 sentence writeup covering: what it actually is/does, why it scored well (be specific, don't just restate the score), and who it might matter to. No marketing language, no superlatives. If the raw content is thin, say so honestly rather than padding.

Title: {title}
Type: {content_type}
Substance score: {substance_score}/5 ({substance_reasoning})
Trend score: {trend_score}/5
Raw content excerpt:
{raw_excerpt}

Writeup:"""


def generate_writeup(item):
    if not GEMINI_API_KEY:
        return None
    raw_excerpt = item["raw_excerpt"] or "(no raw content captured for this item)"
    prompt = WRITEUP_PROMPT.format(
        title=item["title"],
        content_type=item["content_type"],
        substance_score=item["substance_score"],
        substance_reasoning=item["substance_reasoning"],
        trend_score=item["trend_score"],
        raw_excerpt=raw_excerpt[:2500],
    )
    try:
        resp = requests.post(
            f"{GEMINI_API}?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[warn] writeup generation failed for {item['title']}: {e}")
        return None


TABLE_NAME_MAP = {"repo": "repos", "video": "videos", "news": "news"}


def get_digest_items(conn, digest_date):
    """Pull every item tagged with today's digest date across all three tables."""
    items = []
    for table in ("repos", "videos", "news"):
        rows = conn.execute(
            f"""SELECT url, title, content_type, substance_score, substance_reasoning,
                       trend_score, raw_excerpt, writeup
                FROM {table} WHERE included_in_digest LIKE ?""",
            (f'%"{digest_date}"%',),
        ).fetchall()
        for r in rows:
            items.append(dict(r))
    return items


def main(digest_date):
    if not GEMINI_API_KEY:
        print("[warn] GEMINI_API_KEY not set — skipping writeup generation entirely.")
        return

    conn = get_connection()
    items = get_digest_items(conn, digest_date)
    print(f"Generating writeups for {len(items)} digest items ({digest_date}).")

    for item in items:
        if item["writeup"]:
            continue  # already generated in a prior run, don't regenerate/re-bill
        writeup = generate_writeup(item)
        if writeup:
            table = TABLE_NAME_MAP[item["content_type"]]
            conn.execute(
                f"UPDATE {table} SET writeup = ? WHERE url = ?",
                (writeup, item["url"]),
            )
            conn.commit()
            print(f"[writeup] {item['title'][:50]}")

    conn.close()


if __name__ == "__main__":
    import argparse
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    args = parser.parse_args()
    main(args.date)
