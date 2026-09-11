# Failed nightly run — 2026-09-11

## Summary

The nightly pipeline (`scripts/run_nightly.py`) ran but **digest generation
crashed**, so no digest was produced for 2026-09-11. Per the routine's sanity
check ("digest file empty or missing entirely"), no data changes were
committed. This file is the only thing committed for this run.

## Step results

| Step | Status |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 20 candidate articles scored (19 new, 1 tier-2) |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 277 candidate videos scored (2 transcript-fetch warnings, non-fatal) |
| Digest generation (`generate_digest.py`) | ❌ **FAILED** |
| Narrative writeups (`generate_writeups.py`) | ✅ OK (no-op — 0 digest items, since digest generation failed) |
| Word report (`generate_docx_report.py`) | ✅ OK (skipped — no digest items) |

Overall exit code: 1 (one step failed).

## Root cause (for the repo owner)

`generate_digest.py` crashed with:

```
TypeError: '<' not supported between instances of 'int' and 'str'
  File "scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
  File "scripts/generate_digest.py", line 78, in <lambda>
    key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0),
```

`is_numeric_trend()` (line 53-59) checks `int(item["trend_score"])` to decide
whether a trend score is usable, but the sort key on line 78 then uses the
*raw* `i["trend_score"]` value rather than casting it to `int`. Some rows
store `trend_score` as a numeric string (e.g. `"1"`) rather than an int, so
the sort ends up comparing `int` and `str` tuple elements across different
items and Python raises. The same pattern (line 84, `top_trend`) casts with
`int(...)`, so `top_substance`'s key on line 78 is the outlier.

Per the routine's instructions, this was **not** fixed automatically —
flagging it here for manual review.

## Data state

- `git pull` confirmed this branch already had the latest repo-sourcing data
  from the GitHub Actions workflow (commit `7d3d857`, 2026-09-10).
- `source_news.py` and `source_videos.py` did write new rows to
  `data/ai_digest.db` (news: 21 total rows, videos: 559 total rows, repos:
  6476 total rows), but per the sanity-check rule those changes are **not**
  committed in this branch/PR — only this failure report is.
- No `sqlite3`/`OperationalError`/`IntegrityError` tracebacks occurred; the
  DB itself is healthy. The failure is a pure Python bug in the digest
  ranking logic.

## Recommendation

Fix the sort key in `generate_digest.py` line 78 to cast
`i["trend_score"]` to `int` when `is_numeric_trend(i)` is true (matching the
pattern already used on line 84), then re-run the pipeline.
