# Composite Actions - DataOps Pipeline

This directory contains reusable composite actions that eliminate code duplication across our GitHub Actions workflows.

## Overview

Our DataOps pipeline uses modular composite actions to ensure consistency and maintainability across all workflows.

## Available Composite Actions

### 1. Setup SQL Server (`setup-sqlserver`)

**Location:** `.github/actions/setup-sqlserver/action.yml`

**Purpose:** Installs SQL Server tools and waits for SQL Server to be ready.

**Inputs:**
- `sa-password` (required): SQL Server SA password

**Usage:**
```yaml
- name: Setup SQL Server
  uses: ./.github/actions/setup-sqlserver
  with:
    sa-password: ${{ secrets.SA_PASSWORD }}
```

---

### 2. Restore AdventureWorks Database (`restore-adventureworks`)

**Location:** `.github/actions/restore-adventureworks/action.yml`

**Purpose:** Downloads and restores the AdventureWorks 2014 database with user creation and schema setup.

**Inputs:**
- `sa-password` (required): SQL Server SA password
- `dbt-password` (required): DBT user password

**What it does:**
- Downloads AdventureWorks 2014 backup file
- Restores database to SQL Server container
- Creates `dbt_user` and `imrandbtnew` logins/users
- Creates `bronze`, `silver`, and `gold` schemas

**Usage:**
```yaml
- name: Restore AdventureWorks Database
  uses: ./.github/actions/restore-adventureworks
  with:
    sa-password: ${{ secrets.SA_PASSWORD }}
    dbt-password: ${{ secrets.DBT_PASSWORD }}
```

---

### 3. Setup DBT Environment (`setup-dbt`)

**Location:** `.github/actions/setup-dbt/action.yml`

**Purpose:** Sets up Python, installs DBT, creates profiles.yml, and installs dependencies.

**Inputs:**
- `dbt-profile-content` (required): Content for DBT profiles.yml
- `dbt-version` (optional, default: '1.8.5'): DBT SQL Server version
- `python-version` (optional, default: '3.9'): Python version

**What it does:**
- Installs Python
- Installs `dbt-sqlserver` and `dbt-fabric`
- Creates `profiles.yml` from secret
- Runs `dbt deps` to install packages

**Usage:**
```yaml
- name: Setup DBT Environment
  uses: ./.github/actions/setup-dbt
  with:
    dbt-profile-content: ${{ secrets.DBT_PROFILE }}
    dbt-version: '1.8.5'
    python-version: '3.9'
```

---

### 4. Run DBT Workflow (`run-dbt-workflow`)

**Location:** `.github/actions/run-dbt-workflow/action.yml`

**Purpose:** Executes the complete DBT workflow with validation, compilation, model runs, and testing.

**Inputs:**
- `target` (required): DBT target environment (`dev`, `prod`)
- `run-models` (optional, default: 'true'): Whether to run DBT models
- `run-tests` (optional, default: 'true'): Whether to run DBT tests
- `generate-docs` (optional, default: 'false'): Whether to generate documentation

**What it does:**
- Validates DBT project structure (`dbt debug`)
- Compiles DBT models (`dbt compile`)
- Runs DBT models (`dbt run`) if enabled
- Executes data quality tests (`dbt test`) if enabled
- Generates documentation (`dbt docs generate`) if enabled

**Usage:**
```yaml
- name: Run DBT Pipeline
  uses: ./.github/actions/run-dbt-workflow
  with:
    target: prod
    run-models: 'true'
    run-tests: 'true'
    generate-docs: 'false'
```

---

## Benefits of Using Composite Actions

### ✅ Code Reusability
- Write once, use everywhere
- Eliminates 300+ lines of duplicate code across workflows

### ✅ Consistency
- Ensures all workflows use identical setup steps
- Reduces configuration drift

### ✅ Maintainability
- Update in one place, propagates to all workflows
- Easier to review and test changes

### ✅ Readability
- Workflows are more concise and easier to understand
- Clear separation of concerns

---

## Workflow Integration Examples

### Example: Complete Deployment Pipeline

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2019-latest
        # ... service config

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      # Step 1: Setup SQL Server
      - name: Setup SQL Server
        uses: ./.github/actions/setup-sqlserver
        with:
          sa-password: ${{ secrets.SA_PASSWORD }}

      # Step 2: Restore Database
      - name: Restore AdventureWorks Database
        uses: ./.github/actions/restore-adventureworks
        with:
          sa-password: ${{ secrets.SA_PASSWORD }}
          dbt-password: ${{ secrets.DBT_PASSWORD }}

      # Step 3: Setup DBT
      - name: Setup DBT Environment
        uses: ./.github/actions/setup-dbt
        with:
          dbt-profile-content: ${{ secrets.DBT_PROFILE }}

      # Step 4: Run DBT Workflow
      - name: Run DBT Pipeline
        uses: ./.github/actions/run-dbt-workflow
        with:
          target: prod
          run-models: 'true'
          run-tests: 'true'
```

---

## Migration Guide

### Before (Old Approach)
```yaml
- name: Install SQL Server tools
  run: |
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    # ... 10+ lines of setup code

- name: Wait for SQL Server
  run: |
    # ... 10+ lines of wait logic

- name: Download and restore database
  run: |
    # ... 60+ lines of restore logic

- name: Set up Python
  uses: actions/setup-python@v4
  # ...

- name: Install DBT
  run: |
    # ... 5+ lines

# Total: ~100+ lines per job
```

### After (New Approach)
```yaml
- name: Setup SQL Server
  uses: ./.github/actions/setup-sqlserver
  with:
    sa-password: ${{ secrets.SA_PASSWORD }}

- name: Restore AdventureWorks Database
  uses: ./.github/actions/restore-adventureworks
  with:
    sa-password: ${{ secrets.SA_PASSWORD }}
    dbt-password: ${{ secrets.DBT_PASSWORD }}

- name: Setup DBT Environment
  uses: ./.github/actions/setup-dbt
  with:
    dbt-profile-content: ${{ secrets.DBT_PROFILE }}

# Total: ~15 lines per job (85% reduction!)
```

---

## Testing Composite Actions

To test a composite action locally:

```bash
# Create a test workflow
.github/workflows/test-composite-actions.yml

# Push to a feature branch
git checkout -b test/composite-actions
git add .github/actions/
git commit -m "feat: add composite actions"
git push origin test/composite-actions

# Trigger workflow manually or via PR
```

---

## Troubleshooting

### Issue: Composite action not found
**Solution:** Ensure you've checked out the repository with `actions/checkout@v3` before using local composite actions.

### Issue: Inputs not being passed correctly
**Solution:** Verify input names match exactly in both the composite action definition and usage.

### Issue: Environment variables not available
**Solution:** Composite actions don't inherit `env` from workflow level. Pass as inputs instead.

---

## Future Enhancements

- [ ] Add health check composite action
- [ ] Add rollback composite action
- [ ] Add notification composite action
- [ ] Version tagging for composite actions
- [ ] Add integration tests for each action

---

## Related Documentation

- [GitHub Actions Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
- [Project Deployment Runbook](../../DEPLOYMENT_RUNBOOK.md)
- [Troubleshooting Guide](../../TROUBLESHOOTING.md)

---

**Maintained by:** DataOps Team
**Last Updated:** December 2025
**Version:** 1.0.0
