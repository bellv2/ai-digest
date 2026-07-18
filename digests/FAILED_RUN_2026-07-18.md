# Failed nightly run — 2026-07-18

## Outcome
Digest generation crashed. No digest was produced. Per the routine's sanity-check
rules, no data changes were committed — this report is the only file committed
for tonight's run.

## Step results
- ✅ Schema migration — no changes needed, all required columns already present.
- ✅ News/RSS sourcing — OK. 15 new articles ingested (9 feeds, post arXiv-cap).
- ✅ YouTube sourcing — OK. 279 new candidate videos ingested.
- ❌ Digest generation — **FAILED**, exit code 1.

## Why the sanity check blocked the commit
The digest file in `digests/` was not created (the `digests/` directory didn't
even exist before this report). That alone is one of the routine's explicit
"do not commit" conditions, regardless of the other checks.

(For reference, the other checks did *not* independently trigger: only one of
the three pipeline steps failed, and the traceback is unrelated to
`sqlite3`/`OperationalError`/`IntegrityError`.)

## Root cause (diagnosis only — not fixed, per instructions)
```
File "scripts/generate_digest.py", line 180, in <module>
    main()
File "scripts/generate_digest.py", line 161, in main
    top_substance, top_trend, overlap, flagged = build_digest(conn)
File "scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
TypeError: '<' not supported between instances of 'int' and 'str'
```

In `build_digest()` (`scripts/generate_digest.py:76-86`), the sort keys mix
`i["trend_score"]` (read straight from SQLite, so it can be a string like
`"3"`) with the literal `int` fallback `0` used when `is_numeric_trend(i)` is
false. `is_numeric_trend()` only *checks* whether `trend_score` converts to
`int` — it doesn't return the converted value — so a numeric-but-string
`trend_score` ends up compared against an `int` `0` in the same sort-key
tuple, which raises `TypeError`. This affects both the `top_substance` (line
78) and `overlap` (line 91, via `int(...)` inconsistency) sort keys.

## Data state (informational — not committed)
DB row counts after this run (uncommitted, left in the working tree):
- repos: 739 (unchanged — sourced separately via GitHub Actions)
- videos: 0 → 279
- news: 0 → 15
- snapshots: 913 → 1192

These row-count changes look plausible on their own; the block is solely due
to the missing digest file.

## Next steps
The repository owner should fix the sort-key type mismatch in
`build_digest()` and re-run the pipeline.
