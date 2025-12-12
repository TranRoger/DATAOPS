# DataOps Pipeline Architecture Diagrams

## 1. Overall Architecture - Local vs CI/CD

```mermaid
graph TB
    subgraph "LOCAL DEVELOPMENT ENVIRONMENT"
        subgraph "Docker Compose Stack"
            AW[("AdventureWorks 2014<br/>SQL Server<br/>Port 1433")]

            subgraph "Airflow Orchestration"
                AWS[Airflow Webserver<br/>localhost:8080<br/>admin/admin]
                ASC[Airflow Scheduler<br/>Schedule: Every 1 hour]
                PG[("PostgreSQL<br/>Metadata DB<br/>Port 5432")]
            end

            DBT_LOCAL[DBT Container<br/>Port 8081<br/>docker exec commands]
        end

        SLACK_LOCAL[Slack Notifications<br/>Local Webhook]

        ASC -->|Orchestrates| DBT_LOCAL
        DBT_LOCAL -->|Transform Data| AW
        ASC -->|Send Alerts| SLACK_LOCAL
        AWS -->|Monitor DAGs| ASC
        PG -->|Store Metadata| ASC
    end

    subgraph "CI/CD PIPELINE (GitHub Actions Runner)"
        GH[GitHub Actions<br/>Ubuntu Latest]

        subgraph "CI Jobs (Parallel)"
            LINT_SQL[SQLFluff Linting]
            LINT_PY[Python Quality<br/>Black, Flake8, Pylint]
            PR_CHECK[PR Validation]
        end

        subgraph "CD Jobs - Setup on Runner"
            SQL_SERVICE[SQL Server Service<br/>Ephemeral Container]
            RESTORE[Download & Restore<br/>AdventureWorks 2014]
            DBT_CI[DBT CLI<br/>pip install dbt-sqlserver]
        end

        subgraph "DBT Execution (Direct CLI)"
            DEPS[dbt deps]
            COMPILE[dbt compile]
            RUN[dbt run]
            TEST[dbt test]
            DOCS[dbt docs generate]
        end

        ARTIFACTS[GitHub Artifacts<br/>30-day retention]
        PAGES[GitHub Pages<br/>Public Docs]

        GH -->|Trigger on push/PR| LINT_SQL & LINT_PY & PR_CHECK
        LINT_SQL & LINT_PY --> COMPILE

        GH -->|Setup| SQL_SERVICE
        SQL_SERVICE --> RESTORE
        RESTORE --> DBT_CI
        DBT_CI --> DEPS
        DEPS --> COMPILE
        COMPILE --> RUN
        RUN --> TEST
        TEST --> DOCS

        DOCS --> ARTIFACTS
        DOCS --> PAGES
    end

    DEV[Developer] -->|docker-compose up| AW
    DEV -->|git push| GH

    style AW fill:#ff6b6b
    style DBT_LOCAL fill:#4ecdc4
    style DBT_CI fill:#4ecdc4
    style GH fill:#c7ecee
    style PAGES fill:#b197fc
    style SLACK_LOCAL fill:#fab005
    style SQL_SERVICE fill:#ff6b6b
    style ASC fill:#ffe66d
```

**Key Points:**
- **Local:** Airflow runs 24/7 in Docker, schedules DBT transformations
- **CI/CD:** GitHub Actions runs DBT directly via CLI (NO Airflow)
- **Scheduling:** Only happens in local Airflow, NOT in GitHub Actions

---

## 2. Local Development with Airflow DAG

