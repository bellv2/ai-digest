# Failed nightly run 2026-10-24

Nothing was committed except this file. Four of six steps failed:
News/RSS sourcing, YouTube sourcing, narrative writeups, Word report.

Cause (environment, not code): `pip` resolves to /usr/bin/pip (Debian, python 3.13 dist-packages),
but `python3` is /usr/local/bin/python3. Modules such as `requests` and `docx` were not importable.
`pip install --upgrade pip` also failed (Debian-managed pip: "RECORD file not found"), and every
run prints a `_distutils_hack` .pth error.

Only schema migration and digest generation succeeded (digest built from stale data, 793 items).
The digest and DB changes were discarded. Likely fix: run `python3 -m pip install -r requirements.txt`
(or fix the interpreter in the routine's setup).
