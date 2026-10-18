import requests
import pytest
import psycopg2

def test_youtube_api_responses(airflow_variable):
    api_key = airflow_variable("API_KEY")
    channel_handle = airflow_variable("CHANNEL_HANDLE")

    url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={channel_handle}&key={api_key}"

    try:
        response = requests.get(url)
        assert response.status_code == 200
    except:
        pytest.fail(f"Request to YouTube API failed for channel handle '{channel_handle}' with API key '{api_key}'")



def test_real_postgres_connection(real_postgres_connection):
    conn = None
    try:
        cursor = real_postgres_connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert result[0] == 1
    except Exception as e:
        pytest.fail(f"Error connecting to PostgreSQL: {e}")
    finally:
        if cursor is not None:
            cursor.close()