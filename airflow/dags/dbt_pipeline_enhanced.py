"""
DBT Data Pipeline DAG - Enhanced Production Version

This DAG orchestrates the complete DBT transformation pipeline with:
- Medallion architecture (Bronze -> Silver -> Gold)
- Source freshness checks
- Data quality testing at each layer
- Comprehensive error handling and retries
- Email notifications on failure
- Proper task dependencies and scheduling

Author: DataOps Team
Last Updated: 2025-12-10
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

# Uncomment below if you want to enable email notifications
# from airflow.operators.email import EmailOperator

# Default arguments for all tasks
default_args = {
    "owner": "dataops_team",
    "depends_on_past": False,
    "email": ["dataops@company.com"],  # Update with your email
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

# DAG definition
dag = DAG(
    dag_id="dbt_pipeline_enhanced",
    default_args=default_args,
    description="Enhanced DBT pipeline with full medallion architecture, data quality checks, and error handling",
    schedule_interval="0 2 * * *",  # Daily at 2 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "dataops", "medallion", "production"],
    max_active_runs=1,
    doc_md=__doc__,
)

# Container name for DBT
DBT_CONTAINER = "dbt_airflow_project-dbt-1"

# ============================================================================
# TASK 1: Source Freshness Check
# ============================================================================
check_source_freshness = BashOperator(
    task_id="check_source_freshness",
    bash_command=f"docker exec {DBT_CONTAINER} dbt source freshness",
    dag=dag,
    doc_md="""
    ### Check Source Freshness

    Validates that source data is fresh according to configured thresholds:
    - Warns if data is older than expected
    - Errors if data is critically stale

    **Configuration**: See `dbt/models/bronze/src_adventureworks.yml`
    """,
)

# ============================================================================
# BRONZE LAYER: Extract and Basic Cleaning
# ============================================================================
dbt_run_bronze = BashOperator(
    task_id="dbt_run_bronze",
    bash_command=f"docker exec {DBT_CONTAINER} dbt run --models bronze",
    dag=dag,
    doc_md="""
    ### Bronze Layer - Run Models

    Executes all bronze layer models (views):
    - `brnz_customers`: Raw customer data
    - `brnz_sales_orders`: Combined sales order header and detail
    - `brnz_products`: Product master data

    **Materialization**: Views for flexibility
    """,
)

dbt_test_bronze = BashOperator(
    task_id="dbt_test_bronze",
    bash_command=f"docker exec {DBT_CONTAINER} dbt test --models bronze",
    dag=dag,
    doc_md="""
    ### Bronze Layer - Data Quality Tests

    Executes all tests on bronze models:
    - Schema tests (unique, not_null, accepted_values)
    - dbt_expectations tests (data types, value ranges)
    - Custom generic tests (no future dates, positive values)

    **Test Files**: `dbt/models/bronze/schema.yml`
    """,
)

# ============================================================================
# SILVER LAYER: Business Logic Transformations
# ============================================================================
dbt_run_silver = BashOperator(
    task_id="dbt_run_silver",
    bash_command=f"docker exec {DBT_CONTAINER} dbt run --models silver",
    dag=dag,
    doc_md="""
    ### Silver Layer - Run Models

    Executes all silver layer models (tables):
    - `slvr_customers`: Cleaned customer data with computed fields
    - `slvr_sales_orders`: Sales data with business logic applied
    - `slvr_products`: Enriched product data

    **Materialization**: Tables for performance
    **Transformations**: CASE statements, calculated fields, data type conversions
    """,
)

dbt_test_silver = BashOperator(
    task_id="dbt_test_silver",
    bash_command=f"docker exec {DBT_CONTAINER} dbt test --models silver",
    dag=dag,
    doc_md="""
    ### Silver Layer - Data Quality Tests

    Validates transformed data quality:
    - Relationship tests (foreign key integrity)
    - Business rule validations
    - Data quality tests from `dbt/tests/data_quality/`

    **Test Files**: `dbt/models/silver/schema.yml`, `dbt/tests/data_quality/`
    """,
)

# ============================================================================
# GOLD LAYER: Business-Ready Aggregations
# ============================================================================
dbt_run_gold = BashOperator(
    task_id="dbt_run_gold",
    bash_command=f"docker exec {DBT_CONTAINER} dbt run --models gold",
    dag=dag,
    doc_md="""
    ### Gold Layer - Run Models

    Executes all gold layer models (tables):
    - `gld_sales_summary`: Daily sales aggregations and metrics
    - `gld_customer_metrics`: Customer lifetime value and KPIs
    - `gld_product_performance`: Product-level performance metrics

    **Materialization**: Tables for BI tool consumption
    **Use Case**: Direct connection to dashboards and reports
    """,
)

dbt_test_gold = BashOperator(
    task_id="dbt_test_gold",
    bash_command=f"docker exec {DBT_CONTAINER} dbt test --models gold",
    dag=dag,
    doc_md="""
    ### Gold Layer - Data Quality Tests

    Final validation of business-ready data:
    - Aggregation correctness
    - Metric validity
    - KPI threshold checks

    **Test Files**: `dbt/models/gold/schema.yml`
    """,
)

# ============================================================================
# FINAL VALIDATION: Generate DBT Documentation
# ============================================================================
dbt_generate_docs = BashOperator(
    task_id="dbt_generate_docs",
    bash_command=f"docker exec {DBT_CONTAINER} dbt docs generate",
    dag=dag,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    doc_md="""
    ### Generate DBT Documentation

    Creates fresh documentation artifacts:
    - Data lineage DAG
    - Model documentation
    - Test results

    **Access**: Run `dbt docs serve` to view
    """,
)

# ============================================================================
# ERROR HANDLING: Notification Tasks
# ============================================================================


def send_failure_notification(**context):
    """
    Custom failure notification with context details
    """
    task_instance = context["task_instance"]
    dag_run = context["dag_run"]
    exception = context.get("exception", "No exception info")

    failure_msg = f"""
    DAG Failure Alert

    DAG: {dag_run.dag_id}
    Task: {task_instance.task_id}
    Execution Date: {context['execution_date']}
    Run ID: {dag_run.run_id}

    Error: {exception}

    Log URL: {task_instance.log_url}

    Action Required: Check logs and retry failed task
    """

    print(failure_msg)
    return failure_msg


notify_failure = PythonOperator(
    task_id="notify_failure",
    python_callable=send_failure_notification,
    trigger_rule=TriggerRule.ONE_FAILED,
    provide_context=True,
    dag=dag,
    doc_md="""
    ### Failure Notification

    Triggered when ANY task in the pipeline fails.
    Sends detailed error information for troubleshooting.

    **Trigger Rule**: ONE_FAILED (runs if any upstream task fails)
    """,
)

# Optional: Email notification (uncomment and configure SMTP in Airflow)
# send_failure_email = EmailOperator(
#     task_id='send_failure_email',
#     to=['dataops@company.com'],
#     subject='[ALERT] DBT Pipeline Failed - {{ ds }}',
#     html_content="""
#     <h3>DBT Pipeline Failure</h3>
#     <p><strong>DAG:</strong> {{ dag.dag_id }}</p>
#     <p><strong>Execution Date:</strong> {{ ds }}</p>
#     <p><strong>Failed Task:</strong> Check Airflow UI for details</p>
#     <p><a href="{{ ti.log_url }}">View Logs</a></p>
#     """,
#     trigger_rule=TriggerRule.ONE_FAILED,
#     dag=dag,
# )

