# Nightly run failed — 2026-09-21

## Summary

Digest generation failed, so no digest was produced for 2026-09-21. Per the
routine's sanity-check rules, no data changes were committed — this failure
report is the only file committed for this run.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 2 new articles |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 276 new candidate videos (several transcript-fetch warnings due to YouTube IP blocking, non-fatal) |
| Digest generation (`generate_digest.py`) | ❌ **FAILED** |
| Narrative writeup generation (Gemini) | ✅ OK (no-op — 0 digest items, since digest step failed) |
| Word report generation | ✅ OK (skipped — no digest items) |

Overall script exit code: 1 (one step failed).

## Root cause

`generate_digest.py` crashed in `build_digest()` while building the
`top_substance` ranking:

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

The sort key on line 78 is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

`is_numeric_trend()` only checks whether `trend_score` *can* be cast to
`int` — it doesn't actually cast it. So items with a numeric-string
`trend_score` (e.g. `"5"`) keep the raw string in the sort key, while items
without a numeric trend fall back to the int `0`. Python's tuple comparison
then tries to compare a `str` to an `int` across two items and raises
`TypeError`. This is a pre-existing bug in the digest script, not a data
issue — not fixed here per the routine's instructions (scripts are out of
scope for this routine).

## Sanity-check condition triggered

- **Digest file missing entirely for today** (`digests/2026-09-21.md` was
  never created). This alone is a stop condition, independent of the
  "more than one step failed" rule (only one step actually failed here).

No `sqlite3`/`OperationalError`/`IntegrityError` tracebacks were seen, and
the sourced-data row counts before/after this run look plausible (not
committed either way, out of caution):

| Table | Before | After |
|---|---|---|
| repos | 7481 | 7481 (unchanged — repo sourcing is a separate GH Actions job) |
| videos | 282 | 558 (+276, matches sourcing log) |
| news | 1 | 3 (+2, matches sourcing log) |
| snapshots | 10925 | 11201 (+276) |

## Action taken

- No changes to `data/` were committed (news/video sourcing results from
  this run were discarded, since the digest that depends on them couldn't
  be generated).
- This report was committed by itself to a `claude/`-prefixed branch, per
  instructions.
- No attempt was made to fix `generate_digest.py`.

## Suggested follow-up (for the repo owner)

Fix `is_numeric_trend`/the sort key in `generate_digest.py` so numeric
`trend_score` strings are cast to `int` before sorting, e.g.:

```python
key=lambda i: (i["substance_score"], int(i["trend_score"]) if is_numeric_trend(i) else 0)
```
