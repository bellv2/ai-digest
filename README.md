# ai-digest

Automated nightly pipeline that sources, scores, and digests AI-related repos, YouTube videos, and news — filtered for genuine substance and real trend velocity rather than popularity alone.

## Structure

```
ai-digest/
├── data/
│   └── ai_digest.db       ← SQLite database (repos, videos, news, snapshots tables)
├── digests/
│   └── YYYY-MM-DD.md      ← weekly generated digest, one file per week
├── docs/
│   └── scoring_rubric.md  ← the master scoring rubric — grading standard for the LLM scoring pass
├── scripts/                ← sourcing, scoring, and digest-generation scripts (in progress)
└── README.md
```

## How it works

1. **Sourcing** — nightly routine pulls candidate repos (GitHub search API, by recency not popularity), videos (YouTube Data API, by upload date), and news (RSS feeds, tiered by source trust) per the keyword/search parameters defined in `docs/scoring_rubric.md`.
2. **Scoring** — every new item is scored on two independent axes, Substance and Trend, using the measurable formulas/checklists in the rubric. Vision analysis (Gemini Flash-Lite) is escalated only when genuinely necessary per the vision-tiering logic.
3. **Storage** — all scored items are stored permanently in `data/ai_digest.db`, regardless of whether they make a digest. This is the durable memory layer — nothing is lost even if it's never "trending."
4. **Digest** — generated weekly as a Markdown file in `digests/`, pulling the top 5 items per section (Top Substance / Top Trend / Overlap) from the trailing 7 days.

## Automation

Runs nightly via a Claude Code cloud Routine (not dependent on any local machine being on). See `docs/scoring_rubric.md` → "Pipeline Operational Notes" for dedup logic, re-scoring cadence, and retention policy.

## Secrets

This repo requires the following secrets to be configured (never committed as plaintext):
- `GEMINI_API_KEY` — for vision-tier analysis calls
- `YOUTUBE_API_KEY` — for YouTube Data API sourcing
- `GITHUB_TOKEN` — for GitHub search API (higher rate limits authenticated)
