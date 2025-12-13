# Data Vault 2.0 Implementation - Seismic Data Warehouse

## Overview

Complete Data Vault 2.0 implementation for storing historical seismic survey data from 1991-1994 and recovered archive data.

**Status:** Complete and Validated
**Total Records:** 18,245 records
**Data Quality:** 100% (30/30 tests passed)

## Architecture

### Hubs (Core Business Entities)

| Hub | Records | Business Key | Hash Key |
|-----|---------|-------------|----------|
| hub_well | 20 | well_id | well_hash_key (MD5) |
| hub_survey | 3 | survey_type_id | survey_hash_key (MD5) |
| hub_sensor | 50 | sensor_id | sensor_hash_key (MD5) |

### Links (Relationships)

| Link | Records | Connects |
|------|---------|----------|
| link_seismic_reading | 7,352 | Well to Survey to Sensor |

### Satellites (Historical Data)

| Satellite | Records | Tracks |
|-----------|---------|--------|
| sat_well_details | 20 | Well attributes |
| sat_survey_details | 3 | Survey metadata |
| sat_sensor_details | 50 | Sensor specifications |
| sat_seismic_measurements | 10,820 | Seismic readings |

## Usage

### Build the Vault

cd ~/socar-hackathon
python3 track_2_data_vault/scripts/build_data_vault.py

text

### Query Example

import pandas as pd

hub_well = pd.read_parquet('track_2_data_vault/vault_data/hub_well.parquet')
sat_measurements = pd.read_parquet('track_2_data_vault/vault_data/sat_seismic_measurements.parquet')
link_reading = pd.read_parquet('track_2_data_vault/vault_data/link_seismic_reading.parquet')

complete = sat_measurements.merge(link_reading, on='link_hash_key').merge(hub_well, on='well_hash_key')
print(f"Total readings: {len(complete)}")

text

## Data Provenance

Every record includes:
- load_timestamp - ISO 8601 ingestion time
- record_source - Original filename
- hash_key - MD5 deterministic identifier
- hash_diff - Change detection hash

## Key Features

- Complete audit trail
- Source tracking on every row
- Immutable business keys
- No information loss
- Referential integrity enforced
- Parallel loading capability
- Incremental updates supported

## Hash Key Generation

import hashlib

hash_key = hashlib.md5(f"WELL|{well_id}".encode()).hexdigest()

text

## Technical Specifications

- Format: Apache Parquet
- Compression: Snappy
- Hash Algorithm: MD5
- Encoding: UTF-8
- Timestamp Format: ISO 8601

Author: SOCAR Hackathon Team
Date: December 13, 2025
Version: 1.0.0
