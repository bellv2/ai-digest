# Failed nightly run — 2026-11-22

Nothing from this run was committed (DB changes and generated digest discarded).

- Overall exit code: 1; 4 of the pipeline steps failed (News/RSS sourcing, YouTube sourcing, Gemini writeups, Word report). Schema migration and digest generation succeeded.
- Cause: `ModuleNotFoundError` for `requests` and `docx`. `pip install -r requirements.txt` reported packages satisfied under `/usr/local/lib/python3.13`, but `python3` resolves to a different interpreter that does not see them (also `_distutils_hack` .pth errors; `pip install --upgrade pip` failed: "Cannot uninstall pip 24.0, RECORD file not found" — Debian-installed).
- Not a data/sqlite issue. Likely fix: environment setup (use a venv or the same interpreter for pip and python3).
- Per routine rules, no fix attempted.
