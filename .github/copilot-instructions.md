# GitHub Copilot Instructions

## Project Overview
This is a DataOps project implementing an automated data transformation pipeline using DBT (Data Build Tool) orchestrated by Apache Airflow. The pipeline extracts data from SQL Server (AdventureWorks 2014), transforms it through a medallion architecture (Bronze → Silver → Gold), and is orchestrated using Airflow DAGs with automated testing and CI/CD pipelines.

## Architecture & Data Flow

### Medallion Architecture (Bronze/Silver/Gold)
- **Bronze Layer** (`dbt/models/bronze/`): Raw data extraction and basic cleaning from source tables
  - Materialized as **views** for flexibility
  - Naming: `brnz_<entity>.sql` (e.g., `brnz_sales_orders.sql`)
  - Use `{{ source('adventureworks', 'TableName') }}` to reference source tables
  - Example: `brnz_sales_orders.sql` joins SalesOrderHeader and SalesOrderDetail

- **Silver Layer** (`dbt/models/silver/`): Business logic transformations
  - Materialized as **tables** for performance
  - Naming: `slvr_<entity>.sql` (e.g., `slvr_sales_orders.sql`)
  - Reference bronze models using `{{ ref('brnz_sales_orders') }}`
  - Add calculated fields, data type conversions, case statements for business logic

- **Gold Layer** (`dbt/models/gold/`): Business-ready aggregated data marts
  - Materialized as **tables** for BI tools
  - Naming: `gld_<metric>.sql` (e.g., `gld_sales_summary.sql`)
  - Aggregations, metrics, and analysis-ready datasets

### Container Architecture
All services run in Docker containers orchestrated via `docker-compose.yml`:
- **sqlserver**: AdventureWorks 2014 source database (port 1433)
- **postgres**: Airflow metadata storage (port 5432)
- **airflow-webserver**: Web UI (port 8080, admin/admin)
- **airflow-scheduler**: DAG execution
- **dbt**: DBT transformation container

## Critical Development Workflows

### DBT Operations (Always use docker-compose exec)
```bash
# Install DBT packages (dbt_utils, dbt_expectations)
docker-compose exec dbt dbt deps

# Run models by layer
docker-compose exec dbt dbt run --models bronze
docker-compose exec dbt dbt run --models silver
docker-compose exec dbt dbt run --models gold

# Run specific model and downstream dependencies
docker-compose exec dbt dbt run --select +slvr_sales_orders+

# Test models
docker-compose exec dbt dbt test --models bronze
docker-compose exec dbt dbt test

# Debug connection issues
docker-compose exec dbt dbt debug
```

### Airflow Operations
```bash
# Trigger DAG manually
docker-compose exec airflow-webserver airflow dags trigger dbt_transform

# List all DAGs
docker-compose exec airflow-webserver airflow dags list

# View task logs
docker-compose logs airflow-scheduler -f
```

### Database Access
```bash
# Create DBT user (required on first setup)
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "CREATE LOGIN imrandbtnew WITH PASSWORD = 'Imran@12345'; USE AdventureWorks2014; CREATE USER imrandbtnew FOR LOGIN imrandbtnew; ALTER ROLE db_owner ADD MEMBER imrandbtnew;"

# Query SQL Server
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "SELECT COUNT(*) FROM AdventureWorks2014.Sales.SalesOrderHeader"
```

### Container Management
```bash
# Start all services (after git clone)
docker-compose build --no-cache
docker-compose up -d

# Stop everything
docker-compose down

# Clean rebuild (when dependencies change)
docker-compose down -v
docker system prune -a
docker-compose build --no-cache && docker-compose up -d
```

## Project-Specific Conventions

### Source Definitions
- Define sources in `dbt/models/bronze/src_adventureworks.yml`
- Multiple schemas: `Sales`, `Production`, `Person`
- Example source reference: `{{ source('adventureworks', 'SalesOrderHeader') }}`

### Schema Files & Testing
- Each layer has `schema.yml` with model documentation and tests
- Use `dbt_expectations` package for advanced tests (e.g., `expect_column_values_to_be_of_type`)
- Custom generic tests in `dbt/tests/generic/` (e.g., `test_no_future_dates.sql`)
- Data quality tests in `dbt/tests/data_quality/` (e.g., `test_positive_revenue.sql`)

### DBT Configuration Patterns
```yaml
# dbt_project.yml materialization defaults
models:
  dbt_sqlserver_project:
    bronze:
      +materialized: view
      +schema: bronze
    silver:
      +materialized: table
      +schema: silver
    gold:
      +materialized: table
      +schema: gold
```

### Airflow DAG Pattern
- DAG file: `airflow/dags/dbt_dag.py`
- Uses BashOperator to execute `docker exec` commands (NOT DockerOperator)
- Task dependencies: `dbt_run_bronze >> dbt_test_bronze >> dbt_run_silver >> dbt_test_silver`
- Schedule: Every 5 minutes (`timedelta(minutes=5)`)

## Common Pitfalls & Troubleshooting

### Volume Mount Issues
If you see "failed to compute cache key" errors:
1. Ensure directories exist: `mkdir -p ./dbt ./airflow/{dags,logs,plugins}`
2. Clean Docker: `docker-compose down -v && docker system prune -a`
3. Rebuild: `docker-compose build --no-cache`

### DBT Connection Issues
- Connection config is in `dbt/profiles.yml` (NOT environment variables)
- Driver: `ODBC Driver 17 for SQL Server`
- Server: `sqlserver` (container name, not localhost when inside containers)
- Always run `docker-compose exec dbt dbt debug` to verify connection

### First-Time Setup Sequence
1. `docker-compose up -d` (wait 1-2 minutes)
2. `docker-compose exec sqlserver /tmp/restore_db.sh` (restore AdventureWorks)
3. Create DBT user (see Database Access above)
4. `docker-compose exec dbt dbt deps`
5. `docker-compose exec dbt dbt debug`
6. `docker-compose exec dbt dbt run`

### Port Conflicts
Default ports: 8080 (Airflow), 1433 (SQL Server), 5432 (Postgres). Modify in `docker-compose.yml` if conflicts occur.

## CI/CD Pipeline
- **DBT CI** (`.github/workflows/dbt-ci.yml`): Lints SQL with SQLFluff, runs Python linting
- **Python Quality** (`.github/workflows/python-quality.yml`): Black, Flake8, Pylint on Airflow DAGs
- Triggers: Pushes to `main`, `develop`, `feature/**` branches

## Key Files Reference
- `dbt/dbt_project.yml`: Project config, materialization defaults
- `dbt/profiles.yml`: Database connection (imrandbtnew/Imran@12345)
- `dbt/packages.yml`: External packages (dbt_utils, dbt_expectations)
- `airflow/dags/dbt_dag.py`: Orchestration logic
- `docker-compose.yml`: Service definitions and networking
- `dbt/models/sources.yml`: Source freshness checks (Sales.Customer)

## When Adding New Models
1. Create SQL file in appropriate layer directory
2. Add model documentation in `schema.yml`
3. Add tests (unique, not_null, relationships, custom tests)
4. Run locally: `docker-compose exec dbt dbt run --select +new_model+`
5. Test: `docker-compose exec dbt dbt test --select new_model`
6. Update Airflow DAG if new layer dependencies exist

## External Packages Usage
- **dbt_utils**: Use for macros like `generate_surrogate_key`, `star`
- **dbt_expectations**: Advanced tests like `expect_column_values_to_be_of_type`, `expect_column_values_to_be_in_set`
- Must run `dbt deps` after modifying `packages.yml`
