# Failed nightly run — 2026-10-18

Nothing from this run was committed (data/ and the generated digest were left uncommitted).

- `run_nightly.py` exit code: 1. Two of the three core steps failed (News/RSS sourcing, YouTube sourcing); digest generation, schema migration OK.
- Cause: missing Python modules at run time (`feedparser`, `requests`, `docx`) despite `pip install -r requirements.txt` reporting success for only feedparser/youtube-transcript-api/feedparser-sgmllib. The pip/setuptools upgrade also failed (`Cannot uninstall pip 24.0, RECORD file not found` — Debian-managed pip), and the Python site setup logs `No module named '_distutils_hack'` on every invocation.
- Writeup (Gemini) and Word report steps also failed with missing `requests` / `docx`.
- Likely fix: check requirements.txt coverage (requests, python-docx) and the environment's Python/pip setup (e.g. use a venv or `--ignore-installed`).
- No sqlite3/OperationalError/IntegrityError tracebacks. No items were scored this run.
