# Failed nightly run — 2026-10-29

`scripts/run_nightly.py` exited 1. Four of six steps failed, so nothing from the run was committed.

- OK: schema migration; digest generation (digest written from existing data only, 788 items from the trailing 7 days, not committed)
- FAILED: News/RSS sourcing, YouTube sourcing, narrative writeups, Word report

Cause: environment, not data. `pip install --upgrade pip setuptools` failed ("Cannot uninstall pip 24.0, RECORD file not found", Debian-managed). Afterwards `pip install -r requirements.txt` installed only feedparser and youtube-transcript-api. `requests` and `python-docx` are not importable (`ModuleNotFoundError`), and every Python process prints a `_distutils_hack` .pth error.

No sqlite3/OperationalError/IntegrityError tracebacks were seen.

Suggested fix: make the routine's setup script install requirements into a venv, or skip the pip/setuptools self-upgrade.
