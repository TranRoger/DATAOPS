# Deployment Runbook

## Overview
This runbook provides comprehensive procedures for deploying the DataOps DBT pipeline using GitHub Actions CI/CD workflows.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Environments](#deployment-environments)
3. [Automated Deployment](#automated-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### Required GitHub Secrets
Configure these secrets in **Settings → Secrets and variables → Actions**:

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `SA_PASSWORD` | SQL Server SA password | `YourStrong@Passw0rd123` |
| `DBT_PASSWORD` | DBT user password | `DbtUser@12345` |
| `DBT_PROFILE` | Complete profiles.yml content | See profiles.yml template below |

**DBT_PROFILE Template:**
```yaml
dbt_airflow_project:
  target: dev
  outputs:
    dev:
      type: sqlserver
      driver: 'ODBC Driver 18 for SQL Server'
      server: localhost
      port: 1433
      database: AdventureWorks2014
      schema: dbo_dev
      user: dbt_user
      password: '<YOUR_DBT_PASSWORD>'
      encrypt: true
      trust_cert: true
      threads: 4
    prod:
      type: sqlserver
      driver: 'ODBC Driver 18 for SQL Server'
      server: <PROD_SERVER>
      port: 1433
      database: AdventureWorks2014
      schema: dbo
      user: dbt_user
      password: '<YOUR_DBT_PASSWORD>'
      encrypt: true
      trust_cert: true
      threads: 2
```

### Environment Protection Rules
1. Navigate to **Settings → Environments**
2. Create environments:
   - `development` - No protection rules
   - `production` - Enable required reviewers

---

## Deployment Environments

### Development Environment
- **Branch:** `develop`
- **Target:** `dev`
- **Schema:** `dbo_dev`
- **Deployment:** Automatic on push
- **Approval:** Not required
- **Threads:** 4

### Production Environment
- **Branch:** `main`
- **Target:** `prod`
- **Schema:** `dbo`
- **Deployment:** Automatic on push (with approval)
- **Approval:** Required (configure in GitHub settings)
- **Threads:** 2

---

## Automated Deployment

### Development Deployment

**Trigger:** Push to `develop` branch

```bash
# Make changes to your code
git checkout develop
git add .
git commit -m "feat: your changes"
git push origin develop
```

**Workflow Execution:**
1. Pre-deployment validation runs
   - SQL Server container starts
   - AdventureWorks database restored
   - DBT connection validated
   - Models compiled (dry run)

2. Deploy job executes
   - `dbt deps` - Install packages
   - `dbt run` - Execute models
   - `dbt test` - Run data quality tests
   - `dbt docs generate` - Create documentation

3. Post-deployment health check
   - Database connectivity verified
   - Sample queries executed

4. Notification sent
   - Slack notification (if configured)
   - GitHub Actions summary

**Monitor Progress:**
- Go to: https://github.com/TranRoger/DATAOPS/actions
- Click on the latest workflow run
- Monitor each job's progress

### Production Deployment

**Trigger:** Push to `main` branch (typically via PR merge)

```bash
# Create pull request from develop to main
git checkout develop
git pull origin develop
gh pr create --base main --head develop --title "Release: v1.0.0" --body "Production deployment"

# Or via GitHub UI:
# 1. Go to Pull Requests
# 2. Click "New pull request"
# 3. Base: main, Compare: develop
# 4. Create pull request
# 5. Request review
# 6. Merge after approval
```

**Workflow Execution:**
1. Same as development but with:
   - Production environment protection
   - Required reviewer approval
   - Production database target
   - `dbo` schema instead of `dbo_dev`

---

## Manual Deployment

### Using GitHub Actions UI

1. Navigate to **Actions** tab
2. Select **Deploy DBT Pipeline** workflow
3. Click **Run workflow**
4. Select branch (develop or main)
5. Click **Run workflow** button

### Using GitHub CLI

```bash
# Trigger development deployment
gh workflow run deploy.yml --ref develop

# Trigger production deployment
gh workflow run deploy.yml --ref main

# Check workflow status
gh run list --workflow=deploy.yml --limit 5
```

### Local Deployment (Development Only)

```bash
# Start containers
docker-compose up -d

# Restore database
docker-compose exec sqlserver /tmp/restore_db.sh

# Run DBT
docker-compose exec dbt dbt deps
docker-compose exec dbt dbt run --target dev
docker-compose exec dbt dbt test --target dev
```

---

## Rollback Procedures

### Using Rollback Workflow

The project includes a dedicated rollback workflow for failed deployments.

**Trigger Rollback:**

1. **Via GitHub Actions UI:**
   - Go to **Actions** tab
   - Select **Rollback DBT Deployment** workflow
   - Click **Run workflow**
   - Enter the commit SHA or tag to rollback to
   - Click **Run workflow**

2. **Via GitHub CLI:**
```bash
# Rollback to specific commit
gh workflow run rollback.yml -f version=abc1234

# Rollback to previous tag
gh workflow run rollback.yml -f version=v1.0.0
```

### Manual Rollback Steps

If the automated rollback fails:

1. **Identify last good deployment:**
```bash
# View deployment history
git log --oneline --decorate

# Or check GitHub Actions runs
gh run list --workflow=deploy.yml
```

2. **Revert to last good commit:**
```bash
# Option 1: Revert specific commit
git revert <bad-commit-sha>
git push origin develop

# Option 2: Hard reset (use with caution)
git reset --hard <good-commit-sha>
git push origin develop --force
```

3. **Re-run deployment:**
   - The push will automatically trigger deployment workflow

### Emergency Production Rollback

**Critical: Use only in emergency situations**

1. **Create hotfix branch:**
```bash
git checkout main
git pull origin main
git checkout -b hotfix/rollback-emergency
```

2. **Revert to last stable commit:**
```bash
git revert <bad-commit-sha>
# Or cherry-pick good changes
git cherry-pick <good-commit-sha>
```

3. **Fast-track to production:**
```bash
git push origin hotfix/rollback-emergency

# Create emergency PR
gh pr create --base main --head hotfix/rollback-emergency \
  --title "HOTFIX: Emergency rollback" \
  --body "Emergency rollback due to production incident"

# Request immediate review and merge
```

4. **Verify rollback:**
```bash
# Check deployment status
gh run list --workflow=deploy.yml --limit 1

# Monitor logs
gh run view --log
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptoms:**
```
Error: Could not connect to SQL Server
```

**Solutions:**
```bash
# Verify secrets are set
gh secret list

# Check SQL Server container health
docker ps --filter "ancestor=mcr.microsoft.com/mssql/server:2019-latest"

# View workflow logs
gh run view <run-id> --log
```

#### 2. DBT Package Installation Failures

**Symptoms:**
```
Error: Package 'dbt_utils' not found
```

**Solutions:**
- Verify `dbt/packages.yml` is correct
- Check `dbt deps` step logs
- Clear DBT cache:
```bash
docker-compose exec dbt rm -rf dbt_packages/
docker-compose exec dbt dbt deps
```

#### 3. Model Compilation Errors

**Symptoms:**
```
Compilation Error: relation does not exist
```

**Solutions:**
- Check source definitions in `dbt/models/sources.yml`
- Verify database restore completed
- Check table names in source database:
```bash
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "$SA_PASSWORD" \
  -Q "SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('Sales')"
```

#### 4. Test Failures

**Symptoms:**
```
FAIL 1 test_unique_brnz_customers_CustomerID
```

**Solutions:**
- Review test logs in workflow output
- Run tests locally:
```bash
docker-compose exec dbt dbt test --select brnz_customers
```
- Fix data quality issues or adjust test thresholds

#### 5. Container Filesystem Issues

**Symptoms:**
```
Cannot open backup device '/tmp/AdventureWorks2014.bak'
```

**Solutions:**
- Verified in workflow: backup is copied into container with `docker cp`
- Check container ID is correct
- Verify backup downloaded successfully

---

## Post-Deployment Verification

### Automated Checks (Included in Workflow)

The deployment workflow automatically runs:
- ✅ DBT test suite
- ✅ Model freshness checks
- ✅ Database connectivity test
- ✅ Sample query validation

### Manual Verification Steps

#### 1. Verify Models Executed

```bash
# Check models in database
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U imrandbtnew -P "Imran@12345" \
  -d AdventureWorks2014 -Q "
    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA IN ('bronze', 'silver', 'gold', 'dbo_dev')
    ORDER BY TABLE_SCHEMA, TABLE_NAME;
  "
```

#### 2. Verify Data Quality

```bash
# Check row counts
docker-compose exec dbt dbt run-operation test_data_counts
```

#### 3. Check DBT Documentation

```bash
# Generate and view docs locally
docker-compose exec dbt dbt docs generate
docker-compose exec dbt dbt docs serve --port 8081
```

Open: http://localhost:8081

#### 4. Validate Lineage

- Review DBT docs lineage graph
- Verify all model dependencies resolved
- Check for circular dependencies

#### 5. Performance Check

```sql
-- Check execution times in DBT logs
SELECT
    model_name,
    execution_time,
    status
FROM dbt_run_results
WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM dbt_run_results)
ORDER BY execution_time DESC;
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Code reviewed and approved
- [ ] GitHub secrets configured
- [ ] Environment protection rules set
- [ ] Backup of production database (if applicable)
- [ ] Stakeholders notified

### During Deployment
- [ ] Monitor workflow progress in GitHub Actions
- [ ] Check for errors in logs
- [ ] Verify pre-deployment validation passed
- [ ] Confirm deploy job completed
- [ ] Review post-deployment health check

### Post-Deployment
- [ ] Verify models created in target schemas
- [ ] Run manual verification queries
- [ ] Check DBT documentation updated
- [ ] Review test results
- [ ] Monitor application logs
- [ ] Notify stakeholders of completion

---

## Monitoring and Alerts

### GitHub Actions Monitoring

**View Recent Deployments:**
```bash
# List recent workflow runs
gh run list --workflow=deploy.yml --limit 10

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

**Status Badges:**

Add to README.md:
```markdown
![Deploy Status](https://github.com/TranRoger/DATAOPS/actions/workflows/deploy.yml/badge.svg)
```

### Set Up Alerts

1. **GitHub Actions Notifications:**
   - Go to: **Watch** → **Custom** → Check **Actions**

2. **Email Notifications:**
   - Automatic on workflow failure

3. **Slack Integration (Optional):**
   - Configure webhook URL in secrets
   - Update notify job in deploy.yml

---

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|-------------|
| DevOps Lead | roger@example.com | 24/7 |
| Database Admin | dba@example.com | Business hours |
| On-Call Engineer | oncall@example.com | 24/7 |

---

## References

- [Deploy Workflow](.github/workflows/deploy.yml)
- [Rollback Workflow](.github/workflows/rollback.yml)
- [DBT Documentation](https://docs.getdbt.com/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [SQL Server on Docker](https://hub.docker.com/_/microsoft-mssql-server)

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-12 | 1.0 | Initial deployment runbook | Roger |
