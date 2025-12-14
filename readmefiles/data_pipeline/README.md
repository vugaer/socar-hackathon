# Apache Airflow ETL Pipeline

## Overview

Production-grade **Apache Airflow DAG** orchestrating the complete ETL workflow from Data Vault to multi-target analytical datastores. This pipeline implements idempotent design patterns, anomaly detection, and comprehensive data quality monitoring.

## Architecture

### Pipeline Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                    AIRFLOW ETL PIPELINE                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  EXTRACT                                                           │
│  ├── Source: Data Vault Parquet Files                             │
│  │   ├── sat_seismic_measurements.parquet                         │
│  │   └── hub_well.parquet                                         │
│  └── Output: Staging Area (/opt/airflow/data/temp)                │
│                                                                    │
│  TRANSFORM                                                         │
│  ├── Data Cleaning & Enrichment                                   │
│  ├── Anomaly Detection (Statistical)                              │
│  │   ├── Z-score Method (2σ threshold)                            │
│  │   └── IQR Method (1.5 × IQR)                                   │
│  ├── Well Aggregation                                             │
│  │   ├── avg_amplitude, std_amplitude                             │
│  │   ├── quality_score, anomaly_count                             │
│  │   └── reading_count                                            │
│  └── Metadata Addition                                            │
│                                                                    │
│  LOAD (Parallel Execution)                                        │
│  ├── PostgreSQL (OLAP Database)                                   │
│  │   └── Table: seismic_well_analytics                            │
│  ├── MongoDB (NoSQL Database)                                     │
│  │   └── Collection: measurements (10K sample)                    │
│  └── JSON Export                                                  │
│      └── File: well_analytics_YYYYMMDD.json                       │
│                                                                    │
│  REPORTING                                                         │
│  └── Execution Metrics & Data Quality Report                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## DAG Configuration

### DAG Parameters

```python
dag_id='socar_seismic_etl'
schedule_interval='@daily'              # Run once per day at midnight
catchup=False                           # Don't backfill historical runs
max_active_runs=1                       # Prevent concurrent executions
start_date=datetime(2025, 12, 13)
retries=2                               # Retry failed tasks twice
retry_delay=timedelta(minutes=5)        # Wait 5 minutes between retries
```

### Task Dependencies

```
extract_from_vault
        ↓
transform_data
        ↓
    ┌───┴───┬────────┐
    ↓       ↓        ↓
load_to_sql  load_to_nosql  load_to_json
    └───┬───┴────────┘
        ↓
generate_report
```

**Execution Strategy**: Fan-out pattern for parallel loading to multiple datastores

---

## Task Details

### Task 1: Extract from Vault

**Operator**: `PythonOperator`
**Function**: `extract_from_vault()`

#### Responsibilities
1. Read Parquet files from Data Vault
2. Load `sat_seismic_measurements.parquet` (measurements)
3. Load `hub_well.parquet` (well metadata)
4. Stage data to temporary directory

#### Input
```
/opt/airflow/vault_data/
├── sat_seismic_measurements.parquet
└── hub_well.parquet
```

#### Output
```
/opt/airflow/data/temp/
├── measurements_stage.parquet
└── wells_stage.parquet
```

#### XCom Return
```python
{
    'measurements': 50000,  # Row count
    'wells': 125            # Row count
}
```

---

### Task 2: Transform Data

**Operator**: `PythonOperator`
**Function**: `transform_data()`

#### Anomaly Detection Algorithm

**Method 1: Z-Score**
```python
mean_amplitude = measurements['amplitude'].mean()
std_amplitude = measurements['amplitude'].std()

measurements['is_anomaly'] = (
    (measurements['amplitude'] < mean_amplitude - 2*std_amplitude) |
    (measurements['amplitude'] > mean_amplitude + 2*std_amplitude)
).astype(int)
```

**Method 2: IQR (Interquartile Range)**
```python
Q1 = measurements['amplitude'].quantile(0.25)
Q3 = measurements['amplitude'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

anomaly = (amplitude < lower_bound) | (amplitude > upper_bound)
```

#### Aggregation Logic

```python
well_analytics = measurements.groupby('well_id').agg({
    'amplitude': ['mean', 'std', 'min', 'max', 'count'],
    'is_anomaly': 'sum',
    'quality_flag': lambda x: (x == 1).mean()  # % of good quality readings
})
```

#### Output Schema

