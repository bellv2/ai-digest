# Failed nightly run 2026-10-20

No data committed. Sanity check failed: 4 of 6 steps failed (more than one).

- OK: schema migration, digest generation (digests/2026-10-20.md written, 1755 bytes; not committed)
- FAILED: news/RSS sourcing, YouTube sourcing, Gemini writeups, Word report

Cause: `ModuleNotFoundError` for `requests` and `docx`. `pip` (/usr/bin/pip) targets Python 3.13, but `python3` is /usr/local/bin/python3 (3.11), so requirements were installed into the wrong interpreter. Also `pip install --upgrade pip` failed (Debian-managed pip, no RECORD file), and `git pull` reported no upstream tracking for the branch.

Suggested fix: install with `python3 -m pip install -r requirements.txt --break-system-packages`. No traceback mentioned sqlite3/OperationalError/IntegrityError.
