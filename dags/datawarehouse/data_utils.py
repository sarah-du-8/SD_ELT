import psycopg2
from psycopg2.extras import RealDictCursor
from airflow.providers.postgres.hooks.postgres import PostgresHook

TABLE = "sd_api"


def get_conn_cursor():
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_elt", database="elt_db")
    conn = hook.get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cur


def close_conn_cursor(conn, cur):
    cur.close()
    conn.close()


def create_schema(schema):
    conn, cur = get_conn_cursor()
    try:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        conn.commit()
    finally:
        close_conn_cursor(conn, cur)


def create_table(schema):
    conn, cur = get_conn_cursor()
    try:
        table_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{TABLE} (
                "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                "Video_Title" TEXT NOT NULL,
                "Upload_Date" TIMESTAMP NOT NULL,
                "Duration" VARCHAR(20) NOT NULL,
                "Video_Views" INT,
                "Likes_Count" INT,
                "Comments_Count" INT
            );
        """
        cur.execute(table_sql)
        conn.commit()
    finally:
        close_conn_cursor(conn, cur)


def get_video_ids(cur, schema):
    cur.execute(f"""SELECT "Video_ID" FROM {schema}.{TABLE};""")
    rows = cur.fetchall()
    return [row["Video_ID"] for row in rows]