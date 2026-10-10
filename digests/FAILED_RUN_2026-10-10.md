# Failed nightly run 2026-10-10

`scripts/run_nightly.py` exited 1 with 4 of 6 steps failed. Nothing from the run was committed.

- OK: schema migration, digest generation (digests/2026-10-10.md written locally, 834 items from 3 tables, not committed)
- FAILED: News/RSS sourcing, YouTube sourcing, Gemini writeups, Word report
- Cause: `ModuleNotFoundError` for `requests` (and `docx`) in the routine environment. The `pip install --upgrade pip` step errored (Debian-managed pip, no RECORD file), and `requests`/`python-docx` were not importable afterward. No sqlite3 errors seen.
- Fix needed: repair the routine environment's Python dependencies (e.g. `pip install --ignore-installed requests python-docx`) and re-run.
