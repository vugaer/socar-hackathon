#!/bin/bash

echo "=========================================="
echo "  SEISMIC ANALYTICS DIAGNOSTICS"
echo "=========================================="
echo ""

echo "1. CHECK SOURCE DATA FILES"
echo "----------------------------"
echo "Master CSV files:"
ls -lh ../data/master*.csv
echo ""
echo "Vault parquet files:"
ls -lh ../track_2_data_vault/vault_data/*.parquet
echo ""

echo "2. CHECK DIMENSIONAL DATABASE"
echo "----------------------------"
cd dimensional_model
if [ -f "dimensional_model.db" ]; then
    echo "Database exists: $(ls -lh dimensional_model.db)"
    echo ""
    echo "Table counts:"
    sqlite3 dimensional_model.db "SELECT 'dim_well', COUNT(*) FROM dim_well;"
    sqlite3 dimensional_model.db "SELECT 'dim_sensor', COUNT(*) FROM dim_sensor;"
    sqlite3 dimensional_model.db "SELECT 'dim_time', COUNT(*) FROM dim_time;"
    sqlite3 dimensional_model.db "SELECT 'dim_data_source', COUNT(*) FROM dim_data_source;"
    sqlite3 dimensional_model.db "SELECT 'fact_sensor_reading', COUNT(*) FROM fact_sensor_reading;"
    sqlite3 dimensional_model.db "SELECT 'fact_survey_event', COUNT(*) FROM fact_survey_event;"
    echo ""
    echo "Sample from dim_well:"
    sqlite3 dimensional_model.db "SELECT * FROM dim_well LIMIT 3;"
    echo ""
    echo "Sample from fact_sensor_reading:"
    sqlite3 dimensional_model.db "SELECT * FROM fact_sensor_reading LIMIT 3;"
else
    echo "❌ Database does not exist!"
fi
echo ""

echo "3. CHECK DATA MARTS CSV FILES"
echo "----------------------------"
cd ../dashboard/data_marts
echo "CSV files:"
ls -lh *.csv 2>/dev/null || echo "No CSV files found"
echo ""
echo "Row counts:"
wc -l *.csv 2>/dev/null || echo "No CSV files"
echo ""
echo "mart_well_performance.csv content:"
head -5 mart_well_performance.csv 2>/dev/null || echo "File empty or missing"
echo ""
echo "mart_sensor_analysis.csv content:"
head -5 mart_sensor_analysis.csv 2>/dev/null || echo "File empty or missing"
echo ""

echo "4. CHECK MASTER DATA CONTENT"
echo "----------------------------"
cd ../../../data
echo "master_wells.csv (first 3 rows):"
head -3 master_wells.csv
echo ""
echo "master_sensors.csv (first 3 rows):"
head -3 master_sensors.csv
echo ""

echo "5. CHECK VAULT DATA"
echo "----------------------------"
cd ../track_2_data_vault/vault_data
echo "Checking parquet files with Python:"
python3 << 'PYTHON'
import pandas as pd
import os

files = ['hub_well.parquet', 'hub_sensor.parquet', 'link_seismic_reading.parquet', 'sat_seismic_measurements.parquet']

for f in files:
    if os.path.exists(f):
        df = pd.read_parquet(f)
        print(f"\n{f}: {len(df)} rows")
        if len(df) > 0:
            print(df.head(2))
    else:
        print(f"\n{f}: NOT FOUND")
PYTHON

echo ""
echo "=========================================="
echo "  DIAGNOSTICS COMPLETE"
echo "=========================================="
