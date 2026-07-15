"""
Sources candidate videos from YouTube (by upload recency, not popularity/relevance),
scores them per docs/scoring_rubric.md, and stores results in data/ai_digest.db.

Requires YOUTUBE_API_KEY in the environment.
Transcript access uses the unofficial youtube-transcript-api library since the
official Data API only allows transcript downloads for videos you own — see
the rubric's Sourcing section for why this workaround exists.
"""

import os
import re
import sys
import time
import requests
from datetime import datetime, timedelta, timezone

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, NoTranscriptFound, VideoUnavailable,
)

sys.path.insert(0, os.path.dirname(__file__))
from db_utils import (
    get_connection, now_iso, item_exists, get_item, log_snapshot,
    get_snapshot_history, is_settled, mark_settled,
)
from youtube_prefilter import evaluate_prefilter

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

# Per rubric's Sourcing / Search Parameters section
PRIMARY_KEYWORDS = [
    "claude", "claude code", "chatgpt", "gemini", "ai tools",
    "ai workflow", "ai revenue generating strategies",
]
SUBSTANCE_KEYWORDS = [
    "fine-tuning", "agent framework", "open source model",
    "ai benchmark", "ai research paper",
]
NEGATIVE_FILTER_PHRASES = [
    "make money with ai", "ai side hustle", "passive income ai",
]
REVENUE_BUCKET_KEYWORD = "ai revenue generating strategies"

SUPERLATIVES = [
    "insane", "game-changing", "game changing", "you need this", "mind-blowing",
    "mind blowing", "unbelievable", "crazy", "next level", "revolutionary",
]

SPONSOR_PHRASES = ["sponsored", "this video is brought to you by", "paid promotion"]
PAID_CTA_PHRASES = ["join my community", "enroll now", "buy my course", "get the course",
                     "sign up for my", "patreon.com", "gumroad.com"]


URL_PATTERN = re.compile(r"https?://\S+")


def parse_duration_seconds(iso_duration):
    """Parse ISO 8601 duration (e.g. PT4M13S) from contentDetails into seconds."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration or "")
    if not match:
        return None
    h, m, s = (int(x) if x else 0 for x in match.groups())
    return h * 3600 + m * 60 + s
    params = {**params, "key": YOUTUBE_API_KEY}
    resp = requests.get(f"{YOUTUBE_API}/{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def yt_get(endpoint, params):
    params = {**params, "key": YOUTUBE_API_KEY}
    resp = requests.get(f"{YOUTUBE_API}/{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def search_videos(window_hours=48):
    """Search by upload date, not relevance/viewCount — per rubric, avoids popularity pre-filtering."""
    since = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_keywords = [(k, False) for k in PRIMARY_KEYWORDS] + [(k, False) for k in SUBSTANCE_KEYWORDS] + \
                   [(REVENUE_BUCKET_KEYWORD, True)]
    results = {}
    for keyword, is_revenue_bucket in all_keywords:
        try:
            data = yt_get("search", {
                "part": "snippet", "q": keyword, "type": "video",
                "order": "date", "publishedAfter": since, "maxResults": 25,
            })
            for item in data.get("items", []):
                vid = item["id"]["videoId"]
                title_lower = item["snippet"]["title"].lower()

                # Negative filter: generic money-making titles only allowed in via the
                # dedicated revenue-strategies keyword bucket, per rubric.
                matches_negative = any(p in title_lower for p in NEGATIVE_FILTER_PHRASES)
                if matches_negative and not is_revenue_bucket:
                    continue

                if vid not in results:
                    results[vid] = {"item": item, "matched_keywords": []}
                results[vid]["matched_keywords"].append(keyword)
            time.sleep(0.3)
        except requests.RequestException as e:
            print(f"[warn] search failed for keyword '{keyword}': {e}")
    return results


def get_video_stats(video_ids):
    """Batch-fetch statistics + snippet for up to 50 IDs per call."""
    stats = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        try:
            data = yt_get("videos", {"part": "statistics,snippet,contentDetails", "id": ",".join(batch)})
            for item in data.get("items", []):
                stats[item["id"]] = item
        except requests.RequestException as e:
            print(f"[warn] stats fetch failed for batch: {e}")
    return stats


def get_channel_baseline(channel_id, exclude_video_id):
    """Returns (avg_views, upload_count_available) from the channel's last 10 uploads."""
    try:
        ch_data = yt_get("channels", {"part": "contentDetails", "id": channel_id})
        items = ch_data.get("items", [])
        if not items:
            return 0, 0
        uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        pl_data = yt_get("playlistItems", {"part": "contentDetails", "playlistId": uploads_playlist, "maxResults": 15})
        video_ids = [v["contentDetails"]["videoId"] for v in pl_data.get("items", [])
                     if v["contentDetails"]["videoId"] != exclude_video_id][:10]
        if not video_ids:
            return 0, 0
        stats = get_video_stats(video_ids)
        views = [int(s["statistics"].get("viewCount", 0)) for s in stats.values()]
        if not views:
            return 0, 0
        return sum(views) / len(views), len(views)
    except requests.RequestException as e:
        print(f"[warn] channel baseline fetch failed for {channel_id}: {e}")
        return 0, 0


