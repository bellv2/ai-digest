# Failed nightly run 2026-11-24

Nothing from this run was committed, per the sanity-check rules. Four of the six steps failed.

- Passed: schema migration, digest generation.
- Failed: news/RSS sourcing, YouTube sourcing, Gemini writeups (`ModuleNotFoundError: requests`), Word report (`ModuleNotFoundError: docx`).
- Environment problem: `pip install --upgrade pip setuptools` errored ("Cannot uninstall pip 24.0, RECORD file not found", installed by Debian).
  After that, `python3` reports `No module named '_distutils_hack'` from `distutils-precedence.pth`.
  It also can't import `requests` or `docx`, although `pip list` shows them installed. This looks like a mismatch between the pip and python3 environments.
- The digest file `digests/2026-11-24.md` was generated, but it is based on stale data because the sourcing steps failed. It was not committed.
- `data/ai_digest.db` was modified locally and not committed.
