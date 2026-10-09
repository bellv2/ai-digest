# Failed nightly run — 2026-10-09

Nothing from this run was committed (DB changes and generated digest discarded).

## Cause
- `pip install --upgrade pip setuptools` failed: "Cannot uninstall pip 24.0, RECORD file not found (installed by debian)".
- The partial upgrade left a broken `distutils-precedence.pth` (`ModuleNotFoundError: No module named '_distutils_hack'`).
- Afterwards `requests` and `docx` were not importable in the run.
- `git pull` also failed (no upstream configured for the working branch).

## run_nightly.py results (exit 1)
- OK: Schema migration
- FAILED: News/RSS sourcing (missing module)
- FAILED: YouTube sourcing (`No module named 'requests'`)
- OK: Digest generation (but ran without fresh news/video data)
- FAILED: Narrative writeup generation (`No module named 'requests'`)
- FAILED: Word report generation (`No module named 'docx'`)

More than one step failed with a non-zero exit, so per the routine's rules nothing was committed. No sqlite errors were observed.
Likely fix: environment setup (avoid upgrading debian-managed pip/setuptools; ensure requests, python-docx are installed).
