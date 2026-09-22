from airflow import DAG
import pendulum
from datetime import datetime, timedelta
from api.video_stats import get_playlist_lists, get_video_ids, extract_video_data, save_to_json

#Define local zone
local_zn = pendulum.timezone("Europe/Malta")
