# Failed Nightly Run — 2026-08-16

## Summary

The nightly pipeline failed at the digest generation step. Per the sanity-check
rules for this routine, no changes were committed and no PR was opened.

## What ran

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK — no changes needed |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 2 new candidate articles found |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 275 candidate videos found (several transcript fetches failed due to YouTube IP blocking, handled gracefully as warnings) |
| Digest generation (`generate_digest.py`) | ❌ **FAILED** — see below |
| Narrative writeup generation (Gemini) | ✅ OK (ran against 0 digest items, since digest generation failed first) |
| Word report generation | ✅ OK (skipped — no digest items for 2026-08-16) |

Overall script exit code: 1 (one step failed).

## Why this run was not committed

The sanity check condition "the digest file generated in `digests/` is empty
or missing entirely" was met: `digests/2026-08-16.md` was never created.

## Root cause (diagnosis only — not fixed, per instructions)

`generate_digest.py` raised:

```
TypeError: '<' not supported between instances of 'str' and 'int'
  File "scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(...)
```

`trend_score` is declared `TEXT` in the schema (it can hold the literal
`"pending"` for videos under 48h). In `build_digest()`'s `top_substance` sort
key (line 78), the tie-break value is used as-is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

When `is_numeric_trend(i)` is `True`, the raw string (e.g. `"5"`) is used
instead of being cast to `int`. When two items tie on `substance_score` and
one has a numeric string trend score while another falls back to the `int`
`0`, Python's tuple comparison hits `str < int` and raises. Pulled 1051 items
across the 3 tables this run, apparently enough to hit this tie case for the
first time.

This is a pre-existing latent bug in the ranking sort key, not something
introduced by this run's sourcing steps. No scoring logic, rubric, or scripts
were modified, per instructions — this is a diagnosis only, left for the
repository owner to fix.

## Data state

Sourcing steps did write new rows to `data/ai_digest.db` in the working tree
(2 news, up to 275 candidate videos, subject to scoring/dedup), but per the
sanity-check protocol **none of these changes were committed**. Current row
counts in the (uncommitted, local-only) working copy: repos=3903, news=3,
videos=557.

## Recommended fix (for the repository owner)

In `scripts/generate_digest.py`, cast the trend value to `int` in the
`top_substance` sort key, mirroring how `top_trend`'s key already does
`int(i["trend_score"])`:

```python
key=lambda i: (i["substance_score"], int(i["trend_score"]) if is_numeric_trend(i) else 0)
```
