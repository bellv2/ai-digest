"""
Orchestrates the full nightly pipeline in the correct dependency order:
  1. source_repos.py   — must run first; populates cited_arxiv_ids for step 3's cap
  2. source_news.py    — depends on repos' arXiv citations for the volume cap
  3. source_videos.py  — independent, order doesn't matter relative to 1/2
  4. generate_digest.py — must run last; reads from all three tables

Each step is isolated: a failure in one script is logged and the pipeline
continues to the next step rather than aborting the whole night, since a
broken YouTube run shouldn't prevent repos/news from being scored.

Exit code reflects overall health: 0 if all steps succeeded, 1 if any step
failed — used by the routine to decide whether auto-merge is safe (see
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
    ("source_repos.py", "GitHub repo sourcing"),
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
            capture_output=True, text=True, timeout=3000,  # 50 min ceiling per step
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
