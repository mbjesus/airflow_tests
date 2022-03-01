from airflow.models import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from pandas import json_normalize
import json

from datetime import datetime

default_args = {
    'start_date': datetime(2022, 1, 1)
}


def _processing_user(ti):
    users = ti.xcom_pull(task_ids=['extracting_user'])

    if not len(users) or 'results' not in users[0]:
        raise ValueError('User is empty')

    user = users[0]['results'][0]
    processed_user = json_normalize({
        'firstname': user['name']['first']
        , 'lastname': user['name']['last']
        , 'country': user['location']['country']
        , 'username': user['login']['username']
        , 'password': user['login']['password']
        , 'email': user['email']
    })

    processed_user.to_csv('/tmp/processed_user.csv', index=False, header=False)


with DAG(
        'user_processing'
        , schedule_interval='@daily'
        , default_args=default_args
        , catchup=False) as dag:
    # Define tasks/operators
    creating_table = SqliteOperator(
        task_id='creating_table'
        #You should create a SQL3 connection in Airflow to database file db_sqlite_test_airflow with sqlite_conn_id='db_sqlite_test_airflow'.
        , sqlite_conn_id='db_sqlite_test_airflow'
        , sql='''
            CREATE TABLE IF NOT EXISTS use  rs (
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
        ## You should create a HTTP connection with URL https://randomuser.me/ and http_conn_id='user_api_test_airflow'
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

    processing_users = PythonOperator(
        task_id='processing_users'
        , python_callable=_processing_user
    )

    storing_user = BashOperator(
        task_id='storing_user'
        , bash_command='echo -e ".separator ," "\n.import /tmp/processed_user.csv users" | sqlite3  /home/mbjesus/airflow/dags/airflow_tests/db_sqlite_test_airflow.db'
    )

    ## Setting the preference order to the Operators (tasks).
    creating_table >> is_api_available >> extracting_user >> processing_users >> storing_user
