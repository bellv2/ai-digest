"""
Sources candidate articles from tiered RSS feeds, scores them per
docs/scoring_rubric.md, and stores results in data/ai_digest.db.

No API key required — RSS is public. Feed URLs verified working as of
implementation; see notes on Ars Technica/The Verge below (blocked from
cloud IPs) and the Anthropic feed (third-party mirror, no official RSS exists).
"""

import os
import re
import sys
import time
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
from db_utils import get_connection, now_iso, item_exists

# Per rubric's Sourcing / RSS section. Tier reflects trust level for the
# Substance rubric's Primary Source Check and the Trend corroboration formula.
#
# NOTE: Ars Technica and The Verge block requests from cloud-provider IPs
# (403 regardless of user-agent) — same class of problem as the YouTube
# transcript blocking. Excluded from the active list until a proxy solution
# is worth the added complexity; revisit if Tier 2 coverage feels thin.
#
# NOTE: Anthropic has no official RSS feed. Using a third-party-maintained
# mirror that points to real claude.com/blog URLs — functional but adds a
# small dependency risk if that maintainer stops updating it.
FEEDS = {
    # Tier 1 — primary sources
    "https://openai.com/news/rss.xml": 1,
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_claude.xml": 1,
    "https://deepmind.google/blog/rss.xml": 1,
    "https://huggingface.co/blog/feed.xml": 1,
    "http://export.arxiv.org/rss/cs.AI": 1,
    # Tier 2 — technical/editorial analysis
    "https://www.technologyreview.com/topic/artificial-intelligence/feed": 2,
    "https://lastweekin.ai/feed": 2,
    "https://thegradient.pub/rss/": 2,
    # Tier 3 — velocity signal, weighted lower on substance by default
    "https://venturebeat.com/feed/": 3,
}

PRIMARY_SOURCE_DOMAINS = [
    "openai.com", "anthropic.com", "claude.com", "deepmind.google",
    "huggingface.co", "arxiv.org",
]

QUANTIFIED_PATTERN = re.compile(
    r"\d+(\.\d+)?\s?(%|percent|x|times|billion|million|gb|mb|tb|ms|seconds?|tokens?)\b",
    re.IGNORECASE,
)
CAVEAT_PATTERN = re.compile(
    r"\bhowever\b|\balthough\b|\bbut\b.{0,30}\blimitation\b|\bcaveat\b|\bstill (fails|struggles)\b|"
    r"\bnot (yet|without)\b|\bfalls short\b",
    re.IGNORECASE,
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "new", "how", "what", "why", "this", "that", "its", "as", "at", "by", "from",
}

ARXIV_ID_FROM_LINK = re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", re.IGNORECASE)


def get_repo_cited_arxiv_ids(conn):
    """
    Cross-reference set: arXiv papers cited by any sourced repo's README.
    Per the rubric's arXiv-flooding fix — a paper only earns a spot in the
    news feed if a repo in the pipeline actually cites it, since arXiv's raw
    daily volume (hundreds of papers) would otherwise drown out real news.
    """
    cited = set()
    try:
        rows = conn.execute("SELECT cited_arxiv_ids FROM repos WHERE cited_arxiv_ids IS NOT NULL AND cited_arxiv_ids != ''").fetchall()
        for (ids_str,) in rows:
            cited.update(i.strip() for i in ids_str.split(",") if i.strip())
    except Exception as e:
        print(f"[warn] could not read repos.cited_arxiv_ids (has source_repos.py been run yet?): {e}")
    return cited


def source_domain(url):
    return urlparse(url).netloc.replace("www.", "")


def fetch_feed(url):
    try:
        f = feedparser.parse(url)
        return f.entries
    except Exception as e:
        print(f"[warn] failed to fetch feed {url}: {e}")
        return []


def within_window(entry, window_hours=48):
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return True  # can't determine age, include conservatively rather than silently drop
    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - pub_dt) <= timedelta(hours=window_hours)


