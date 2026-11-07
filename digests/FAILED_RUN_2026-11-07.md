# Failed run 2026-11-07

Nightly pipeline not committed: 4 of 6 steps failed (exit code 1).

- OK: schema migration, digest generation (digests/2026-11-07.md generated locally, not committed)
- FAILED: news/RSS sourcing, YouTube sourcing, Gemini writeups, Word report
- Cause: environment, not data. `ModuleNotFoundError: No module named 'requests'` and `'docx'`.
  `pip install --upgrade pip setuptools` failed (Debian-managed pip: "Cannot uninstall pip 24.0, RECORD file not found"),
  and `pip install -r requirements.txt` only installed feedparser, youtube-transcript-api; requests and python-docx were not importable by python3.
  Also noisy `_distutils_hack` .pth error on every python invocation.
- `git pull` reported no upstream tracking for this branch.
- No sqlite errors. Because news and video sourcing failed, the digest only reflects previously committed data.
- Recommended: fix the routine environment's Python setup (venv, or install requests/python-docx for python3.13) and rerun.
