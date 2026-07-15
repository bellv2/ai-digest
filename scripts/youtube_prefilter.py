"""
Implements docs/youtube_prefilter_criteria.md — decides whether a video is
worth deep analysis (transcript fetch) based on title/description/comment
sketchiness signals, independent of the caption-availability gate in
source_videos.py's main flow.
"""

import re
import time
import requests

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

RESOURCE_DOMAINS = [
    "github.com", "gitlab.com", "huggingface.co", "arxiv.org", "doi.org",
    "docs.anthropic.com", "platform.openai.com", "ai.google.dev",
]
PROMO_DOMAINS = [
    "skool.com", "gumroad.com", "patreon.com", "ko-fi.com", "buymeacoffee.com",
    "teachable.com", "kajabi.com", "circle.so", "calendly.com",
]
PROMO_URL_PATTERNS = [
    r"\?ref=", r"\?via=", r"\?aff=", r"/affiliate/",
]
NEUTRAL_DOMAINS = [
    "twitter.com", "x.com", "linkedin.com", "instagram.com",
    "youtube.com/@", "youtube.com/channel", "youtube.com/c/",
]

URL_PATTERN = re.compile(r"https?://\S+")

TITLE_RED_PATTERNS = [
    r"\$[\d,]+\s*(k|K)?\s*(/|per\s+)?(day|month|week)",  # recurring income claim
    r"made\s+me\s+\$[\d,]+\s*(k|K)?\b",  # lump-sum income claim ("made me $220K")
    r"\bearn(ed)?\s+\$[\d,]+\s*(k|K)?\b",
    r"\bsecret\b", r"\bhack\b", r"\bbefore it'?s banned\b",
    r"they don'?t want you to know",
]
TITLE_GREEN_PATTERNS = [
    r"\bv?\d+\.\d+(\.\d+)?\b",  # version numbers
    r"\bvs\.?\b",
    r"\bhow does\b.*\bwork\b",
    r"\bgpt-?\d|\bswe-?bench|\bclaude|\bgemini",
]

DESC_CTA_PATTERNS = [
    r"link in bio", r"join my", r"limited spots", r"click below",
    r"dm me for",
]


def classify_url(url):
    url_lower = url.lower()
    if any(d in url_lower for d in NEUTRAL_DOMAINS):
        return "neutral"
    if any(d in url_lower for d in PROMO_DOMAINS) or any(re.search(p, url_lower) for p in PROMO_URL_PATTERNS):
        return "promo"
    if any(d in url_lower for d in RESOURCE_DOMAINS):
        return "resource"
    return "neutral"  # unclassified links default to neutral, not penalized


def classify_all_links(description):
    urls = URL_PATTERN.findall(description)
    counts = {"resource": 0, "promo": 0, "neutral": 0}
    first_bucket = None
    for i, url in enumerate(urls):
        bucket = classify_url(url)
        counts[bucket] += 1
        if i == 0:
            first_bucket = bucket
    return counts, first_bucket


def score_title(title):
    red = sum(1 for p in TITLE_RED_PATTERNS if re.search(p, title, re.IGNORECASE))
    green = sum(1 for p in TITLE_GREEN_PATTERNS if re.search(p, title, re.IGNORECASE))
    all_caps_words = [w for w in title.split() if w.isupper() and len(w) > 1 and w not in ("AI", "LLM", "API")]
    if len(all_caps_words) >= 2:
        red += 1
    return max(red - green, 0)


def score_description(description):
    link_counts, first_link_bucket = classify_all_links(description)
    red = 0
    green = 0

    if first_link_bucket == "promo":
        red += 1
    if link_counts["promo"] >= 3:
        red += 1
    if any(re.search(p, description, re.IGNORECASE) for p in DESC_CTA_PATTERNS):
        red += 1
    if link_counts["promo"] > 0 and link_counts["resource"] == 0 and len(description.split()) < 30:
        red += 1  # entirely CTA-driven, no real content description

    if link_counts["resource"] >= 1:
        green += 1
    if re.search(r"\d{1,2}:\d{2}", description):  # timestamps/chapters
        green += 1
    if len(description.split()) >= 60:  # substantive prose, not just link dump
        green += 1

    return max(red - green, 0), link_counts


def get_top_comments(video_id, api_key, max_results=10):
    """commentThreads.list — 1 quota unit per call, negligible cost per rubric verification."""
    try:
        resp = requests.get(
            f"{YOUTUBE_API}/commentThreads",
            params={
                "part": "snippet", "videoId": video_id, "order": "relevance",
                "maxResults": max_results, "key": api_key,
            },
            timeout=15,
        )
        if resp.status_code == 403:
            return None  # comments disabled — treat as neutral, not a red flag
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.RequestException:
        return None


def check_comments(video_id, api_key):
    """
    Returns (decisive_red_flag: bool, reasoning: str).
    Only called for borderline title+description scores, per the criteria doc.
    """
    comments = get_top_comments(video_id, api_key)
    time.sleep(0.2)
    if comments is None:
        return False, "comments_unavailable_or_disabled"

    if not comments:
        return False, "no_comments_found"

    # Check pinned/top comment for promotional content — first result is highest-relevance
    top_snippet = comments[0]["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
    if classify_all_links(top_snippet)[1] == "promo":
        return True, "top_comment_is_promotional"

    scam_flags = 0
    substantive_count = 0
    for c in comments:
        text = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        like_count = c["snippet"]["topLevelComment"]["snippet"].get("likeCount", 0)
        if re.search(r"\bscam\b|\bmisleading\b|\bfake\b", text, re.IGNORECASE) and like_count >= 3:
            scam_flags += 1
        if len(text.split()) >= 15 and ("?" in text or re.search(r"\bcode\b|\bmodel\b|\bbenchmark\b", text, re.IGNORECASE)):
            substantive_count += 1

    if scam_flags >= 1:
        return True, f"{scam_flags} comment(s) flagging scam/misleading with community agreement"

    return False, f"{substantive_count}/{len(comments)} comments substantive, no red flags"


def evaluate_prefilter(title, description, video_id=None, youtube_api_key=None):
    """
    Main entry point implementing the combined decision logic from
    docs/youtube_prefilter_criteria.md. Returns a dict with the decision
    and all diagnostic fields for storage.
    """
    title_score = score_title(title)
    desc_score, link_counts = score_description(description)
    combined = title_score + desc_score

    result = {
        "title_sketchiness_score": title_score,
        "description_sketchiness_score": desc_score,
        "resource_link_count": link_counts["resource"],
        "promo_link_count": link_counts["promo"],
        "neutral_link_count": link_counts["neutral"],
        "comment_check_performed": 0,
        "comment_check_result": None,
        "worth_deep_analysis": None,
        "skip_reason": None,
    }

    if combined == 0:
        result["worth_deep_analysis"] = True
        return result

    if combined >= 3:
        result["worth_deep_analysis"] = False
        result["skip_reason"] = f"sketchy_content:{combined}"
        return result

    # Borderline (1-2) — escalate to comment check if we have the means to
    if video_id and youtube_api_key:
        decisive_red_flag, reasoning = check_comments(video_id, youtube_api_key)
        result["comment_check_performed"] = 1
        result["comment_check_result"] = reasoning
        if decisive_red_flag:
            result["worth_deep_analysis"] = False
            result["skip_reason"] = f"sketchy_content:comment_check:{reasoning}"
            return result

    result["worth_deep_analysis"] = True
    return result
