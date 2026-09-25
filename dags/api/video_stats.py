import json
import requests
from pathlib import Path
from datetime import date

from airflow.decorators import task
from airflow.models import Variable

API_KEY = Variable.get("API_KEY")
CHANNEL_HANDLE = Variable.get("CHANNEL_HANDLE", default_var="MrBeast")

BASE_URL = "https://youtube.googleapis.com/youtube/v3"
CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast's channel ID
MAX_RESULTS = 50
CACHE_DIR = Path("/opt/airflow/data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@task
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


@task
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


def _batch_list(video_id_list, batch_size):
    for i in range(0, len(video_id_list), batch_size):
        yield video_id_list[i:i + batch_size]


@task
def extract_video_data(video_ids):
    extracted_data = []

    try:
        for batch in _batch_list(video_ids, MAX_RESULTS):
            video_ids_str = ",".join(batch)

            params = {
                "part": "contentDetails,snippet,statistics",
                "id": video_ids_str,
                "key": API_KEY,
            }
            response = requests.get(f"{BASE_URL}/videos", params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                snippet = item["snippet"]
                content_details = item["contentDetails"]
                statistics = item["statistics"]

                video_data = {
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "publishedAt": snippet["publishedAt"],
                    "duration": content_details["duration"],
                    "viewCount": statistics.get("viewCount"),
                    "likeCount": statistics.get("likeCount"),
                    "commentCount": statistics.get("commentCount"),
                }
                extracted_data.append(video_data)

        return extracted_data  # now runs after ALL batches

    except requests.exceptions.RequestException as e:
        raise e


@task
def save_to_json(extracted_data):
    Path("/opt/airflow/data").mkdir(exist_ok=True)
    file_path = f"/opt/airflow/data/SD_ELT_{date.today()}.json"

    with open(file_path, "w", encoding="utf-8") as json_outfiles:
        json.dump(extracted_data, json_outfiles, indent=4, ensure_ascii=False)