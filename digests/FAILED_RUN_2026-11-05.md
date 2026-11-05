# Failed nightly run — 2026-11-05

Nothing from this run was committed. Sanity check failed: 4 of 5 pipeline steps failed (exit code 1).

- OK: Schema migration, Digest generation (local digest written, but built from existing data only)
- FAILED: News/RSS sourcing, YouTube sourcing, Narrative writeup (Gemini), Word report

## Cause (environmental, not a data problem)
- `pip install --upgrade pip setuptools` errored: "Cannot uninstall pip 24.0, RECORD file not found" (Debian-managed pip).
- Every script then printed `ModuleNotFoundError: No module named '_distutils_hack'` from `distutils-precedence.pth`.
- `python3` then could not import `requests` or `docx`, although `pip list` shows `requests 2.34.2`, `python-docx 1.2.0` and `setuptools 84.2.1` installed. This looks like a mismatch between the pip and python3 site-packages, or a setuptools upgrade that broke the Debian setup.
- No sqlite3, OperationalError or IntegrityError tracebacks were seen.

## Suggested fix
Skip the pip/setuptools self-upgrade in the routine prompt (or use a venv), and check that `pip` and `python3` point at the same interpreter.
