# Dimensional Analytics - Star Schema Model

## Overview

Enterprise-grade **dimensional data warehouse** implementing Kimball's star schema methodology. This module transforms Data Vault 2.0 structures into business-optimized fact and dimension tables for high-performance analytical queries and dashboard visualization.

## Architecture

### Star Schema Design

```
┌──────────────────────────────────────────────────────────────────────┐
│                      STAR SCHEMA ARCHITECTURE                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    FACT TABLE (Center)                               │
│            ┌───────────────────────────────┐                         │
│            │   fact_sensor_reading         │                         │
│            │  ─────────────────────────    │                         │
│            │  reading_key (PK)             │                         │
│            │  well_key (FK) ────────┐      │                         │
│            │  sensor_key (FK) ──────┼──┐   │                         │
│            │  time_key (FK) ────────┼──┼─┐ │                         │
│            │  source_key (FK) ──────┼──┼─┼─┤                         │
│            │  depth, amplitude      │  │ │ │                         │
│            │  is_anomaly            │  │ │ │                         │
│            └────────────────────────┘  │ │ │                         │
│                                        │ │ │                         │
│  DIMENSION TABLES (Spokes)             │ │ │                         │
│                                        │ │ │                         │
│  ┌─────────────────┐                  │ │ │                         │
│  │  dim_well       │ ◄────────────────┘ │ │                         │
│  │  ─────────────  │                    │ │                         │
│  │  well_key (PK)  │                    │ │                         │
│  │  well_id        │                    │ │                         │
│  │  well_name      │                    │ │                         │
│  │  latitude       │                    │ │                         │
│  │  longitude      │                    │ │                         │
│  └─────────────────┘                    │ │                         │
│                                         │ │                         │
│  ┌─────────────────┐                   │ │                         │
│  │  dim_sensor     │ ◄─────────────────┘ │                         │
│  │  ─────────────  │                     │                         │
│  │  sensor_key(PK) │                     │                         │
│  │  sensor_id      │                     │                         │
│  │  sensor_type    │                     │                         │
│  │  manufacturer   │                     │                         │
│  └─────────────────┘                     │                         │
│                                          │                         │
│  ┌─────────────────┐                    │                         │
│  │  dim_time       │ ◄──────────────────┘                         │
│  │  ─────────────  │                                              │
│  │  time_key (PK)  │                                              │
│  │  full_date      │                                              │
│  │  year, quarter  │                                              │
│  │  month, day     │                                              │
│  └─────────────────┘                                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Fact Tables

#### fact_sensor_reading

**Grain**: One row per seismic sensor measurement

```sql
CREATE TABLE fact_sensor_reading (
    reading_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_key INTEGER NOT NULL,
    sensor_key INTEGER NOT NULL,
    time_key INTEGER NOT NULL,
    source_key INTEGER NOT NULL,
    timestamp DATETIME,
    depth REAL,
    amplitude REAL,
    frequency REAL,
    phase REAL,
    quality_flag INTEGER,
    is_anomaly INTEGER,
    data_quality_score REAL,
    FOREIGN KEY (well_key) REFERENCES dim_well(well_key),
    FOREIGN KEY (sensor_key) REFERENCES dim_sensor(sensor_key),
    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (source_key) REFERENCES dim_data_source(source_key)
);
```

**Indexes**:
- `idx_fact_well` ON (well_key)
- `idx_fact_sensor` ON (sensor_key)
- `idx_fact_time` ON (time_key)
- `idx_fact_anomaly` ON (is_anomaly)

#### fact_survey_event

**Grain**: One row per survey execution

```sql
CREATE TABLE fact_survey_event (
    event_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_key INTEGER NOT NULL,
    time_key INTEGER NOT NULL,
    source_key INTEGER NOT NULL,
    survey_id VARCHAR(50),
    survey_type VARCHAR(100),
    survey_start_date DATE,
    survey_end_date DATE,
    total_readings INTEGER,
    avg_amplitude REAL,
    data_quality_rate REAL,
    FOREIGN KEY (well_key) REFERENCES dim_well(well_key)
);
```

---

### Dimension Tables

#### dim_well (SCD Type 2)

**Business Key**: well_id

```sql
CREATE TABLE dim_well (
    well_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id VARCHAR(50) NOT NULL,
    well_name VARCHAR(100),
    latitude REAL,
    longitude REAL,
    basin VARCHAR(100),
    field VARCHAR(100),
    operator VARCHAR(100),
    spud_date DATE,
    completion_date DATE,
    well_status VARCHAR(50),
    total_depth REAL,
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_current INTEGER DEFAULT 1,
    UNIQUE(well_id, effective_date)
);
```

**SCD Type 2 Example**:
```
well_key | well_id | operator | effective_date | is_current
---------|---------|----------|----------------|------------
1        | W-001   | SOCAR    | 2020-01-01     | 0
2        | W-001   | BP       | 2023-05-15     | 1
```

#### dim_sensor (SCD Type 2)

```sql
CREATE TABLE dim_sensor (
    sensor_key INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    installation_date DATE,
    calibration_date DATE,
    sensor_status VARCHAR(50),
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_current INTEGER DEFAULT 1
);
```

#### dim_time (Pre-populated)

```sql
CREATE TABLE dim_time (
    time_key INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    week_of_year INTEGER,
    is_weekend INTEGER
);
```

**Date Range**: 1990-01-01 to 2030-12-31 (14,975 rows)

#### dim_data_source

```sql
CREATE TABLE dim_data_source (
    source_key INTEGER PRIMARY KEY AUTOINCREMENT,
    source_format VARCHAR(50),
    source_type VARCHAR(50),
    file_extension VARCHAR(10)
);
```

**Pre-populated Values**:
```
source_key | source_format | source_type | file_extension
-----------|---------------|-------------|---------------
1          | CSV           | Flat File   | .csv
2          | JSON          | Structured  | .json
3          | Parquet       | Columnar    | .parquet
4          | SEGY          | Seismic     | .segy
5          | SGX           | Legacy      | .sgx
```

---

## Data Marts

### mart_well_performance

Business-optimized view for well analytics.

```sql
CREATE VIEW mart_well_performance AS
SELECT 
    w.well_id,
    w.well_name,
    w.latitude,
    w.longitude,
    w.basin,
    w.field,
    w.operator,
    s.source_format,
    COUNT(f.reading_key) as total_readings,
    AVG(f.amplitude) as avg_amplitude,
    STDDEV(f.amplitude) as std_amplitude,
    AVG(f.data_quality_score) as data_quality_rate,
    SUM(f.is_anomaly) as anomaly_count,
    MIN(f.depth) as min_depth,
    MAX(f.depth) as max_depth
