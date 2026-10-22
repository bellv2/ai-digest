# Failed nightly run 2026-10-22

Nothing from this run was committed. Four of six steps failed (exit code 1).

- OK: schema migration, digest generation
- FAILED: news/RSS sourcing, YouTube sourcing, narrative writeups (Gemini), Word report
- Cause: missing Python modules (`requests`, `docx`, ...). `pip install --upgrade pip setuptools` failed
  ("Cannot uninstall pip 24.0, RECORD file not found", Debian-installed), and the later
  `pip install -r requirements.txt` only installed feedparser, feedparser-sgmllib and
  youtube-transcript-api. Every Python start also printed a `_distutils_hack` ModuleNotFoundError from
  /usr/lib/python3/dist-packages/distutils-precedence.pth.
- No fix attempted, per routine rules.
