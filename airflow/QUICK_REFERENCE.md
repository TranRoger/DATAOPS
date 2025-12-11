# Airflow DAG Quick Reference

## Quick Commands

### Trigger DAG Manually
```bash
docker-compose exec airflow-webserver airflow dags trigger dbt_pipeline_enhanced
```

### Check DAG Status
```bash
docker-compose exec airflow-webserver airflow dags list
docker-compose exec airflow-webserver airflow dags state dbt_pipeline_enhanced
```

### View Recent DAG Runs
```bash
docker-compose exec airflow-webserver airflow dags list-runs -d dbt_pipeline_enhanced --limit 10
```

### Pause/Unpause DAG
```bash
# Pause
docker-compose exec airflow-webserver airflow dags pause dbt_pipeline_enhanced

# Unpause
docker-compose exec airflow-webserver airflow dags unpause dbt_pipeline_enhanced
```

### Test Individual Task
```bash
docker-compose exec airflow-webserver airflow tasks test dbt_pipeline_enhanced dbt_run_silver 2025-12-10
```

### View Task Logs
```bash
docker-compose exec airflow-webserver airflow tasks logs dbt_pipeline_enhanced dbt_run_silver 2025-12-10
```

### Clear Failed Task (for retry)
```bash
docker-compose exec airflow-webserver airflow tasks clear dbt_pipeline_enhanced --task-regex "dbt_test_silver" --start-date 2025-12-10 --yes
```

## Task Sequence

1. **check_source_freshness** - Validate data freshness
2. **dbt_run_bronze** - Extract raw data
3. **dbt_test_bronze** - Test bronze layer
4. **dbt_run_silver** - Transform data
5. **dbt_test_silver** - Test silver layer
6. **dbt_run_gold** - Aggregate metrics
7. **dbt_test_gold** - Test gold layer
8. **dbt_generate_docs** - Create documentation
9. **notify_success** - Send success alert
10. **notify_failure** - Send failure alert (on any failure)

## Common Scenarios

### Scenario 1: Bronze Test Fails
```bash
# Check what failed
docker-compose exec dbt dbt test --models bronze --store-failures

# Fix the issue in source data or model
# Then clear and retry
docker-compose exec airflow-webserver airflow tasks clear dbt_pipeline_enhanced --task-regex "dbt_test_bronze" --yes
```

### Scenario 2: Need to Re-run Full Pipeline
```bash
# Clear all tasks
docker-compose exec airflow-webserver airflow dags backfill dbt_pipeline_enhanced -s 2025-12-10 -e 2025-12-10 --reset-dagruns
```

### Scenario 3: Test Silver Layer Changes Locally
```bash
# Run silver models only
docker-compose exec dbt dbt run --models silver

# Test silver models
docker-compose exec dbt dbt test --models silver

# If good, trigger full pipeline
docker-compose exec airflow-webserver airflow dags trigger dbt_pipeline_enhanced
```

### Scenario 4: Check Why Source Freshness Failed
```bash
# Run freshness check manually
docker-compose exec dbt dbt source freshness

# Check source configuration
cat dbt/models/bronze/src_adventureworks.yml

# Verify source data exists
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "SELECT MAX(ModifiedDate) FROM AdventureWorks2014.Sales.SalesOrderHeader"
```

## Monitoring Checklist

### Daily Checks
- [ ] DAG ran successfully (check Airflow UI)
- [ ] All tasks green
- [ ] No error emails received
- [ ] Data updated in gold layer

### When Investigating Failures
1. Check Airflow UI for failed task (red square)
2. Click task → View Log
3. Look for error message in logs
4. Check corresponding DBT log: `./dbt/logs/dbt.log`
5. Fix issue in model or source data
6. Clear failed task and retry

## Email Notification Setup

### Enable Email Alerts

1. Edit `docker-compose.yml` and add to `airflow-webserver` environment:
```yaml
- AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com
- AIRFLOW__SMTP__SMTP_PORT=587
- AIRFLOW__SMTP__SMTP_USER=your-email@gmail.com
- AIRFLOW__SMTP__SMTP_PASSWORD=your-app-password
- AIRFLOW__SMTP__SMTP_MAIL_FROM=airflow@company.com
```

2. Uncomment the `send_failure_email` task in `dbt_pipeline_enhanced.py`

3. Restart Airflow:
```bash
docker-compose restart airflow-webserver airflow-scheduler
```

4. Test email:
```bash
docker-compose exec airflow-webserver python -c "
from airflow.utils.email import send_email
send_email('your-email@gmail.com', 'Test Email', 'Airflow email working!')
"
```

## Performance Optimization

### If Pipeline Runs Too Slow

1. **Check table sizes**:
```bash
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "
SELECT
    t.name AS TableName,
    SUM(p.rows) AS RowCount
FROM sys.tables t
INNER JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0,1)
GROUP BY t.name
ORDER BY RowCount DESC
"
```

2. **Optimize slow models**:
   - Use incremental materialization for large tables
   - Add filters to limit data scanned
   - Create indexes on join columns

3. **Increase container resources** in `docker-compose.yml`:
```yaml
dbt:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## Troubleshooting Matrix

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| DAG not showing | Syntax error | Check `docker-compose logs airflow-scheduler` |
| Container not found | Wrong container name | Run `docker ps \| grep dbt` |
| Source freshness fail | Stale data | Check source database update time |
| Bronze test fail | Bad source data | Review test failures in DBT logs |
| Silver test fail | Business logic error | Check model transformations |
| Gold test fail | Aggregation issue | Verify calculation logic |
| Task timeout | Resource constraints | Increase retry delay or resources |
| All tasks skip | DAG paused | Run `airflow dags unpause` |

## References

- **Full Documentation**: `airflow/DAG_DOCUMENTATION.md`
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **DAG Code**: `airflow/dags/dbt_pipeline_enhanced.py`
- **DBT Models**: `dbt/models/`
- **Troubleshooting**: `TROUBLESHOOTING.md`
