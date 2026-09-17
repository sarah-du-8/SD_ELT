import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY not found — check your .env file")

BASE_URL = "https://youtube.googleapis.com/youtube/v3"
CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast's channel ID
MAX_RESULTS = 50
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_playlist_id(channel_id: str, use_cache: bool = True) -> str:
    """Return the 'uploads' playlist ID for a given channel (cached)."""
    cache_file = CACHE_DIR / f"playlist_id_{channel_id}.json"

    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text())["playlist_id"]

    params = {"part": "contentDetails", "id": channel_id, "key": API_KEY}
    response = requests.get(f"{BASE_URL}/channels", params=params)
    response.raise_for_status()
    data = response.json()

    items = data.get("items")
    if not items:
        raise ValueError(f"No channel found for id: {channel_id}")

    playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    cache_file.write_text(json.dumps({"playlist_id": playlist_id}))
    return playlist_id


def get_video_ids(playlist_id: str, limit: int | None = None, use_cache: bool = True) -> list[str]:
    """Return video IDs from a playlist, handling pagination (cached)."""
    cache_file = CACHE_DIR / f"video_ids_{playlist_id}.json"

    if use_cache and cache_file.exists():
        video_ids = json.loads(cache_file.read_text())
        return video_ids[:limit] if limit else video_ids

    video_ids = []
    page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "maxResults": MAX_RESULTS,
            "playlistId": playlist_id,
            "key": API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(f"{BASE_URL}/playlistItems", params=params)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
            if limit and len(video_ids) >= limit:
                cache_file.write_text(json.dumps(video_ids))
                return video_ids

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    cache_file.write_text(json.dumps(video_ids))
    return video_ids


def batch_list(video_id_list, batch_size):
    for i in range(0, len(video_id_list), batch_size):
        yield video_id_list[i:i + batch_size]


if __name__ == "__main__":
    playlist_id = get_playlist_id(CHANNEL_ID)
    print("Uploads playlist ID:", playlist_id)

    video_ids = get_video_ids(playlist_id, limit=10)
    print(f"Fetched {len(video_ids)} video IDs")

    for vid in video_ids:
        print(vid)