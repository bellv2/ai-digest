# Failed nightly run — 2026-11-03

Nothing was committed except this note.

- Schema migration: OK
- News/RSS sourcing: FAILED (`ModuleNotFoundError: requests`)
- YouTube sourcing: FAILED (`ModuleNotFoundError: requests`)
- Digest generation: OK (ran on stale data, so it was not committed)
- Narrative writeups: FAILED (`requests` missing)
- Word report: FAILED (`docx` missing)

Likely cause: `pip install --upgrade pip setuptools` errored (`Cannot uninstall pip 24.0, RECORD file not found`, Debian-managed). It also left a broken `_distutils_hack` .pth. `pip install -r requirements.txt` then reported installing only feedparser, youtube-transcript-api and their dependencies. `requests` and `python-docx` were not importable at run time.

No sqlite3 errors. No fixes attempted, as per routine rules.
