"""
DBT Medallion Architecture Data Transformation Pipeline

## Overview
Orchestrates DBT transformations following medallion architecture pattern.
Data flows through three quality layers with automated testing at each stage.

## Architecture Layers

### Bronze (Raw)
- **Purpose**: Extract and standardize source data
- **Models**: brnz_sales_orders, brnz_customers, brnz_products
- **Materialization**: Views (flexibility, zero storage overhead)
- **Tests**: PK uniqueness, FK integrity, no future dates

### Silver (Transformed)
- **Purpose**: Apply business logic and data quality rules
- **Models**: slvr_sales_orders (calculated metrics), slvr_customers (enriched)
- **Materialization**: Tables (query performance)
- **Tests**: Calculated field accuracy, positive value constraints

### Gold (Analytics)
- **Purpose**: Business-ready aggregated metrics and KPIs
- **Models**: gld_sales_summary (daily metrics), gld_customer_metrics (LTV)
- **Materialization**: Tables (optimized for BI tools)
- **Tests**: Aggregation accuracy, relationship integrity

## Schedule & Ownership
- **Schedule**: Every 5 minutes
- **Owner**: DataOps Team
- **Tags**: dbt, sqlserver, medallion, data-pipeline
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# from airflow.utils.task_group import TaskGroup

# Default arguments for all tasks in the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

dag = DAG(
    "dbt_transform",
    default_args=default_args,
    description="Run dbt models",
    schedule_interval=timedelta(minutes=5),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "sqlserver"],
)

# Define tasks using BashOperator to execute dbt commands in the dbt container
# dbt_run = BashOperator(
#     task_id='dbt_run',
#     bash_command='docker exec dbt_airflow_project-dbt-1 dbt run',
#     dag=dag,
# )

dbt_run_bronze = BashOperator(
    task_id="dbt_run_bronze_to_silver",
    bash_command="docker exec dbt_airflow_project-dbt-1 dbt run --models bronze",
    dag=dag,
)

dbt_test_bronze = BashOperator(
    task_id="dbt_test_bronze_to_silver",
    bash_command="docker exec dbt_airflow_project-dbt-1 dbt test --models bronze",
    dag=dag,
)

dbt_run_silver = BashOperator(
    task_id="dbt_run_silver_to_gold",
    bash_command="docker exec dbt_airflow_project-dbt-1 dbt run --models silver",
    dag=dag,
)

dbt_test_silver = BashOperator(
    task_id="dbt_test_silver_to_gold",
    bash_command="docker exec dbt_airflow_project-dbt-1 dbt test --models silver",
    dag=dag,
)


# Set task dependencies
dbt_run_bronze >> dbt_test_bronze >> dbt_run_silver >> dbt_test_silver