FROM fact_sensor_reading f
JOIN dim_well w ON f.well_key = w.well_key
JOIN dim_data_source s ON f.source_key = s.source_key
WHERE w.is_current = 1
GROUP BY w.well_id, w.well_name, w.latitude, w.longitude, s.source_format;
```

### mart_sensor_analysis

```sql
CREATE VIEW mart_sensor_analysis AS
SELECT 
    s.sensor_id,
    s.sensor_type,
    s.manufacturer,
    s.model,
    COUNT(f.reading_key) as total_measurements,
    AVG(f.amplitude) as avg_amplitude,
    AVG(f.frequency) as avg_frequency,
    AVG(f.data_quality_score) as avg_quality,
    SUM(f.is_anomaly) as anomaly_count
FROM fact_sensor_reading f
JOIN dim_sensor s ON f.sensor_key = s.sensor_key
WHERE s.is_current = 1
GROUP BY s.sensor_id, s.sensor_type, s.manufacturer, s.model;
```

### mart_survey_summary

```sql
CREATE VIEW mart_survey_summary AS
SELECT 
    se.survey_id,
    se.survey_type,
    w.well_name,
    se.survey_start_date,
    se.survey_end_date,
    se.total_readings,
    se.avg_amplitude,
    se.data_quality_rate
FROM fact_survey_event se
JOIN dim_well w ON se.well_key = w.well_key
WHERE w.is_current = 1;
```

---

## ETL Process

### Execution Flow

```bash
cd track_3_analytics/dimensional_model
python3 run_etl.py
```

#### Step 1: Initialize Database (`run_etl.py`)

Executes SQL DDL scripts:
- `create_dimensions.sql`
- `create_facts.sql`
- `create_data_marts.sql`

#### Step 2: Load Dimensions (`etl/etl_dimensions.py`)

```
Sources → Dimensions
─────────────────────
master_wells.csv      → dim_well
master_sensors.csv    → dim_sensor
Generated (1990-2030) → dim_time
Hardcoded values      → dim_data_source
```

#### Step 3: Load Facts (`etl/etl_facts.py`)

```
Sources → Facts
──────────────────────────────────
vault/sat_seismic_measurements → fact_sensor_reading
Aggregated readings            → fact_survey_event
```

#### Step 4: Export Data Marts (`etl/etl_data_marts.py`)

```
Views → CSV Files
───────────────────────────────────────────
mart_well_performance → mart_well_performance.csv
mart_sensor_analysis  → mart_sensor_analysis.csv
mart_survey_summary   → mart_survey_summary.csv
```

**Output Location**: `track_3_analytics/dashboard/data_marts/`

---

## Anomaly Detection

### Statistical Methods

#### Method 1: Z-Score (Standard Deviation)

```python
mean_amp = df['amplitude'].mean()
std_amp = df['amplitude'].std()

