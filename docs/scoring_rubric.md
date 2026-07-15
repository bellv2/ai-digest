# AI Content Curation — Master Scoring Rubric

This document is the grading standard fed to the LLM scoring pass. Every item (repo, video, article) gets scored on two independent axes — **Substance** and **Trend** — plus a vision-escalation check. Scores are 1–5 integers. No half-points; if genuinely torn between two scores, round down (bias toward skepticism, not hype).

---

## Core Principles (apply to all categories)

1. **Substance and Trend are scored independently.** A brand-new repo with 3 stars can score 5 on Substance and 1 on Trend. A viral video can score 5 on Trend and 1 on Substance. Never let one axis influence the other.
2. **Default to skepticism.** If evidence for a claim is missing, ambiguous, or only asserted (not shown), score it low. The burden of proof is on the content, not the grader.
3. **Judge the artifact, not the packaging.** A poorly-titled repo with genuine innovation still scores high on Substance. A slick, well-produced video with no real content still scores low.
4. **Ties go to "boring."** When uncertain whether something is a genuine innovation or a repackaging of known work, assume repackaging.

---

## AXIS 1: SUBSTANCE (1–5)

### Repos

Substance is computed as a **base score from measurable signals**, then adjusted by disqualifiers. Do not eyeball "novelty" in the abstract — run the checklist.

**Step 1 — Paper/Reference Check (worth up to 2 points)**
- README or repo description links to an arXiv ID, DOI, or named paper → **+2**
- README references a named technique/paper in prose but no direct link → **+1**
- No reference to any external research or prior art → **+0**

**Step 2 — Comparative Evidence Check (worth up to 2 points)**
- Contains a benchmark table/chart comparing against ≥2 named alternatives, with numbers → **+2**
- Contains at least one quantified claim (e.g. "40% faster than X," "reduces memory by 2.3GB") with a stated methodology or reproducible script → **+1**
- Contains only unquantified claims ("faster," "better," "efficient") with no numbers → **+0**

**Step 3 — Engineering Depth Check (worth up to 1 point)**
- Commit count ≥ 15 AND commits span ≥ 5 distinct days (not a single dump) → **+1**
- Fewer than 15 commits, or all commits within a single day → **+0**

**Base score = sum of Steps 1–3, mapped as: 5→5, 4→5, 3→4, 2→3, 1→2, 0→1**

**Substance disqualifiers (override base score, cap at 2 regardless of Step 1–3 total):**
- Repo has zero executable code files (only a README/concept doc) → cap at **1**
- README makes a specific quantified claim that does not appear anywhere reproducible in code/scripts (claim without receipts) → cap at **2**
- >90% of code is textually identical to a pre-existing, more-starred repo (near-duplicate/fork with cosmetic renaming) → cap at **1**

**Data to pull per repo (via GitHub API):** `description`, `readme_text`, `commit_count`, `commit_date_range`, `stargazers_count`, `forks_count`, `created_at`, presence of `.py`/`.ipynb`/other code file extensions, any linked arXiv/DOI pattern matched via regex on README text.

### YouTube Videos

