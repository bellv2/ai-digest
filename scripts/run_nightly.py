"""
Orchestrates the pipeline steps that run inside the Claude Code Routine:
  1. ensure_schema.py    — must run first; adds any columns the scripts below expect
  2. source_news.py      — depends on repos' arXiv citations (populated separately)
  3. source_videos.py    — independent, order doesn't matter relative to news
  4. generate_digest.py  — must run last; reads from all three tables

NOTE: source_repos.py is NOT part of this script. It runs separately via
GitHub Actions (.github/workflows/source-repos.yml), since Claude Code
Routines restrict GitHub API traffic to only the attached repository. The
routine runs `git pull` before this script, to pick up the Actions
workflow's committed repo/arXiv data.

Each step is isolated: a failure in one script is logged and the pipeline
continues to the next step rather than aborting the whole night, since a
broken YouTube run shouldn't prevent news from being scored.

Exit code reflects overall health: 0 if all steps succeeded, 1 if any step
failed — used by the routine to decide whether it's safe to commit (see
docs/routine_prompt.md's sanity-check requirement).
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

SCRIPTS_DIR = Path(__file__).parent
STEPS = [
    ("ensure_schema.py", "Schema migration (ensures DB matches script expectations)"),
    ("source_news.py", "News/RSS sourcing"),
    ("source_videos.py", "YouTube sourcing"),
    ("generate_digest.py", "Digest generation"),
]


def run_step(script_name, description):
    print(f"\n{'=' * 60}\n[{datetime.now(timezone.utc).isoformat()}] Starting: {description} ({script_name})\n{'=' * 60}")
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script_name)],
            capture_output=True, text=True, timeout=3000,
        )
        elapsed = time.time() - start
        print(result.stdout)
        if result.stderr:
            print(f"[stderr]\n{result.stderr}")
        success = result.returncode == 0
        status = "OK" if success else f"FAILED (exit code {result.returncode})"
        print(f"[{description}] {status} in {elapsed:.0f}s")
        return success
    except subprocess.TimeoutExpired:
        print(f"[{description}] TIMED OUT after {time.time() - start:.0f}s")
        return False
    except Exception as e:
        print(f"[{description}] CRASHED: {e}")
        return False


def main():
    results = {}
    for script_name, description in STEPS:
        results[script_name] = run_step(script_name, description)

    print(f"\n{'=' * 60}\nNightly run summary\n{'=' * 60}")
    all_ok = True
    for script_name, description in STEPS:
        status = "✅ OK" if results[script_name] else "❌ FAILED"
        print(f"  {status} — {description}")
        if not results[script_name]:
            all_ok = False

    if not all_ok:
        print("\n[warn] one or more steps failed — routine should review before auto-merging.")
        sys.exit(1)

    print("\nAll steps completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
