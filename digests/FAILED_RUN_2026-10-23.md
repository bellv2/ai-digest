# Failed nightly run: 2026-10-23

Nothing from this run was committed. 4 of 6 steps failed, which meets the stop condition.

## Cause
The failures were environmental, not data or scoring problems:
- `pip install --upgrade pip setuptools` failed to uninstall the Debian-managed pip 24.0 (no RECORD file).
- `pip install -r requirements.txt` was run with `/usr/bin/pip`, but `python3` resolves to `/usr/local/bin/python3` (3.11.17). The packages did not land on that interpreter.
- Every `python3` invocation also printed a `_distutils_hack` .pth error.
- As a result, `requests` and `python-docx` were missing at run time.

## Step results
- OK: Schema migration
- FAILED: News/RSS sourcing (ModuleNotFoundError)
- FAILED: YouTube sourcing (`No module named 'requests'`)
- OK: Digest generation. It ran only on stale data (788 items, trailing 7 days) with no fresh news or videos, so it was discarded.
- FAILED: Narrative writeup generation (`No module named 'requests'`)
- FAILED: Word report generation (`No module named 'docx'`)

No sqlite3 errors occurred. The DB and digest changes were reverted and not committed.

## Suggested fix
Make the routine's environment install requirements with the same interpreter that runs the scripts (`python3 -m pip install -r requirements.txt`), and fix the distutils-precedence.pth issue.
