# Failed nightly run — 2026-10-11

Nothing from this run was committed (only this file).

## What happened
- Step 1: `pip install` targeted Python 3.13 while `python3` is 3.11, so the first run of `run_nightly.py` failed 4/6 steps with `ModuleNotFoundError` (requests, docx). I re-installed with `python3 -m pip` and re-ran.
- Second run: schema migration, news, YouTube sourcing, writeups and docx reported OK, but **Digest generation FAILED**:
  `generate_digest.py` line 76 (`build_digest`, `top_substance` sort) -> `TypeError: '<' not supported between instances of 'int' and 'str'`.
  Likely a string-typed `substance_score`/`trend_score` among the newly sourced video rows (1098 items in trailing 7 days).
- `digests/2026-10-11.md` on disk is stale (written by the first run before new sourcing); not committed.
- Narrative writeups: all 12 Gemini calls returned 404 (model `gemini-2.5-flash-lite` not found) yet the step reported OK, so the docx has no real narratives.
- Security note: the Gemini API key is printed in full in the warning URLs in the script output; consider rotating it and stripping the key from logged errors.

## Left uncommitted in the working tree
data/ai_digest.db (modified), digests/2026-10-11.{md,docx}.

No scripts were modified.
