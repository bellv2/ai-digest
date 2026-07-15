"""
Generates the weekly Markdown digest per docs/scoring_rubric.md's Digest
Inclusion Rules: top 5 by Substance, top 5 by Trend, top 5 Overlap (4+ on
both axes), plus a Flagged/Debunked section for newsworthy disqualifiers.

Pulls from items scored/updated in the trailing 7 days across all three
tables (repos, videos, news). Disqualified items are excluded from ranked
sections by default, per rubric, unless the disqualifier itself is
newsworthy — currently: any item with a disqualifier AND substance_score
would otherwise have been >=3 (i.e. it looked credible before the
disqualifier caught something), which is exactly the "don't miss this was
debunked" case the rubric describes.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from db_utils import get_connection, append_digest_tag

DIGESTS_DIR = Path(__file__).parent.parent / "digests"
SECTION_SIZE = 5
LOOKBACK_DAYS = 7

TABLES = ["repos", "videos", "news"]


def fetch_recent_items(conn, table, since_iso):
    rows = conn.execute(
        f"""SELECT url, title, substance_score, substance_reasoning, trend_score,
                   trend_reasoning, disqualifier_applied, date_first_seen
            FROM {table}
            WHERE date_first_seen >= ? OR date_last_updated >= ?""",
        (since_iso, since_iso),
    ).fetchall()
    items = []
    for r in rows:
        items.append({
            "content_type": table,
            "url": r["url"],
            "title": r["title"] or "(untitled)",
            "substance_score": r["substance_score"],
            "substance_reasoning": r["substance_reasoning"],
            "trend_score": r["trend_score"],
            "trend_reasoning": r["trend_reasoning"],
            "disqualifier": r["disqualifier_applied"],
        })
    return items


def is_numeric_trend(item):
    """Trend can be the string 'pending' for videos under 48hrs — exclude from trend ranking."""
    try:
        int(item["trend_score"])
        return True
    except (TypeError, ValueError):
        return False


def build_digest(conn):
    since = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).isoformat()
    all_items = []
    for table in TABLES:
        all_items.extend(fetch_recent_items(conn, table, since))

    print(f"Pulled {len(all_items)} items from trailing {LOOKBACK_DAYS} days across {len(TABLES)} tables.")

    clean_items = [i for i in all_items if not i["disqualifier"]]
    flagged_items = [
        i for i in all_items
        if i["disqualifier"] and i["substance_score"] is not None and i["substance_score"] >= 3
    ]

    top_substance = sorted(
        [i for i in clean_items if i["substance_score"] is not None],
        key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0),
        reverse=True,
    )[:SECTION_SIZE]

    top_trend = sorted(
        [i for i in clean_items if is_numeric_trend(i)],
        key=lambda i: (int(i["trend_score"]), i["substance_score"] or 0),
        reverse=True,
    )[:SECTION_SIZE]

    overlap = sorted(
        [i for i in clean_items if i["substance_score"] is not None and i["substance_score"] >= 4
         and is_numeric_trend(i) and int(i["trend_score"]) >= 4],
        key=lambda i: (i["substance_score"] + int(i["trend_score"])),
        reverse=True,
    )[:SECTION_SIZE]

    flagged = sorted(flagged_items, key=lambda i: i["substance_score"], reverse=True)[:SECTION_SIZE]

    return top_substance, top_trend, overlap, flagged


def format_item(item, show_trend=True, show_substance=True):
    lines = [f"**[{item['title']}]({item['url']})** — _{item['content_type']}_"]
    if show_substance and item["substance_score"] is not None:
        lines.append(f"  Substance: {item['substance_score']}/5 — {item['substance_reasoning']}")
    if show_trend and is_numeric_trend(item):
        lines.append(f"  Trend: {item['trend_score']}/5 — {item['trend_reasoning']}")
    return "\n".join(lines)


def render_markdown(date_str, top_substance, top_trend, overlap, flagged):
    lines = [f"# AI Digest — {date_str}", ""]

    lines.append("## 🏆 Overlap — highest on both axes")
    lines.append("")
    if overlap:
        for item in overlap:
            lines.append(format_item(item))
            lines.append("")
    else:
        lines.append("_Nothing cleared both thresholds this week._")
        lines.append("")

    lines.append("## 🧠 Top Substance")
    lines.append("")
    if top_substance:
        for item in top_substance:
            lines.append(format_item(item, show_trend=False))
            lines.append("")
    else:
        lines.append("_No items scored this week._")
        lines.append("")

    lines.append("## 📈 Top Trend")
    lines.append("")
    if top_trend:
        for item in top_trend:
            lines.append(format_item(item, show_substance=False))
            lines.append("")
    else:
        lines.append("_No items with a computed trend score this week (many may still be in their 48hr pending window)._")
        lines.append("")

    if flagged:
        lines.append("## ⚠️ Flagged / Debunked")
        lines.append("_Items that looked credible but tripped a disqualifier — worth knowing what didn't hold up._")
        lines.append("")
        for item in flagged:
            lines.append(format_item(item))
            lines.append(f"  Flag: `{item['disqualifier']}`")
            lines.append("")

    return "\n".join(lines)


def mark_included(conn, items, date_str):
    for item in items:
        append_digest_tag(conn, item["content_type"], item["url"], date_str)


def main():
    conn = get_connection()
    top_substance, top_trend, overlap, flagged = build_digest(conn)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    markdown = render_markdown(date_str, top_substance, top_trend, overlap, flagged)

    DIGESTS_DIR.mkdir(exist_ok=True)
    out_path = DIGESTS_DIR / f"{date_str}.md"
    out_path.write_text(markdown)

    for items in (top_substance, top_trend, overlap):
        mark_included(conn, items, date_str)
    conn.commit()
    conn.close()

    print(f"Digest written to {out_path}")
    print(f"  Overlap: {len(overlap)}, Top Substance: {len(top_substance)}, Top Trend: {len(top_trend)}, Flagged: {len(flagged)}")


if __name__ == "__main__":
    main()
