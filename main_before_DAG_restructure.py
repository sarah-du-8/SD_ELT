from datetime import datetime, timedelta

import pendulum
from airflow import DAG

from api.video_stats import (
    get_playlist_id,
    get_video_ids,
    extract_video_data,
    save_to_json,
    CHANNEL_ID
)
from datawarehouse.dwh import staging_table, core_table
from dataquality.soda import yt_elt_data_quality, staging_schema, core_schema

# Define local timezone
local_tz = pendulum.timezone("Europe/Malta")

# Default args
default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2026, 9, 22, tzinfo=local_tz),
}

staging_schema = "staging"
core_schema = "core"

with DAG(
    dag_id="produce_json",
    default_args=default_args,
    description="DAG to produce JSON file with raw data",
    schedule="0 14 * * *",
    catchup=False,
) as dag:

    playlist_id = get_playlist_id(CHANNEL_ID)
    video_ids = get_video_ids(playlist_id)
    extract_data = extract_video_data(video_ids)
    save_to_json_task = save_to_json(extract_data)

    # Define dependencies 
    playlist_id >> video_ids >> extract_data >> save_to_json_task


with DAG(
    dag_id="update_db",
    default_args=default_args,
    description="DAG to process JSON file and insert data into both staging and core schemas",
    schedule="0 15 * * *",
    catchup=False,
) as dag:

    update_staging = staging_table()
    update_core = core_table()

    # Define dependencies
    update_staging >> update_core



with DAG(
    dag_id="data_quality",
    default_args=default_args,
    description="DAG to check the data quality on both layers in the db",
    schedule=None,
    catchup=False,
) as dag:

    soda_validate_staging = yt_elt_data_quality(staging_schema)
    soda_validate_core = yt_elt_data_quality(core_schema)

    soda_validate_staging >> soda_validate_core