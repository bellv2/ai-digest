# Nightly Run Failed — 2026-07-19

## Summary

The nightly pipeline (`scripts/run_nightly.py`) ran with 3 of 4 steps succeeding, but
**digest generation failed and produced no output file**, which trips the sanity-check
stop condition. No data or digest changes have been committed.

## Step results

| Step | Result |
|---|---|
| Schema migration (`ensure_schema.py`) | ✅ OK — no changes needed |
| News/RSS sourcing (`source_news.py`) | ✅ OK — 6 new candidate articles across 9 feeds |
| YouTube sourcing (`source_videos.py`) | ✅ OK — 276 candidate videos found in window |
| Digest generation (`generate_digest.py`) | ❌ FAILED — `TypeError`, no digest file written |

## Root cause

`generate_digest.py` raised:

```
TypeError: '<' not supported between instances of 'int' and 'str'
  File "scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
```

In `build_digest()`, the `top_substance` sort key is:

```python
key=lambda i: (i["substance_score"], i["trend_score"] if is_numeric_trend(i) else 0)
```

`is_numeric_trend()` only checks that `trend_score` can be coerced to `int` via
`int(item["trend_score"])`, but the value itself is not converted — when `trend_score`
is stored as a numeric string (e.g. `"3"`), the raw string is used as the sort key's
second element instead of an int. Other items fall back to the int `0` when trend is
`"pending"`/non-numeric. Mixing `str` and `int` in the second tuple position across
items makes the tuple comparison raise `TypeError` once Python needs to break a tie on
`substance_score` and compare the second elements.

This is a pre-existing bug in `generate_digest.py`, not something introduced by this
run. Per routine instructions, no fix was attempted — flagging for owner review.

## Action taken

- No changes to `data/` or `digests/*.md` digest output were committed.
- Only this failure report was committed, to a `claude/`-prefixed branch, as instructed.
- The routine did not open a PR against `main` (only opens a PR on a passing sanity check).

## Suggested fix (for owner, not applied)

Coerce `trend_score` to `int` in the sort key wherever `is_numeric_trend(i)` is true,
e.g. `int(i["trend_score"]) if is_numeric_trend(i) else 0`, matching the pattern already
used correctly in the `top_trend` and `overlap` sort keys just below it.
