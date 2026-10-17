# Failed nightly run, 2026-10-17

No pipeline output was committed. Only this file is.

## Why the sanity check failed
More than one step failed (exit code 1):
- News/RSS sourcing: `ModuleNotFoundError: feedparser`
- YouTube sourcing: `ModuleNotFoundError: requests`
- Narrative writeup generation: `ModuleNotFoundError: requests`
- Word report generation: `ModuleNotFoundError: docx`

Schema migration and digest generation reported OK. The digest was built only from existing data, because no new news or videos were sourced.

## Likely root cause (environment, not code)
`pip` (`/usr/bin/pip`) belongs to Python 3.13, but `python3` (`/usr/local/bin/python3`) is Python 3.11. `pip install -r requirements.txt` therefore installed packages for a different interpreter. The `pip install --upgrade pip` step also failed with "Cannot uninstall pip 24.0, RECORD file not found" because Debian installed it.

Suggested fix, for the owner to apply: install with `python3 -m pip install -r requirements.txt --break-system-packages`.

## Other notes
- `git pull` failed on the working branch because it has no upstream. `git pull origin main` says "Already up to date".
- No sqlite3 errors appeared in the output.
- `data/ai_digest.db` and `digests/2026-10-17.md` were modified or created locally but deliberately not committed.
