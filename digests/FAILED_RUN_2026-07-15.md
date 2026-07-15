# Failed Nightly Run — 2026-07-15

The nightly pipeline completed with an overall exit code of 0 (the orchestrator's
per-step error isolation swallowed these failures), but two of the four steps
produced effectively no usable data due to underlying bugs/config issues. Per the
sanity-check rules, nothing from this run was committed.

## What happened

| Step | Reported status | Actual result |
|---|---|---|
| GitHub repo sourcing | ✅ OK (4s) | **0/11 topic searches succeeded** — all returned HTTP 403 |
| News/RSS sourcing | ✅ OK (10s) | Worked normally — 10 candidate articles sourced |
| YouTube sourcing | ✅ OK (87s) | **0/290 candidate videos written** — 100% insert failure |
| Digest generation | ✅ OK (0s) | Ran, but only had news data to pull from (repos/videos empty) |

## Root causes

1. **Repo sourcing — token scope mismatch, not a transient rate limit.**
   Every GitHub search request returned 403. Direct diagnostic call:
   ```
   curl -H "Authorization: Bearer $GH_TOKEN" "https://api.github.com/search/repositories?q=topic:llm&per_page=1"
   → 403 {"message":"This GitHub API path is not available: sessions are bound to
     their configured repositories. Use repository-scoped endpoints
     (repos/{owner}/{repo}/...)."}
   ```
   The `GH_TOKEN` available in this execution environment is a Claude Code
   session token scoped to `bellv2/ai-digest` only. `scripts/source_repos.py`
   needs a general-purpose GitHub PAT with search API access to do topic-based
   repo discovery across all of GitHub — the session token cannot do this by
   design. This will fail identically on every future run until a proper PAT is
   provided via `GH_TOKEN` (or a differently-named secret) in the pipeline's
   environment.

2. **Video sourcing — schema mismatch.**
   `scripts/source_videos.py` (around line 305) inserts into
   `title_sketchiness_score` and `description_sketchiness_score` columns that do
   not exist in the `videos` table in `data/ai_digest.db`. Every one of the 290
   candidate videos found in the window failed to insert with:
   `table videos has no column named title_sketchiness_score`.
   Either the schema migration for these columns was never applied to
   `data/ai_digest.db`, or the insert statement is stale relative to the current
   schema. `PRAGMA table_info(videos)` confirms the columns are absent.

   Separately (not the primary blocker, but worth noting): several transcript
   fetches also failed with YouTube IP-blocking errors
   (`youtube_transcript_api` "IP has been blocked by YouTube") — expected from a
   cloud IP and not itself a reason to halt, but it compounds the video step's
   yield even once the schema issue is fixed.

## What was NOT done

- No changes to `data/ai_digest.db` were committed — it was reverted to its
  pre-run state.
- No digest file was committed — the one generated this run only reflected the
  10 news items (repos and videos were entirely absent), which would be
  misleading to publish as a normal night's digest.
- No attempt was made to fix `scripts/source_videos.py` or reconfigure
  credentials, per instructions to flag rather than fix.

## Suggested follow-up for a human

- Provide a general-purpose GitHub PAT (with public repo search access) as
  `GH_TOKEN` (or update `scripts/source_repos.py` to read a differently-named
  secret) in the pipeline's actual runtime environment, distinct from the
  Claude Code session token.
- Add/backfill the `title_sketchiness_score` and `description_sketchiness_score`
  columns on the `videos` table (or update `source_videos.py` if those columns
  were intentionally renamed/removed) and confirm `data/ai_digest.db`'s schema
  matches what the ingestion scripts expect.
- Once fixed, re-run the pipeline; only the News/RSS step is currently healthy.