# ============================================================================
# SUCCESS NOTIFICATION
# ============================================================================


def send_success_notification(**context):
    """
    Success notification with pipeline statistics
    """
    dag_run = context["dag_run"]

    success_msg = f"""
    DBT Pipeline Completed Successfully

    DAG: {dag_run.dag_id}
    Execution Date: {context['execution_date']}
    Run ID: {dag_run.run_id}
    Duration: {dag_run.end_date - dag_run.start_date if dag_run.end_date else 'Running'}

    All layers processed:
    ✓ Source freshness validated
    ✓ Bronze layer: Extracted and tested
    ✓ Silver layer: Transformed and tested
    ✓ Gold layer: Aggregated and tested
    ✓ Documentation generated

    Pipeline Status: SUCCESS
    """

    print(success_msg)
    return success_msg


notify_success = PythonOperator(
    task_id="notify_success",
    python_callable=send_success_notification,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    provide_context=True,
    dag=dag,
    doc_md="""
    ### Success Notification

    Triggered when ALL tasks complete successfully.
    Provides pipeline execution summary.

    **Trigger Rule**: ALL_SUCCESS
    """,
)

# ============================================================================
# TASK DEPENDENCIES - Medallion Architecture Flow
# ============================================================================

# Phase 1: Source validation
check_source_freshness >> dbt_run_bronze

# Phase 2: Bronze layer (extract and test)
dbt_run_bronze >> dbt_test_bronze

# Phase 3: Silver layer (transform and test)
dbt_test_bronze >> dbt_run_silver >> dbt_test_silver

# Phase 4: Gold layer (aggregate and test)
dbt_test_silver >> dbt_run_gold >> dbt_test_gold

# Phase 5: Documentation and notifications
dbt_test_gold >> dbt_generate_docs >> notify_success

# Error handling: All tasks feed into failure notification
[
    check_source_freshness,
    dbt_run_bronze,
    dbt_test_bronze,
    dbt_run_silver,
    dbt_test_silver,
    dbt_run_gold,
    dbt_test_gold,
    dbt_generate_docs,
] >> notify_failure
