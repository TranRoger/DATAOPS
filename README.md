# DBT + Airflow + SQL Server DataOps Project

[![DBT CI](https://github.com/TranRoger/DATAOPS/workflows/DBT%20CI%20Pipeline/badge.svg)](https://github.com/TranRoger/DATAOPS/actions/workflows/dbt-ci.yml)
[![Python Quality](https://github.com/TranRoger/DATAOPS/workflows/Python%20Code%20Quality/badge.svg)](https://github.com/TranRoger/DATAOPS/actions/workflows/python-quality.yml)
[![Deploy DBT Pipeline](https://github.com/TranRoger/DATAOPS/workflows/Deploy%20DBT%20Pipeline/badge.svg)](https://github.com/TranRoger/DATAOPS/actions/workflows/deploy.yml)

---

## 📚 Project Overview

Automated data transformation pipeline implementing **Medallion Architecture** (Bronze → Silver → Gold) using **DBT** and **Apache Airflow**, orchestrated through **Docker Compose** locally and **GitHub Actions** for CI/CD.

![Overall Architecture](docs/overall-architecture.svg)

### Key Features
- ✅ **Medallion Architecture**: Bronze/Silver/Gold data layers
- ✅ **Airflow Orchestration**: Scheduled DBT transformations (local)
- ✅ **Automated Testing**: Schema tests, custom data quality checks
- ✅ **CI/CD Pipeline**: GitHub Actions for deployment automation
- ✅ **Data Lineage**: Auto-generated DBT documentation

**📖 For detailed architecture, design decisions, and implementation details, see [report.md](report.md)**

**🎨 For architecture diagrams, see [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)**

---

## 🏗️ Architecture Components

| Component | Environment | Purpose |
|-----------|-------------|---------|
| ![Airflow](docs/airflow.svg) **Airflow** | Local | Orchestrates DBT transformations (hourly schedule) |
| ![DBT](docs/dbt.svg) **DBT** | Local + CI/CD | Data transformations (Bronze → Silver → Gold) |
| ![GitHub Actions](docs/github-action.svg) **GitHub Actions** | CI/CD | Automated testing & deployment |
| **SQL Server** | Local + CI/CD | AdventureWorks 2014 source database |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- 8GB+ RAM (for SQL Server container)

### 1️⃣ Clone Repository
```bash
git clone <repository-url>
cd dataops
  - Purpose: Container orchestration
  - Services Defined:
    1. **airflow-webserver**: Web interface for Airflow
       - Port: 8080
       - Usage: Monitor and manage DAGs

    2. **airflow-scheduler**: Airflow task scheduler
       - Purpose: Executes DAGs based on schedule
       - Dependencies: PostgreSQL for metadata

    3. **postgres**: Airflow metadata database
       - Purpose: Stores Airflow state and history
       - Port: 5432

    4. **sqlserver**: Source database
       - Purpose: Stores raw data
       - Port: 1433
       - Database: AdventureWorks

    5. **dbt**: DBT transformation container
       - Purpose: Executes DBT commands
       - Mounts: ./dbt directory for access to models

### Removed Components
The following components from the original structure were removed as they weren't essential:
- `dbt/tests/` - Tests are now included in schema.yml files
- `dbt/macros/` - Using standard macros from dbt_utils package
- `dbt/intermediate/` - Using two-layer (staging/marts) architecture
- `docker/airflow/` and `docker/dbt/` - Docker configurations included in main docker-compose.yml

## Container Workflow
1. **Data Flow**:
   ```
   SQL Server (source) → DBT (transformation) → SQL Server (transformed)
   ```

2. **Process Flow**:
   ```
   Airflow Scheduler → Triggers DBT Container → Runs Models → Updates Status
   ```

3. **Monitoring Flow**:
   ```
   Airflow UI → View Logs → Check Task Status → Monitor Transformations
   ```

## Step-by-Step Implementation Guide

### 1. Initial Setup

```

### 2️⃣ Start Services
```bash
# Build and start all containers
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready (~2 minutes)
docker-compose logs -f
```

### 3️⃣ Initialize Database
```bash
# Restore AdventureWorks database
docker-compose exec sqlserver /tmp/restore_db.sh

# Create DBT user
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" \
  -Q "CREATE LOGIN imrandbtnew WITH PASSWORD = 'Imran@12345'; USE AdventureWorks2014; CREATE USER imrandbtnew FOR LOGIN imrandbtnew; ALTER ROLE db_owner ADD MEMBER imrandbtnew;"
```

### 4️⃣ Run DBT Transformations
```bash
# Install DBT packages
docker-compose exec dbt dbt deps

# Run all models (Bronze → Silver → Gold)
docker-compose exec dbt dbt run

# Run tests
docker-compose exec dbt dbt test

# Generate documentation
docker-compose exec dbt dbt docs generate
docker-compose exec dbt dbt docs serve --port 8081
```

### 5️⃣ Access Services
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **DBT Docs**: http://localhost:8081
- **SQL Server**: localhost:1433 (sa/YourStrong@Passw0rd)

---

## 📂 Project Structure

```
dataops/
├── .github/workflows/          # CI/CD pipelines
│   ├── dbt-ci.yml             # DBT compilation & docs generation
│   ├── python-quality.yml     # Python linting
│   ├── pr-check.yml           # PR validation
│   ├── deploy.yml             # Automated deployment
│   └── rollback.yml           # Rollback workflow
├── airflow/
│   ├── dags/
│   │   └── dbt_dag.py         # Orchestration DAG (Bronze → Silver → Gold)
│   └── logs/                  # Execution logs
├── dbt/
│   ├── models/
│   │   ├── bronze/            # Raw data extraction (views)
│   │   ├── silver/            # Business transformations (tables)
│   │   └── gold/              # Aggregated metrics (tables)
│   ├── tests/                 # Custom data quality tests
│   ├── dbt_project.yml        # DBT configuration
│   ├── profiles.yml           # Database connections
│   └── packages.yml           # dbt_utils, dbt_expectations
├── docs/                      # Architecture diagrams & images
├── docker-compose.yml         # Container orchestration
└── README.md                  # This file
```

---

## 🔧 Development Workflows

### Local Development (Airflow + Docker)
```bash
# Run specific model layer
docker-compose exec dbt dbt run --models bronze
docker-compose exec dbt dbt run --models silver
docker-compose exec dbt dbt run --models gold

# Run specific model with dependencies
docker-compose exec dbt dbt run --select +slvr_sales_orders+

# Test specific layer
docker-compose exec dbt dbt test --models bronze

# Trigger Airflow DAG manually
docker-compose exec airflow-webserver airflow dags trigger dbt_transform
```

### CI/CD (GitHub Actions)
```bash
# On every push/PR:
# ✅ SQL linting (SQLFluff)
# ✅ Python quality checks (Flake8, Black, Pylint)
# ✅ DBT compilation
# ✅ PR validation

# On merge to develop/main:
# ✅ Automated deployment
# ✅ DBT run + test
# ✅ Documentation generation
# ✅ Artifact upload
```

---

## 📊 Data Pipeline

### Medallion Architecture Layers

| Layer | Materialization | Purpose | Models |
|-------|-----------------|---------|--------|
| **Bronze** | Views | Raw data extraction | `brnz_sales_orders`, `brnz_customers`, `brnz_products` |
| **Silver** | Tables | Business transformations | `slvr_sales_orders`, `slvr_customers`, `slvr_products` |
| **Gold** | Tables | Aggregated metrics | `gld_sales_summary`, `gld_customer_metrics`, `gld_product_performance` |

**Data Flow**:
```
AdventureWorks (Source) → Bronze (Extract) → Silver (Transform) → Gold (Aggregate)
```

---

## 🧪 Testing

### Schema Tests
```yaml
# dbt/models/*/schema.yml
tests:
  - unique
  - not_null
  - relationships
  - accepted_values
  - dbt_expectations.expect_column_values_to_be_of_type
```

### Custom Tests
- `test_no_future_dates.sql` - Validates date columns
- `test_positive_values.sql` - Ensures numeric constraints
- `test_positive_revenue.sql` - Business logic validation

---

## 🚢 Deployment

### Environments

| Branch | Environment | Trigger | Auto-deploy |
|--------|-------------|---------|-------------|
| `develop` | Development | Push | ✅ Yes |
| `main` | Production | Push | ✅ Yes |

### Rollback
```bash
# Via GitHub Actions UI:
# Actions → "Manual Rollback" → Run workflow
# Inputs: target commit, environment, reason
```

---

## 📖 Documentation

- **[report.md](report.md)** - Complete project report with architecture, design decisions
- **[docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)** - Mermaid diagrams
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🛠️ Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker-compose down -v
docker system prune -a
docker-compose build --no-cache && docker-compose up -d
```

**DBT connection error:**
```bash
docker-compose exec dbt dbt debug
```

**Airflow DAG not appearing:**
```bash
docker-compose logs airflow-scheduler
docker-compose restart airflow-scheduler
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Push and create Pull Request
4. Wait for CI checks to pass
5. Merge after approval

---

## 📄 License

[LICENSE](LICENSE)

---

## 👥 Team

- **Data Engineering Team**
- Course: DataOps / Data Engineering
- Year: 2025
- ✅ Model compilation and execution
- ✅ Data quality test execution
- ✅ Post-deployment health checks
- ✅ Deployment artifacts and logs
- ✅ Deployment summaries
- ✅ Slack notifications (configurable)

**Deployment Process:**
```bash
# Development
git push origin develop  # Triggers automatic deployment

# Production
git push origin main     # Triggers automatic deployment
```

### Rollback Capability

**Manual Rollback Workflow:**
- Navigate to: Actions → "Manual Rollback" → "Run workflow"
- Provide: Target commit SHA, Environment, Reason
- Automated rollback execution with validation

**See**: [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md) for detailed procedures

### Monitoring & Notifications

**Deployment Monitoring:**
- Real-time workflow status in GitHub Actions
- Deployment summaries with key metrics
- Artifact retention (30 days for dev, 90 days for prod)
- Deployment history tracking

**Notifications:**
- ✅ Slack webhooks for deployment status
- ✅ GitHub Action summaries
- ✅ Deployment record generation
- ✅ Failure alerts with troubleshooting steps

**Configuration:**
```bash
# Set Slack webhook (optional)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Or add to GitHub Secrets:
# Repository → Settings → Secrets → New repository secret
# Name: SLACK_WEBHOOK_URL
# Value: <your-webhook-url>
```

### Deployment Documentation

- **Runbook**: [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md) - Complete deployment procedures
- **Rollback Guide**: Included in runbook
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Deployment windows, checklists, verification steps

## Best Practices

1. **Version Control**
   - Keep all code in version control
   - Use meaningful commit messages following conventional commits format
   - Create feature branches for new development
   - Examples: `feat: add new model`, `fix: correct date calculation`

2. **Testing**
   - Write tests for all DBT models
   - Test data quality and business logic
   - Run tests locally before pushing: `dbt test`
   - Ensure all CI checks pass before merging

3. **Documentation**
   - Document all models and transformations
   - Keep README up to date
   - Use clear naming conventions
   - Add column-level documentation in schema.yml files

4. **Security**
   - Never commit sensitive credentials
   - Use environment variables for secrets
   - Use GitHub Secrets for CI/CD credentials
   - Regularly update dependencies

5. **Deployment**
   - Always deploy to development first
   - Verify changes in dev before promoting to prod
   - Never deploy on Fridays or before holidays
   - Have rollback plan ready for production deployments
   - Follow deployment runbook procedures

## Troubleshooting

Common issues and solutions:

1. **Container Connection Issues**
   - Check if all containers are running: `docker-compose ps`
   - Verify network connectivity: `docker network ls`

2. **DBT Errors**
   - Check profiles.yml configuration
   - Verify database credentials
   - Run `dbt debug` for diagnostics

3. **Airflow DAG Issues**
   - Check DAG syntax
   - Verify task dependencies
   - Check Airflow logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For additional support:
- Check the project issues
- Contact the development team
- Refer to DBT and Airflow documentation