Substance is computed from **measurable claim-to-evidence ratio**, not vibes. Use the transcript (via YouTube's caption/transcript API) as primary evidence source.

**Step 1 — Evidence Density Check (worth up to 2 points)**
- Transcript contains ≥3 distinct instances of specific, checkable content: on-screen code shown, a specific benchmark number stated, or a specific technical mechanism explained (not just named) → **+2**
- Transcript contains 1–2 such instances → **+1**
- Transcript contains 0 specific/checkable instances (pure narration/opinion) → **+0**

**Step 2 — Claim-Density Check (worth up to 2 points, inverse scoring — fewer unsupported superlatives is better)**
- Count superlative/hype terms in transcript: "insane," "game-changing," "you need this," "mind-blowing," "unbelievable," "crazy," "next level," "revolutionary." Count instances per 1,000 words of transcript.
- < 2 per 1,000 words → **+2**
- 2–5 per 1,000 words → **+1**
- \> 5 per 1,000 words → **+0**

**Step 3 — Call-to-Action Check (worth up to 1 point)**
- Video description/transcript's primary CTA is to a free resource (repo, docs, further reading) → **+1**
- Primary CTA is a paid course, affiliate link, "join my community," or sponsored product → **+0**

**Base score = sum of Steps 1–3, mapped as: 5→5, 4→5, 3→4, 2→3, 1→2, 0→1**

**Substance disqualifiers (override base score, cap at 2 regardless of Step 1–3 total):**
- Title or thumbnail contains a specific capability claim (e.g. "beats GPT-5 at coding") that is never substantiated with any evidence in the transcript → cap at **1**
- Sponsored segment (detect via "sponsored," "this video is brought to you by," or YouTube's paid-promotion flag) occupies >30% of the video's runtime → cap at **2**
- Video is a re-upload/clip compilation of another creator's content with no original analysis added (check: transcript >70% overlapping text with an earlier-published video on the same topic) → cap at **1**

**Pre-screen gate (runs before transcript fetch attempt):**
Testing during implementation revealed that most transcript-fetch failures aren't actually YouTube blocking the request — they're videos that simply have no captions at all, which the transcript library reports with a misleadingly generic "IP blocked" error message regardless of true cause. YouTube's own video metadata (`contentDetails.caption`) reports caption availability directly and reliably (~90% accuracy validated against live fetch attempts), so this is checked first and is decisive: if `caption != "true"`, no transcript attempt is made at all.

For videos that do have captions available, a second cheap metadata-only check still applies before fetching, to skip videos unlikely to carry substantive evidence even if a transcript exists — reducing unnecessary calls and further limiting exposure to the genuine (rare) cloud-IP rate-limiting that still occurs occasionally:
- Duration ≥ 120 seconds (very short Shorts rarely carry substantive evidence)
- Description contains either a URL or ≥40 words (signals real content vs. a one-line caption)
- Title isn't pure clickbait-hype phrasing with zero substantive keywords (tutorial, benchmark, build, compare, etc.)

Videos that fail either gate are scored directly from title/description, capped at Substance ≤2 (same treatment as a failed transcript fetch), without attempting the transcript call. The skip reason is stored (`no_captions_available` or `skipped_prescreen:<reason>`) for auditability.

**Data to pull per video (via YouTube Data API + transcript):** `title`, `description`, `transcript_text` (only if both gates pass), `duration`, `caption` (from contentDetails), `published_at`, `channel_id`, `view_count`, sponsor-segment flag if available, word count of transcript for per-1000-word normalization.

### News/Articles

**Step 1 — Primary Source Check (worth up to 2 points)**
- Article contains ≥1 hyperlink to a primary source (official company blog/model card, arXiv/paper, SEC filing, government filing) → **+2**
- Article names a primary source in prose but does not link it (e.g. "according to OpenAI's blog post") → **+1**
- No primary source named or linked; sourced only from other news articles or unnamed "sources" → **+0**

**Step 2 — Number Specificity Check (worth up to 2 points)**
- Every quantified claim in the article (benchmark %, funding amount, user count, etc.) has a stated unit and source → **+2**
- Some quantified claims present but at least one lacks a clear source or unit → **+1**
- No specific numbers at all, or numbers are vague ("massive," "huge jump") → **+0**

**Step 3 — Limitation Disclosure Check (worth up to 1 point)**
- Article explicitly states at least one limitation, caveat, or context that tempers the headline claim → **+1**
- No limitations/caveats mentioned anywhere in the body → **+0**

**Base score = sum of Steps 1–3, mapped as: 5→5, 4→5, 3→4, 2→3, 1→2, 0→1**

**Substance disqualifiers (override base score, cap at 2):**
- Headline contains a specific capability/benchmark claim that is never substantiated with a number or source anywhere in the body → cap at **1**
- ≥70% of article text is a near-verbatim match to a company press release (mechanical text-similarity check against the press release if available) → cap at **2**

**Data to pull per article:** `headline`, `body_text`, `source_domain`, `published_at`, count of outbound hyperlinks by domain type (official company domain / arxiv.org / other-news-domain / none), regex-detected number+unit patterns in body text.

---

## AXIS 2: TREND (1–5)

Trend is about **velocity relative to baseline**, never raw totals. A small thing moving fast outranks a big thing moving slowly.

### Repos

**Formula:** `star_velocity_ratio = (stars gained in last 48hrs) / (average daily stars over repo's full lifetime, minimum denominator of 0.5 to avoid divide-by-near-zero distortion on brand-new repos)`

**Fork engagement:** `fork_ratio = forks_count / stargazers_count`

| Score | Criteria (both conditions must be met unless noted) |
|---|---|
| **5** | `star_velocity_ratio ≥ 8` AND `fork_ratio ≥ 0.15` |
| **4** | `star_velocity_ratio ≥ 8` OR (`star_velocity_ratio ≥ 4` AND `fork_ratio ≥ 0.10`) |
| **3** | `star_velocity_ratio` between 2 and 4 |
| **2** | `star_velocity_ratio` between 0.5 and 2 (roughly flat) |
| **1** | `star_velocity_ratio < 0.5` (declining or dead) |

**Data to pull:** star count snapshot stored daily (requires the routine to log `stargazers_count` each run to compute deltas — first run for any repo has no velocity data and defaults to score 3 pending a second data point), `forks_count`, `created_at`.

### YouTube Videos

**Formula:** `view_velocity_ratio = (views in first 48hrs after publish) / (channel's trailing average views-per-video over its last 10 uploads)`

| Score | Criteria |
|---|---|
| **5** | `view_velocity_ratio ≥ 3` (tripling the channel's own baseline) |
| **4** | `view_velocity_ratio` between 1.5 and 3 |
| **3** | `view_velocity_ratio` between 0.75 and 1.5 (performing at normal rate) |
| **2** | `view_velocity_ratio` between 0.3 and 0.75 |
| **1** | `view_velocity_ratio < 0.3` |

**Small-channel floor:** if channel has <10 prior uploads (insufficient baseline data), score using absolute view count instead: ≥5,000 views in 48hrs → 4, ≥1,000 → 3, ≥200 → 2, below 200 → 1. Flag these items in storage as `baseline_method: absolute` so scores are comparable-but-flagged rather than silently inconsistent with the ratio method.

**Data to pull:** `view_count` at time of scoring, `published_at` (to compute hours-since-publish and require ≥48hrs elapsed before scoring trend — items younger than 48hrs get `trend_score: pending` and are re-scored on the next run), channel's last 10 video view counts for baseline.

### News
Trend is weighted lowest for this category — news trending is mostly a function of outlet size, not importance.

**Formula:** `corroboration_count = number of distinct source_domains (from the configured Tier 1/2/3 RSS list) publishing an article on the same story (matched via shared named entity + topic keyword overlap ≥60%) within a 48-hour window of the first-seen article`

Syndicated wire copy (identical AP/Reuters byline appearing on multiple outlet domains) counts as **one** source, not multiple — dedupe by byline+first-paragraph text match before counting.

| Score | Criteria |
|---|---|
| **5** | `corroboration_count ≥ 4` |
| **4** | `corroboration_count` = 2–3 |
| **3** | `corroboration_count` = 1, AND that source is Tier 1 or Tier 2 |
| **2** | `corroboration_count` = 1, AND that source is Tier 3 |
| **1** | `corroboration_count` = 0 (single unlisted/low-tier source, no pickup elsewhere) |

**Data to pull:** `source_domain` mapped against the configured tier list, `published_at` for all matched articles, named-entity extraction on headline for topic matching.

---

## SOURCING / SEARCH PARAMETERS

This runs *before* scoring — it determines what enters the pipeline at all. Keep it separate from the scoring logic above: a keyword match gets an item scored, it does not by itself affect substance or trend scores.

### YouTube search keywords

**Primary keywords (search each independently, not combined into one query):**
`claude`, `claude code`, `chatgpt`, `gemini`, `ai tools`, `ai workflow`, `ai revenue generating strategies`

**Substance-skewing keywords (added to counteract the primary list's bias toward product/tutorial content):**
`fine-tuning`, `agent framework`, `open source model`, `ai benchmark`, `ai research paper`

**Search method:** query YouTube Data API's `search` endpoint sorted by `date` (upload recency), not by `relevance` or `viewCount` — sorting by relevance/views is already popularity-filtered and defeats the "don't miss the small channel" goal established earlier. Pull results across a rolling 48-hour upload window each run.

**Negative filter — "revenue strategies" bucket handled separately:**
Videos matching only generic money-making phrasing in the title (e.g. "make money with AI," "AI side hustle," "passive income AI") are **excluded from the general pool** by default, since this phrasing correlates heavily with low-substance schemes. These are only included if they *also* match the `ai revenue generating strategies` keyword search specifically — i.e. that keyword is the intentional bucket for this content type, and it still goes through the full substance rubric above (so a low-substance "side hustle" video scores low and gets filtered out on substance, not on the keyword alone). Do not let a title match on the negative-filter phrases silently pull a video into scoring through one of the other keyword buckets.

**Data retention on keyword matches:** store which keyword(s) triggered inclusion per video (`matched_keywords: [...]`) — useful later for tuning which keywords are actually surfacing good content vs. noise.

### GitHub repo sourcing

**Search method:** use GitHub's search API filtered by `created:>[rolling 48hr window]` or `pushed:>[rolling 48hr window]`, sorted by `updated`/recency — not GitHub's Trending page, which is already popularity-filtered and would reintroduce the bias this project is trying to avoid.

**Topic/keyword filters:** search across relevant topics/keywords such as `llm`, `agent`, `rag`, `fine-tuning`, `ai-tools`, `claude`, `gpt`, `gemini`, plus the substance-skewing terms `benchmark`, `inference-optimization`, `evaluation` to catch efficiency/research-flavored repos that generic AI-tool searches miss.

**No minimum star threshold applied at sourcing time** — filtering by popularity here is exactly what would cause the "low-traffic repos get ignored" problem. Every result in the date window gets scored regardless of star count; the scoring rubric (not the sourcing step) is what determines whether it surfaces in the digest.

### News/RSS sourcing

**Feed list (Tier 1 — primary sources):** OpenAI News, Anthropic News, Google DeepMind Blog, Hugging Face Blog, arXiv cs.AI

**Feed list (Tier 2 — technical/editorial analysis):** MIT Technology Review AI, Ars Technica, The Verge AI, Last Week in AI, The Gradient

**Feed list (Tier 3 — velocity signal, weighted lower on substance by default per the rubric above):** VentureBeat, Hacker News (AI-tagged threads)

**Pull method:** poll each feed's RSS endpoint every run; store `source_domain` against its tier so the Trend axis corroboration check (Axis 2, News section) can reference tier at scoring time.

**arXiv volume cap:** arXiv's cs.AI feed publishes hundreds of papers daily — far more than the blog/editorial feeds — and would otherwise dominate the news pool numerically without being genuinely more newsworthy. Discovered during implementation testing (485 of 495 sourced items were raw arXiv papers in one run). Fix: an arXiv paper only enters the news pipeline if it's cited by a repo already sourced in the `repos` table (cross-referenced via arXiv ID extracted from repo READMEs, per the repo Substance rubric's Step 1 paper-reference check). This means `source_repos.py` must run before `source_news.py` in the nightly pipeline order for the cap to have data to check against. Papers with no repo implementation yet are excluded from news, not lost — they can still surface later if a repo citing them gets sourced in a future run.

---

## VISION ESCALATION LOGIC

Applied **after** an item clears its text-based Substance/Trend threshold (don't waste vision calls on items that'll be filtered out anyway).

**Tier 1 — Always analyze (no threshold check needed):**
- Any image classified as a chart, graph, benchmark table, or comparison plot.
- Detect via: filename/alt-text containing "benchmark," "results," "chart," "comparison," OR a cheap pre-classification pass.

**Tier 2 — Deduction trigger (analyze only if item already passed text threshold):**
- Text contains a referential phrase pointing at an image without stating the underlying number/claim in words — e.g. "as shown below," "the chart shows," "results improved significantly" with no figure stated nearby, "see figure X."
- For video: creator makes a live-demo claim ("watch how fast this generates...") — sample a representative frame to verify real UI/output vs. talking-head only.

**Tier 3 — Skip entirely:**
- Decorative images, author headshots, logos, generic stock photography, thumbnails with no claim attached.

**Vision output feeds back into scoring:** if Tier 1/2 analysis contradicts or fails to support the surrounding text's claim, apply the relevant Substance disqualifier (auto-cap at 2) and note the discrepancy in the item's stored notes field.

---

## PIPELINE OPERATIONAL NOTES

These govern how the rubric above is actually applied run-over-run — without them, the formulas above can't execute correctly on a recurring schedule.

**Dedup check (runs before scoring, for every sourced item):**
Before scoring any item, check its URL against the database. If already present:
- Do not re-run vision analysis on it again (vision cost is a one-time check per item, not per run).
- Do re-fetch its velocity-relevant metrics (star count, view count) to update the Trend axis — Trend is the one axis that requires fresh data on every run for items still within their scoring window.
- Do not re-run the Substance axis checklist — Substance is scored once, at first sighting, and does not change on re-runs (a repo's README/commit history doesn't need re-grading nightly).

**Snapshot logging (required for velocity formulas to function):**
- Repos: log `stargazers_count` once per run for every repo already in the database, so `star_velocity_ratio` has real deltas to compute against, not just a single snapshot.
- Videos: log `view_count` once per run until the video crosses the 48-hour mark, then Trend is scored once and frozen (re-scoring view velocity indefinitely would make older items artificially decay in a way that isn't meaningful for this use case).

**Re-scoring window:** an item is actively tracked (re-fetched for Trend) for 14 days after first sighting, then considered settled and no longer polled — its last-computed scores remain in the database permanently, just no longer updated.

**Digest cadence:** generated weekly, pulling from all items scored in the trailing 7 days at time of generation. **Section size: top 5 per section** (Top Substance, Top Trend, Overlap), per the Digest Inclusion Rules above.

**Vision model:** Google Gemini Flash-Lite, called via the Gemini API, per the cost-efficiency decision made earlier — never a general-purpose or higher-cost Gemini tier.

**Retention policy:** every scored item remains permanently in the database regardless of whether it appeared in any digest. Digests are a filtered view; the database is the complete historical record. This is the mechanism that satisfies the original "don't lose the quiet, low-traffic item" requirement — it's always queryable later even if it never made a weekly digest headline.

---

## SCORE STORAGE FORMAT (complete field list)

Each item stored with both raw scores and the reasoning, not just the number — the reasoning is what makes the score auditable later. Fields below apply across all three content types; category-specific fields are noted.

```
url: unique identifier / dedup key
content_type: repo | video | news
date_first_seen: timestamp
date_last_updated: timestamp (last time Trend was re-fetched)

substance_score: 1-5
substance_reasoning: one sentence citing the specific evidence (or lack of it)
substance_step_breakdown: {step1: 0-2, step2: 0-2, step3: 0-1}

trend_score: 1-5 | "pending" (if under 48hrs old, videos only)
trend_reasoning: one sentence citing the specific velocity metric
baseline_method: ratio | absolute (videos only, per small-channel floor rule)

vision_used: true/false
vision_tier: 1/2/3/none
vision_findings: null or one sentence if analysis was run

disqualifier_applied: null or which one

matched_keywords: [...] (videos — which search keyword(s) triggered inclusion)
matched_topics: [...] (repos — which GitHub topic search(es) triggered inclusion)
source_tier: 1/2/3 (news — which tier list the source belongs to)

included_in_digest: [] (list of digest dates this item appeared in, empty if never)
```

---

## DIGEST INCLUSION RULES

- **Top Substance section:** highest substance_score items regardless of trend_score, tie-broken by trend_score.
- **Top Trend section:** highest trend_score items regardless of substance_score, tie-broken by substance_score.
- **Overlap section:** items scoring 4+ on both axes — these are the "don't miss this" items.
- Items with any disqualifier applied are excluded from all sections regardless of numeric score, unless the disqualifier itself is newsworthy (e.g. "this widely-shared repo's benchmark claims don't hold up") — in which case it goes in a separate **Flagged/Debunked** section.
