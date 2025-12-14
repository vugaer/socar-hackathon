# Data Vault 2.0 - Enterprise Data Warehouse

## Overview

This module implements **Data Vault 2.0** methodology for seismic data warehousing, providing a scalable, auditable, and agile foundation for enterprise analytics. The architecture follows Dan Linstedt's best practices with hash-key based referential integrity and full historicization.

## Architecture

### Data Vault Components

```
┌──────────────────────────────────────────────────────────────────┐
│                   DATA VAULT 2.0 ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HUB TABLES (Business Keys)                                     │
│  ├── hub_well          → well_id (business key)                 │
│  ├── hub_survey        → survey_type_id (business key)          │
│  └── hub_sensor        → sensor_id (business key)               │
│                                                                  │
│  LINK TABLES (Relationships)                                    │
│  └── link_seismic_reading  → (well + survey + sensor)           │
│                                                                  │
│  SATELLITE TABLES (Descriptive Attributes)                      │
│  ├── sat_well_details          → Well metadata                  │
│  ├── sat_survey_details        → Survey metadata                │
│  ├── sat_sensor_details        → Sensor metadata                │
│  └── sat_seismic_measurements  → Actual seismic readings        │
│                                                                  │
│  METADATA (Audit Columns)                                       │
│  ├── load_timestamp    → ETL execution time                     │
│  ├── record_source     → Source file/system                     │
│  └── hash_diff         → Change detection hash                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Vault Entities

### Hub Tables

Hubs store unique business keys with hash-key surrogate identifiers.

#### hub_well
```sql
Columns:
- well_hash_key       : MD5(WELL|well_id)
- well_id             : Business key
- load_timestamp      : Load time
- record_source       : Source system

Grain: One row per unique well
Primary Key: well_hash_key
Business Key: well_id
```

#### hub_survey
```sql
Columns:
- survey_hash_key     : MD5(SURVEY|survey_type_id)
- survey_type_id      : Business key
- load_timestamp      : Load time
- record_source       : Source system

Grain: One row per unique survey type
Primary Key: survey_hash_key
Business Key: survey_type_id
```

#### hub_sensor
```sql
Columns:
- sensor_hash_key     : MD5(SENSOR|sensor_id)
- sensor_id           : Business key
- load_timestamp      : Load time
- record_source       : Source system

Grain: One row per unique sensor
Primary Key: sensor_hash_key
Business Key: sensor_id
```

---

### Link Tables

Links establish many-to-many relationships between hubs.

#### link_seismic_reading
```sql
Columns:
- link_hash_key       : MD5(READING|well_id|survey_type_id|sensor_id|timestamp)
- well_hash_key       : FK → hub_well
- survey_hash_key     : FK → hub_survey
- sensor_hash_key     : FK → hub_sensor (nullable for SGX data)
- load_timestamp      : Load time
- record_source       : Source file

Grain: One row per unique seismic reading event
Primary Key: link_hash_key
Foreign Keys: well_hash_key, survey_hash_key, sensor_hash_key
```

**Business Rules:**
- SGX files → sensor_hash_key = NULL (no sensor tracking)
- Archive files → sensor_hash_key populated

---

### Satellite Tables

Satellites store descriptive attributes with full history tracking.

#### sat_well_details
```sql
Columns:
- well_hash_key       : FK → hub_well
- well_id             : Natural key
- well_name           : Well name
- latitude            : Geographic coordinate
- longitude           : Geographic coordinate
- basin               : Basin name
- field               : Field name
- operator            : Operator company
- spud_date           : Spud date
- completion_date     : Completion date
- well_status         : Current status
- total_depth         : Total depth (ft)
- load_timestamp      : Load time
- record_source       : Source file
- hash_diff           : MD5 of all descriptive attributes

Grain: One row per well per change
Primary Key: (well_hash_key, load_timestamp)
```

#### sat_seismic_measurements
```sql
Columns:
- link_hash_key       : FK → link_seismic_reading
- timestamp           : Measurement timestamp
- depth_ft            : Depth (feet)
- amplitude           : Seismic amplitude
- frequency           : Frequency (Hz)
- phase               : Phase angle
- quality_flag        : Quality indicator (0=poor, 1=good)
- load_timestamp      : Load time
- record_source       : Source file
- hash_diff           : MD5(depth|amplitude|quality)

Grain: One row per seismic measurement
Primary Key: (link_hash_key, load_timestamp)
```

---

## Hash Key Generation

### Algorithm

```python
import hashlib

def generate_hash_key(*values):
    """Generate MD5 hash key for Data Vault"""
    combined = '|'.join(str(v) for v in values)
    return hashlib.md5(combined.encode()).hexdigest()

# Examples
well_hash_key = generate_hash_key('WELL', 12345)
# Output: 'a1b2c3d4e5f6...' (32-character hex string)