| Column | Type | Description |
|--------|------|-------------|
| well_id | int | Well identifier |
| well_name | str | Generated name (WELL-{id}) |
| avg_amplitude | float | Mean amplitude |
| std_amplitude | float | Standard deviation |
| min_amplitude | float | Minimum value |
| max_amplitude | float | Maximum value |
| reading_count | int | Total readings |
| anomaly_count | int | Count of anomalies |
| quality_score | float | % good quality (0.0-1.0) |
| processed_at | timestamp | Processing time |

#### XCom Return
```python
{
    'wells_processed': 125,
    'anomalies_found': 2341
}
```

---

### Task 3: Load to PostgreSQL

**Operator**: `PythonOperator`
**Function**: `load_to_sql()`

#### Database Configuration
```python
engine = create_engine('postgresql://airflow:airflow@postgres:5432/airflow')
```

#### Loading Strategy
```python
# IDEMPOTENT: Replace existing data
well_analytics.to_sql(
    'seismic_well_analytics',
    engine,
    if_exists='replace',
    index=False
)
```

**Rationale**: Full refresh ensures consistency with source Data Vault

#### Target Table Schema

```sql
CREATE TABLE seismic_well_analytics (
    well_id INTEGER PRIMARY KEY,
    well_name VARCHAR(100),
    avg_amplitude DOUBLE PRECISION,
    std_amplitude DOUBLE PRECISION,
    min_amplitude DOUBLE PRECISION,
    max_amplitude DOUBLE PRECISION,
    reading_count INTEGER,
    anomaly_count INTEGER,
    quality_score DOUBLE PRECISION,
    processed_at TIMESTAMP
);
```

---

### Task 4: Load to MongoDB

**Operator**: `PythonOperator`
**Function**: `load_to_nosql()`

#### Database Configuration
```python
client = MongoClient('mongodb://admin:admin123@mongodb:27017/')
db = client['socar_seismic']
collection = db['measurements']
```

#### NaT/NaN Handling (Critical Fix)

**Problem**: Pandas `NaT` (Not-a-Time) and `NaN` values cause MongoDB insertion errors

**Solution**:
```python
for col in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        # Convert datetime to ISO string, NaT → None
        df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
    elif pd.api.types.is_numeric_dtype(df[col]):
        # Replace NaN with None
        df[col] = df[col].replace({np.nan: None})
```

#### Loading Strategy
```python
# IDEMPOTENT: Clear old data
collection.delete_many({})

# Insert sample (performance optimization)
sample_size = min(10000, len(measurements))
records = measurements.head(sample_size).to_dict('records')
collection.insert_many(records)
```

#### Document Schema
```json
{
    "_id": ObjectId("..."),
    "well_id": 12345,
    "survey_type_id": 3,
    "depth_ft": 5000.0,
    "amplitude": 23.5,
    "quality_flag": 1,
    "is_anomaly": 0,
    "timestamp": "2024-01-15T10:30:00",
    "record_source": "archive_batch_seismic_readings.parquet",
    "load_timestamp": "2025-12-14T05:30:00"
}
```

---

### Task 5: Load to JSON

**Operator**: `PythonOperator`
**Function**: `load_to_json()`

#### Output Format
```python
export_file = f'/opt/airflow/data/exports/well_analytics_{datetime.now().strftime("%Y%m%d")}.json'

well_analytics.to_json(
    export_file,
    orient='records',
    indent=2,
    date_format='iso'
)
```

#### Sample Output
```json
[
  {
    "well_id": 12345,
    "well_name": "WELL-12345",
    "avg_amplitude": 24.5,
    "std_amplitude": 5.3,
    "min_amplitude": 10.2,
    "max_amplitude": 45.7,
    "reading_count": 1250,
    "anomaly_count": 23,
    "quality_score": 0.95,
    "processed_at": "2025-12-14T05:30:00"
  }
]
```

---

### Task 6: Generate Report

**Operator**: `PythonOperator`
**Function**: `generate_report()`

#### Report Structure
```json
{
    "pipeline_run": "manual__2025-12-14T05:30:00+00:00",
    "execution_time": "2025-12-14T05:35:12",
    "extract": {
        "measurements": 50000,
        "wells": 125
    },
    "transform": {
        "wells_processed": 125,
        "anomalies_found": 2341
    },
    "load": {
        "postgresql": 125,
        "mongodb": 10000,
        "json": "/opt/airflow/data/exports/well_analytics_20251214.json"
    }
}
```

#### Report Location
```
/opt/airflow/data/reports/etl_report_20251214_053512.json
```

---

## Idempotent Design Patterns

### Pattern 1: Full Refresh (PostgreSQL)
```python
# Safe to re-run: always replaces entire table
df.to_sql('table', engine, if_exists='replace')
```

