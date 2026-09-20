# Failed nightly run — 2026-09-20

## Outcome
Sanity check failed. No data or digest changes were committed to `main`. This
report is the only file committed.

## What ran successfully
- Schema migration (`ensure_schema.py`) — OK, no changes needed
- News/RSS sourcing (`source_news.py`) — OK, 2 new articles scored (out of 9 feeds, post arXiv-cap dedup)
- YouTube sourcing (`source_videos.py`) — OK, 274 new videos scored (some transcript fetches failed with YouTube IP-block warnings — non-fatal, handled by the script's own fallback)

## What failed
**Digest generation (`generate_digest.py`) — FAILED**, exit code 1:

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

As a downstream effect, no digest was written to `digests/` for
2026-09-20, `generate_writeups.py` found 0 digest items to write up, and
`generate_docx_report.py` skipped report generation.

## Likely root cause (not fixed, per instructions not to touch scoring/pipeline logic)
In `scripts/generate_digest.py`, `build_digest()` sorts `top_substance` by:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

`trend_score` is stored as `TEXT` in the DB (it can hold the literal string
`"pending"` for videos under 48h). When `is_numeric_trend(i)` is true, the
raw string value (e.g. `"7"`) is used as the second sort key instead of
`int(i["trend_score"])`. When two items tie on `substance_score`, Python
compares the second tuple elements — a string trend_score against the `int`
`0` used for non-numeric-trend items — which raises
`TypeError: '<' not supported between instances of 'str' and 'int'`.
This is a pre-existing bug in the digest-ranking code, not a data issue;
it was left in place per the routine's instructions not to modify scoring
or pipeline scripts.

## Sanity-check trigger
- Digest file for 2026-09-20 is missing entirely from `digests/` → commit blocked.

## Row counts (informational — DB changes were NOT committed)
| table | before | after |
|---|---|---|
| repos | 7386 | 7386 |
| videos | 282 | 556 (+274) |
| news | 1 | 3 (+2) |
| snapshots | 10802 | 11076 (+274) |

Row count deltas look plausible (they match the "new" counts logged by
`source_news.py` and `source_videos.py`) and did not independently trigger
the sanity check.

## Recommended next step
Fix the sort key in `generate_digest.py` line 78 to coerce `trend_score` to
`int` when `is_numeric_trend(i)` is true, e.g.
`int(i["trend_score"]) if is_numeric_trend(i) else 0`, then re-run the
pipeline.
