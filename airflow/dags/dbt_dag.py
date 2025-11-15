from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=15),
}

dag = DAG(
    'dbt_transform',
    default_args=default_args,
    description='Run dbt models',
    schedule_interval=timedelta(minutes=5),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['dbt', 'sqlserver'],
)

# Define tasks using BashOperator to execute dbt commands in the dbt container
# dbt_run = BashOperator(
#     task_id='dbt_run',
#     bash_command='docker exec dbt_airflow_project-dbt-1 dbt run',
#     dag=dag,
# )

dbt_run_bronze = BashOperator(
    task_id='dbt_run_bronze_to_silver',
    bash_command='docker exec dbt_airflow_project-dbt-1 dbt run --models bronze',
    dag=dag,
)

dbt_test_bronze = BashOperator(
    task_id='dbt_test_bronze_to_silver',
    bash_command='docker exec dbt_airflow_project-dbt-1 dbt test --models bronze',
    dag=dag,
)

dbt_run_silver = BashOperator(
    task_id='dbt_run_silver_to_gold',
    bash_command='docker exec dbt_airflow_project-dbt-1 dbt run --models silver',
    dag=dag,
)

dbt_test_silver = BashOperator(
    task_id='dbt_test_silver_to_gold',
    bash_command='docker exec dbt_airflow_project-dbt-1 dbt test --models silver',
    dag=dag,
)


# Set task dependencies
dbt_run_bronze >> dbt_test_bronze >> dbt_run_silver >> dbt_test_silver