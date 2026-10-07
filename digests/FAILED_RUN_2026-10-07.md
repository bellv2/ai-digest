# Failed nightly run 2026-10-07

Nothing from the run was committed. Four of six steps failed.

- OK: schema migration, digest generation (digests/2026-10-07.md was produced but not committed)
- FAILED: news/RSS sourcing, YouTube sourcing, Gemini writeups (`ModuleNotFoundError: requests`), Word report (`ModuleNotFoundError: docx`)

Likely cause: environment setup. `pip install --upgrade pip` failed (Debian-managed pip, "RECORD file not found"). After that, `requests` and `python-docx` were not importable even though requirements.txt lists them. Site-packages also emitted a `_distutils_hack` error on every Python start.
`git pull` also did not complete: the branch has no upstream tracking set.

Nothing was fixed. Suggested fix: add `--ignore-installed` or skip the pip self-upgrade in the routine's setup, then re-run.