```mermaid
graph LR
    subgraph "Developer Workflow"
        DEV[Developer]
    end

    subgraph "Docker Compose Environment"
        subgraph "Airflow Stack"
            WEB[Airflow Webserver<br/>localhost:8080]
            SCHEDULER[Airflow Scheduler<br/>timedelta hours=1]
            PG[(PostgreSQL<br/>Metadata)]
        end

        subgraph "DBT Container - Task Groups"
            subgraph "Bronze Layer"
                B_RUN[dbt_run_bronze<br/>BashOperator]
                B_TEST[dbt_test_bronze<br/>BashOperator]
            end

            subgraph "Silver Layer"
                S_RUN[dbt_run_silver<br/>BashOperator]
                S_TEST[dbt_test_silver<br/>BashOperator]
            end

            subgraph "Gold Layer"
                G_RUN[dbt_run_gold<br/>BashOperator]
                G_TEST[dbt_test_gold<br/>BashOperator]
            end
        end

        SQL[("SQL Server<br/>AdventureWorks 2014")]

        SLACK[Slack Webhook<br/>task_failure_alert<br/>task_success_alert]
    end

    DEV -->|Trigger manually| WEB

    WEB --> SCHEDULER
    SCHEDULER -->|Read/Write State| PG

    SCHEDULER -->|docker exec dbt| B_RUN
    B_RUN --> B_TEST
    B_TEST --> S_RUN
    S_RUN --> S_TEST
    S_TEST --> G_RUN
    G_RUN --> G_TEST

    B_RUN & S_RUN & G_RUN -->|Query/Transform| SQL

    B_RUN & S_RUN & G_RUN -.->|On Failure| SLACK
    B_TEST & S_TEST & G_TEST -.->|Success after Retry| SLACK

    style DEV fill:#c7ecee
    style WEB fill:#ffe66d
    style SCHEDULER fill:#ffe66d
    style SQL fill:#ff6b6b
    style SLACK fill:#fab005
    style B_RUN fill:#ffe66d
    style B_TEST fill:#ffe66d
    style S_RUN fill:#95e1d3
    style S_TEST fill:#95e1d3
    style G_RUN fill:#a8e6cf
    style G_TEST fill:#a8e6cf
```

**Task Flow:**
```python
# airflow/dags/dbt_dag.py
bronze_group >> silver_group >> gold_group

# Each group:
dbt_run_<layer> >> dbt_test_<layer>
```

---

## 3. CI/CD Pipeline (GitHub Actions Only)

```mermaid
graph TB
    START([Git Push to<br/>develop/main])

    subgraph "GitHub Actions Runner"
        subgraph "CI (Parallel)"
            LINT_SQL[Lint SQL<br/>SQLFluff<br/>tsql dialect]
            LINT_PY[Lint Python<br/>Flake8, Black, Pylint]
            PR_CHECK[PR Validation<br/>Title, Size, Conflicts]
        end

        subgraph "DBT Compilation"
            INSTALL_DBT[Install DBT<br/>dbt-sqlserver==1.8.5]
            CREATE_PROFILE[Create profiles.yml<br/>from GitHub Secret]
            DBT_DEPS[dbt deps<br/>dbt_utils, dbt_expectations]
            DBT_COMPILE[dbt compile<br/>Validate Models]
        end

        subgraph "Documentation Generation"
            SQL_SVC[SQL Server Service<br/>Container on Runner]
            RESTORE_DB[Download AdventureWorks<br/>Restore Database]
            CREATE_USERS[Create DBT Users<br/>imrandbtnew, dbt_user]
            CREATE_SCHEMAS[Create Schemas<br/>bronze, silver, gold]
            DBT_DOCS[dbt docs generate<br/>Lineage + Catalog]
        end

        subgraph "Deployment"
            ENV{Branch?}
            SETUP_SQL[Setup SQL Server Service]
            DBT_RUN[dbt run<br/>Execute All Models]
            DBT_TEST[dbt test<br/>Data Quality Checks]
        end
    end

    subgraph "Outputs"
        ARTIFACT[GitHub Artifacts<br/>catalog.json<br/>manifest.json<br/>index.html]
        SUMMARY[Job Summary<br/>Deployment Report]
    end

    START --> LINT_SQL & LINT_PY & PR_CHECK

    LINT_SQL --> INSTALL_DBT
    LINT_PY --> INSTALL_DBT
    PR_CHECK --> INSTALL_DBT

    INSTALL_DBT --> CREATE_PROFILE
    CREATE_PROFILE --> DBT_DEPS
    DBT_DEPS --> DBT_COMPILE

    DBT_COMPILE --> SQL_SVC
    SQL_SVC --> RESTORE_DB
    RESTORE_DB --> CREATE_USERS
    CREATE_USERS --> CREATE_SCHEMAS
    CREATE_SCHEMAS --> DBT_DOCS

    DBT_DOCS --> ENV
    ENV -->|main/develop| SETUP_SQL

    SETUP_SQL --> DBT_RUN
    DBT_RUN --> DBT_TEST

    DBT_TEST --> ARTIFACT
    DBT_DOCS --> ARTIFACT
    DBT_TEST --> SUMMARY

    style START fill:#c7ecee
    style LINT_SQL fill:#ffe66d
    style LINT_PY fill:#ffe66d
    style DBT_COMPILE fill:#95e1d3
    style DBT_DOCS fill:#a8e6cf
    style DBT_RUN fill:#51cf66
    style DBT_TEST fill:#51cf66
    style SQL_SVC fill:#ff6b6b
```

**Important:** GitHub Actions uses **direct DBT CLI**, NOT Airflow orchestration.