def get_transcript_text(video_id):
    """Returns transcript text, or empty string if unavailable — falls back gracefully per rubric note."""
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id)
        time.sleep(1.5)  # avoid triggering YouTube's burst-rate abuse detection across many sequential fetches
        return " ".join(snippet.text for snippet in fetched)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        time.sleep(0.5)
        return ""
    except Exception as e:
        print(f"[warn] transcript fetch failed for {video_id}: {e}")
        time.sleep(3)  # back off harder on unexpected errors specifically
        return ""


def score_substance(transcript_text, description_text, title_text):
    """Implements rubric Steps 1-3 for videos, plus disqualifiers."""
    full_text = f"{title_text} {description_text} {transcript_text}"
    word_count = max(len(transcript_text.split()), 1)

    # Step 1 — Evidence Density: checkable instances (code shown, benchmark number, mechanism explained)
    checkable_patterns = [
        r"\bcode\b.{0,20}\bscreen\b", r"\bbenchmark\b", r"\d+(\.\d+)?\s?(%|tokens?/s|ms|seconds?)\b",
        r"\blet me show you\b", r"\bhere's the (code|output|result)\b",
    ]
    checkable_count = sum(len(re.findall(p, transcript_text, re.IGNORECASE)) for p in checkable_patterns)
    step1 = 2 if checkable_count >= 3 else (1 if checkable_count >= 1 else 0)

    # Step 2 — Claim Density (inverse): superlatives per 1000 words
    superlative_count = sum(transcript_text.lower().count(s) for s in SUPERLATIVES)
    superlative_rate = (superlative_count / word_count) * 1000
    step2 = 2 if superlative_rate < 2 else (1 if superlative_rate <= 5 else 0)

    # Step 3 — Call to Action
    has_paid_cta = any(p in full_text.lower() for p in PAID_CTA_PHRASES)
    step3 = 0 if has_paid_cta else 1

    base_total = step1 + step2 + step3
    base_map = {5: 5, 4: 5, 3: 4, 2: 3, 1: 2, 0: 1}
    base_score = base_map[min(base_total, 5)]

    disqualifier = None
    # Title makes a specific capability claim never substantiated in transcript
    title_claim = re.search(r"\bbeats?\b|\boutperforms?\b|\bvs\.?\b", title_text, re.IGNORECASE)
    if title_claim and checkable_count == 0:
        base_score = min(base_score, 1)
        disqualifier = "unsubstantiated_title_claim"

    sponsor_mentioned = any(p in full_text.lower() for p in SPONSOR_PHRASES)
    if sponsor_mentioned:
        # Can't measure runtime % without video analysis; flag conservatively per rubric intent.
        base_score = min(base_score, 2)
        disqualifier = disqualifier or "sponsored_content_flagged"

    if not transcript_text:
        # No transcript available at all — can't verify evidence claims, score conservatively.
        base_score = min(base_score, 2)
        disqualifier = disqualifier or "no_transcript_available"

    return base_score, (step1, step2, step3), disqualifier


def score_trend(view_count, baseline_avg, baseline_sample_size):
    if baseline_sample_size < 10:
        # Small-channel floor per rubric — use absolute view thresholds instead of ratio.
        if view_count >= 5000:
            score = 4
        elif view_count >= 1000:
            score = 3
        elif view_count >= 200:
            score = 2
        else:
            score = 1
        return score, "absolute", f"view_count={view_count} (insufficient baseline, n={baseline_sample_size})"

    ratio = view_count / baseline_avg if baseline_avg > 0 else 0
    if ratio >= 3:
        score = 5
    elif ratio >= 1.5:
        score = 4
    elif ratio >= 0.75:
        score = 3
    elif ratio >= 0.3:
        score = 2
    else:
        score = 1
    return score, "ratio", f"view_velocity_ratio={ratio:.2f}"


