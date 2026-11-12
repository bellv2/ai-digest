# Failed nightly run 2026-11-12

Nothing from this run was committed, in line with the sanity-check rules.

## Cause
The environment is missing Python dependencies, so most pipeline steps crashed on import:
- `pip install --upgrade pip setuptools` failed with "Cannot uninstall pip 24.0, RECORD file not found" (Debian-managed pip).
- `pip install -r requirements.txt` reported only feedparser, youtube-transcript-api and feedparser-sgmllib as installed. `requests` and `python-docx` still could not be imported afterwards (`ModuleNotFoundError: No module named 'requests'` / `'docx'`).
- Every step also prints a `_distutils_hack` .pth warning, which suggests the setuptools state is broken.
- `git pull` failed because the branch has no upstream tracking.

## Step results
- Schema migration: OK
- News/RSS sourcing: FAILED
- YouTube sourcing: FAILED (`import requests`)
- Digest generation: OK, but built only from stale data (842 items, trailing 7 days), because news and video sourcing did not run
- Narrative writeups (Gemini): FAILED (`import requests`)
- Word report: FAILED (`import docx`)

Exit code was 1, with more than one step failed. The digest and `data/ai_digest.db` changes were left uncommitted.

## Suggested fix
Make the routine environment's setup script install the dependencies into a working Python environment, for example a venv, then re-run.
