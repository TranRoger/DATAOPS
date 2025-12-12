# Quick Reference: Composite Actions

## 🚀 Quick Start Guide

### 1. Basic Database + DBT Setup
```yaml
steps:
  - uses: actions/checkout@v3

  - uses: ./.github/actions/setup-sqlserver
    with:
      sa-password: ${{ secrets.SA_PASSWORD }}

  - uses: ./.github/actions/restore-adventureworks
    with:
      sa-password: ${{ secrets.SA_PASSWORD }}
      dbt-password: ${{ secrets.DBT_PASSWORD }}

  - uses: ./.github/actions/setup-dbt
    with:
      dbt-profile-content: ${{ secrets.DBT_PROFILE }}
```

### 2. Complete Environment (All-in-One)
```yaml
steps:
  - uses: actions/checkout@v3

  - uses: ./.github/actions/setup-complete-environment
    with:
      sa-password: ${{ secrets.SA_PASSWORD }}
      dbt-password: ${{ secrets.DBT_PASSWORD }}
      dbt-profile-secret: ${{ secrets.DBT_PROFILE }}
```

### 3. Run DBT Pipeline
```yaml
steps:
  # After setup...

  - uses: ./.github/actions/run-dbt-workflow
    with:
      target: prod
      run-models: 'true'
      run-tests: 'true'
      generate-docs: 'false'
```

---

## 📋 Available Actions

| Action | Purpose | Key Inputs |
|--------|---------|------------|
| `setup-sqlserver` | Install SQL tools & wait | `sa-password` |
| `restore-adventureworks` | Restore DB + users | `sa-password`, `dbt-password` |
| `setup-dbt` | Setup Python & DBT | `dbt-profile-content` |
| `run-dbt-workflow` | Execute DBT pipeline | `target`, `run-models`, `run-tests` |
| `setup-complete-environment` | All-in-one setup | All above |

---

## 🎯 Common Patterns

### Development Environment
```yaml
- uses: ./.github/actions/run-dbt-workflow
  with:
    target: dev
    run-models: 'true'
    run-tests: 'false'  # Skip tests in dev
```

### Production Deployment
```yaml
- uses: ./.github/actions/run-dbt-workflow
  with:
    target: prod
    run-models: 'true'
    run-tests: 'true'   # Always test in prod
    generate-docs: 'true'
```

### CI/CD Validation (No DB)
```yaml
- uses: ./.github/actions/setup-dbt
  with:
    dbt-profile-content: ${{ secrets.DBT_PROFILE }}

# Then compile only
- run: cd dbt && dbt compile --profiles-dir .
```

---

## ⚠️ Important Notes

### Required Secrets
- `SA_PASSWORD` - SQL Server admin password
- `DBT_PASSWORD` - DBT user password
- `DBT_PROFILE` - Complete DBT profiles.yml content

### SQL Server Service
All database actions require SQL Server service:
```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    env:
      ACCEPT_EULA: Y
      SA_PASSWORD: ${{ secrets.SA_PASSWORD }}
    ports:
      - 1433:1433
```

### Checkout First
Always checkout code before using composite actions:
```yaml
- uses: actions/checkout@v3  # Required!
- uses: ./.github/actions/...
```

---

## 🐛 Troubleshooting

### Action not found
```bash
# Ensure you checked out code
- uses: actions/checkout@v3
```

### Input not being passed
```yaml
# ❌ Wrong
with:
  sa_password: ${{ secrets.SA_PASSWORD }}

# ✅ Correct (use hyphens)
with:
  sa-password: ${{ secrets.SA_PASSWORD }}
```

### SQL Server not ready
```yaml
# Add health check to service
options: >-
  --health-cmd "/opt/mssql-tools18/bin/sqlcmd ..."
  --health-interval 10s
```

---

## 📖 Full Documentation
See [.github/actions/README.md](.github/actions/README.md) for complete details.

---

**Last Updated:** December 12, 2025
