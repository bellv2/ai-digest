# Nightly Run Failed — 2026-09-07

## Summary

`scripts/run_nightly.py` failed at the digest-generation step. Per the
routine's sanity-check rules, no data or digest changes were committed
from this run.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 4 new candidate articles |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 270 candidate videos found (several transcript fetches failed due to YouTube IP blocking, handled gracefully by the script) |
| Digest generation (`generate_digest.py`) | ❌ **FAILED** |
| Narrative writeup generation (`generate_writeups.py`) | ✅ OK (no-op — 0 digest items, since digest generation failed first) |
| Word report generation (`generate_docx_report.py`) | ✅ OK (no-op — no digest items for 2026-09-07) |

Overall exit code: 1 (one step failed).

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

This is not a `sqlite3`/`OperationalError`/`IntegrityError` issue — it's a
Python type bug in the sort key. In `build_digest` (scripts/generate_digest.py:76-80),
the sort key for `top_substance` uses:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

`is_numeric_trend()` returns `True` whenever `int(item["trend_score"])`
succeeds — including when `trend_score` is stored as a numeric **string**
(e.g. `"1"`, as produced by `source_news.py`). In that case the key falls
back to the raw (string) `trend_score` instead of casting it to `int`, unlike
the `top_trend` sort a few lines below (line 84) which does
`int(i["trend_score"])` correctly. When the item list mixes items whose
trend_score is an `int` (default `0` fallback) with items whose trend_score
is a numeric string, Python's `sorted()` fails comparing `str` to `int`.

This run had both video items (`trend="pending"` → falls back to `0`, an
int) and news items with numeric string trend scores in the same
7-day window, which triggered the mismatch.

## Sanity check outcome

- Digest file for 2026-09-07 was **not generated** (missing entirely) →
  commit/push blocked per routine rules.
- No `sqlite3`/`OperationalError`/`IntegrityError` traceback occurred.
- Row counts after sourcing look plausible (repos: 6069, videos: 552,
  news: 5, snapshots: 9330) — no implausible swings.
- Only one of the three core steps (schema, news, videos vs. digest)
  failed, but the missing-digest-file condition alone is sufficient to
  block committing per the routine's rules.

## Data state

`data/ai_digest.db` was modified in the workspace (new rows from
successful news/video sourcing) but **was not committed**, per instructions
not to commit anything when the sanity check fails. Those newly-sourced
rows will need to be re-fetched (or the DB fix applied and rerun) on a
future successful run.

## Recommended fix (not applied — routine does not self-fix)

In `scripts/generate_digest.py:78`, mirror the `int(...)` cast used on
line 84:

```python
key=lambda i: (i["substance_score"], int(i["trend_score"]) if is_numeric_trend(i) else 0)
```
