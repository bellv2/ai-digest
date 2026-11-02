# Failed nightly run — 2026-11-02

Nothing from the pipeline was committed. 4 of 6 steps failed, so the sanity check stopped the run.

## Cause
The environment is broken. `pip` belongs to the system Python 3.13 under `/usr/lib/python3/dist-packages`. `python3` is `/usr/local/bin/python3`. `pip install -r requirements.txt` therefore did not install packages where the scripts look for them.
- `requests` and `python-docx` are missing at runtime (`ModuleNotFoundError`).
- Every command prints a `_distutils_hack` `.pth` error.
- `pip install --upgrade pip` failed with "Cannot uninstall pip 24.0, RECORD file not found" because Debian owns that package.

## Step results
- Schema migration: OK
- News/RSS sourcing: FAILED (missing module)
- YouTube sourcing: FAILED (`requests` missing)
- Digest generation: OK, but it ran on stale data, since there was no new sourcing
- Gemini writeups: FAILED (`requests` missing)
- Word report: FAILED (`docx` missing)

There were no sqlite errors. The generated digest and DB changes were discarded.

## Suggested fix
Install the dependencies with `python3 -m pip` so they go to the interpreter that runs the scripts, or use a venv. Then re-run.
