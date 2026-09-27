# Failed nightly run — 2026-09-27

## Summary

The nightly pipeline (`scripts/run_nightly.py`) ran but the **Digest
generation** step crashed, and no digest file was produced for
2026-09-27. Per the sanity-check rules for this routine, no changes were
committed and the issue was not fixed automatically.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK — no schema changes needed |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 2 new articles found (news table: 1 → 3) |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 279 candidate videos processed, several transcript fetches failed due to YouTube IP blocking (expected from cloud IPs, non-fatal) (videos table: 282 → 561) |
| **Digest generation (`generate_digest.py`)** | ❌ **FAILED**, exit code 1 |
| Narrative writeup generation (Gemini) (`generate_writeups.py`) | ✅ OK (no-op — 0 digest items existed to write up, since digest generation failed first) |
| Word report generation (`generate_docx_report.py`) | ✅ OK (skipped — no digest items found for 2026-09-27) |

Overall: 1 of 6 steps failed (not more than one, so the "more than one
step failed" condition alone would not block), but the missing digest
file condition below does.

## Why this run was not committed

- **Digest file missing**: `digests/2026-09-27.md` was never created
  because `generate_digest.py` crashed before writing output. The
  most recent digest file remains `digests/2026-07-20.md`.

## The crash

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
TypeError: '<' not supported between instances of 'str' and 'int'
```

Root cause (for the repo owner to review — not fixed here, per
instructions not to modify scoring logic or scripts): in
`build_digest()` (scripts/generate_digest.py:76-80), the sort key is
`(i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)`.
`is_numeric_trend()` (scripts/generate_digest.py:53-59) checks whether
`trend_score` casts to `int`, but returns `True` without actually
converting the value — so items pass through with `trend_score` still
as a `str` (e.g. `"1"`) while items that fail the check fall back to
the `int` literal `0`. Sorting a list containing both `str` and `int`
values in the same tuple position raises `TypeError`. Likely fix is to
cast with `int(item["trend_score"])` inside the key function, but that
change was intentionally left for the repo owner per this routine's
instructions.

## Database state (not committed)

Row counts changed during sourcing (repo sourcing itself is out of
scope for this routine and unaffected):

| Table | Before | After |
|---|---|---|
| repos | 8059 | 8059 (unchanged, expected — sourced separately) |
| videos | 282 | 561 |
| news | 1 | 3 |
| snapshots | 11693 | 11972 |

These counts look plausible (no runaway growth, no drops) and no
`sqlite3.OperationalError` / `IntegrityError` occurred. The only
blocking condition is the missing digest file.

`data/ai_digest.db` was modified locally by this run but is **not**
included in this commit, so the sourced news/video data from tonight
is not persisted to the branch. Re-running the pipeline tomorrow will
re-source and re-attempt the digest.

## Action needed

The repo owner should fix the `is_numeric_trend()` / sort-key bug in
`scripts/generate_digest.py` (or otherwise normalize `trend_score`
typing) before the next run can succeed.
