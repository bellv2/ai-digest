# Failed run 2026-11-19

Nightly pipeline aborted at the sanity check. Nothing from the run was committed.

- pip upgrade of pip/setuptools failed (Debian-managed pip, "Cannot uninstall pip 24.0, RECORD file not found").
- `pip install -r requirements.txt` only installed feedparser, youtube-transcript-api and feedparser-sgmllib. `requests` and `python-docx` are still not importable. This looks like an environment problem.
- Every step's stderr shows `ModuleNotFoundError: No module named '_distutils_hack'` from `distutils-precedence.pth`.

Step results:
- Schema migration: OK
- News/RSS sourcing: FAILED
- YouTube sourcing: FAILED (`No module named 'requests'`)
- Digest generation: OK (a digest was generated from existing data only, not committed)
- Gemini writeups: FAILED (`No module named 'requests'`)
- Word report: FAILED (`No module named 'docx'`)

More than one step failed, so per the routine rules nothing else was committed. Fix the routine environment's Python packages (`requests`, `python-docx`) and re-run.
