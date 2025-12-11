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
from airflow.utils.email import send_email
import os
import logging
import requests
import json

# Configure logger
logger = logging.getLogger(__name__)

# Notification Configuration
# Set SLACK_WEBHOOK_URL in Airflow Variables or environment variable
# export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_notification(message, color="danger", webhook_url=SLACK_WEBHOOK_URL):
    """
    Send notification to Slack channel via webhook.

    Args:
        message: Dict with title, text, and fields
        color: "good" (green), "warning" (yellow), "danger" (red)
        webhook_url: Slack webhook URL

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not webhook_url:
        logger.warning("Slack webhook URL not configured. Skipping Slack notification.")
        return False

    try:
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": message.get("title", "Airflow Notification"),
                    "text": message.get("text", ""),
                    "fields": message.get("fields", []),
                    "footer": "DataOps Orchestration System",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        response = requests.post(
            webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10
        )

        if response.status_code == 200:
            logger.info("✅ Slack notification sent successfully")
            return True
        else:
            logger.error(f"❌ Slack notification failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error sending Slack notification: {str(e)}")
        return False


def task_failure_alert(context):
    """
    Callback function triggered on task failure.
    Sends detailed alert with task context and error information.

    Args:
        context: Airflow context dictionary containing task instance details
    """
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    dag_id = context.get("dag").dag_id
    task_id = context.get("task").task_id
    execution_date = context.get("execution_date")

    subject = f"Airflow Task Failed: {dag_id}.{task_id}"

    # HTML email content (for email notification option)
    # Uncomment and assign to variable if using send_email()
    # html_content = f"""
    # <h2>DataOps Pipeline Failure Alert</h2>
    # <p><strong>Status:</strong> <span style="color: red;">FAILED</span></p>
    # ... (full HTML template available in comments)
    # """

    # Log the failure
    logger.error(f"❌ Task {task_id} failed on try {task_instance.try_number}/{task_instance.max_tries}")
    logger.error(f"Exception: {exception}")

    # === NOTIFICATION OPTIONS ===

    # Option 1: Slack Notification (Recommended - Easy to set up)
    slack_message = {
        "title": f"❌ Pipeline Failed: {dag_id}.{task_id}",
        "text": f"Task failed on attempt {task_instance.try_number}/{task_instance.max_tries}",
        "fields": [
            {"title": "DAG", "value": dag_id, "short": True},
            {"title": "Task", "value": task_id, "short": True},
            {"title": "Execution Date", "value": str(execution_date), "short": True},
            {
                "title": "Retries Left",
                "value": str(task_instance.max_tries - task_instance.try_number),
                "short": True,
            },
            {"title": "Error", "value": f"```{str(exception)[:200]}...```", "short": False},
        ],
    }
    send_slack_notification(slack_message, color="danger")

    # Option 2: Email Notification (Requires SMTP configuration)
    # Uncomment and configure SMTP settings in airflow.cfg
    # send_email(
    #     to=['dataops-team@example.com'],
    #     subject=subject,
    #     html_content=html_content
    # )

    # Option 3: Microsoft Teams Webhook
    # teams_webhook_url = "YOUR_TEAMS_WEBHOOK_URL"
    # requests.post(teams_webhook_url, json={...})

    # Option 4: Log to File (Always enabled as fallback)
    logger.warning(f"[NOTIFICATION] {subject}")
    logger.info("Full error details logged in Airflow task logs")


def task_success_alert(context):
    """
    Callback function triggered on task success after previous failures.
    Logs recovery information.

    Args:
        context: Airflow context dictionary containing task instance details
    """
    task_instance = context.get("task_instance")

    if task_instance.try_number > 1:
        task_id = context.get("task").task_id
        retry_count = task_instance.try_number - 1

        logger.info(f"✅ Task {task_id} succeeded on retry {retry_count} after previous failures")

        # Send Slack success notification
        slack_message = {
            "title": f"✅ Pipeline Recovered: {context.get('dag').dag_id}.{task_id}",
            "text": f"Task succeeded after {retry_count} retry attempt(s)",
            "fields": [
                {"title": "Task", "value": task_id, "short": True},
                {"title": "Retry Count", "value": str(retry_count), "short": True},
            ],
        }
        send_slack_notification(slack_message, color="good")


