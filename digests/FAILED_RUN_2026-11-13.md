# Failed nightly run — 2026-11-13

Nothing from this run was committed except this note.

- `pip install --upgrade pip setuptools` failed (pip is Debian-managed: "Cannot uninstall pip 24.0, RECORD file not found"). The `requirements.txt` install reported success, but `requests` and `python-docx` were not importable afterwards.
- Every Python run printed `ModuleNotFoundError: No module named '_distutils_hack'`, so the setuptools upgrade likely left the environment broken.
- `git pull` did nothing: the branch has no upstream tracking, so no fresh Actions-sourced data was fetched.
- run_nightly.py exit code was 1. Failed steps:
  - News/RSS sourcing
  - YouTube sourcing
  - Narrative writeup generation (Gemini)
  - Word report generation
- Passed steps: schema migration, digest generation. The digest (`digests/2026-11-13.md`) was generated from stale data only, so it was not committed.
- `data/ai_digest.db` was modified locally by the run but not committed.

Likely fix: make the dependency install robust in the routine environment (for example `pip install --ignore-installed`, or skip the pip/setuptools upgrade), and set upstream tracking for `git pull`.
