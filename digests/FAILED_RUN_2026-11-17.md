# Failed run 2026-11-17

Nothing was committed except this file. The sanity check tripped: exit code was non-zero and more than one step failed.

- OK: schema migration, digest generation (digest ran only on existing data, so it is stale)
- FAILED: news/RSS sourcing, YouTube sourcing, Gemini writeups, Word report

Cause: environment, not data. `pip install --upgrade pip setuptools` failed ("Cannot uninstall pip 24.0, RECORD file not found", Debian-managed pip). It left Python without `_distutils_hack`, and `requests` and `python-docx` were not importable (ModuleNotFoundError) even though `pip install -r requirements.txt` reported success for feedparser and youtube-transcript-api.

Fix suggestion: change the routine's setup to skip the pip/setuptools upgrade (or use `--ignore-installed pip`), and ensure `requests` and `python-docx` get installed.

No sqlite errors were seen. The modified data/ai_digest.db and digests/2026-11-17.md were left uncommitted.
