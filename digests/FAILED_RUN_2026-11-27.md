# Failed run 2026-11-27

Nothing from the pipeline was committed. Five steps ran; four failed with `ModuleNotFoundError` (`requests`, `docx`) and only schema migration and digest generation succeeded.

- `pip install --upgrade pip` failed ("Cannot uninstall pip 24.0, RECORD file not found", Debian-managed). `pip install -r requirements.txt` reported everything already satisfied.
- `python3` (which resolves to the system interpreter) could not import `requests` or `docx`, although pip reported them installed under `/usr/local/lib/python3.13`. This is probably a mismatch between the `pip` and `python3` interpreters.
- Failed: news/RSS sourcing, YouTube sourcing, Gemini writeups, Word report.
- Succeeded: schema migration, digest generation (924 items from the trailing 7 days, but with no fresh news or video data). The digest was discarded.
- No sqlite errors were seen.

Fix the environment (setup script should install into the interpreter that `python3` uses, e.g. `python3 -m pip install -r requirements.txt --break-system-packages`) and re-run.