link_hash_key = generate_hash_key('READING', well_id, survey_id, sensor_id, timestamp)
```

### Hash Key Standards

| Entity | Hash Key Format | Example |
|--------|----------------|---------|
| Well | `MD5(WELL|well_id)` | `MD5(WELL|12345)` |
| Survey | `MD5(SURVEY|survey_type_id)` | `MD5(SURVEY|3)` |
| Sensor | `MD5(SENSOR|sensor_id)` | `MD5(SENSOR|SEN-001)` |
| Reading | `MD5(READING|well|survey|sensor|time)` | `MD5(READING|12345|3|SEN-001|2024-01-01)` |

---

## ETL Process

### Build Script (`build_data_vault.py`)

```bash
cd track_2_data_vault/scripts
python3 build_data_vault.py
```

#### Execution Flow

```
Step 1: Load Master Data
  ├── master_wells.csv    → hub_well + sat_well_details
  ├── master_surveys.csv  → hub_survey + sat_survey_details
  └── master_sensors.csv  → hub_sensor + sat_sensor_details

Step 2: Load Seismic Data
  ├── solutions/tmp/*.parquet → link_seismic_reading
  └── solutions/tmp/*.parquet → sat_seismic_measurements

Step 3: Verify Integrity
  ├── Check hash key uniqueness
  ├── Validate foreign key references
  └── Confirm metadata presence
```

#### Source Data Mapping

| Source File | Target Table | Mapping |
|------------|-------------|---------|
| `master_wells.csv` | `hub_well` | well_id → well_hash_key |
| `master_wells.csv` | `sat_well_details` | All columns + hash_diff |
| `archive*.parquet` | `link_seismic_reading` | well_id + survey_type_id + sensor_id |
| `archive*.parquet` | `sat_seismic_measurements` | depth_ft, amplitude, quality_flag |
| `all_legacy*.parquet` | `link_seismic_reading` | well_id + survey_type_id (NO sensor) |

---

## Data Quality Tests

### Test Suite (`data_quality_tests.py`)

```bash
cd track_2_data_vault/tests
python3 data_quality_tests.py
```

#### Test Categories

**1. Uniqueness Tests**
- ✅ Hub hash keys must be unique
- ✅ Business keys must be unique within hubs

**2. Referential Integrity Tests**
- ✅ Link → Hub foreign keys must exist
- ✅ Satellite → Link foreign keys must exist

**3. Completeness Tests**
- ✅ Critical fields (depth, amplitude, quality_flag) must not be NULL
- ✅ Metadata columns (load_timestamp, record_source) must exist

**4. Format Tests**
- ✅ Hash keys must match MD5 format (32 hex characters)
- ✅ Timestamps must be valid ISO 8601

**5. Business Rule Tests**
- ✅ SGX data: sensor_hash_key = NULL allowed
- ✅ Archive data: sensor_hash_key must exist
- ✅ Quality flag ∈ {0, 1}

#### Example Test Output

```
======================================================================
TEST 1: Hub Hash Key Uniqueness
======================================================================

✅ PASS | hub_well - Hash Key Uniqueness
   All hash keys are unique
   - total_records: 125
   - unique_keys: 125
   - duplicates: 0

✅ PASS | hub_survey - Hash Key Uniqueness
   All hash keys are unique
   - total_records: 3
   - unique_keys: 3
   - duplicates: 0

======================================================================
TEST 3: Referential Integrity
======================================================================

✅ PASS | Link → Hub_Well Integrity
   All well references are valid
   - link_records: 50000
   - valid_references: 50000
   - orphaned_references: 0
```

---

## Storage Format

### Parquet Configuration

```python
# Optimized for analytical queries
compression='snappy'         # Balance between speed and size
row_group_size=100000        # Optimize for 100K row scans
schema_version='2.6'         # Latest Parquet schema
```

### File Structure

```
track_2_data_vault/vault_data/
├── hub_well.parquet               # ~5KB (125 rows)
├── hub_survey.parquet             # ~1KB (3 rows)
├── hub_sensor.parquet             # ~3KB (10 rows)
├── sat_well_details.parquet       # ~25KB (125 rows × 15 cols)
├── sat_survey_details.parquet     # ~2KB (3 rows × 10 cols)
├── sat_sensor_details.parquet     # ~5KB (10 rows × 12 cols)
├── link_seismic_reading.parquet   # ~2.5MB (50K links)
└── sat_seismic_measurements.parquet  # ~15MB (50K measurements × 8 cols)
```

---

## Query Patterns

### Pattern 1: Hub Lookup

```python
import pandas as pd

# Get well metadata
hub_well = pd.read_parquet('vault_data/hub_well.parquet')
sat_well = pd.read_parquet('vault_data/sat_well_details.parquet')

well_info = hub_well.merge(sat_well, on='well_hash_key')
print(well_info[['well_id', 'well_name', 'latitude', 'longitude']])
```

### Pattern 2: Link Traversal

```python
# Get all readings for a specific well
link = pd.read_parquet('vault_data/link_seismic_reading.parquet')
sat_measurements = pd.read_parquet('vault_data/sat_seismic_measurements.parquet')

well_hash = 'a1b2c3...'  # Known well hash key
well_links = link[link['well_hash_key'] == well_hash]

readings = well_links.merge(sat_measurements, on='link_hash_key')
print(readings[['depth_ft', 'amplitude', 'quality_flag']])
```

### Pattern 3: Multi-Hub Join

```python
# Full denormalized view
hub_well = pd.read_parquet('vault_data/hub_well.parquet')
hub_sensor = pd.read_parquet('vault_data/hub_sensor.parquet')
link = pd.read_parquet('vault_data/link_seismic_reading.parquet')
sat_measurements = pd.read_parquet('vault_data/sat_seismic_measurements.parquet')

df = (link
      .merge(hub_well, on='well_hash_key')
      .merge(hub_sensor, on='sensor_hash_key', how='left')
      .merge(sat_measurements, on='link_hash_key'))

print(df[['well_id', 'sensor_id', 'depth_ft', 'amplitude']])
```

---

## Performance Tuning

### Indexing Strategy (if using SQL backend)

```sql
-- Hub indexes
CREATE INDEX idx_well_hash ON hub_well(well_hash_key);
CREATE INDEX idx_well_business_key ON hub_well(well_id);

-- Link indexes
CREATE INDEX idx_link_well ON link_seismic_reading(well_hash_key);
CREATE INDEX idx_link_survey ON link_seismic_reading(survey_hash_key);
CREATE INDEX idx_link_sensor ON link_seismic_reading(sensor_hash_key);

-- Satellite indexes
CREATE INDEX idx_sat_measurement_link ON sat_seismic_measurements(link_hash_key);
CREATE INDEX idx_sat_measurement_time ON sat_seismic_measurements(timestamp);
```

### Partitioning Recommendations

```python
# Partition by load date for incremental loads
df.to_parquet(
    'vault_data/sat_seismic_measurements',
    partition_cols=['load_date'],
    compression='snappy'
)
```

---

## Data Lineage

### Metadata Tracking

Every table includes:
- `load_timestamp`: When data was loaded (ISO 8601)
- `record_source`: Source file/system identifier

```python
# Query lineage
sat = pd.read_parquet('vault_data/sat_seismic_measurements.parquet')
lineage = sat[['record_source', 'load_timestamp']].drop_duplicates()

print("Data Sources:")
print(lineage.groupby('record_source')['load_timestamp'].min())
```

---

## Maintenance

### Incremental Loading

```python
from track_2_data_vault.scripts.build_data_vault import DataVaultBuilder

builder = DataVaultBuilder(source_dir='data', vault_dir='vault_data')

# Load only new files
new_files = ['new_survey_2024.parquet']
for file in new_files:
    seismic_data = pd.read_parquet(file)
    link = builder.build_link_seismic_reading(seismic_data, file)
    sat = builder.build_sat_seismic_measurements(seismic_data, file)

    # Append to existing vault
    builder.save_vault_table(link, 'link_seismic_reading', mode='append')
    builder.save_vault_table(sat, 'sat_seismic_measurements', mode='append')
```

### Historical Tracking

```python
# Track changes to well metadata
sat_well = pd.read_parquet('vault_data/sat_well_details.parquet')

# Get all versions for a specific well
well_history = sat_well[sat_well['well_id'] == 12345].sort_values('load_timestamp')
print(well_history[['well_status', 'operator', 'load_timestamp']])
```

---

## Best Practices

1. **Never Delete Data**: Archive instead of delete
2. **Hash Key Consistency**: Always use same algorithm
3. **Metadata Discipline**: Always populate load_timestamp and record_source
4. **Referential Integrity**: Validate before loading satellites
5. **Idempotent Loads**: Design for safe re-execution

---

## Troubleshooting

### Issue: Duplicate Hash Keys

```python
# Check for duplicates
hub = pd.read_parquet('vault_data/hub_well.parquet')
duplicates = hub[hub.duplicated('well_hash_key', keep=False)]
print(f"Found {len(duplicates)} duplicates")
```

### Issue: Orphaned Links

```python
# Find orphaned links
link = pd.read_parquet('vault_data/link_seismic_reading.parquet')
hub_well = pd.read_parquet('vault_data/hub_well.parquet')

orphans = link[~link['well_hash_key'].isin(hub_well['well_hash_key'])]
print(f"Found {len(orphans)} orphaned links")
```

---

## References

- Dan Linstedt, *Building a Scalable Data Warehouse with Data Vault 2.0*
- SOCAR Data Architecture Standards
- Apache Parquet Format Specification

---

## License

MIT License - Part of Drillica Platform
