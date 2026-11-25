# Failed run 2026-11-25

Nothing from this run was committed (sanity check failed: exit code 1 and 4 of 6 steps failed).

- OK: Schema migration, Digest generation (digests/2026-11-25.md produced locally, not committed)
- FAILED: News/RSS sourcing, YouTube sourcing, Narrative writeups, Word report
- Cause: `ModuleNotFoundError` for `requests` and `docx` (python-docx) even though both are in requirements.txt.
  `pip install --upgrade pip setuptools` errored ("Cannot uninstall pip 24.0, RECORD file not found", Debian-installed pip), and the environment shows a broken `_distutils_hack` .pth warning. Dependencies appear not to have installed properly.
- No sqlite errors were observed. No fixes attempted.
