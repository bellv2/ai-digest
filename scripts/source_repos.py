"""
Sources candidate repos from GitHub (by recency, not popularity), scores them
per docs/scoring_rubric.md, and stores results in data/ai_digest.db.

Requires GH_API_TOKEN in the environment (higher rate limits authenticated).
"""

import os
import re
import sys
import time
import requests
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from db_utils import (
    get_connection, now_iso, item_exists, get_item, log_snapshot,
    get_snapshot_history, is_settled, mark_settled,
)

GITHUB_TOKEN = os.environ.get("GH_API_TOKEN")
GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Per rubric's Sourcing / Search Parameters section
SEARCH_TOPICS = [
    "llm", "agent", "rag", "fine-tuning", "ai-tools", "claude", "gpt", "gemini",
    "benchmark", "inference-optimization", "evaluation",
]

ARXIV_PATTERN = re.compile(r"arxiv\.org/abs/\d{4}\.\d{4,5}|arxiv\.org/pdf/\d{4}\.\d{4,5}", re.IGNORECASE)
ARXIV_ID_PATTERN = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.IGNORECASE)


def extract_arxiv_ids(readme_text):
    """Returns normalized arXiv IDs (e.g. '2401.12345') cited in the README, for cross-referencing
    against the news pipeline's arXiv cap — see docs/scoring_rubric.md's arXiv handling note."""
    return sorted(set(ARXIV_ID_PATTERN.findall(readme_text)))
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+")
QUANTIFIED_CLAIM_PATTERN = re.compile(
    r"\d+(\.\d+)?\s?(%|x|times|percent|gb|mb|ms|seconds?)\b", re.IGNORECASE
)
CODE_FILE_EXTENSIONS = (".py", ".ipynb", ".js", ".ts", ".go", ".rs", ".cpp", ".c", ".java")


def search_repos(window_hours=48):
    """
    Pull repos created or pushed within the rolling window, sorted by recency
    (not GitHub's Trending page) — per the rubric's no-popularity-filter rule.
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = {}
    for topic in SEARCH_TOPICS:
        query = f"topic:{topic} pushed:>{since}"
        try:
            resp = requests.get(
                f"{GITHUB_API}/search/repositories",
                headers=HEADERS,
                params={"q": query, "sort": "updated", "order": "desc", "per_page": 25},
                timeout=15,
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                results[item["html_url"]] = item  # dedupe across topic searches by URL
            time.sleep(1)  # stay well under rate limits across the multi-topic loop
        except requests.RequestException as e:
            print(f"[warn] search failed for topic '{topic}': {e}")
    return list(results.values())


def get_readme_text(repo_full_name):
    try:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo_full_name}/readme",
            headers={**HEADERS, "Accept": "application/vnd.github.raw+json"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.text
        if resp.status_code == 403:
            print(f"[warn] rate-limited fetching README for {repo_full_name} — check GH_API_TOKEN is set")
        elif resp.status_code != 404:
            print(f"[warn] unexpected status {resp.status_code} fetching README for {repo_full_name}")
    except requests.RequestException as e:
        print(f"[warn] README fetch failed for {repo_full_name}: {e}")
    return ""


def get_commit_stats(repo_full_name):
    """Returns (commit_count, distinct_days) from the most recent 100 commits (API page cap)."""
    try:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo_full_name}/commits",
            headers=HEADERS,
            params={"per_page": 100},
            timeout=15,
        )
        if resp.status_code == 200:
            commits = resp.json()
            dates = set()
            for c in commits:
                date_str = c.get("commit", {}).get("author", {}).get("date", "")
                if date_str:
                    dates.add(date_str[:10])
            return len(commits), len(dates)
        if resp.status_code == 403:
            print(f"[warn] rate-limited fetching commits for {repo_full_name} — check GH_API_TOKEN is set")
        elif resp.status_code != 409:  # 409 = empty repo, not an error worth logging
            print(f"[warn] unexpected status {resp.status_code} fetching commits for {repo_full_name}")
        return 0, 0
    except requests.RequestException as e:
        print(f"[warn] commit fetch failed for {repo_full_name}: {e}")
        return 0, 0


def get_repo_file_extensions(repo_full_name):
    """Check the repo tree for presence of any recognized code file extension."""
    try:
        resp = requests.get(
            f"{GITHUB_API}/repos/{repo_full_name}/git/trees/HEAD",
            headers=HEADERS,
            params={"recursive": "1"},
            timeout=15,
        )
        if resp.status_code == 200:
            tree = resp.json().get("tree", [])
            return any(entry["path"].lower().endswith(CODE_FILE_EXTENSIONS) for entry in tree if entry.get("type") == "blob")
        if resp.status_code == 403:
            print(f"[warn] rate-limited fetching tree for {repo_full_name} — check GH_API_TOKEN is set")
        elif resp.status_code != 404:
            print(f"[warn] unexpected status {resp.status_code} fetching tree for {repo_full_name}")
    except requests.RequestException as e:
        print(f"[warn] tree fetch failed for {repo_full_name}: {e}")
    return False


def score_substance(readme_text, commit_count, distinct_days, has_code):
    """Implements rubric Steps 1-3 for repos, plus disqualifiers."""
    step1 = 2 if ARXIV_PATTERN.search(readme_text) or DOI_PATTERN.search(readme_text) else (
        1 if re.search(r"\bpaper\b|\btechnique\b|\bmethod\b", readme_text, re.IGNORECASE) else 0
    )
    has_benchmark_table = bool(re.search(r"\|.*\|.*\|", readme_text)) and len(QUANTIFIED_CLAIM_PATTERN.findall(readme_text)) >= 2
    step2 = 2 if has_benchmark_table else (1 if QUANTIFIED_CLAIM_PATTERN.search(readme_text) else 0)
    step3 = 1 if (commit_count >= 15 and distinct_days >= 5) else 0

    base_total = step1 + step2 + step3
    base_map = {5: 5, 4: 5, 3: 4, 2: 3, 1: 2, 0: 1}
    base_score = base_map[min(base_total, 5)]

    disqualifier = None
    if not has_code:
        base_score = min(base_score, 1)
        disqualifier = "no_executable_code"
    elif QUANTIFIED_CLAIM_PATTERN.search(readme_text) and not has_benchmark_table and step2 == 1 and commit_count < 3:
        # Weak signal heuristic: claim present but almost no engineering behind it.
        base_score = min(base_score, 2)
        disqualifier = "claim_without_receipts"

    return base_score, (step1, step2, step3), disqualifier


def score_trend(conn, url, stars, forks, created_at):
    """Implements the rubric's star_velocity_ratio / fork_ratio formula."""
    history = get_snapshot_history(conn, url, "stargazers_count")
    log_snapshot(conn, url, "repo", "stargazers_count", stars)

    if not history:
        # First sighting — no delta data yet, defaults to 3 per rubric.
        return 3, "first snapshot — no velocity data yet, defaulted per rubric"

    oldest_date, oldest_value = history[0]["snapshot_date"], history[0]["metric_value"]
    lifetime_days = max(
        (datetime.now(timezone.utc) - datetime.fromisoformat(created_at.replace("Z", "+00:00"))).days, 1
    )
    avg_daily = max(stars / lifetime_days, 0.5)  # rubric's minimum denominator guard
    recent_gain = max(stars - oldest_value, 0)
    velocity_ratio = recent_gain / avg_daily
    fork_ratio = forks / stars if stars > 0 else 0

    if velocity_ratio >= 8 and fork_ratio >= 0.15:
        score = 5
    elif velocity_ratio >= 8 or (velocity_ratio >= 4 and fork_ratio >= 0.10):
        score = 4
    elif 2 <= velocity_ratio < 4:
        score = 3
    elif 0.5 <= velocity_ratio < 2:
        score = 2
    else:
        score = 1

    reasoning = f"velocity_ratio={velocity_ratio:.2f}, fork_ratio={fork_ratio:.2f}"
    return score, reasoning


