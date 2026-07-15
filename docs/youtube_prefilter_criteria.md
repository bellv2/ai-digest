# YouTube Pre-Filter Criteria

This document governs the gate that runs **before** a video reaches transcript fetching, vision analysis, or the full Substance/Trend scoring in `scoring_rubric.md`. Its job is narrower and cheaper: decide whether a video is worth the expensive analysis at all, using only metadata that's already returned by the initial search/stats API calls — title, description, and (optionally) top comments. No transcript, no vision call, no extra API cost beyond what's already being pulled.

A video that fails this gate skips straight to a capped, conservative score (per the main rubric's existing `no_captions_available` / `skipped_prescreen` handling) — it does not get discarded outright, since even a sketchy-looking video is still stored per the retention policy. This filter only decides how much further work it earns.

---

## Core distinction: Resource Link vs. Promotional Link

The single most important judgment call this filter makes is telling apart a link that supports the video's substance from a link that's just monetization. Not all links are equal, and treating them identically was the gap in the original pre-screen.

**Classify every URL found in the description into one of three buckets:**

### Resource links (signal of substance — do NOT penalize)
- `github.com`, `gitlab.com`, `huggingface.co` — actual code/model referenced
- `arxiv.org`, `doi.org` — papers
- Official docs domains (`docs.anthropic.com`, `platform.openai.com`, `ai.google.dev`, etc.)
- The creator's own long-form blog/Substack *if* the linked post itself contains technical detail (can't verify without fetching — treat neutrally, don't penalize or reward)

### Promotional/referral links (signal of monetization — do NOT count as substance evidence)
- `skool.com`, `gumroad.com`, `patreon.com`, `ko-fi.com`, `buymeacoffee.com`
- Any URL containing `?ref=`, `?via=`, `?aff=`, `/affiliate/`, or a personal referral code pattern
- Course/cohort platforms: `teachable.com`, `kajabi.com`, `circle.so`
- Calendly/booking links (`calendly.com`) — signals a sales funnel, not evidence
- Discord/community invite links positioned as the primary CTA

### Neutral links (neither signal — ignore)
- Social media profile links (Twitter/X, LinkedIn, Instagram) used for creator identity, not calls-to-action
- YouTube's own links (other videos, channel links)

**Detection method:** regex/domain-match against the classified lists above, applied to every URL extracted from the description via the existing `URL_PATTERN`. Store counts of each bucket per video: `resource_link_count`, `promo_link_count`, `neutral_link_count`.

---

## Title Signals

**Red flags (each detected instance adds to a sketchiness score):**
- Specific dollar amount + time period combination (e.g. "$5,000 in one month," "$500/day") — near-universal signature of income-claim content, regardless of genre
- Superlative + urgency combination: "SECRET," "HACK," "before it's banned," "they don't want you to know"
- Numbered listicle framing with no technical noun ("5 ways to," "3 tricks") — weak signal alone, only counts combined with another red flag
- All-caps words beyond a single acronym (e.g. "THIS WILL SHOCK YOU") — count of all-caps words ≥2 excluding known acronyms (AI, LLM, API, etc.)

**Green flags (each offsets sketchiness):**
- Specific version numbers, model names, or technical terms (e.g. "v2.1.210," "GPT-5.6," "SWE-Bench")
- Comparison framing between named tools ("X vs Y") — signals evaluative content over promotional content
- Question-format technical titles ("How does X actually work")

**Title sketchiness score:** count(red flags) − count(green flags), floor at 0.

---

## Description Signals

**Structural red flags:**
- Primary/first link in the description is a promotional link (per the classification above) — the position matters; a promo link buried after genuine resource links is a lesser signal than one leading the description
- ≥3 promotional links present anywhere in the description
- Description contains explicit CTA phrasing: "link in bio," "join my," "limited spots," "click below to," "DM me for"
- Description is entirely CTA/promotional with no content description of the video itself (i.e., doesn't describe what's actually demonstrated/discussed)

**Structural green flags:**
- ≥1 resource link present
- Description includes timestamps/chapters (signals structured, substantive content)
- Description explains the video's actual technical content in prose (not just a CTA list)

**Description sketchiness score:** count(structural red flags) − count(structural green flags), floor at 0.

---

## Comment Signals (optional escalation — only pull if title+description score is borderline)

Pulling comments costs an extra API call per video, so this tier only activates when the title+description combined sketchiness score lands in a genuinely ambiguous middle range (see thresholds below) — not on every video.

**What to check in the top 10 comments by relevance:**
- Is the creator's own pinned comment (if any) itself a promotional link? → treat as equivalent to a promotional link leading the description
- Ratio of comments engaging with actual video content (asking technical questions, referencing specific timestamps/claims) vs. generic engagement-bait replies ("first!", emoji-only, unrelated) — a high ratio of substantive engagement is a green flag; can't easily automate sentiment, so use a simple heuristic: comment length ≥15 words AND contains a question mark or technical term = "substantive"
- Any comments flagging the video as misleading/scam in a way that has multiple upvotes/replies agreeing — strong red flag if present, rare but decisive when found

**Comment signal is advisory, not scored numerically** — if a pinned promotional comment or multiple "this is a scam" replies are found, it overrides a borderline score toward "skip deep analysis" regardless of the title/description math.

---

## Combined Decision Logic

```
combined_sketchiness = title_sketchiness_score + description_sketchiness_score

if combined_sketchiness == 0:
    → proceed to deep analysis (transcript/vision) directly, no comment check needed

if combined_sketchiness in [1, 2]:
    → borderline: pull top 10 comments, apply Comment Signals check
    → if comment check finds a decisive red flag: skip deep analysis
    → otherwise: proceed to deep analysis

if combined_sketchiness >= 3:
    → skip deep analysis entirely, no comment check needed (already decisive)
    → score directly from title/description per the main rubric's capped fallback
```

**Storage:** every video's `title_sketchiness_score`, `description_sketchiness_score`, `resource_link_count`, `promo_link_count`, and (if pulled) `comment_check_result` are stored alongside the existing scoring fields — this is diagnostic data worth keeping, same reasoning as the main rubric's audit-trail requirement.

---

## Relationship to the main scoring rubric

This filter runs **before** and **independently of** the caption-availability gate in `scoring_rubric.md`. The two gates serve different purposes and both must pass for a transcript fetch to happen:

1. **This document's gate** — is the video worth analyzing at all, based on content-intent signals (sketchy/promotional vs. substantive)?
2. **`scoring_rubric.md`'s caption gate** — does the video even have a transcript available to fetch?

A video must clear both to reach a transcript attempt. Failing either results in the same outcome: score capped at Substance ≤2, computed from title/description alone, with the specific skip reason stored for auditability (`sketchy_content:<score>` for this gate, `no_captions_available` for the caption gate).
