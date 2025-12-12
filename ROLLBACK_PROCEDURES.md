# Rollback Procedures

## Overview
This document provides detailed procedures for rolling back failed deployments in the DataOps DBT pipeline.

## Table of Contents
1. [When to Rollback](#when-to-rollback)
2. [Rollback Strategy](#rollback-strategy)
3. [Automated Rollback](#automated-rollback)
4. [Manual Rollback](#manual-rollback)
5. [Emergency Procedures](#emergency-procedures)
6. [Post-Rollback Verification](#post-rollback-verification)

---

## When to Rollback

### Rollback Triggers

**Immediate Rollback Required:**
- ❌ Critical data quality test failures
- ❌ Production application errors
- ❌ Database corruption or data loss
- ❌ Performance degradation >50%
- ❌ Security vulnerability introduced

**Consider Rollback:**
- ⚠️ Non-critical test failures
- ⚠️ Minor performance issues
- ⚠️ Unexpected data results
- ⚠️ Dependency issues

**Do Not Rollback:**
- ✅ Warning messages only
- ✅ Non-production environments
- ✅ Fixable issues within SLA

### Decision Matrix

| Severity | Impact | Action | Approval Required |
|----------|--------|--------|-------------------|
| Critical | Production down | Immediate rollback | No (post-incident review) |
| High | Data quality issues | Rollback within 1 hour | Team lead approval |
| Medium | Performance degradation | Assess and decide | Yes |
| Low | Non-critical warnings | Monitor and fix forward | Yes |

---

## Rollback Strategy

### Strategy Options

#### 1. Git Revert (Recommended)
**Use for:** Most deployments
**Pros:** Preserves history, safe, reversible
**Cons:** Creates additional commit

#### 2. Forward Fix
**Use for:** Minor issues, quick fixes available
**Pros:** No rollback needed, fixes root cause
**Cons:** Takes longer, risk of further issues

#### 3. Database Restore
**Use for:** Data corruption, schema issues
**Pros:** Complete recovery
**Cons:** Data loss between backup and rollback

#### 4. Feature Flag Disable
**Use for:** Feature-specific issues
**Pros:** Fast, no deployment needed
**Cons:** Requires feature flag infrastructure

---

## Automated Rollback

### Using Rollback Workflow

The project includes `.github/workflows/rollback.yml` for automated rollbacks.

#### Step 1: Identify Target Version

```bash
# View recent deployments
gh run list --workflow=deploy.yml --limit 10

# View commit history
git log --oneline --decorate -20

# View tags
git tag -l
```

#### Step 2: Trigger Rollback

**Via GitHub Actions UI:**

1. Go to: https://github.com/TranRoger/DATAOPS/actions
2. Select **"Rollback DBT Deployment"** workflow
3. Click **"Run workflow"**
4. Fill in parameters:
   - **Branch:** `develop` or `main`
   - **Version:** Commit SHA or tag (e.g., `abc1234` or `v1.0.0`)
   - **Target Environment:** `dev` or `prod`
5. Click **"Run workflow"**

**Via GitHub CLI:**

```bash
# Rollback development to specific commit
gh workflow run rollback.yml \
  -f version=abc1234 \
  -f environment=dev

# Rollback production to previous tag
gh workflow run rollback.yml \
  -f version=v1.0.0 \
  -f environment=prod

# Monitor rollback progress
gh run watch
```

#### Step 3: Monitor Rollback

```bash
# View rollback status
gh run list --workflow=rollback.yml --limit 1

# View detailed logs
gh run view --log

# Check if completed successfully
gh run view --exit-status
```

### Rollback Workflow Process

The automated rollback performs:

1. **Checkout target version**
   ```bash
   git checkout <version>
   ```

2. **Install dependencies**
   ```bash
   pip install -r dbt/requirements.txt
   dbt deps
   ```

3. **Run DBT with retry**
   ```bash
   dbt run --target <environment>
   dbt test --target <environment>
   ```

4. **Verify rollback**
   - Database connectivity test
   - Sample queries
   - Model count validation

---

## Manual Rollback

### Development Environment Rollback

#### Option 1: Git Revert

```bash
# Identify problematic commit
git log --oneline develop -10

# Revert the commit
git revert <bad-commit-sha>

# Or revert multiple commits
git revert <oldest-bad-commit>..<newest-bad-commit>

# Push to trigger deployment
git push origin develop
```

#### Option 2: Git Reset (Use with Caution)

```bash
# Hard reset to last good commit
git checkout develop
git pull origin develop
git reset --hard <good-commit-sha>

# Force push (requires permission)
git push origin develop --force

# Notify team
echo "Emergency rollback performed on develop branch"
```

#### Option 3: Cherry-Pick Good Commits

```bash
# Create rollback branch
git checkout -b rollback/fix-deployment develop

# Reset to before bad commits
git reset --hard <last-good-commit>

# Cherry-pick good commits if needed
git cherry-pick <good-commit-1>
git cherry-pick <good-commit-2>

# Push and create PR
git push origin rollback/fix-deployment
gh pr create --base develop --head rollback/fix-deployment
```

### Production Environment Rollback

**⚠️ CRITICAL: Production rollbacks require approval**

#### Emergency Rollback Process

1. **Declare Incident:**
```bash
# Create incident issue
gh issue create --title "INCIDENT: Production deployment failure" \
  --label incident,critical \
  --body "Deployment at $(date) failed. Initiating rollback."
```

2. **Notify Stakeholders:**
```bash
# Send notifications (customize for your setup)
echo "Production rollback in progress" | mail -s "URGENT" stakeholders@example.com
```

3. **Create Hotfix Branch:**
```bash
git checkout main
git pull origin main
git checkout -b hotfix/rollback-$(date +%Y%m%d-%H%M)
```

4. **Revert Bad Changes:**
```bash
# Option A: Revert specific commits
git revert <bad-commit-sha>

# Option B: Reset to last stable release
git reset --hard <last-stable-tag>

# Option C: Restore from backup branch
git reset --hard origin/release/v1.0.0
```

5. **Fast-Track Deployment:**
```bash
# Push hotfix
git push origin hotfix/rollback-*

# Create emergency PR with bypass approval (if configured)
gh pr create --base main --head hotfix/rollback-* \
  --title "🚨 EMERGENCY ROLLBACK" \
  --body "Critical production rollback. Auto-merge approved." \
  --label emergency

# Merge immediately (if you have permission)
gh pr merge --squash --delete-branch
```

6. **Monitor Rollback Deployment:**
```bash
# Watch deployment
gh run watch

# Check status every 30 seconds
watch -n 30 'gh run list --workflow=deploy.yml --limit 1'
```

---

## Emergency Procedures

### Database Corruption Rollback

**If database state is corrupted:**

1. **Stop all services:**
```bash
docker-compose down
```

2. **Restore from backup:**
```bash
# If you have a backup
docker-compose up -d sqlserver
docker cp /path/to/backup.bak sqlserver:/tmp/
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "$SA_PASSWORD" -Q "
    RESTORE DATABASE AdventureWorks2014
    FROM DISK = '/tmp/backup.bak'
    WITH REPLACE;
  "
```

3. **Or restore from scratch:**
```bash
docker-compose exec sqlserver /tmp/restore_db.sh
```

4. **Redeploy last good version:**
```bash
git checkout <last-good-commit>
docker-compose exec dbt dbt deps
docker-compose exec dbt dbt run --target prod
```

### Service Unavailable

**If deployment causes service outage:**

1. **Immediate Action - Disable failing component:**
```bash
# Stop Airflow DAGs
docker-compose exec airflow-webserver airflow dags pause dbt_transform

# Or stop entire service
docker-compose stop dbt
```

2. **Rollback via Git:**
```bash
git revert HEAD
git push origin main --force-with-lease
```

3. **Verify services restored:**
```bash
# Check service health
docker-compose ps
curl http://localhost:8080/health

# Verify database access
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U dbt_user -P "$DBT_PASSWORD" \
  -d AdventureWorks2014 -Q "SELECT @@VERSION"
```

---

## Post-Rollback Verification

### Verification Checklist

#### 1. Code Version
```bash
# Verify correct version deployed
git log -1 --oneline

# Check GitHub Actions deployment
gh run list --workflow=deploy.yml --limit 1
```

#### 2. Database State
```bash
# Check model tables exist
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U imrandbtnew -P "Imran@12345" \
  -d AdventureWorks2014 -Q "
    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA IN ('bronze', 'silver', 'gold')
    ORDER BY TABLE_SCHEMA, TABLE_NAME;
  "
```

#### 3. Data Quality
```bash
# Run all tests
docker-compose exec dbt dbt test

# Check specific critical tests
docker-compose exec dbt dbt test --select tag:critical
```

#### 4. Application Health
```bash
# Check Airflow status
curl http://localhost:8080/health

# Verify DAG can run
docker-compose exec airflow-webserver airflow dags test dbt_transform $(date +%Y-%m-%d)
```

#### 5. Performance
```sql
-- Check query performance
SELECT
    COUNT(*) as row_count,
    MAX(ModifiedDate) as last_update
FROM bronze.brnz_customers;

-- Should return quickly (<1 second)
```

### Post-Rollback Report

Document the rollback with:

```markdown
## Rollback Report

**Date:** YYYY-MM-DD HH:MM UTC
**Environment:** Production/Development
**Rollback From:** [bad-commit-sha]
**Rollback To:** [good-commit-sha]

**Reason:**
- [Description of issue]

**Actions Taken:**
1. [Step 1]
2. [Step 2]

**Verification:**
- [ ] Code version correct
- [ ] Database state restored
- [ ] Tests passing
- [ ] Application healthy
- [ ] Performance acceptable

**Root Cause:**
[Analysis of what went wrong]

**Prevention Measures:**
[Steps to prevent recurrence]

**Approver:** [Name]
```

---

## Root Cause Analysis

After rollback, conduct RCA:

### Investigation Steps

1. **Review Logs:**
```bash
# Deployment logs
gh run view <failed-run-id> --log > deployment-failure.log

# Application logs
docker-compose logs dbt > dbt-errors.log
docker-compose logs airflow-scheduler > airflow-errors.log
```

2. **Identify Failure Point:**
- Which step failed?
- What error message?
- Was it reproducible?

3. **Check Changes:**
```bash
# View changes in failed deployment
git diff <good-commit> <bad-commit>

# Review specific files
git show <bad-commit>:<file-path>
```

4. **Test Locally:**
```bash
# Checkout failed version
git checkout <bad-commit>

# Attempt to reproduce
docker-compose down -v
docker-compose up -d
docker-compose exec dbt dbt run
```

### Prevention Measures

**Update CI/CD:**
- Add missing tests
- Enhance validation checks
- Implement smoke tests

**Update Documentation:**
- Document the failure scenario
- Update deployment checklist
- Enhance monitoring

**Team Communication:**
- Share lessons learned
- Update team runbook
- Review approval processes

---

## Rollback Testing

### Test Rollback Procedure Quarterly

```bash
# 1. Deploy test version
git checkout develop
git tag test-rollback-$(date +%Y%m%d)
git push origin test-rollback-$(date +%Y%m%d)

# 2. Trigger deployment
gh workflow run deploy.yml

# 3. Perform rollback
gh workflow run rollback.yml -f version=<previous-tag>

# 4. Verify rollback successful
gh run view --log

# 5. Document results
echo "Rollback test $(date): PASS/FAIL" >> rollback-test-log.md
```

---

## Contact Information

### Escalation Path

| Level | Role | Contact | Response Time |
|-------|------|---------|---------------|
| L1 | On-Call Engineer | oncall@example.com | Immediate |
| L2 | DevOps Lead | roger@example.com | 15 minutes |
| L3 | Engineering Manager | manager@example.com | 30 minutes |
| L4 | CTO | cto@example.com | 1 hour |

### Emergency Contacts

**24/7 On-Call:** oncall@example.com
**Slack Channel:** #incidents
**PagerDuty:** https://yourcompany.pagerduty.com

---

## References

- [Deployment Runbook](DEPLOYMENT_RUNBOOK.md)
- [Rollback Workflow](.github/workflows/rollback.yml)
- [Incident Response Plan](INCIDENT_RESPONSE.md) _(if exists)_
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-12 | 1.0 | Initial rollback procedures | Roger |
