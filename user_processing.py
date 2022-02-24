from airflow.models import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
import json

from datetime import datetime

default_args = {
    'start_date': datetime(2022, 1, 1)
}

with DAG(
        'user_processing'
        , schedule_interval='@daily'
        , default_args=default_args
        , catchup=False) as dag:
    # Define tasks/operators
    creating_table = SqliteOperator(
        task_id='creating_table'
        , sqlite_conn_id='db_sqlite_test_airflow'
        , sql='''
            CREATE TABLE users (
                email TEXT PRIMARY KEY NOT NULL
                , firstname TEXT NOT NULL
                , lastname TEXT NOT NULL
                , country TEXT NOT NULL
                , username TEXT NOT NULL
                , password TEXT NOT NULL
            );
        '''
    )

    is_api_available = HttpSensor(
        task_id='is_api_available'
        , http_conn_id='user_api_test_airflow'
        , endpoint='api/'

    )

    extracting_user = SimpleHttpOperator(
        task_id='extracting_user'
        , http_conn_id='user_api_test_airflow'
        , endpoint='api/'
        , method='GET'
        , response_filter=lambda response: json.loads(response.text)
        , log_response=True

    )
