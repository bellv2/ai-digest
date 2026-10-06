# Failed nightly run 2026-10-06

Nothing from this run was committed. Sanity check failed: 2 of 3 core steps failed (news, YouTube) and exit code was non-zero.

- Schema migration: OK
- News/RSS sourcing: FAILED (ModuleNotFoundError: feedparser/requests)
- YouTube sourcing: FAILED (ModuleNotFoundError: requests)
- Digest generation: OK, but output discarded (no new data sourced)
- Writeups (Gemini): FAILED (no module 'requests')
- Word report: FAILED (no module 'docx')

Cause: the environment's dependency install did not leave a working Python env. `pip install --upgrade pip setuptools` errored ("Cannot uninstall pip 24.0, RECORD file not found", Debian-installed), and every run printed a `_distutils_hack` ModuleNotFoundError from distutils-precedence.pth (broken setuptools after the upgrade attempt). Required modules were then not importable at run time.
No sqlite errors were seen. No fix attempted.
