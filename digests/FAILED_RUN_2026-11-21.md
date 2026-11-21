# Failed run 2026-11-21

Nightly pipeline not committed. 4 of 5 steps failed (news, YouTube, writeups, docx) with `ModuleNotFoundError` (requests, docx, ...).

Cause: environment mismatch. `pip` installs into Python 3.13 (`/root/.local/lib/python3.13`), but `python3` resolves to `/usr/local/bin/python3` (3.11). The `pip install --upgrade pip` step also errored (debian-managed pip), and a `_distutils_hack` .pth error appears on every run.

Only schema migration and digest generation ran. The digest (digests/2026-11-21.md) and DB changes were not committed. No fixes attempted, per routine rules.