def process_repo(conn, repo):
    url = repo["html_url"]
    full_name = repo["full_name"]

    if item_exists(conn, "repos", url):
        if is_settled(conn, "repos", url):
            return  # past 14-day window, no longer polled per rubric
        # Re-fetch trend-relevant data only; substance is scored once at first sighting.
        stars = repo["stargazers_count"]
        forks = repo["forks_count"]
        trend_score, trend_reasoning = score_trend(conn, url, stars, forks, repo["created_at"])
        conn.execute(
            """UPDATE repos SET trend_score=?, trend_reasoning=?, stargazers_count=?,
               forks_count=?, date_last_updated=? WHERE url=?""",
            (trend_score, trend_reasoning, stars, forks, now_iso(), url),
        )
        if (datetime.now(timezone.utc) - datetime.fromisoformat(
            get_item(conn, "repos", url)["date_first_seen"])).days >= 14:
            mark_settled(conn, "repos", url)
        return

    # New item — full substance + trend scoring
    readme_text = get_readme_text(full_name)
    commit_count, distinct_days = get_commit_stats(full_name)
    has_code = get_repo_file_extensions(full_name)
    substance_score, (s1, s2, s3), disqualifier = score_substance(readme_text, commit_count, distinct_days, has_code)
    trend_score, trend_reasoning = score_trend(conn, url, repo["stargazers_count"], repo["forks_count"], repo["created_at"])
    cited_arxiv_ids = extract_arxiv_ids(readme_text)

    substance_reasoning = (
        f"paper_ref={s1}/2, comparative_evidence={s2}/2, engineering_depth={s3}/1"
        + (f", disqualifier={disqualifier}" if disqualifier else "")
    )

    conn.execute(
        """INSERT INTO repos (
            url, content_type, title, date_first_seen, date_last_updated,
            substance_score, substance_reasoning, substance_step1, substance_step2, substance_step3,
            trend_score, trend_reasoning, vision_used, vision_tier, disqualifier_applied,
            included_in_digest, settled, matched_topics, stargazers_count, forks_count, created_at,
            cited_arxiv_ids, raw_excerpt
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,'none',?,'[]',0,?,?,?,?,?,?)""",
        (
            url, "repo", repo.get("name"), now_iso(), now_iso(),
            substance_score, substance_reasoning, s1, s2, s3,
            trend_score, trend_reasoning, disqualifier,
            "", repo["stargazers_count"], repo["forks_count"], repo["created_at"],
            ",".join(cited_arxiv_ids), readme_text[:3000],
        ),
    )
    print(f"[new] {full_name} — substance={substance_score} trend={trend_score}")


def main():
    if not GITHUB_TOKEN:
        print("[warn] GH_API_TOKEN not set — unauthenticated rate limit is only 60 requests/hour, "
              "the run will likely fail partway through. Set it before running for real.")
    conn = get_connection()
    repos = search_repos()
    print(f"Found {len(repos)} candidate repos in window.")
    for repo in repos:
        try:
            process_repo(conn, repo)
        except Exception as e:
            print(f"[error] failed on {repo.get('full_name')}: {e}")
        conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
