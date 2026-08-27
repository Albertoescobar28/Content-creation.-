---
type: setup-guide
updated_at: 2026-08-27
---

# API Setup for /ideate

`/ideate` scrapes three platforms for real competitor content. Two of
the three need a free credential; the third (Reddit) works out of the
box. None of this costs money at the volume this skill uses.

Put everything in a `.env` file at the repo root (already gitignored —
never commit real keys). Copy `.env.example` to `.env` and fill in the
values as you get them.

## 1. YouTube Data API key (free)

1. Go to https://console.cloud.google.com/ and sign in with any Google
   account.
2. Create a new project (top-left project dropdown → "New Project").
   Name it anything, e.g. "content-ideation".
3. In the search bar, type "YouTube Data API v3" and open it, then
   click **Enable**.
4. Go to **APIs & Services → Credentials → Create Credentials → API
   key**. Copy the key it generates.
5. (Optional but recommended) Click "Restrict key" and limit it to
   "YouTube Data API v3" so it can't be misused if leaked.
6. Put it in `.env` as `YOUTUBE_API_KEY=your-key-here`.

Free quota is 10,000 units/day. Each channel scan in this skill costs
roughly 100-150 units, so you can run `/ideate` many times a day
before hitting the limit.

## 2. Reddit (free "script" app — needed in practice)

`reddit_scan.py` can read Reddit's public `/top.json` listings without
any credentials, but in testing Reddit 403-blocked that public path
outright (it aggressively blocks cloud/datacenter IPs regardless of
User-Agent). So treat this as required, not optional:

1. Log into Reddit, go to https://www.reddit.com/prefs/apps
2. Click **"create another app..."** at the bottom.
3. Choose type **"script"**. Name and description can be anything.
   Set the redirect URI to `http://localhost:8080` (required field,
   unused for this).
4. After creating it, note the string under the app name (client ID)
   and the "secret" field (client secret).
5. Put them in `.env`:
   ```
   REDDIT_CLIENT_ID=your-client-id
   REDDIT_CLIENT_SECRET=your-secret
   REDDIT_USER_AGENT=ideation-skill/1.0 by u/your-reddit-username
   ```

## 3. Apify token (Instagram scraping)

Instagram has no public API for this, so the skill uses Apify, a
scraping platform with a free tier.

1. Go to https://apify.com/ and sign up (free tier includes monthly
   usage credit, no card required to start).
2. Once logged in, go to **Settings → Integrations** (or visit
   https://console.apify.com/settings/integrations).
3. Copy your **Personal API token**.
4. Put it in `.env` as `APIFY_API_TOKEN=your-token-here`.

The skill calls the `apify/instagram-reel-scraper` actor. The free
tier's monthly credit covers scanning a handful of competitor accounts
regularly; if you scan a lot of accounts you may need to add a payment
method for overage, but nothing runs automatically without you
triggering `/ideate`.

## After setup

From the repo root:

```bash
cp .env.example .env
# edit .env and fill in the values above
```

The scripts read these as normal environment variables — however you
load `.env` into your shell (e.g. `export $(cat .env | xargs)`, or a
tool like `direnv`) is up to you; nothing here auto-loads it.
