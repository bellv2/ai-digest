# Failed run 2026-11-04

Nothing from this run was committed (DB changes and digest left uncommitted).

- Step 1: `pip install --upgrade pip setuptools` errored (pip 24.0 is Debian-managed, cannot uninstall). requirements.txt install reported success (feedparser, youtube-transcript-api), but `requests` and `docx` (python-docx) are not importable in the environment.
- Every Python invocation also prints `ModuleNotFoundError: No module named '_distutils_hack'` from distutils-precedence.pth (likely caused by the setuptools upgrade attempt).
- run_nightly.py: schema migration OK, digest generation OK (828 items, 7-day window). FAILED: News/RSS sourcing, YouTube sourcing (`requests` missing), Gemini writeups (`requests` missing), Word report (`docx` missing).
- 4 of 6 steps failed, so the sanity check blocked commit. No sqlite errors observed.
- Likely fix: ensure requirements.txt includes requests and python-docx, and/or fix the environment setup script (avoid upgrading pip/setuptools on Debian system Python).
