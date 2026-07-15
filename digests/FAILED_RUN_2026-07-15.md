# Failed Nightly Run — 2026-07-15

## Summary

The nightly pipeline (`scripts/run_nightly.py`) ran 4 steps. 3 succeeded; digest
generation failed, so no digest file was produced for today. Per the sanity-check
rules, no data changes were committed — only this report.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK — added missing columns (`repos.cited_arxiv_ids`, several `videos.*_sketchiness/link` columns) |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 10 new articles sourced across 9 feeds |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 294 candidate videos found, all scored/inserted |
| Digest generation (`generate_digest.py`) | ❌ FAILED (exit code 1) |

Overall `run_nightly.py` exit code: 1 (one step failed).

## Failure detail

```
Pulled 304 items from trailing 7 days across 3 tables.
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

`build_digest()` sorts `clean_items` by the tuple
`(substance_score, trend_score if is_numeric_trend(item) else 0)`
(`scripts/generate_digest.py:76-80`). When some items have a numeric `trend_score`
column value stored as `str` (e.g. `"1"`) rather than `int`, and others fall back to
the literal `int` `0`, the second tuple element mixes `str` and `int` types across
items, which Python's sort cannot compare. This looks like a pre-existing type
consistency issue between how `trend_score` is written (as text) vs. read/compared
in `generate_digest.py`, not something introduced by tonight's sourcing steps.

## Why this run was not committed

- The digest file in `digests/` was not generated (missing entirely) — one of the
  documented stop conditions.

No fix was attempted, per instructions. The sourced news/video data from this run
was left uncommitted (`data/ai_digest.db` has local uncommitted changes) so it is
not lost, but nothing was pushed. A human should investigate the `trend_score`
type-consistency bug in `generate_digest.py` before the next run is expected to
produce a digest.
