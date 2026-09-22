# Failed Nightly Run — 2026-09-22

## Summary

The nightly digest pipeline (`scripts/run_nightly.py`) failed at the
**Digest generation** step. No digest was produced for 2026-09-22, so per the
routine's sanity-check rules, no data or digest changes were committed.

## Pipeline step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 14 candidate articles found across 9 feeds |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 271 candidate videos found (several transcript fetches blocked by YouTube IP rate-limiting, handled as warnings) |
| **Digest generation (`generate_digest.py`)** | ❌ **FAILED** — see below |
| Narrative writeup generation (Gemini) | ⚠️ Ran but no-op (0 digest items, since digest generation failed upstream) |
| Word report generation | ⚠️ Ran but no-op (skipped — no digest items found for 2026-09-22) |

Overall script exit code: 1.

## Root cause

`generate_digest.py` crashed with:

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

The `top_substance` sort key at `generate_digest.py:78` is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0),
```

When `is_numeric_trend(i)` is true, the raw `trend_score` value is used as-is
instead of being cast with `int(...)`. Since `trend_score` appears to be
stored inconsistently (some rows as a string, some as an int) across the
`repos`/`videos`/`news` tables, the resulting sort keys mix `str` and `int` in
the second tuple position, which `sorted()` cannot compare.

This also likely explains why the last successful digest in `digests/` is
dated 2026-07-20 — the digest step may have been silently failing (or
producing no output) for some time. Repo/news/video sourcing has continued
to commit data via the separate GitHub Actions workflow in the meantime.

## Data sourced this run (not committed)

Sourcing itself succeeded and populated new candidate rows in
`data/ai_digest.db` (news + videos), but per the routine's instructions this
run does not commit any data or digest changes when the digest file is
missing. The database changes from this run were left uncommitted in the
working tree.

## Recommended next step

A human (or a separate, explicitly-scoped fix task) should patch
`generate_digest.py:78` to coerce `trend_score` to `int` consistently before
sorting, e.g. `int(i["trend_score"]) if is_numeric_trend(i) else 0`, and
investigate why `trend_score` values have inconsistent types in storage.
This routine does not modify scoring logic or scripts, so no fix was
attempted here.
