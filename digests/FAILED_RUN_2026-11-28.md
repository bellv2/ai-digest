# Failed nightly run 2026-11-28

Nothing was committed except this file. Four of the five pipeline steps failed.

- OK: Schema migration, Digest generation (digest ran on stale data, 930 items from the trailing 7 days)
- FAILED: News/RSS sourcing, YouTube sourcing, Gemini writeups, Word report

Cause (environmental): `pip install --upgrade pip setuptools` failed ("Cannot uninstall pip 24.0, RECORD file not found", Debian-managed).
After that, every Python process printed `ModuleNotFoundError: _distutils_hack`.
`requests` and `python-docx` (both in requirements.txt) were not importable, so the failed steps died on `import requests` / `from docx import Document`.
The sourcing scripts likely failed the same way. Only feedparser, youtube-transcript-api and feedparser-sgmllib were installed.

No sqlite3 errors were seen.
The generated digest `digests/2026-11-28.md` and the modified `data/ai_digest.db` were left uncommitted.
The routine's pip setup step probably needs to change, for example installing into a venv or skipping the pip/setuptools upgrade.
