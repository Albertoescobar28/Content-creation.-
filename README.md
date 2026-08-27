# Content Creation

Personal-brand content system for a blue-collar men's fat-loss coaching
business, built around the PBA `/ideate` skill.

## Structure

- `.claude/skills/ideate/` — the `/ideate` Claude Code skill (scans
  competitor YouTube/Reddit/Instagram, generates 10 sourced content
  ideas per run). See `API_SETUP.md` before running it.
- `principles.md`, `hook-frameworks.md`, `voice-rules.md` — Briar's
  course material, agency-wide, applies to every student.
- `my-brand/` — this brand's specifics:
  - `audience.md` — ICP (done)
  - `story-arc.md` — personal story raw material (done)
  - `pillars.md` — content pillars (**draft**, needs confirmation)
  - `voice.md` — voice signature + samples (**pending**, needs input)
  - `competitors.md` — YouTube/Reddit/Instagram competitor list (**not
    yet created** — see candidate shortlist from setup conversation)
- `ideas/` — generated ideation briefs land here, one per `/ideate` run.

## Getting to a working `/ideate` run

1. Fill in `my-brand/voice.md` (send real captions/scripts) and
   confirm `my-brand/pillars.md`.
2. Create `my-brand/competitors.md` (see draft shortlist from setup).
3. Follow `API_SETUP.md` to get a YouTube key, a Reddit script-app
   credential, and an Apify token.
4. Run `/ideate`.
