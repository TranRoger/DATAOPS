# DBT Pipeline Enhanced - Visual Architecture

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DBT PIPELINE ENHANCED                             │
│                    (dbt_pipeline_enhanced DAG)                           │
└─────────────────────────────────────────────────────────────────────────┘

                              START
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: SOURCE VALIDATION                                            │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  check_source_freshness                                      │     │
│  │  • Validates data freshness from source systems              │     │
│  │  • Warns if data > threshold (6-24 hours depending on table) │     │
│  │  • Stops pipeline if data critically stale (>12-48 hours)    │     │
│  │  Command: dbt source freshness                               │     │
│  │  Retries: 2 (exponential backoff)                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: BRONZE LAYER (Extract)                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_run_bronze                                              │     │
│  │  • Extracts raw data from source                             │     │
│  │  • Creates views: brnz_customers, brnz_sales_orders,         │     │
│  │    brnz_products                                             │     │
│  │  • Joins SalesOrderHeader + SalesOrderDetail                 │     │
│  │  Command: dbt run --models bronze                            │     │
│  │  Materialization: VIEW                                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_test_bronze (DATA QUALITY GATE #1)                     │     │
│  │  • Tests primary keys (unique, not_null)                     │     │
│  │  • Validates data types (dbt_expectations)                   │     │
│  │  • Custom tests: no future dates, positive values            │     │
│  │  Command: dbt test --models bronze                           │     │
│  │  ⚠️  Pipeline STOPS if tests fail                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: SILVER LAYER (Transform)                                     │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_run_silver                                              │     │
│  │  • Applies business logic transformations                    │     │
│  │  • Creates tables: slvr_customers, slvr_sales_orders,        │     │
│  │    slvr_products                                             │     │
│  │  • CASE statements (Online/Offline channel)                  │     │
│  │  • Calculated fields (gross_amount, effective_unit_price)    │     │
│  │  • Data type conversions                                     │     │
│  │  Command: dbt run --models silver                            │     │
│  │  Materialization: TABLE                                      │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_test_silver (DATA QUALITY GATE #2)                     │     │
│  │  • Tests referential integrity (foreign keys)                │     │
│  │  • Validates business rules                                  │     │
│  │  • Data quality tests: positive revenue, no duplicates       │     │
│  │  Command: dbt test --models silver                           │     │
│  │  ⚠️  Pipeline STOPS if tests fail                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: GOLD LAYER (Aggregate)                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_run_gold                                                │     │
│  │  • Creates business-ready aggregations                       │     │
│  │  • Creates tables: gld_sales_summary, gld_customer_metrics,  │     │
│  │    gld_product_performance                                   │     │
│  │  • Daily sales metrics, customer lifetime value              │     │
│  │  • KPIs for dashboards and reports                           │     │
│  │  Command: dbt run --models gold                              │     │
│  │  Materialization: TABLE (optimized for BI tools)             │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_test_gold (DATA QUALITY GATE #3)                       │     │
│  │  • Validates metric calculations                             │     │
│  │  • Tests aggregation correctness                             │     │
│  │  • KPI threshold checks                                      │     │
│  │  Command: dbt test --models gold                             │     │
│  │  ⚠️  Pipeline STOPS if tests fail                            │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: DOCUMENTATION & NOTIFICATION                                 │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  dbt_generate_docs                                           │     │
│  │  • Generates fresh DBT documentation                         │     │
│  │  • Creates data lineage DAG                                  │     │
│  │  • Updates model and column descriptions                     │     │
│  │  Command: dbt docs generate                                  │     │
│  │  Trigger: ALL_SUCCESS                                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  notify_success                                              │     │
│  │  • Sends success notification                                │     │
│  │  • Includes pipeline statistics                              │     │
│  │  • Execution duration and timestamp                          │     │
│  │  Trigger: ALL_SUCCESS                                        │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                              END ✓


                      ┌──────────────────┐
                      │  ERROR HANDLING  │
                      └──────────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌──────────────────┐
│  notify_failure │                          │  Email Alert     │
│  (Always runs   │                          │  (Optional)      │
│   on failure)   │                          │                  │
│                 │                          │  Requires SMTP   │
│  Trigger:       │                          │  configuration   │
│  ONE_FAILED     │                          │                  │
│                 │                          │  See docs for    │
│  Logs:          │                          │  setup steps     │
│  • Failed task  │                          └──────────────────┘
│  • Error msg    │
│  • Log URL      │
│  • Timestamp    │
└─────────────────┘
```

## Error Handling Flow

```
                     ANY TASK FAILS
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   Automatic Retry Mechanism       │
        │   • Attempt 1: Immediate          │
        │   • Attempt 2: +5 minutes         │
        │   • Attempt 3: +10 minutes        │
        │   (Exponential backoff)           │
        └───────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌───────────┐           ┌─────────────┐
        │  SUCCESS  │           │   FAILURE   │
        │  (Retry   │           │   (After 2  │
        │   worked) │           │   retries)  │
        └─────┬─────┘           └──────┬──────┘
              │                        │
              ▼                        ▼
    Continue pipeline        ┌──────────────────┐
                             │  notify_failure  │
                             │  • Log details   │
                             │  • Send email    │
                             │  • Stop pipeline │
                             └──────────────────┘
```

## Scheduling Timeline

```
Daily Schedule: 0 2 * * * (2 AM UTC)

┌────────────────────────────────────────────────────────────────┐
│                    24-Hour Timeline                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  00:00                12:00                23:59                │
│    │                    │                    │                  │
│    ▼         02:00      ▼                    ▼                  │
│    │           ★        │                    │                  │
│    │      [Pipeline     │                    │                  │
│    │       Executes]    │                    │                  │
│    │           │        │                    │                  │
│    │           ▼        │                    │                  │
│    │      02:00-02:15   │                    │                  │
│    │      (Typical      │                    │                  │
│    │       duration:    │                    │                  │
│    │       10-15 min)   │                    │                  │
│    │                    │                    │                  │
│    └────────────────────┴────────────────────┘                  │
│                                                                 │
│  ★ = Pipeline Start Time (2 AM UTC)                            │
│                                                                 │
│  Why 2 AM?                                                      │
│  • Off-peak hours (low system load)                            │
│  • Overnight data loads completed                              │
│  • Results ready for morning business users                    │
│  • Minimal user impact if issues occur                         │
└────────────────────────────────────────────────────────────────┘
```

## Data Quality Gates

```
                    BRONZE LAYER
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Tests: Schema Validation      │
        │  • Unique IDs                  │
        │  • No NULL in required fields  │
        │  • Correct data types          │
        │  • No future dates             │
        └────────────────┬───────────────┘
                         │
                    ✓ PASS │ ✗ FAIL → STOP
                         │
                         ▼
                    SILVER LAYER
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Tests: Business Logic         │
        │  • Foreign key integrity       │
        │  • Positive revenue values     │
        │  • No duplicate orders         │
        │  • Customer-order consistency  │
        └────────────────┬───────────────┘
                         │
                    ✓ PASS │ ✗ FAIL → STOP
                         │
                         ▼
                    GOLD LAYER
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Tests: Metric Validation      │
        │  • Aggregation correctness     │
        │  • KPI thresholds met          │
        │  • Metric calculation accuracy │
        └────────────────┬───────────────┘
                         │
                    ✓ PASS │ ✗ FAIL → STOP
                         │
                         ▼
                  DOCUMENTATION
                         │
                         ▼
                     SUCCESS ✓
```

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Docker Environment                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  sqlserver       │         │  postgres        │             │
│  │  (Port 1433)     │◄────────│  (Port 5432)     │             │
│  │                  │         │                  │             │
│  │  AdventureWorks  │         │  Airflow         │             │
│  │  2014 Database   │         │  Metadata DB     │             │
│  └────────┬─────────┘         └────────┬─────────┘             │
│           │                            │                        │
│           │ reads                      │ stores                 │
│           │                            │ state                  │
│           ▼                            ▼                        │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  dbt             │         │  airflow-        │             │
│  │  (Container)     │◄────────│  webserver       │             │
│  │                  │  exec   │  (Port 8080)     │             │
│  │  DBT Models      │         │                  │             │
│  │  + Tests         │         │  Admin UI        │             │
│  └──────────────────┘         └──────────────────┘             │
│           ▲                            │                        │
│           │                            │                        │
│           │ exec commands              │ schedules              │
│           │                            │                        │
│  ┌────────┴───────────────────────────▼──────────┐             │
│  │  airflow-scheduler                            │             │
│  │                                                │             │
│  │  • Executes DAGs on schedule                  │             │
│  │  • Runs tasks via docker exec                 │             │
│  │  • Monitors task status                       │             │
│  │  • Handles retries and failures               │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Container Names:
• dbt_airflow_project-dbt-1 (DBT execution)
• dbt_airflow_project-airflow-webserver-1 (UI)
• dbt_airflow_project-airflow-scheduler-1 (Orchestration)
• dbt_airflow_project-sqlserver-1 (Source DB)
• dbt_airflow_project-postgres-1 (Airflow metadata)
```

## Performance Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    Expected Task Durations                       │
├──────────────────────┬──────────────────┬───────────────────────┤
│ Task                 │ Duration         │ Notes                 │
├──────────────────────┼──────────────────┼───────────────────────┤
│ check_freshness      │ 10-30 sec        │ Quick validation      │
│ dbt_run_bronze       │ 1-3 min          │ Views are fast        │
│ dbt_test_bronze      │ 30 sec           │ Schema tests          │
│ dbt_run_silver       │ 3-5 min          │ Table materialization │
│ dbt_test_silver      │ 1-2 min          │ Business logic tests  │
│ dbt_run_gold         │ 2-4 min          │ Aggregations          │
│ dbt_test_gold        │ 1 min            │ Metric validation     │
│ dbt_generate_docs    │ 30 sec           │ Doc generation        │
│ notify_success       │ <5 sec           │ Notification          │
├──────────────────────┼──────────────────┼───────────────────────┤
│ TOTAL PIPELINE       │ 10-15 min        │ End-to-end            │
└──────────────────────┴──────────────────┴───────────────────────┘

⚠️  If your pipeline takes >20 minutes:
   • Check for data growth (larger tables)
   • Consider incremental models
   • Optimize queries (add indexes)
   • Increase container resources
```

## Quick Access URLs

```
┌─────────────────────────────────────────────────────────────────┐
│  Service                │ URL                                     │
├─────────────────────────┼─────────────────────────────────────────┤
│  Airflow Web UI         │ http://localhost:8080                   │
│  (Credentials)          │ Username: admin / Password: admin       │
│                         │                                         │
│  DBT Docs (after gen)   │ docker-compose exec dbt dbt docs serve  │
│                         │ http://localhost:8081                   │
└─────────────────────────┴─────────────────────────────────────────┘
```

---

**Legend:**
- `│` Pipeline flow
- `▼` Sequential execution
- `◄` Data/command flow
- `✓` Success path
- `✗` Failure path
- `⚠️` Warning/Important
- `★` Scheduled trigger