---

## 4. DBT Medallion Architecture Layers

```mermaid
graph LR
    subgraph "Source Database"
        SOH[(Sales.SalesOrderHeader)]
        SOD[(Sales.SalesOrderDetail)]
        CUST[(Sales.Customer)]
        PROD[(Production.Product)]
    end

    subgraph "Bronze Layer (Views)"
        BSALES[brnz_sales_orders<br/>source + ref<br/>Materialized: view]
        BCUST[brnz_customers<br/>source<br/>Materialized: view]
        BPROD[brnz_products<br/>source<br/>Materialized: view]
    end

    subgraph "Silver Layer (Tables)"
        SSALES[slvr_sales_orders<br/>ref brnz_sales_orders<br/>+ Business Logic<br/>Materialized: table]
        SCUST[slvr_customers<br/>ref brnz_customers<br/>+ Enrichment<br/>Materialized: table]
        SPROD[slvr_products<br/>ref brnz_products<br/>+ Calculated Fields<br/>Materialized: table]
    end

    subgraph "Gold Layer (Tables)"
        GSALES[gld_sales_summary<br/>Daily Aggregations<br/>Materialized: table]
        GCUST[gld_customer_metrics<br/>Customer LTV<br/>Materialized: table]
        GPROD[gld_product_performance<br/>Product Profitability<br/>Materialized: table]
    end

    SOH -->|source adventureworks| BSALES
    SOD -->|source adventureworks| BSALES
    CUST -->|source adventureworks| BCUST
    PROD -->|source adventureworks| BPROD

    BSALES -->|ref| SSALES
    BCUST -->|ref| SCUST
    BPROD -->|ref| SPROD

    SSALES -->|ref + aggregate| GSALES
    SSALES -->|ref| GCUST
    SCUST -->|ref| GCUST
    SPROD -->|ref| GPROD
    SSALES -->|ref| GPROD

    style SOH fill:#ff6b6b
    style SOD fill:#ff6b6b
    style CUST fill:#ff6b6b
    style PROD fill:#ff6b6b
    style BSALES fill:#ffe66d
    style BCUST fill:#ffe66d
    style BPROD fill:#ffe66d
    style SSALES fill:#95e1d3
    style SCUST fill:#95e1d3
    style SPROD fill:#95e1d3
    style GSALES fill:#a8e6cf
    style GCUST fill:#a8e6cf
    style GPROD fill:#a8e6cf
```

**Model Reference Patterns:**
```sql
-- Bronze: Extract from source
{{ source('adventureworks', 'SalesOrderHeader') }}

-- Silver: Transform bronze models
{{ ref('brnz_sales_orders') }}

-- Gold: Aggregate silver models
{{ ref('slvr_sales_orders') }}
```

---

## 5. Environment Comparison

| Aspect | Local (Docker Compose) | CI/CD (GitHub Actions) |
|--------|------------------------|------------------------|
| **Orchestration** | ✅ Airflow DAGs | ❌ Direct DBT CLI |
| **SQL Server** | ✅ Persistent Container | ✅ Ephemeral Service |
| **DBT Execution** | `docker exec dbt dbt run` | `dbt run` |
| **Scheduling** | ✅ timedelta(hours=1) | ❌ Event-driven only |
| **Notifications** | ✅ Slack Webhook | ❌ GitHub Summary |
| **Purpose** | Development & Demo | Automated Deployment |
| **Runs** | Continuously (24/7) | On git push/PR |
| **State Management** | ✅ PostgreSQL Metadata | ❌ Stateless |
| **Retry Logic** | ✅ Exponential Backoff | ⚠️ GitHub Actions retry |

---

## Architecture Decision Rationale

### Why Airflow Only in Local?

**For Learning/Demo (Current Project):**
- ✅ Demonstrates production-like orchestration
- ✅ Shows scheduling capabilities
- ✅ No cloud infrastructure cost
- ✅ Easy to debug and iterate

**For Production (Future):**
- Would deploy Airflow to cloud (AWS MWAA, Cloud Composer)
- Airflow runs 24/7 on dedicated infrastructure
- GitHub Actions only for CI/CD, NOT scheduling

### Why GitHub Actions for CI/CD?

**Advantages:**
- ✅ Event-driven (triggers on code changes)
- ✅ Built-in to GitHub (no setup needed)
- ✅ Free for public repos
- ✅ Validates code before deployment

**NOT for:**
- ❌ Regular scheduling (use Airflow)
- ❌ Complex orchestration (use Airflow)
- ❌ State management (use Airflow)
