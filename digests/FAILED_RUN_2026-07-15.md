# Failed Nightly Run — 2026-07-15 (second run today)

The nightly pipeline completed with an overall exit code of 0 (the orchestrator's
per-step error isolation swallowed the failures), but two of the four steps
produced effectively no usable data. Per the sanity-check rules, nothing from
this run was committed — `data/ai_digest.db` was reverted to its pre-run state
and the generated digest file was discarded.

## What happened

| Step | Reported status | Actual result |
|---|---|---|
| GitHub repo sourcing | ✅ OK (4s) | **0/11 topic searches succeeded** — all returned HTTP 403 |
| News/RSS sourcing | ✅ OK (8s) | Worked normally — 10 candidate articles sourced |
| YouTube sourcing | ✅ OK (70s) | **0/294 candidate videos written** — 100% insert failure |
| Digest generation | ✅ OK (0s) | Ran, but only had news data to pull from (repos/videos empty) |

## Root cause: this is a regression, not a new bug

This exact combination of failures (repo-sourcing 403 + video schema mismatch)
was already hit and correctly flagged earlier today — see commit `a889e2b`
("Flag failed nightly run: repo sourcing token scope + video schema mismatch")
on branch `claude/vibrant-edison-e55mpf`, which added a `digests/FAILED_RUN_2026-07-15.md`
of its own with full diagnosis.

In response, commit `1666a91` ("fix: schema migration for stale db columns,
rename GH_TOKEN to avoid collision") added an `ensure_schema.py` step to
`scripts/run_nightly.py`'s `STEPS` list, which fixed the video schema issue.

The very next commit, `9ed96bf` ("add github actions workflow for repo
sourcing"), added `.github/workflows/source-repos.yml` to move repo sourcing
to its own scheduled GitHub Action — a good change in principle. But its diff
to `scripts/run_nightly.py` **removed the `ensure_schema.py` step it had just
added** and **left `source_repos.py` in the `STEPS` list**, i.e. it did the
opposite of what the new workflow's existence implies it should have done
(drop `source_repos.py` from the nightly script now that GH Actions owns it,
keep/expand schema migration). Net effect: the video schema bug is back, and
`run_nightly.py` still runs repo sourcing in-process on top of the new
Actions-based sourcing.

Concretely, `data/ai_digest.db`'s `videos` table is still missing:
`title_sketchiness_score`, `description_sketchiness_score`,
`resource_link_count`, `promo_link_count`, `neutral_link_count`,
`comment_check_performed`, `comment_check_result`. Every one of the 294
candidate videos found in this run's window failed to insert with e.g.:
`table videos has no column named title_sketchiness_score`.

The repo-sourcing 403s are the same known/expected issue as before: the
session's GitHub token is scoped to `bellv2/ai-digest` only and cannot hit
the global search API that `scripts/source_repos.py` needs. This is why repo
sourcing was moved to its own GitHub Actions workflow — but `run_nightly.py`
was not updated to stop running it too.

## What was NOT done

- No changes to `data/ai_digest.db` were committed — reverted to pre-run state.
- No digest file was committed — the one generated this run only reflected the
  10 news items (repos and videos were entirely absent), which would be
  misleading to publish as a normal night's digest.
- No attempt was made to fix `scripts/run_nightly.py`, `scripts/source_videos.py`,
  or the `STEPS` list, per instructions to flag rather than fix.

## Suggested follow-up for a human

- In `scripts/run_nightly.py`, re-add `("ensure_schema.py", "Schema migration
  ...")` to `STEPS` (ideally first, as it was in commit `1666a91`), and remove
  `("source_repos.py", "GitHub repo sourcing")` now that
  `.github/workflows/source-repos.yml` owns that step on its own schedule.
- Confirm the new `source-repos.yml` workflow has actually run successfully at
  least once (it uses `secrets.GITHUB_TOKEN`, the default Actions token, which
  is also fairly restricted — worth double-checking it can hit the search API
  before assuming repo sourcing is now handled).
- Once `run_nightly.py` is fixed, re-run the pipeline.
