# Failed nightly run — 2026-08-22

## Summary

The nightly pipeline failed at the **Digest generation** step. No digest was produced for 2026-08-22, so per the sanity-check rules this run's data/digest changes were **not committed**.

## Step results

| Step | Result |
|---|---|
| Schema migration | ✅ OK |
| News/RSS sourcing | ✅ OK (10 new candidate articles found) |
| YouTube sourcing | ✅ OK (277 candidate videos found; several transcript fetches failed with YouTube IP-blocking warnings, non-fatal) |
| Digest generation | ❌ FAILED |
| Narrative writeup generation | ✅ OK (0 items, since digest failed) |
| Word report generation | ✅ OK (skipped — no digest items) |

## Failure details

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

### Likely root cause

In `build_digest()` (`scripts/generate_digest.py:76-80`), the sort key for `top_substance` is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0),
```

When `is_numeric_trend(i)` is `True`, the raw `i["trend_score"]` value is used as-is instead of being cast with `int(...)`. If `trend_score` is stored as a numeric string (e.g. `"3"`) rather than an integer for some rows, Python compares that string against the integer `0` fallback used for non-numeric-trend items with the same `substance_score`, which raises the `TypeError` seen above. `top_trend` and `overlap` (lines 82-93) already wrap `trend_score` in `int(...)` in their sort keys, so this appears to be an inconsistency specific to the `top_substance` sort key.

This is a pre-existing bug in the digest generation script, not something introduced by this run. Per instructions, I have not attempted to fix it.

## Sanity-check condition triggered

- **Digest file missing entirely**: no `digests/2026-08-22.md` was generated (only the older `digests/2026-07-20.md` exists in the directory).

## Data state

`data/ai_digest.db` was modified in the working tree by the successful News/RSS and YouTube sourcing steps (new candidate items scored), but these changes were **not committed**, per the "commit nothing" rule when a sanity-check condition is triggered.
