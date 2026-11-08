# Failed nightly run 2026-11-08

Nothing from this run was committed except this note.

## What happened
- `pip install --upgrade pip setuptools` failed: "Cannot uninstall pip 24.0, RECORD file not found" (pip was installed by Debian).
- `pip install -r requirements.txt` then reported only feedparser, feedparser-sgmllib and youtube-transcript-api as installed.
- Every Python process printed `ModuleNotFoundError: No module named '_distutils_hack'` while processing `distutils-precedence.pth`. That suggests setuptools was left half-upgraded.
- `requests` and `python-docx` (`docx`) could not be imported when the scripts ran.
- `git pull` did not complete cleanly because the branch has no upstream tracking.

## run_nightly.py results (exit code 1)
- OK: Schema migration
- FAILED: News/RSS sourcing
- FAILED: YouTube sourcing (`No module named 'requests'`)
- OK: Digest generation. It ran on existing data (825 items in the trailing 7 days) and wrote `digests/2026-11-08.md`, but that digest was left uncommitted.
- FAILED: Narrative writeup generation (`No module named 'requests'`)
- FAILED: Word report generation (`No module named 'docx'`)

## Why nothing else was committed
More than one step failed with a non-zero exit code. No sqlite3 errors appeared. No new items were sourced, so the digest only reflects older data. The cause looks like a broken Python environment, not a data problem.

## Suggested fix
Check the environment's Python setup. Setuptools or pip is probably broken, and `requests` and `python-docx` need to be importable. Then rerun.