def title_keywords(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def score_substance(title, summary, link, tier):
    full_text = f"{title} {summary}"
    domain = source_domain(link)

    # Step 1 — Primary Source Check
    is_primary_domain = any(d in domain for d in PRIMARY_SOURCE_DOMAINS)
    if is_primary_domain:
        step1 = 2
    elif re.search(r"according to|reports? (that|from)|cited? (by|from)", full_text, re.IGNORECASE):
        step1 = 1
    else:
        step1 = 0

    # Step 2 — Number Specificity
    quant_matches = QUANTIFIED_PATTERN.findall(full_text)
    step2 = 2 if len(quant_matches) >= 2 else (1 if quant_matches else 0)

    # Step 3 — Limitation Disclosure
    step3 = 1 if CAVEAT_PATTERN.search(full_text) else 0

    base_total = step1 + step2 + step3
    base_map = {5: 5, 4: 5, 3: 4, 2: 3, 1: 2, 0: 1}
    base_score = base_map[min(base_total, 5)]

    disqualifier = None
    # Headline makes a claim with no number anywhere in the body
    headline_has_claim = bool(re.search(r"\bbeats?\b|\boutperforms?\b|\bfaster\b|\bcheaper\b|\bbetter\b", title, re.IGNORECASE))
    if headline_has_claim and not quant_matches:
        base_score = min(base_score, 1)
        disqualifier = "unsubstantiated_headline_claim"

    return base_score, (step1, step2, step3), disqualifier


def score_trend(title, published_dt, all_recent_entries, tier):
    """Corroboration count — distinct source domains covering the same story within 48hrs."""
    this_keywords = title_keywords(title)
    if not this_keywords:
        return 1, "no_keywords_extracted"

    corroborating_domains = set()
    for other_url, other_tier, other_title, other_link, other_dt in all_recent_entries:
        if other_link == published_dt[1]:
            continue
        other_keywords = title_keywords(other_title)
        if not other_keywords:
            continue
        overlap = len(this_keywords & other_keywords) / max(len(this_keywords | other_keywords), 1)
        if overlap >= 0.6:
            corroborating_domains.add(source_domain(other_link))

    count = len(corroborating_domains)
    if count >= 4:
        score = 5
    elif count >= 2:
        score = 4
    elif count == 1 and tier <= 2:
        score = 3
    elif count == 1:
        score = 2
    else:
        score = 1
    return score, f"corroboration_count={count}"


def main():
    conn = get_connection()
    cited_arxiv_ids = get_repo_cited_arxiv_ids(conn)
    print(f"Cross-reference set: {len(cited_arxiv_ids)} arXiv IDs cited by sourced repos.")

    all_entries = []  # (feed_url, tier, title, link, published_dt) — for corroboration matching
    parsed_by_feed = {}

    for feed_url, tier in FEEDS.items():
        entries = fetch_feed(feed_url)
        parsed_by_feed[feed_url] = (entries, tier)
        for entry in entries:
            if not within_window(entry):
                continue
            title = entry.get("title", "")
            link = entry.get("link", "")

            # arXiv cap: only include if a sourced repo actually cites this paper.
            arxiv_match = ARXIV_ID_FROM_LINK.search(link)
            if arxiv_match and arxiv_match.group(1) not in cited_arxiv_ids:
                continue

            published = entry.get("published_parsed") or entry.get("updated_parsed")
            pub_dt = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
            all_entries.append((feed_url, tier, title, link, pub_dt))
        time.sleep(0.3)

    print(f"Found {len(all_entries)} candidate articles across {len(FEEDS)} feeds in window (post arXiv-cap).")

    for feed_url, tier, title, link, pub_dt in all_entries:
        if not link or item_exists(conn, "news", link):
            continue

        entries, _ = parsed_by_feed[feed_url]
        matching_entry = next((e for e in entries if e.get("link") == link), None)
        summary = matching_entry.get("summary", "") if matching_entry else ""

        substance_score, (s1, s2, s3), disqualifier = score_substance(title, summary, link, tier)
        trend_score, trend_reasoning = score_trend(title, (feed_url, link), all_entries, tier)

        substance_reasoning = (
            f"primary_source={s1}/2, number_specificity={s2}/2, limitation_disclosure={s3}/1"
            + (f", disqualifier={disqualifier}" if disqualifier else "")
        )

        try:
            conn.execute(
                """INSERT INTO news (
                    url, content_type, title, date_first_seen, date_last_updated,
                    substance_score, substance_reasoning, substance_step1, substance_step2, substance_step3,
                    trend_score, trend_reasoning, vision_used, vision_tier, disqualifier_applied,
                    included_in_digest, settled, source_domain, source_tier, published_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,'none',?,'[]',0,?,?,?)""",
                (
                    link, "news", title, now_iso(), now_iso(),
                    substance_score, substance_reasoning, s1, s2, s3,
                    trend_score, trend_reasoning, disqualifier,
                    source_domain(link), tier, pub_dt.isoformat(),
                ),
            )
            print(f"[new] {title[:60]} — substance={substance_score} trend={trend_score} (tier {tier})")
        except Exception as e:
            print(f"[error] failed to store {link}: {e}")
        conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
