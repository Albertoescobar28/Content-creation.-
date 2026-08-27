#!/usr/bin/env python3
"""Validate a draft ideation brief before it's written to ideas/.

Checks:
  1. Every idea's source.url actually resolves (HEAD, falling back to GET).
  2. No two ideas cite the same creator.

Usage:
  python3 validator.py /tmp/ideate-draft.json
Exits non-zero and prints a JSON error list on failure.
"""
import json
import sys
import urllib.request

TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (ideation-skill validator)"


def url_reachable(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method=method)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                if 200 <= resp.status < 400:
                    return True
        except Exception:
            continue
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: validator.py <path-to-draft.json>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    with open(path) as f:
        data = json.load(f)

    ideas = data.get("ideas", [])
    errors = []

    seen_creators = {}
    for idea in ideas:
        idea_id = idea.get("id")
        source = idea.get("source", {})
        url = source.get("url")
        creator = source.get("creator")

        if not url:
            errors.append({"idea_id": idea_id, "type": "missing_url", "detail": "source.url is missing"})
        elif not url_reachable(url):
            errors.append({"idea_id": idea_id, "type": "unreachable_url", "detail": url})

        if creator:
            if creator in seen_creators:
                errors.append({
                    "idea_id": idea_id,
                    "type": "duplicate_creator",
                    "detail": f"'{creator}' already used by idea {seen_creators[creator]}",
                })
            else:
                seen_creators[creator] = idea_id

    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        sys.exit(1)

    print(json.dumps({"valid": True, "errors": []}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
