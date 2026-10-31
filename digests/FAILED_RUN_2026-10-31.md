# Failed nightly run 2026-10-31

Not committed: 4 of 6 steps failed (news/RSS sourcing, YouTube sourcing, Gemini writeups, Word report).

Cause: environment, not data. `pip install --upgrade pip setuptools` failed partway
("Cannot uninstall pip 24.0, RECORD file not found", Debian-installed), leaving a broken
`distutils-precedence.pth` (`No module named '_distutils_hack'`). After that
`import requests` and `import docx` fail, although requirements.txt install reported success.

Only schema migration and digest generation succeeded (digest built from stale 7-day data: 787 items, no new news/video items).
data/ai_digest.db and digests/2026-10-31.md were left uncommitted.

Suggested fix: skip the pip/setuptools self-upgrade in the routine (or use a venv), then re-run.
