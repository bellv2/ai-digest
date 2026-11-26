# Failed nightly run 2026-11-26

`scripts/run_nightly.py` exited 1; 4 of 5 steps failed (only schema migration and digest generation succeeded).

- News/RSS sourcing, YouTube sourcing, Gemini writeups: `ModuleNotFoundError: No module named 'requests'`
- Word report: `ModuleNotFoundError: No module named 'docx'`

Cause: environment mismatch. `pip install -r requirements.txt` reported success (packages in /root/.local/lib/python3.13 and /usr/local/lib/python3.13), but `python3` cannot import them. `pip install --upgrade pip` also failed (debian-managed pip, no RECORD file). Also a harmless `_distutils_hack` .pth warning.

No new news/video items were sourced, so the digest was built from stale data. Per the routine's sanity rules, no data or digest changes were committed. Fix the Python/pip interpreter mismatch in the routine environment and re-run.
