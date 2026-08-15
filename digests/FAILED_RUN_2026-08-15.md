# Failed Nightly Run — 2026-08-15

## Summary

The nightly pipeline ran schema migration, news sourcing, and YouTube
sourcing successfully, but **digest generation failed**, so no digest
file was produced for 2026-08-15. Per the sanity-check rules, no data
changes were committed and the run was aborted before opening a PR.

## Step results

| Step | Result |
|---|---|
| Schema migration | OK — no changes needed |
| News/RSS sourcing | OK — 16 new candidate articles across 9 feeds |
| YouTube sourcing | OK — 277 candidate videos found (several transcript fetches failed with YouTube IP-block warnings, handled gracefully by the script) |
| Digest generation | **FAILED** — see below |
| Narrative writeup generation | OK (skipped — 0 digest items, since digest generation failed first) |
| Word report generation | OK (skipped — no digest items for 2026-08-15) |

## Failure detail

`scripts/generate_digest.py` raised:

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

**Likely root cause** (not fixed, per instructions): in `build_digest()`
(`scripts/generate_digest.py:76`), the `top_substance` sort key is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

`trend_score` is read from SQLite and is a string (or the literal string
`"pending"` for videos <48h old). When `is_numeric_trend(i)` is true, the
raw string value is used as the tie-break key instead of `int(i["trend_score"])`;
the `else 0` fallback is an `int`. Once `sorted()` needs to compare a row
using the string tie-break against a row using the `0` int fallback, the
mixed-type comparison raises `TypeError`. This is a pre-existing bug in
digest generation, not a data corruption issue — `top_trend` and `overlap`
below it in the same file correctly cast with `int(i["trend_score"])`.

## Why the run was not committed

Per the sanity-check rules: the digest file for `digests/2026-08-15.md`
was never generated (missing entirely), so no changes were committed or
pushed. `data/ai_digest.db` has uncommitted local modifications from the
news/video sourcing steps (new candidate articles and videos scored) that
were intentionally left uncommitted.

## Current table row counts (informational, post-run)

- `repos`: 3815
- `videos`: 559
- `news`: 17

## Recommended next step

Fix `scripts/generate_digest.py:76` to cast `i["trend_score"]` to `int()`
in the `top_substance` sort key (matching the pattern already used in
`top_trend` and `overlap`), then re-run the nightly pipeline.
