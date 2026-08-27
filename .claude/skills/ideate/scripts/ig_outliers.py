#!/usr/bin/env python3
"""Scan competitor Instagram accounts for outlier reels via Apify.

Requires env var APIFY_API_TOKEN. See ../../../API_SETUP.md for how to get one.

Uses the apify/instagram-reel-scraper actor (run synchronously). Swap
ACTOR_ID if you prefer a different Apify Instagram actor.

Usage:
  python3 ig_outliers.py handle1 handle2 --output /tmp/ig_outliers.json
"""
import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.request

import _env  # noqa: F401 - loads .env into os.environ as a side effect

ACTOR_ID = "apify~instagram-reel-scraper"
OUTLIER_MULTIPLE = 3.0
POSTS_PER_HANDLE = 30
APIFY_BASE = "https://api.apify.com/v2"


def run_actor_sync(usernames, token):
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={token}"
    payload = {
        "username": usernames,
        "resultsLimit": POSTS_PER_HANDLE,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def find_outliers(items):
    by_owner = {}
    for item in items:
        owner = item.get("ownerUsername") or item.get("username") or "unknown"
        by_owner.setdefault(owner, []).append(item)

    all_outliers = []
    for owner, posts in by_owner.items():
        plays = [p.get("videoPlayCount") or p.get("likesCount") or 0 for p in posts]
        if not plays:
            continue
        median_plays = statistics.median(plays) or 1
        for p, play_count in zip(posts, plays):
            multiple = play_count / median_plays
            if multiple >= OUTLIER_MULTIPLE:
                all_outliers.append({
                    "creator": owner,
                    "platform": "instagram",
                    "caption": (p.get("caption") or "")[:200],
                    "url": p.get("url"),
                    "plays": play_count,
                    "account_median_plays": int(median_plays),
                    "outlier_multiple": round(multiple, 2),
                    "posted_at": p.get("timestamp"),
                })
    all_outliers.sort(key=lambda o: o["outlier_multiple"], reverse=True)
    return all_outliers


def main():
    parser = argparse.ArgumentParser(description="Scan competitor Instagram accounts for outlier reels.")
    parser.add_argument("handles", nargs="+", help="IG handles, without @")
    parser.add_argument("--output", required=True, help="Path to write JSON results")
    args = parser.parse_args()

    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("ERROR: APIFY_API_TOKEN not set. See API_SETUP.md.", file=sys.stderr)
        sys.exit(1)

    handles = [h.lstrip("@").strip() for h in args.handles]
    errors = []
    items = []
    try:
        items = run_actor_sync(handles, token)
    except urllib.error.HTTPError as e:
        errors.append(f"Apify run failed: HTTP {e.code} {e.reason}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"Apify run failed: {e}")

    outliers = find_outliers(items) if items else []

    result = {"outliers": outliers, "errors": errors}
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Found {len(outliers)} outliers across {len(handles)} account(s).")
    if errors:
        print(f"{len(errors)} error(s): {errors}", file=sys.stderr)


if __name__ == "__main__":
    main()
