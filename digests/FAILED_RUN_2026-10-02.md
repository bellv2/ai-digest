# Failed nightly run — 2026-10-02

Nothing from this run was committed except this note. Per the routine's sanity checks, the `data/` changes were left uncommitted.

## What happened
- Schema migration: OK
- News/RSS sourcing: OK
- YouTube sourcing: OK (many new videos scored `substance=2 trend=pending`)
- **Digest generation: FAILED** (`scripts/generate_digest.py`, exit 1). No `digests/2026-10-02.md` was produced.
- Writeup generation: OK, but 0 items (no digest items)
- Word report: OK, skipped (no digest items)

## Error
```
File "scripts/generate_digest.py", line 76, in build_digest
    top_substance = sorted(
TypeError: '<' not supported between instances of 'int' and 'str'
```
The sort in `build_digest` is comparing an int with a str. The input was 1104 items from 3 tables over the trailing 7 days. Likely a score or trend column holds mixed types, for example the `'pending'` trend value or a text-typed score. This was not investigated or fixed, per routine rules.

## Other notes
- `pip install --upgrade pip` failed because the Debian-managed pip has no RECORD file. `requirements.txt` installed fine.
- `git pull` printed a "no upstream" message because the session branch has no tracking branch. The branch was already at `origin/main` (07ccec9), so nothing was missed.
