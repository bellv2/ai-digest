# Failed nightly run — 2026-10-28

Nothing from this run was committed except this note.

## Cause
Environment/dependency problem, not a data problem.
- `pip install --upgrade pip setuptools` failed: "Cannot uninstall pip 24.0, RECORD file not found" (Debian-managed pip).
- `pip install -r requirements.txt` only installed feedparser, youtube-transcript-api and feedparser-sgmllib. `requests` and `python-docx` are listed in requirements.txt but are not importable by `python3` (Python 3.13).
- Every python3 start also printed `No module named '_distutils_hack'` from distutils-precedence.pth.

## Step results (scripts/run_nightly.py, exit 1)
- OK: Schema migration
- FAILED: News/RSS sourcing
- FAILED: YouTube sourcing (`import requests`)
- OK: Digest generation. It was built from the existing trailing-7-day data (798 items) with no new news or video items, so it was not committed.
- FAILED: Narrative writeup generation (`import requests`)
- FAILED: Word report generation (`import docx`)

4 of 6 steps failed, which trips the sanity check. No fixes were attempted.
