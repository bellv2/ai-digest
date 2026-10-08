# Failed nightly run: 2026-10-08

Nothing from this run was committed. Four of the six steps failed, which trips the sanity-check rule.

- OK: schema migration, digest generation. The digest covered 802 items from the trailing 7 days. It was written locally but not committed.
- FAILED: news/RSS sourcing, YouTube sourcing, Gemini writeups. Cause: `ModuleNotFoundError: No module named 'requests'`.
- FAILED: Word report. Cause: `ModuleNotFoundError: No module named 'docx'`.

## Likely cause
The environment is broken, not the pipeline code.
- `pip install --upgrade pip setuptools` errored because the Debian-managed pip has no RECORD file.
- Every run also logs `No module named '_distutils_hack'` from `distutils-precedence.pth`.
- `pip install -r requirements.txt` reported success but installed only feedparser and youtube-transcript-api. `requests` and `python-docx` are listed in `requirements.txt` yet cannot be imported.
- Likely fix: install into a venv, or fix the setuptools and `_distutils_hack` state in the routine environment.
- `git pull` also printed an upstream-tracking message for this branch. The run did not look into it.
