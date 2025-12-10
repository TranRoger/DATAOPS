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
from airflow.utils.task_group import TaskGroup

# Default arguments for all tasks in the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}

# DAG definition
with DAG(
    "dbt_transform",
    default_args=default_args,
    description="DBT medallion architecture (Bronze→Silver→Gold) with automated testing",
    schedule=timedelta(minutes=5),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "sqlserver", "medallion", "data-pipeline"],
    doc_md=__doc__,
) as dag:
    # Bronze Layer: Extract raw data from source systems
    with TaskGroup(group_id="bronze_layer", tooltip="Raw data extraction") as bronze_group:
        dbt_run_bronze = BashOperator(
            task_id="dbt_run_bronze",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt run --models bronze",
        )
        dbt_run_bronze.doc = "Extract raw data from Sales, Production, Person schemas"

        dbt_test_bronze = BashOperator(
            task_id="dbt_test_bronze",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt test --models bronze",
        )
        dbt_test_bronze.doc = "Validate PK uniqueness, FK integrity, data types, no future dates"

        # Bronze layer internal dependencies
        dbt_run_bronze >> dbt_test_bronze

    # Silver Layer: Apply business transformations
    with TaskGroup(group_id="silver_layer", tooltip="Business transformations") as silver_group:
        dbt_run_silver = BashOperator(
            task_id="dbt_run_silver",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt run --models silver",
        )
        dbt_run_silver.doc = "Apply business rules: calculated fields, NULL handling, quality filters"

        dbt_test_silver = BashOperator(
            task_id="dbt_test_silver",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt test --models silver",
        )
        dbt_test_silver.doc = "Validate business logic, positive constraints, accepted values"

        # Silver layer internal dependencies
        dbt_run_silver >> dbt_test_silver

    # Gold Layer: Create business-ready aggregations
    with TaskGroup(group_id="gold_layer", tooltip="Business metrics and KPIs") as gold_group:
        dbt_run_gold = BashOperator(
            task_id="dbt_run_gold",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt run --models gold",
        )
        dbt_run_gold.doc = "Aggregate metrics: daily sales, customer LTV, product profitability"

        dbt_test_gold = BashOperator(
            task_id="dbt_test_gold",
            bash_command="docker exec dbt_airflow_project-dbt-1 dbt test --models gold",
        )
        dbt_test_gold.doc = "Validate aggregations, no NULL metrics, date ranges, relationships"

        # Gold layer internal dependencies
        dbt_run_gold >> dbt_test_gold

    # Define cross-layer dependencies (Medallion architecture flow)
    bronze_group >> silver_group >> gold_group
