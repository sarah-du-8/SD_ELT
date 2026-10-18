import logging
from airflow.providers.standard.operators.bash import BashOperator

logger = logging.getLogger(__name__)

SODA_PATH = "/opt/airflow/include/soda"
DATASOURCE = "yt_elt"

staging_schema = "staging"
core_schema = "core"


def yt_elt_data_quality(schema):
    return BashOperator(
        task_id=f"soda_test_{schema}",
        bash_command=(
            f"soda scan -d {DATASOURCE} "
            f"-c {SODA_PATH}/configuration.yml "
            f"-v SCHEMA={schema} "
            f"{SODA_PATH}/checks.yml"
        ),
    )