# Failed nightly run — 2026-10-12

Nothing from this run was committed (only this file).

- Install: `pip install --upgrade pip setuptools` errored ("Cannot uninstall pip 24.0, RECORD file not found", Debian-managed). `pip install -r requirements.txt` then ran; only feedparser, feedparser-sgmllib and youtube-transcript-api were newly installed.
- `python3 scripts/run_nightly.py` exit code 1. Steps:
  - Schema migration: OK
  - News/RSS sourcing: FAILED
  - YouTube sourcing: FAILED (`ModuleNotFoundError: No module named 'requests'`)
  - Digest generation: OK (831 items from trailing 7 days; no new items were sourced)
  - Narrative writeups (Gemini): FAILED (`No module named 'requests'`)
  - Word report: FAILED (`No module named 'docx'`)
- Every step also printed `ModuleNotFoundError: No module named '_distutils_hack'` from `distutils-precedence.pth`, which points to a broken Python environment (likely caused by the failed setuptools/pip upgrade).
- More than one step failed, so per the routine rules no data or digest was committed.

Suggested fix: make the environment install setuptools/pip cleanly (for example a venv, or skip the pip self-upgrade), then re-run.
