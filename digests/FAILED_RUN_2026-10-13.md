# Failed nightly run 2026-10-13

No data or digest committed.

- `pip install` targeted /usr/bin/python3 (Debian, py3.13) but `python3` resolves to /usr/local/bin/python3, which has no `requests` or `python-docx`.
- `pip install --upgrade pip setuptools` failed (Debian-managed pip, no RECORD file).
- run_nightly.py: schema migration OK, digest generation OK; News/RSS sourcing, YouTube sourcing, Gemini writeups and Word report FAILED with ModuleNotFoundError (`requests`, `docx`).
- 4 of 6 steps failed, so the sanity check was not met. The generated digest was based on stale data (no new news/video items), so it was discarded.

Fix: run `python3 -m pip install -r requirements.txt` (or `/usr/local/bin/python3 -m pip ...`) in the routine's step 1.