def process_video(conn, video_id, video_data, matched_keywords):
    url = f"https://www.youtube.com/watch?v={video_id}"
    snippet = video_data["snippet"]
    stats = video_data.get("statistics", {})
    published_at = snippet["publishedAt"]
    hours_since_publish = (datetime.now(timezone.utc) -
                            datetime.fromisoformat(published_at.replace("Z", "+00:00"))).total_seconds() / 3600
    view_count = int(stats.get("viewCount", 0))

    if item_exists(conn, "videos", url):
        if is_settled(conn, "videos", url):
            return
        log_snapshot(conn, url, "video", "view_count", view_count)
        row = get_item(conn, "videos", url)
        if row["trend_score"] == "pending" and hours_since_publish < 48:
            conn.execute("UPDATE videos SET view_count=?, date_last_updated=? WHERE url=?",
                         (view_count, now_iso(), url))
            return
        baseline_avg, baseline_n = get_channel_baseline(snippet["channelId"], video_id)
        trend_score, method, reasoning = score_trend(view_count, baseline_avg, baseline_n)
        conn.execute(
            """UPDATE videos SET trend_score=?, trend_reasoning=?, baseline_method=?,
               view_count=?, date_last_updated=? WHERE url=?""",
            (trend_score, reasoning, method, view_count, now_iso(), url),
        )
        return

    # New item
    if hours_since_publish < 48:
        trend_score, trend_reasoning, baseline_method = "pending", "under 48hrs, awaiting scoring window", None
    else:
        baseline_avg, baseline_n = get_channel_baseline(snippet["channelId"], video_id)
        trend_score, baseline_method, trend_reasoning = score_trend(view_count, baseline_avg, baseline_n)

    title = snippet.get("title", "")
    description = snippet.get("description", "")
    has_captions = video_data.get("contentDetails", {}).get("caption") == "true"

    # Gate 1: content pre-filter (sketchy/promotional signal), independent of captions
    prefilter = evaluate_prefilter(title, description, video_id=video_id, youtube_api_key=YOUTUBE_API_KEY)

    transcript_text = ""
    skip_reason = None
    if not prefilter["worth_deep_analysis"]:
        skip_reason = prefilter["skip_reason"]
    elif not has_captions:
        # Gate 2: caption availability, only checked if content pre-filter passed
        skip_reason = "no_captions_available"
    else:
        transcript_text = get_transcript_text(video_id)

    substance_score, (s1, s2, s3), disqualifier = score_substance(
        transcript_text, description, title
    )
    if skip_reason:
        disqualifier = skip_reason  # more specific than score_substance's generic fallback reason
    substance_reasoning = (
        f"evidence_density={s1}/2, claim_density={s2}/2, cta={s3}/1"
        + (f", disqualifier={disqualifier}" if disqualifier else "")
    )

    conn.execute(
        """INSERT INTO videos (
            url, content_type, title, date_first_seen, date_last_updated,
            substance_score, substance_reasoning, substance_step1, substance_step2, substance_step3,
            trend_score, trend_reasoning, baseline_method, vision_used, vision_tier, disqualifier_applied,
            included_in_digest, settled, matched_keywords, channel_id, published_at, view_count,
            title_sketchiness_score, description_sketchiness_score, resource_link_count,
            promo_link_count, neutral_link_count, comment_check_performed, comment_check_result
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,'none',?,'[]',0,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            url, "video", title, now_iso(), now_iso(),
            substance_score, substance_reasoning, s1, s2, s3,
            trend_score, trend_reasoning, baseline_method, disqualifier,
            ",".join(matched_keywords), snippet["channelId"], published_at, view_count,
            prefilter["title_sketchiness_score"], prefilter["description_sketchiness_score"],
            prefilter["resource_link_count"], prefilter["promo_link_count"], prefilter["neutral_link_count"],
            prefilter["comment_check_performed"], prefilter["comment_check_result"],
        ),
    )
    log_snapshot(conn, url, "video", "view_count", view_count)
    print(f"[new] {snippet.get('title')[:60]} — substance={substance_score} trend={trend_score}")


def main():
    if not YOUTUBE_API_KEY:
        print("[warn] YOUTUBE_API_KEY not set — the run will fail immediately.")
        return
    conn = get_connection()
    found = search_videos()
    print(f"Found {len(found)} candidate videos in window.")
    video_ids = list(found.keys())
    stats_map = get_video_stats(video_ids)

    for vid, meta in found.items():
        video_data = stats_map.get(vid)
        if not video_data:
            continue
        try:
            process_video(conn, vid, video_data, meta["matched_keywords"])
        except Exception as e:
            print(f"[error] failed on {vid}: {e}")
        conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
