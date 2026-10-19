# Failed nightly run 2026-10-19

Nothing from this run was committed. Two of the three sourcing steps failed, which meets the abort condition.

- Schema migration: OK
- News/RSS sourcing: FAILED, `ModuleNotFoundError: No module named 'requests'`
- YouTube sourcing: FAILED, `ModuleNotFoundError: No module named 'requests'`
- Digest generation: OK, but it ran on stale data (774 items from the trailing 7 days). The output was not committed.
- Gemini writeups: FAILED, missing `requests`
- Word report: FAILED, missing `docx` (python-docx)

Cause: the dependency install step did not provide `requests` or `python-docx`. `pip install --upgrade pip` also failed, because the Debian-managed pip has no RECORD file. A `_distutils_hack` .pth error appears on every Python start. This looks like an environment problem, not a data or SQLite problem.

Suggested fix: use a virtualenv in the routine setup, or `pip install --ignore-installed`.
