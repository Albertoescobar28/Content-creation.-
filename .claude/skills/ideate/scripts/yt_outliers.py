#!/usr/bin/env python3
"""Find outlier videos (views far above a channel's own median) across
competitor YouTube channels, using the YouTube Data API v3.

Requires env var YOUTUBE_API_KEY. See ../../../API_SETUP.md for how to get one.

Usage:
  python3 yt_outliers.py @handle1 @handle2 UCxxxxxxxx --output /tmp/yt_outliers.json
"""
import argparse
import json
import os
import statistics
import sys
import urllib.parse
import urllib.request

import _env  # noqa: F401 - loads .env into os.environ as a side effect

API_BASE = "https://www.googleapis.com/youtube/v3"
OUTLIER_MULTIPLE = 3.0  # a video counts as an outlier at 3x the channel's median views
MAX_VIDEOS_PER_CHANNEL = 50


def api_get(path, params, api_key):
    params = dict(params)
    params["key"] = api_key
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def resolve_channel_id(handle, api_key):
    handle = handle.strip()
    if handle.startswith("UC") and len(handle) == 24:
        return handle
    clean = handle.lstrip("@")
    data = api_get("channels", {"part": "id", "forHandle": clean}, api_key)
    items = data.get("items", [])
    if items:
        return items[0]["id"]
    # Fallback: search by name for older channels without a resolvable handle
    data = api_get("search", {"part": "snippet", "type": "channel", "q": clean, "maxResults": 1}, api_key)
    items = data.get("items", [])
    if items:
        return items[0]["snippet"]["channelId"]
    return None


def get_uploads_playlist(channel_id, api_key):
    data = api_get("channels", {"part": "contentDetails,snippet", "id": channel_id}, api_key)
    items = data.get("items", [])
    if not items:
        return None, None
    playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_title = items[0]["snippet"]["title"]
    return playlist_id, channel_title


def get_recent_video_ids(playlist_id, api_key, limit):
    video_ids = []
    page_token = None
    while len(video_ids) < limit:
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        data = api_get("playlistItems", params, api_key)
        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return video_ids[:limit]


def get_video_stats(video_ids, api_key):
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        data = api_get("videos", {"part": "snippet,statistics", "id": ",".join(batch)}, api_key)
        for item in data.get("items", []):
            views = int(item.get("statistics", {}).get("viewCount", 0))
            videos.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"],
                "views": views,
            })
    return videos


def find_outliers(channel_title, videos):
    if not videos:
        return []
    view_counts = [v["views"] for v in videos]
    median_views = statistics.median(view_counts) or 1
    outliers = []
    for v in videos:
        multiple = v["views"] / median_views
        if multiple >= OUTLIER_MULTIPLE:
            outliers.append({
                "creator": channel_title,
                "platform": "youtube",
                "title": v["title"],
                "url": f"https://www.youtube.com/watch?v={v['video_id']}",
                "views": v["views"],
                "channel_median_views": int(median_views),
                "outlier_multiple": round(multiple, 2),
                "published_at": v["published_at"],
            })
    outliers.sort(key=lambda o: o["outlier_multiple"], reverse=True)
    return outliers


def main():
    parser = argparse.ArgumentParser(description="Scan competitor YouTube channels for outlier videos.")
    parser.add_argument("handles", nargs="+", help="Channel handles (@name) or channel IDs (UC...)")
    parser.add_argument("--output", required=True, help="Path to write JSON results")
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY not set. See API_SETUP.md.", file=sys.stderr)
        sys.exit(1)

    all_outliers = []
    errors = []
    for handle in args.handles:
        try:
            channel_id = resolve_channel_id(handle, api_key)
            if not channel_id:
                errors.append(f"{handle}: could not resolve channel")
                continue
            playlist_id, channel_title = get_uploads_playlist(channel_id, api_key)
            if not playlist_id:
                errors.append(f"{handle}: no uploads playlist found")
                continue
            video_ids = get_recent_video_ids(playlist_id, api_key, MAX_VIDEOS_PER_CHANNEL)
            videos = get_video_stats(video_ids, api_key)
            all_outliers.extend(find_outliers(channel_title, videos))
        except Exception as e:  # noqa: BLE001 - report and continue with other channels
            errors.append(f"{handle}: {e}")

    result = {"outliers": all_outliers, "errors": errors}
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Found {len(all_outliers)} outliers across {len(args.handles)} channel(s).")
    if errors:
        print(f"{len(errors)} error(s): {errors}", file=sys.stderr)


if __name__ == "__main__":
    main()
