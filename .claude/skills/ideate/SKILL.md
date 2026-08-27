---
name: ideate
description: Generate 10 content ideas for the student by scanning YouTube outliers, Reddit top posts, and IG competitor reels, then applying Briar's frameworks + the student's voice. Every idea cites a real source URL.
argument-hint: "[optional: pillar name or topic to focus on]"
allowed-tools: Bash(python3 *) Bash(cat *) Bash(ls *) Bash(grep *) Bash(date *) Read Write
---

You are running the PBA ideation skill for a student. Your job: produce
10 content ideas, each grounded in a real source from the student's
competitor research, written in their voice, applying Briar's
frameworks.

This skill is a port of Mission Control's ideation pipeline. It enforces
the same hard rules MC uses: every idea cites a reachable URL, no
duplicate creators across the brief, and a strict source-quota
distribution.

## Pre-flight: load context

Read these files in order. If any of the first four are missing or
still have `_pending_` placeholders, stop and tell the student to
finish `/onboard` first.

1. `my-brand/voice.md` — voice signature, hard rules, samples
2. `my-brand/pillars.md` — content themes
3. `my-brand/audience.md` — ICP
4. `principles.md` — Briar's positions
5. `hook-frameworks.md` — Briar's hook patterns
6. `voice-rules.md` — universal voice rules (em-dashes etc.)
7. `my-brand/competitors.md` — if MISSING or empty, jump to "Setup
   competitors" below before continuing

If voice.md doesn't have at least 2 voice samples or a voice signature
yet, warn the student: "Your voice doc is light — ideas will be
generic. Consider re-running `/onboard` to refresh, then re-run
`/ideate`." Continue if they want to anyway.

## Setup competitors (only if `my-brand/competitors.md` is missing or empty)

Ask the student:

> "Before I can generate ideas grounded in real research, I need to
> know who you compete with or admire in your space. I'll save your
> answers to `my-brand/competitors.md` so we never have to redo this.
>
> Give me each of these, one section at a time:
>
> 1. **YouTube channels** — 2-5 creators in your niche. Just the
>    handles (e.g., `@dan-koe`, `@iman-gadzhi`) or full channel URLs.
> 2. **Subreddits** — 3-5 subreddits where your audience hangs out
>    (e.g., `r/Entrepreneur`, `r/personalbrand`).
> 3. **Instagram accounts** — 3-5 competitor IG handles whose content
>    you respect (without the @ symbol).
>
> Skip any section that doesn't apply to your niche."

Ask each section as one question. Write `my-brand/competitors.md` as
you go using this schema:

```yaml
---
type: my-brand
section: competitors
status: live
updated_at: <today>
---

# My Competitors

## YouTube channels
- @creator1
- @creator2

## Subreddits
- r/subreddit1
- r/subreddit2

## Instagram handles
- creator1
- creator2
```

After saving, continue to the next step.

## Argument handling

If the student passed an argument (e.g., `/ideate authority`), use it
as a focus filter — all 10 ideas should serve that pillar or topic.
If no argument, spread the 10 ideas across all their pillars roughly
evenly (with the 4/3/2/1 mix described in "The 10 ideas" below).

## Step 1 — Scrape YouTube outliers

Read the YouTube channels from `my-brand/competitors.md`. Run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/yt_outliers.py \
  <space-separated-channel-handles> \
  --output /tmp/yt_outliers.json
```

Tell the student: "Scanning YouTube — this takes 30-60 seconds." After
it finishes, read `/tmp/yt_outliers.json` to confirm. Report how many
outliers you got.

If no YouTube channels are listed, skip this step and tell the
student you'll work without YT signal.

## Step 2 — Scrape Reddit

Read the subreddits from `my-brand/competitors.md`. Run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/reddit_scan.py \
  "<comma-separated-subreddit-names>" \
  --output /tmp/reddit_posts.json
```

(Subreddit names without `r/` prefix; the script strips it if present.)

Tell the student: "Scanning Reddit." Read the output JSON, report
counts.

## Step 3 — Scrape Instagram

Read the IG handles from `my-brand/competitors.md`. Run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ig_outliers.py \
  <space-separated-handles> \
  --output /tmp/ig_outliers.json
