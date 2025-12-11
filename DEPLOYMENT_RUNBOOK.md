# Deployment Runbook - DataOps Pipeline

## Table of Contents
1. [Overview](#overview)
2. [Deployment Workflows](#deployment-workflows)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Deployment Procedures](#deployment-procedures)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Deployment History](#deployment-history)

---

## Overview

This runbook documents the deployment procedures for the DataOps DBT pipeline across development and production environments.

### Deployment Architecture

```
Feature Branch → develop → main
                    ↓         ↓
                   DEV      PROD
```

### Environments

| Environment | Branch | Target | Auto-Deploy | Approval Required |
|-------------|--------|--------|-------------|-------------------|
| **Development** | `develop` | `dev` | ✅ Yes | ❌ No |
| **Production** | `main` | `prod` | ✅ Yes | ⚠️ Recommended |

---

## Deployment Workflows

### 1. Development Deployment
- **Trigger**: Push to `develop` branch
- **Workflow**: `.github/workflows/deploy-dev.yml`
- **Duration**: ~5-10 minutes
- **Automatic**: Yes

### 2. Production Deployment
- **Trigger**: Push to `main` branch
- **Workflow**: `.github/workflows/deploy-prod.yml`
- **Duration**: ~10-15 minutes
- **Automatic**: Yes (with optional manual trigger)

### 3. Manual Rollback
- **Trigger**: Manual via GitHub Actions UI
- **Workflow**: `.github/workflows/rollback.yml`
- **Duration**: ~5-10 minutes
- **Requires**: Target commit SHA + rollback reason

---

## Pre-Deployment Checklist

### Before Merging to `develop` or `main`

- [ ] All CI checks passing (DBT compile, linting, tests)
- [ ] Pull request reviewed and approved
- [ ] No merge conflicts
- [ ] All required tests executed locally
- [ ] Documentation updated (if models changed)
- [ ] Breaking changes documented and communicated

### Additional for Production

- [ ] Development deployment successful and verified
- [ ] Data quality tests passing
- [ ] Stakeholders notified of upcoming changes
- [ ] Rollback plan prepared
- [ ] Backup/snapshot created (optional but recommended)

---

## Deployment Procedures

### Development Deployment

#### Automatic Deployment (Recommended)
1. **Merge PR to `develop` branch**
   ```bash
   git checkout develop
   git pull origin develop
   git merge feature/your-feature-branch
   git push origin develop
   ```

2. **Monitor deployment**
   - Navigate to: GitHub → Actions → "Deploy to Development"
   - Watch workflow progress in real-time
   - Check for any errors or warnings

3. **Verify deployment**
   ```bash
   # Check if models were updated (optional - requires DB access)
   docker-compose exec dbt dbt run --select state:modified+ --target dev
   ```

#### Manual Deployment
1. **Trigger from GitHub Actions**
   - Go to: Actions → "Deploy to Development" → "Run workflow"
   - Select `develop` branch
   - Click "Run workflow"

### Production Deployment

#### Standard Procedure
1. **Create release PR**
   ```bash
   git checkout main
   git pull origin main
   git merge develop
   git push origin main
   ```

2. **Monitor production deployment**
   - Navigate to: GitHub → Actions → "Deploy to Production"
   - Workflow includes environment protection (if configured)
   - Review deployment summary

3. **Post-deployment verification**
   - Check deployment artifacts
   - Verify data quality test results
   - Review deployment logs

#### Emergency Deployment (Manual Trigger)
1. **Navigate to Actions → "Deploy to Production"**
2. **Click "Run workflow"**
3. **Configure options**:
   - Branch: `main`
   - Skip tests: Only for emergency (not recommended)
4. **Provide justification in workflow run name**

---

## Post-Deployment Verification

### Automated Checks (Built into Workflows)
✅ DBT models compiled successfully
✅ All models executed without errors
✅ Data quality tests passed
✅ Deployment artifacts uploaded
✅ Deployment summary generated

### Manual Verification (Recommended)

#### 1. Check Workflow Status
```bash
# Via GitHub CLI
gh run list --workflow=deploy-dev.yml --limit 5
gh run view <run-id> --log
```

#### 2. Verify Model Updates
```bash
# Connect to DBT container
docker-compose exec dbt bash

# Check model state
dbt ls --models state:modified --target dev

# View model results
dbt show --select your_model_name --target dev
```

#### 3. Data Quality Verification
- Review test results in deployment logs
- Check for any warnings or failures
- Verify record counts match expectations

#### 4. Monitoring Dashboard (if available)
- Check key metrics (record counts, freshness, test pass rates)
- Compare before/after deployment
- Look for anomalies

---

## Rollback Procedures

### When to Rollback
- Critical data quality test failures
- Deployment causing production issues
- Incorrect business logic discovered
- Performance degradation

### Rollback Process

#### 1. Identify Target Commit
```bash
# View recent deployments
git log --oneline main -10

# Find last known good commit
# Check deployment artifacts in GitHub Actions
```

#### 2. Execute Rollback via GitHub Actions
1. **Navigate to**: Actions → "Manual Rollback" → "Run workflow"
2. **Fill in required fields**:
   - **Target Commit**: `<commit-sha>` (from step 1)
   - **Environment**: Select `development` or `production`
   - **Reason**: Describe issue requiring rollback
   - **Skip Tests**: Leave as `false` (unless emergency)
3. **Click "Run workflow"**
4. **Monitor rollback progress**

#### 3. Verify Rollback Success
```bash
# Check current deployment state
git log main -1

# Verify models reverted
docker-compose exec dbt dbt ls --target prod

# Run spot-checks on data
```

#### 4. Communicate Rollback
- Notify stakeholders via Slack/email
- Document reason and impact
- Plan forward fix

### Alternative Rollback Methods

#### Method 1: Git Revert + Redeploy
```bash
# Create revert commit
git checkout main
git revert <bad-commit-sha>
git push origin main

# This triggers automatic redeployment
```

#### Method 2: Manual DBT Rollback (Emergency)
```bash
# SSH into server or connect to DBT container
docker-compose exec dbt bash

# Checkout previous version
cd /usr/app/dbt
git checkout <target-commit>

# Run DBT manually
dbt run --target prod
dbt test --target prod
```

---

## Troubleshooting

### Common Deployment Issues

#### Issue 1: DBT Compilation Error
**Symptoms**: Workflow fails at "Compile DBT models" step

**Solutions**:
```bash
# Test locally first
cd dbt
dbt compile --profiles-dir . --target dev

# Check for syntax errors in SQL
sqlfluff lint models/

# Verify profiles.yml is correct
dbt debug --profiles-dir .
```

#### Issue 2: Database Connection Failure
**Symptoms**: "Connection timeout" or "Unable to connect"

**Solutions**:
- Check database credentials in GitHub Secrets
- Verify network connectivity
- Check database service status
- Review profiles.yml configuration

#### Issue 3: Test Failures Post-Deployment
**Symptoms**: `dbt test` step fails

**Solutions**:
```bash
# Run tests locally to identify failures
dbt test --target dev

# Check specific failing test
dbt test --select test_name

# Review test logic in schema.yml
# Fix data quality issues or adjust test thresholds
```

#### Issue 4: Workflow Hangs or Times Out
**Symptoms**: Workflow running > 30 minutes

**Solutions**:
- Check for long-running models (review query plans)
- Increase timeout in workflow (if justified)
- Check database resource utilization
- Cancel and re-run with `--fail-fast` flag

### Emergency Contacts

| Issue Type | Contact | Channel |
|------------|---------|---------|
| **Production Outage** | DataOps Team Lead | Slack: #dataops-alerts |
| **Deployment Failure** | DevOps Engineer | Slack: #devops |
| **Data Quality Issues** | Data Engineer | Slack: #data-quality |
| **After Hours** | On-Call Engineer | PagerDuty |

---

## Deployment History

### Tracking Deployments

#### Via GitHub Actions
1. Navigate to: Repository → Actions
2. Filter by workflow: "Deploy to Production" or "Deploy to Development"
3. View run history, logs, and artifacts

#### Via Deployment Records (Automated)
```bash
# Deployment records stored in .deployments/
ls -la .deployments/

# View specific deployment
cat .deployments/prod_20251211_120000.json
```

#### Example Deployment Record
```json
{
  "deployment_id": "1234567890",
  "commit_sha": "abc123def456",
  "deployed_by": "github_username",
  "deployed_at": "2025-12-11 12:00:00 UTC",
  "environment": "production",
  "target": "prod",
  "status": "success",
  "backup_commit": "xyz789abc012"
}
```

### Monitoring Deployment Success Rates

#### Metrics to Track
- **Deployment Frequency**: How often we deploy
- **Success Rate**: % of successful deployments
- **Mean Time to Deploy**: Average deployment duration
- **Rollback Frequency**: How often we need to rollback
- **Mean Time to Recovery**: Time to fix failed deployments

#### Generating Reports
```bash
# Success rate calculation (example)
TOTAL_RUNS=$(gh run list --workflow=deploy-prod.yml --json status | jq length)
SUCCESS_RUNS=$(gh run list --workflow=deploy-prod.yml --json status | jq '[.[] | select(.status=="success")] | length')
echo "Success Rate: $(echo "scale=2; $SUCCESS_RUNS / $TOTAL_RUNS * 100" | bc)%"
```

---

## Best Practices

### Before Every Deployment
1. Run full test suite locally
2. Review changed files in PR
3. Check for downstream dependencies
4. Notify stakeholders of breaking changes

### During Deployment
1. Monitor workflow logs in real-time
2. Keep Slack/communication channels open
3. Have rollback plan ready
4. Don't deploy during high-traffic periods (production)

### After Deployment
1. Verify critical metrics
2. Run smoke tests
3. Document any issues encountered
4. Update runbook if new patterns emerge

### Production Deployment Windows
- **Recommended**: Tuesday-Thursday, 10 AM - 3 PM
- **Avoid**: Fridays, Mondays (before 10 AM), after hours
- **Never**: Major holidays, during incidents

---

## Appendix

### Useful Commands

#### GitHub CLI
```bash
# List recent workflow runs
gh run list --workflow=deploy-prod.yml --limit 10

# View specific run details
gh run view <run-id> --log

# Re-run failed workflow
gh run rerun <run-id>

# Download artifacts
gh run download <run-id>
```

#### DBT Commands
```bash
# Compile and check for errors
dbt compile --profiles-dir . --target prod

# Run only modified models
dbt run --models state:modified+ --target prod

# Run specific model and downstream
dbt run --select model_name+ --target prod

# Test specific models
dbt test --select model_name --target prod
```

### Related Documentation
- [DBT Project README](../dbt/README.md)
- [CI/CD Workflow Documentation](../README.md#cicd-pipeline)
- [Architecture Overview](../ARCHITECTURE.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-11
**Maintained by**: DataOps Team
