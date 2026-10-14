# Failed nightly run - 2026-10-14

Nothing was committed except this note. Data and digest were discarded.

## What happened
- `pip install -r requirements.txt` only installed feedparser, youtube-transcript-api and feedparser-sgmllib. The `pip install --upgrade pip setuptools` step failed (Debian-managed pip 24.0, no RECORD file), and afterwards `requests` and `python-docx` were not importable. Every script also printed a `_distutils_hack` .pth error.
- `scripts/run_nightly.py` results:
  - Schema migration: OK
  - News/RSS sourcing: FAILED (missing module)
  - YouTube sourcing (`requests` missing): FAILED
  - Digest generation: OK, but it only re-read existing data, so it is stale
  - Gemini writeups (`requests` missing): FAILED
  - Word report (`docx` missing): FAILED
- No sqlite3 errors. No new items were sourced or scored.

## Suggested fix
Make the routine's environment install `requests` and `python-docx` reliably, for example by confirming they are in requirements.txt or the setup script. Skip the pip/setuptools self-upgrade, or use a venv, because it breaks on Debian.
