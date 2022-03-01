from airflow import DAG
from datetime import datetime

default_args = {
    'start_date': datetime(2020, 1, 1)
}

with DAG(dag_id='parallel_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