```

Tell the student: "Scanning Instagram via Apify — this takes the
longest, 60-120 seconds." Read the JSON, report.

Common errors to handle:
- `APIFY_API_TOKEN not set` → tell student to run `/onboard` or paste
  their Apify token into `.env`
- One handle private/missing → script continues with others; just note
  in the brief

## Step 4 — Generate 10 ideas

Now you have three JSON files in /tmp with real outlier content from
the student's competitive set. Synthesize 10 ideas using:

- The student's voice samples + signature (`my-brand/voice.md`)
- Their pillars (`my-brand/pillars.md`)
- Their audience (`my-brand/audience.md`)
- Briar's principles (`principles.md`)
- Briar's hook frameworks (`hook-frameworks.md`)
- The actual outlier content from /tmp/*.json

### Hard quotas (non-negotiable)

The 10 ideas must distribute as:

- **Max 3 from YouTube** (outliers from competitor channels)
- **Max 2 from Reddit** (top posts you can adapt)
- **Min 5 from Instagram** (competitor reels — primary source)

This mirrors MC's distribution rules. IG is primary because it's where
PBA students publish.

### Mix across pillars

If no focus argument was passed:
- 4 ideas serving the student's established pillars (depth)
- 3 ideas testing adjacent angles (range)
- 2 ideas applying a Briar framework they likely haven't tried (stretch)
- 1 contrarian take on something in their pillar (provocation)

### Per-idea schema

For each idea produce:

```yaml
- id: 1
  pillar: <which student pillar this serves>
  format: <IG_carousel | IG_reel | IG_post | X_thread | LinkedIn_post | YT_short | YT_long>
  hook: <opening line, applying a framework from hook-frameworks.md, NO em-dashes>
  body_angle: <2-3 sentences describing what the post argues or shows>
  voice_match: <one short line citing specific element of voice.md (signature, sample, vocab) it adheres to>
  briar_principle: <name + citation, e.g., "P5 — Personal brand converts ~70% higher (principles.md)">
  hook_framework: <name from hook-frameworks.md, e.g., "HF1 — Pain + Benefit + Curiosity">
  source:
    creator: <handle or name>
    platform: <youtube | reddit | instagram>
    url: <FULL real URL from the scraped JSON — must be reachable>
```

### Hard rules for the ideas themselves

- Every `source.url` must be copied verbatim from the scraped JSON.
  Don't paraphrase or shorten URLs.
- Every hook must follow a framework you can name from
  `hook-frameworks.md`.
- No em-dashes anywhere — re-check before saving.
- No two ideas can cite the same creator.
- Each idea must serve one of the student's pillars (not random topics).

## Step 5 — Validate

Write the 10 ideas to a temporary JSON file at `/tmp/ideate-draft.json`
with this top-level shape:

```json
{
  "ideas": [ { ... }, { ... }, ... ]
}
```

Run the validator:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validator.py /tmp/ideate-draft.json
```

It checks two things:
1. Every cited URL resolves (HEAD/GET reachability)
2. No two ideas cite the same creator

If validation FAILS:
- Print the error list to the student so they see what's wrong
- Fix the issues in-place (regenerate the offending idea(s) only,
  with different sources from the scraped pool)
- Re-run the validator
- Retry up to 2 times. If still failing, write what you have to
  `ideas/<date>-brief.md` but flag the unvalidated ideas clearly.

If validation PASSES, continue to step 6.

## Step 6 — Write the brief

Get today's date:

```bash
date +%Y-%m-%d
```

Write to `ideas/<date>-ideate-brief.md` (use the date you got from
the `date` command). File structure:

```yaml
---
type: ideation-brief
generated_at: <full timestamp>
focus: <argument value or "all-pillars">
pillars_covered: [list]
sources_scraped:
  youtube: <N outliers>
  reddit: <N posts>
  instagram: <N reels>
validation: passed | failed-after-retries
---

# Ideation Brief — <date>

## How to use this brief

Each idea below has been grounded in a real outlier from your
competitive research. Pick the ones that excite you. Star or comment
in the file. Next week we'll turn approved ideas into full drafts.

## Ideas

### Idea 1 — <short title>

- **Pillar:** ...
- **Format:** ...
- **Hook:** "..."
- **Body angle:** ...
- **Why it matches your voice:** ...
- **Briar principle applied:** ...
- **Hook framework:** ...
- **Source:** <creator>, [<platform>](<url>)

[... repeat for ideas 2-10 ...]

## Source pool reference

YouTube outliers analyzed: <N>. Top creators: ...
Reddit top posts analyzed: <N>. Top subreddits: ...
Instagram reels analyzed: <N>. Top accounts: ...
```

Also print a clean readable summary to the terminal so the student
can scan without opening the file.

## Step 7 — Wrap up

Tell the student:

1. The path to the brief file (`ideas/<date>-ideate-brief.md`)
2. How many ideas across each pillar
3. Quick suggestion: "Open the file, star the 3-5 you'd actually
   make. Next Friday we'll turn one of those starred ideas into a
   full draft."

If validation failed after retries, name which ideas were flagged and
why — be transparent about it.

## Hard rules (one more time, because these matter most)

- **No fabricated sources.** Every cited URL comes from a scraped JSON
  file in /tmp. If you can't find a real source for an idea, drop the
  idea — don't make one up.
- **No em-dashes** in hooks, body angles, or anywhere in the brief.
- **No two ideas cite the same creator.** Diversity forces broader
  signal.
- **Quotas: ≤3 YouTube, ≤2 Reddit, ≥5 Instagram.** If you can't hit
  the IG minimum (e.g., student has fewer IG competitors), reduce the
  total — output 7 instead of 10 — rather than padding with extra YT.
- **If voice doc is thin** (under 2 voice samples), flag at the top of
  the brief so the student knows the voice-match lines are weaker
  than they could be.
