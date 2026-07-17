# Failed Nightly Run — 2026-07-17

## Summary

The nightly pipeline (`scripts/run_nightly.py`) failed during the digest
generation step. No digest was produced for this date, and no changes have
been committed from this run.

## Step results

- ✅ Schema migration (`ensure_schema.py`) — OK, no changes needed.
- ✅ News/RSS sourcing (`source_news.py`) — OK, 20 candidate articles found
  across 9 feeds.
- ✅ YouTube sourcing (`source_videos.py`) — OK, 277 candidate videos found.
- ❌ Digest generation (`generate_digest.py`) — **FAILED**, exit code 1.

## Failure detail

```
Pulled 724 items from trailing 7 days across 3 tables.
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

Likely root cause: the sort key on `scripts/generate_digest.py:78`
(`i["trend_score"] if is_numeric_trend(i) else 0`) mixes a raw
`trend_score` value (which can be stored as text/string in the DB) with the
integer fallback `0` in the same tuple position, so `sorted()` ends up
comparing a `str` to an `int` across items and raises `TypeError`. This is
a pre-existing bug in the digest-generation sort logic, not something
introduced by this run's sourcing steps.

## Sanity check outcome

This run tripped the "do not commit" guardrail because the digest file in
`digests/` was never generated (the directory did not even exist prior to
this report). Per the runbook, no data or digest changes have been
committed — the sourced news/video rows from this run's `source_news.py`
and `source_videos.py` steps were left uncommitted in the working tree and
are not part of this commit.

## Recommended next step

A human (or a follow-up task) should fix the type-mixing bug in the sort
key at `scripts/generate_digest.py:76-86` (coerce `trend_score` to `int`
consistently before sorting) and re-run the pipeline. This routine does not
modify scoring/digest-generation logic itself, per its instructions.
