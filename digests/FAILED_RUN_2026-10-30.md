# Failed nightly run — 2026-10-30

Nothing from this run was committed (DB changes and the generated digest were left uncommitted).

## Step results
- Schema migration: OK
- News/RSS sourcing: FAILED (`ModuleNotFoundError: No module named 'requests'`)
- YouTube sourcing: FAILED (`No module named 'requests'`)
- Digest generation: OK (digest ran over existing data only, 801 items from trailing 7 days; no new news/video items were sourced)
- Narrative writeups (Gemini): FAILED (`No module named 'requests'`)
- Word report: FAILED (`No module named 'docx'`)

Script exit code: 1. More than one step failed, so the sanity check stopped the commit.

## Likely cause (environment, not data)
- `pip install -r requirements.txt` installed feedparser, youtube-transcript-api only; `requests` and `python-docx` are not importable by `python3`.
- `pip install --upgrade pip` failed ("Cannot uninstall pip 24.0, RECORD file not found" - Debian-managed), and `/usr/local/bin/python3` (3.13) differs from the `/usr/bin/pip` interpreter, so packages likely went to a different Python.
- Each run also prints a `_distutils_hack` .pth error (harmless noise).
- `git pull` did nothing: the branch has no upstream tracking set.

No sqlite errors were observed. Suggest fixing the routine setup (use `python3 -m pip install ...`) and rerunning.
