#!/usr/bin/env python3
"""Pull top posts from competitor/audience subreddits.

Uses Reddit's public JSON listing endpoints, so no API app is strictly
required to get started. If REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET /
REDDIT_USER_AGENT are set, it authenticates via OAuth instead, which is
more reliable and less likely to get rate-limited. See ../../../API_SETUP.md.

Usage:
  python3 reddit_scan.py "subreddit1,subreddit2" --output /tmp/reddit_posts.json
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

TOP_N_PER_SUBREDDIT = 15
TIME_WINDOW = "month"  # hour|day|week|month|year|all
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "ideation-skill/1.0 (by /u/pba-student)")


def get_oauth_token():
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    import base64

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["access_token"]


def fetch_top_posts(subreddit, token, limit):
    params = {"limit": limit, "t": TIME_WINDOW}
    if token:
        url = f"https://oauth.reddit.com/r/{subreddit}/top?{urllib.parse.urlencode(params)}"
        headers = {"Authorization": f"bearer {token}", "User-Agent": USER_AGENT}
    else:
        url = f"https://www.reddit.com/r/{subreddit}/top.json?{urllib.parse.urlencode(params)}"
        headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    posts = []
    for child in data.get("data", {}).get("children", []):
        p = child["data"]
        posts.append({
            "creator": p.get("author"),
            "platform": "reddit",
            "subreddit": subreddit,
            "title": p.get("title"),
            "url": f"https://www.reddit.com{p.get('permalink')}",
            "score": p.get("score"),
            "num_comments": p.get("num_comments"),
            "created_utc": p.get("created_utc"),
        })
    return posts


def main():
    parser = argparse.ArgumentParser(description="Scan subreddits for top posts.")
    parser.add_argument("subreddits", help="Comma-separated subreddit names, with or without r/ prefix")
    parser.add_argument("--output", required=True, help="Path to write JSON results")
    args = parser.parse_args()

    names = [s.strip().lstrip("r/").lstrip("/r/") for s in args.subreddits.split(",") if s.strip()]

    try:
        token = get_oauth_token()
    except Exception as e:  # noqa: BLE001
        print(f"WARNING: OAuth token request failed ({e}); falling back to public JSON.", file=sys.stderr)
        token = None

    all_posts = []
    errors = []
    for name in names:
        try:
            all_posts.extend(fetch_top_posts(name, token, TOP_N_PER_SUBREDDIT))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")

    result = {"posts": all_posts, "errors": errors}
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Found {len(all_posts)} posts across {len(names)} subreddit(s).")
    if errors:
        print(f"{len(errors)} error(s): {errors}", file=sys.stderr)


if __name__ == "__main__":
    main()