def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """
    Callback function triggered when SLA is missed.
    Alerts team about pipeline performance degradation.

    Args:
        dag: The DAG object
        task_list: List of tasks that missed SLA
        blocking_task_list: Tasks blocking SLA tasks
        slas: SLA configuration
        blocking_tis: Blocking task instances
    """
    logger.error(f"SLA MISSED - DAG: {dag.dag_id}, Tasks: {[t.task_id for t in task_list]}")

    # In production: send high-priority alert
    subject = f"SLA BREACH: {dag.dag_id}"
    send_email(
        to=["anhth5659@gmail.com"],
        subject=subject,
        html_content="<p>SLA has been breached. Immediate attention required.</p>",
    )


# Default arguments for all tasks in the DAG
default_args = {
    "owner": "dataops_team",
    "depends_on_past": False,
    "email": ["dataops-team@example.com"],
    "email_on_failure": False,  # Using custom callback instead
    "email_on_retry": False,
    "retries": 2,  # Increased from 1 to 2 for transient failures
    "retry_delay": timedelta(minutes=5),  # Reduced from 15 to 5 minutes
    "retry_exponential_backoff": True,  # Enable exponential backoff (5m, 10m, 20m)
    "max_retry_delay": timedelta(minutes=30),  # Cap maximum retry delay
    "on_failure_callback": task_failure_alert,  # Custom failure handler
    "on_success_callback": task_success_alert,  # Track recoveries
    "execution_timeout": timedelta(minutes=30),  # Kill tasks running > 30 min
    "sla": timedelta(minutes=20),  # Each layer should complete within 20 minutes
}

# DAG definition
with DAG(
    "dbt_transform",
    default_args=default_args,
    description="DBT medallion architecture (Bronze→Silver→Gold) with automated testing",
    schedule=timedelta(hours=1),  # Production: hourly execution
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Prevent concurrent pipeline runs
    dagrun_timeout=timedelta(hours=2),  # Total DAG timeout
    sla_miss_callback=sla_miss_callback,  # SLA breach handler
    tags=["dbt", "sqlserver", "medallion", "data-pipeline", "production"],
    doc_md=__doc__,
) as dag:
    # Bronze Layer: Extract raw data from source systems
    with TaskGroup(group_id="bronze_layer", tooltip="Raw data extraction") as bronze_group:
        dbt_run_bronze = BashOperator(
            task_id="dbt_run_bronze",
            bash_command="docker exec dataops-dbt-1 dbt run --models bronze --profiles-dir /usr/app/dbt",
        )
        dbt_run_bronze.doc = "Extract raw data from Sales, Production, Person schemas"

        dbt_test_bronze = BashOperator(
            task_id="dbt_test_bronze",
            bash_command="docker exec dataops-dbt-1 dbt test --models bronze --profiles-dir /usr/app/dbt",
        )
        dbt_test_bronze.doc = "Validate PK uniqueness, FK integrity, data types, no future dates"

        # Bronze layer internal dependencies
        dbt_run_bronze >> dbt_test_bronze

    # Silver Layer: Apply business transformations
    with TaskGroup(group_id="silver_layer", tooltip="Business transformations") as silver_group:
        dbt_run_silver = BashOperator(
            task_id="dbt_run_silver",
            bash_command="docker exec dataops-dbt-1 dbt run --models silver --profiles-dir /usr/app/dbt",
        )
        dbt_run_silver.doc = "Apply business rules: calculated fields, NULL handling, quality filters"

        dbt_test_silver = BashOperator(
            task_id="dbt_test_silver",
            bash_command="docker exec dataops-dbt-1 dbt test --models silver --profiles-dir /usr/app/dbt",
        )
        dbt_test_silver.doc = "Validate business logic, positive constraints, accepted values"

        # Silver layer internal dependencies
        dbt_run_silver >> dbt_test_silver

    # Gold Layer: Create business-ready aggregations
    with TaskGroup(group_id="gold_layer", tooltip="Business metrics and KPIs") as gold_group:
        dbt_run_gold = BashOperator(
            task_id="dbt_run_gold",
            bash_command="docker exec dataops-dbt-1 dbt run --models gold --profiles-dir /usr/app/dbt",
        )
        dbt_run_gold.doc = "Aggregate metrics: daily sales, customer LTV, product profitability"

        dbt_test_gold = BashOperator(
            task_id="dbt_test_gold",
            bash_command="docker exec dataops-dbt-1 dbt test --models gold --profiles-dir /usr/app/dbt",
        )
        dbt_test_gold.doc = "Validate aggregations, no NULL metrics, date ranges, relationships"

        # Gold layer internal dependencies
        dbt_run_gold >> dbt_test_gold

    # Define cross-layer dependencies (Medallion architecture flow)
    bronze_group >> silver_group >> gold_group
