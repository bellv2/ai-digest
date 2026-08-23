# Failed nightly run: 2026-08-23

## Summary

Digest generation failed with a `TypeError`, so no digest was produced for
today and no data changes were committed. Sourcing steps (news, YouTube)
completed successfully and wrote new rows to the local database, but those
changes are intentionally **not** committed per the sanity-check rule that
a missing digest file blocks the commit.

## Step results

| Step | Result |
|---|---|
| Schema migration | ✅ OK |
| News/RSS sourcing | ✅ OK (3 new candidate articles) |
| YouTube sourcing | ✅ OK (275 candidate videos found; several transcript fetches failed due to YouTube IP blocking, handled as warnings) |
| Digest generation | ❌ **FAILED** |
| Narrative writeup generation | ✅ OK (0 items, since digest failed) |
| Word report generation | ✅ OK (skipped, no digest items) |

## Root cause

`scripts/generate_digest.py`, in `build_digest()` (line 76):

```
TypeError: '<' not supported between instances of 'int' and 'str'
```

```
File "/home/user/ai-digest/scripts/generate_digest.py", line 180, in <module>
    main()
File "/home/user/ai-digest/scripts/generate_digest.py", line 161, in main
    top_substance, top_trend, overlap, flagged = build_digest(conn)
File "/home/user/ai-digest/scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
TypeError: '<' not supported between instances of 'int' and 'str'
```

The sort key on line 78 is `(i["substance_score"], i["trend_score"] if
is_numeric_trend(i) else 0)`. When some items produce a numeric-string
`trend_score` (not cast to `int`) and others fall back to the integer `0`,
Python cannot compare a `str` to an `int` inside the tuple, and sorting
raises. This is the **same failure signature** as prior nightly runs on
2026-08-08, 2026-08-11, 2026-08-16, and 2026-08-22 (see `digests/` history
on those branches) — it does not appear to have been fixed since first
observed.

## Action taken

Per instructions, no fix was attempted and no data or digest changes were
committed. Only this report is committed, to branch
`claude/youthful-ritchie-f2jsr4`.

## Note on branch history

Many prior nightly-run branches (`claude/youthful-ritchie-*`, dozens of
them) appear never to have been merged to `main` — `main` currently only
contains "nightly repo sourcing" commits, and the last digest actually
merged into `main` is dated 2026-07-20, over a month ago. The repository
owner may want to review the backlog of unmerged nightly-run PRs.