df['z_score'] = abs((df['amplitude'] - mean_amp) / std_amp)
df['is_anomaly'] = (df['z_score'] > 2.5).astype(int)
```

**Threshold**: 2.5 standard deviations from mean

#### Method 2: IQR (Interquartile Range)

```python
Q1 = df['amplitude'].quantile(0.25)
Q3 = df['amplitude'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

df['is_anomaly'] = ((df['amplitude'] < lower_bound) | 
                     (df['amplitude'] > upper_bound)).astype(int)
```

**Execution**:
```bash
cd etl
python3 detect_anomalies.py
```

**Output**:
- Updates `fact_sensor_reading.is_anomaly`
- Generates anomaly statistics

---

## Query Examples

### Example 1: Well Performance KPIs

```sql
SELECT 
    well_name,
    total_readings,
    avg_amplitude,
    anomaly_count,
    ROUND(anomaly_count * 100.0 / total_readings, 2) as anomaly_rate_pct
FROM mart_well_performance
ORDER BY total_readings DESC
LIMIT 10;
```

### Example 2: Time-Series Analysis

```sql
SELECT 
    t.year,
    t.month,
    COUNT(f.reading_key) as monthly_readings,
    AVG(f.amplitude) as avg_amplitude
FROM fact_sensor_reading f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.year, t.month
ORDER BY t.year, t.month;
```

### Example 3: Sensor Reliability

```sql
SELECT 
    sensor_id,
    sensor_type,
    manufacturer,
    AVG(avg_quality) as reliability_score,
    anomaly_count
FROM mart_sensor_analysis
ORDER BY reliability_score DESC;
```

---

## Performance Tuning

### Indexing Strategy

```sql
-- Fact table indexes (covering common queries)
CREATE INDEX idx_fact_well_time ON fact_sensor_reading(well_key, time_key);
CREATE INDEX idx_fact_sensor_depth ON fact_sensor_reading(sensor_key, depth);

-- Dimension indexes (SCD lookups)
CREATE INDEX idx_dim_well_current ON dim_well(well_id, is_current);
CREATE INDEX idx_dim_sensor_current ON dim_sensor(sensor_id, is_current);
```

### Query Optimization Tips

**1. Filter on Indexed Columns**
```sql
-- Good: Uses index
WHERE well_key = 123 AND is_current = 1

-- Bad: Full table scan
WHERE well_name LIKE '%ABC%'
```

**2. Use Data Marts**
```sql
-- Good: Pre-aggregated
SELECT * FROM mart_well_performance WHERE well_id = 12345;

-- Bad: Aggregating at runtime
SELECT well_id, AVG(amplitude) FROM fact_sensor_reading GROUP BY well_id;
```

**3. Partition Large Facts**
```sql
-- Partition by year for time-series queries
CREATE TABLE fact_sensor_reading_2024 AS 
SELECT * FROM fact_sensor_reading WHERE year = 2024;
```

---

## Data Quality Metrics

### Completeness

```sql
SELECT 
    'fact_sensor_reading' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN depth IS NULL THEN 1 ELSE 0 END) as null_depth,
    SUM(CASE WHEN amplitude IS NULL THEN 1 ELSE 0 END) as null_amplitude,
    AVG(data_quality_score) as avg_quality_score
FROM fact_sensor_reading;
```

### Referential Integrity

```sql
-- Check for orphaned facts (should return 0)
SELECT COUNT(*) as orphaned_facts
FROM fact_sensor_reading f
LEFT JOIN dim_well w ON f.well_key = w.well_key
WHERE w.well_key IS NULL;
```

---

## Deployment

### SQLite (Development)

```bash
# Database file
dimensional_model.db

# Size: ~50MB for 500K facts
```

### PostgreSQL (Production)

```sql
-- Export to PostgreSQL
pg_restore --host=postgres --port=5432 --username=admin   --dbname=dimensional_analytics dimensional_model.dump
```

---

## Monitoring

### Row Counts

```bash
sqlite3 dimensional_model.db "SELECT 
  'dim_well', COUNT(*) FROM dim_well UNION ALL
  SELECT 'dim_sensor', COUNT(*) FROM dim_sensor UNION ALL
  SELECT 'fact_sensor_reading', COUNT(*) FROM fact_sensor_reading;"
```

### Data Freshness

```sql
SELECT 
    MAX(load_timestamp) as last_load_time,
    JULIANDAY('now') - JULIANDAY(MAX(load_timestamp)) as days_since_load
FROM (
    SELECT load_timestamp FROM fact_sensor_reading
    UNION ALL
    SELECT effective_date FROM dim_well WHERE is_current = 1
);
```

---

## Troubleshooting

### Issue: Foreign Key Violations

```bash
# Enable foreign key constraints
sqlite3 dimensional_model.db "PRAGMA foreign_keys = ON;"

# Check for violations
sqlite3 dimensional_model.db ".lint fkey-indexes"
```

### Issue: Duplicate Dimension Keys

```sql
-- Find duplicates
SELECT well_id, COUNT(*) 
FROM dim_well 
WHERE is_current = 1 
GROUP BY well_id 
HAVING COUNT(*) > 1;
```

---

## Best Practices

1. **Always Use Surrogate Keys**: Never expose natural keys as foreign keys
2. **SCD Type 2 for Dimensions**: Track historical changes
3. **Pre-Aggregate in Data Marts**: Optimize dashboard queries
4. **Index Foreign Keys**: Essential for join performance
5. **Regular Vacuum**: Reclaim space after large deletes

---

## References

- Ralph Kimball, *The Data Warehouse Toolkit*
- Dimensional Modeling Best Practices
- SQLite Performance Tuning Guide

---

## License

MIT License - Part of Drillica Platform
