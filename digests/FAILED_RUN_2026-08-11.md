# Failed Nightly Run — 2026-08-11

**Status:** Digest generation crashed. No digest was produced for this date. No data changes were committed.

## What ran successfully
- Schema migration — OK, no changes needed
- News/RSS sourcing — OK, 24 new articles across 9 feeds (news table: 1 → 25 rows)
- YouTube sourcing — OK, 288 new candidate videos found (videos table: 282 → 570 rows; snapshots: 5541 → 5829). Several transcript fetches failed with YouTube IP-blocking warnings (expected/non-fatal, handled by the script).

## What failed
**Digest generation (`scripts/generate_digest.py`)** crashed with:

```
Traceback (most recent call last):
  File "/home/user/ai-digest/scripts/generate_digest.py", line 180, in <module>
    main()
  File "/home/user/ai-digest/scripts/generate_digest.py", line 161, in main
    top_substance, top_trend, overlap, flagged = build_digest(conn)
  File "/home/user/ai-digest/scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
TypeError: '<' not supported between instances of 'int' and 'str'
```

**Likely root cause (for review, not fixed):** In `build_digest()` (scripts/generate_digest.py:78), the sort key is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0),
```

`is_numeric_trend()` confirms `trend_score` can be parsed as `int`, but the raw (string) value is used in the sort key rather than the parsed `int`. When some items have a numeric-string `trend_score` (e.g. `"3"`) and others fall back to the literal `int` `0` (non-numeric/pending trend), the resulting tuples mix `str` and `int` in the second position, which Python cannot compare, raising `TypeError`.

Downstream steps (narrative writeup, docx report) ran but had nothing to do since 0 digest items existed for 2026-08-11.

## Sanity check result
Digest file for 2026-08-11 is **missing** in `digests/` — this trips the "do not commit" condition in the nightly routine's instructions. Per instructions, no data or digest changes have been committed; only this report is being committed, on a `claude/`-prefixed branch, and no fix has been attempted.

## Row counts after run (informational, not committed)
| table | before | after |
|---|---|---|
| repos | 3455 | 3455 (unchanged — repo sourcing is a separate GH Actions workflow) |
| videos | 282 | 570 |
| news | 1 | 25 |
| snapshots | 5541 | 5829 |

Row count changes look plausible and are not the cause of the failure; they are included here only for the human reviewer's reference. The underlying `data/ai_digest.db` changes from this run were **not committed** (working tree left with the sourcing changes uncommitted, consistent with "commit nothing" per instructions — the repo owner can decide whether to keep or discard them).