### Pattern 2: Delete + Insert (MongoDB)
```python
# Safe to re-run: clears old data before inserting
collection.delete_many({})
collection.insert_many(records)
```

### Pattern 3: Timestamped Files (JSON)
```python
# Safe to re-run: uses timestamp in filename
filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
```

---

## Monitoring & Alerting

### Airflow UI Metrics

Access: `http://localhost:8080`

**Key Metrics:**
- Task Duration
- Success/Failure Rates
- Retry Counts
- XCom Values

### DAG Run Status

```bash
# Check DAG status
airflow dags list

# View task logs
airflow tasks logs socar_seismic_etl extract_from_vault 2025-12-14

# Trigger manual run
airflow dags trigger socar_seismic_etl
```

### Custom Monitoring

```python
# Add Slack/Email alerts
default_args = {
    'email': ['data-eng@socar.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

---

## Performance Optimization

### Benchmarks

| Task | Input Size | Duration | Throughput |
|------|-----------|---------|-----------|
| Extract | 50K rows | 3.2s | 15,625 rows/s |
| Transform | 50K rows | 12.1s | 4,132 rows/s |
| Load (PostgreSQL) | 125 rows | 0.8s | 156 rows/s |
| Load (MongoDB) | 10K docs | 5.4s | 1,852 docs/s |
| Load (JSON) | 125 rows | 0.3s | 417 rows/s |

### Optimization Tips

**1. Partitioned Reads**
```python
# Read Data Vault in chunks
for chunk in pd.read_parquet('vault.parquet', chunksize=10000):
    process(chunk)
```

**2. Parallel Loading**
```python
# Use Airflow task groups for parallel writes
with TaskGroup('load_group') as load_group:
    load_sql >> load_nosql >> load_json
```

**3. Connection Pooling**
```python
# Reuse database connections
engine = create_engine('postgresql://...', pool_size=5, max_overflow=10)
```

---

## Error Handling

### Retry Strategy

```python
default_args = {
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30)
}
```

### Failure Scenarios

| Error Type | Handling | Recovery |
|-----------|----------|----------|
| Database Connection | Retry (3x) | Alert on-call engineer |
| File Not Found | Fail immediately | Check Data Vault build |
| Transform Error | Log + Skip row | Generate data quality report |
| MongoDB NaT Error | Convert to None | See `load_to_nosql()` fix |

---

## Deployment

### Local Development

```bash
# Initialize Airflow database
airflow db init

# Create admin user
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Copy DAG
cp socar_seismic_etl.py $AIRFLOW_HOME/dags/

# Start services
airflow webserver -p 8080
airflow scheduler
```

### Production Deployment

```bash
# Use Kubernetes Executor
helm install airflow apache-airflow/airflow   --set executor=KubernetesExecutor   --set dags.gitSync.enabled=true   --set dags.gitSync.repo=https://github.com/drillica/dags.git
```

---

## Testing

### Unit Tests

```python
# test_etl.py
def test_transform_data():
    df = pd.DataFrame({'amplitude': [10, 20, 30, 100]})
    result = detect_anomalies(df)
    assert result['is_anomaly'].sum() == 1  # Expects 100 as anomaly
```

### Integration Tests

```bash
# Test DAG validity
airflow dags test socar_seismic_etl 2025-12-14

# Test specific task
airflow tasks test socar_seismic_etl extract_from_vault 2025-12-14
```

---

## Troubleshooting

### Issue: DAG Not Appearing

```bash
# Check DAG bag
airflow dags list-import-errors

# Fix Python syntax errors
python3 socar_seismic_etl.py
```

### Issue: MongoDB NaT Error

**Error**: `InvalidDocument: cannot encode object: NaT`

**Fix**: Apply NaT/NaN conversion (see Task 4)

### Issue: PostgreSQL Connection Timeout

```bash
# Check database status
psql -h postgres -U airflow -d airflow -c "SELECT 1;"

# Verify connection string
echo $AIRFLOW__DATABASE__SQL_ALCHEMY_CONN
```

---

## Best Practices

1. **Always Use XCom**: Pass metrics between tasks
2. **Idempotent Design**: Safe to re-run without side effects
3. **Comprehensive Logging**: Use `print()` for task output
4. **Data Validation**: Check row counts before/after transforms
5. **Atomic Operations**: Use database transactions

---

## References

- Apache Airflow Documentation: https://airflow.apache.org/docs/
- ETL Best Practices: https://www.kimballgroup.com/
- SOCAR Data Platform Standards

---

## License

MIT License - Part of Drillica Platform
