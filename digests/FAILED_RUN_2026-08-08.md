# Failed Nightly Run — 2026-08-08

## Summary

The nightly pipeline (`scripts/run_nightly.py`) ran, but **digest generation
failed**, so no digest was produced for 2026-08-08. Per the sanity-check
rules, no data or digest changes were committed — this failure report is the
only file committed on this branch.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 13 new articles across 9 feeds |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 290 candidate videos found (several transcript fetches failed with YouTube IP-block warnings, handled gracefully by the script) |
| **Digest generation (`generate_digest.py`)** | ❌ **FAILED** — see traceback below |
| Narrative writeup generation (Gemini) | ✅ OK (ran, but 0 digest items existed to write up, as a downstream consequence of the digest failure) |
| Word report generation | ✅ OK (skipped — no digest items found for 2026-08-08) |

## Why this run was not committed

- `digests/2026-08-08.md` was never created — the digest file for today is
  **missing entirely**, one of the explicit stop conditions.

## Traceback

```
Traceback (most recent call last):
  File "/home/user/ai-digest/scripts/generate_digest.py", line 180, in <module>
    main()
  File "/home/user/ai-digest/scripts/generate_digest.py", line 161, in main
    top_substance, top_trend, overlap, flagged = build_digest(conn)
                                                 ^^^^^^^^^^^^^^^^^^
  File "/home/user/ai-digest/scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
                    ^^^^^^^
TypeError: '<' not supported between instances of 'int' and 'str'
```

## Likely root cause (not fixed, per instructions)

`build_digest()` in `scripts/generate_digest.py` (around line 76-86) sorts
items by a tuple key `(substance_score, trend_score_or_0)`. `trend_score` is
stored as a numeric string for scored items but the fallback value used for
non-numeric trend items (e.g. videos still `pending` trend scoring) is the
int `0`. When two items tie on `substance_score`, Python compares the second
tuple element and hits a `str` vs `int` comparison, raising the `TypeError`.
This looks like a pre-existing type-consistency bug in the sort key, likely
surfaced now because this window's item mix includes items with string
`trend_score` values alongside items falling back to the int `0` default.

## Data state

`data/ai_digest.db` was modified locally by the news and video sourcing
steps (13 new articles, ~290 candidate videos processed) but **these changes
were intentionally left uncommitted** per the sanity-check rules, since the
digest they would have fed into never generated. The repository owner
should re-run the pipeline (or investigate/fix the digest generation bug)
before this sourced data is committed.

## Next steps for the repository owner

1. Fix the type-inconsistent sort key in `build_digest()` (line 76-86 of
   `scripts/generate_digest.py`) — likely needs `trend_score` fallback to be
   coerced to a consistent numeric type across all branches.
2. Re-run the nightly pipeline once fixed to source today's data fresh (or
   re-run just digest/writeup/docx generation against already-sourced data,
   if still available in a session).
