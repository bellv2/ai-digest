# Routine Setup Guide

This is the exact configuration to enter at claude.ai/code/routines. Routines
run on Anthropic's cloud infrastructure, not your local machine, and do not
have access to GitHub Actions secrets — they use their own Cloud Environment
config instead. See below for both.

---

## Step 1 — Create a Cloud Environment (do this first, separately)

Go to Settings → Environments (or you'll be prompted when creating the
routine) and create a new environment, e.g. named `ai-digest-env`:

**Environment variables** (add each of these — this is where your API keys
actually go, NOT GitHub repo secrets):
- `GEMINI_API_KEY` — your (rotated) Gemini key
- `YOUTUBE_API_KEY` — your (rotated) YouTube key
- `GH_TOKEN` — your (rotated) GitHub personal access token

**Setup script:**
```bash
pip install -r requirements.txt --break-system-packages
```

**Network access:** Default/Trusted should be sufficient — it covers package
registries and common dev domains. If the routine's first few runs show
network errors reaching GitHub API, YouTube API, Gemini API, or RSS feed
domains, widen network access for this environment.

---

## Step 2 — Create the routine

- **Name:** `ai-digest-nightly`
- **Repository:** `bellv2/ai-digest`
- **Environment:** select `ai-digest-env` created above
- **Trigger:** Scheduled — nightly at 4:00 AM (your local timezone; the UI
  converts automatically)
- **Branch pushes:** enable "Allow unrestricted branch pushes" for this
  repository — required for the auto-merge behavior below, since by default
  routines can only push to `claude/`-prefixed branches

## Step 3 — The prompt

Paste the following as the routine's prompt:

---

You are running the nightly ai-digest pipeline. This repository sources,
scores, and digests AI-related repos, YouTube videos, and news. Follow these
steps exactly, in order:

1. Run `python3 scripts/run_nightly.py` from the repository root. This
   orchestrates all four pipeline steps (repo sourcing, news sourcing, video
   sourcing, digest generation) with built-in error isolation — one step
   failing does not stop the others.

2. Read the full output of that command carefully.

3. **Sanity check before committing anything.** Do NOT commit or push if any
   of the following are true:
   - The script's overall exit code was non-zero AND more than one of the
     four steps failed (a single step failing is tolerable and expected
     occasionally — e.g. a transient API timeout — but multiple simultaneous
     failures suggests something is actually broken, like an expired API key
     or a schema mismatch)
   - The digest file generated in `digests/` is empty or missing entirely
   - Any step's output contains a Python traceback mentioning `sqlite3`,
     `OperationalError`, or `IntegrityError` — this indicates database
     corruption risk and should not be silently committed
   - The total row count change across all tables looks wildly implausible
     (e.g. thousands of new rows in one table when a typical night adds
     dozens) — check via `sqlite3 data/ai_digest.db "SELECT COUNT(*) FROM
     repos"` etc. before and after, and use judgment

   If any of these conditions are met: commit nothing, and instead write a
   brief summary of what went wrong to a new file at
   `digests/FAILED_RUN_<date>.md`, commit only that file to a
   `claude/`-prefixed branch, and stop. Do not attempt to fix the underlying
   issue yourself — flag it for human review.

4. **If the sanity check passes:** commit all changes (updated `data/*.db`
   files and the new `digests/*.md` file) directly to `main` with a commit
   message summarizing the run, e.g. `nightly run 2026-07-15: 12 repos, 8
   videos, 6 news items scored, digest generated`. Since unrestricted branch
   pushes are enabled for this repository, you can push directly rather than
   opening a PR — this repository's owner has explicitly chosen fully
   automated nightly commits with no manual review step, on the condition
   that the sanity check above is honored strictly.

5. Do not modify any file outside of `data/`, `digests/`, or committing the
   run's changes. Do not modify scoring logic, rubric documents, or scripts
   — those are edited by the repository owner directly, not by this routine.

6. Keep your final summary to the human short: how many items were sourced
   and scored per category, whether the digest was generated successfully,
   and flag anything unusual you noticed even if it didn't trigger the
   sanity-check stop condition above.

---

## Notes

- First run should be triggered manually ("Run now") rather than waiting for
  the 4am schedule, so you can review the transcript and catch any
  environment/secret misconfiguration before it's unattended.
- Routines share your Claude Pro subscription's usage pool with regular
  interactive sessions — monitor usage for the first week to confirm the
  nightly run's cost is sustainable alongside your normal daytime use.
- If YouTube/Gemini/GitHub keys ever need rotating, update them in the Cloud
  Environment settings (Settings → Environments → `ai-digest-env`), not in
  GitHub repo secrets.
