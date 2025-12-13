"""
Seismic Data ETL Pipeline
Extracts data from vault, transforms, and loads to multiple destinations
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pandas as pd
import json
import os

default_args = {
    'owner': 'socar',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 13),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_vault_data(**context):
    """Extract data from Data Vault"""
    import pyarrow.parquet as pq
    
    vault_dir = '/opt/airflow/vault_data'
    
    # Read measurements
    measurements = pq.read_table(f'{vault_dir}/sat_seismic_measurements.parquet').to_pandas()
    
    # Read wells
    wells = pq.read_table(f'{vault_dir}/hub_well.parquet').to_pandas()
    
    # Read sensors
    sensors = pq.read_table(f'{vault_dir}/hub_sensor.parquet').to_pandas()
    
    print(f"✓ Extracted {len(measurements)} measurements")
    print(f"✓ Extracted {len(wells)} wells")
    print(f"✓ Extracted {len(sensors)} sensors")
    
    # Save to temp location
    measurements.to_parquet('/opt/airflow/data/temp_measurements.parquet')
    wells.to_parquet('/opt/airflow/data/temp_wells.parquet')
    sensors.to_parquet('/opt/airflow/data/temp_sensors.parquet')
    
    return {
        'measurements_count': len(measurements),
        'wells_count': len(wells),
        'sensors_count': len(sensors)
    }

def transform_data(**context):
    """Transform extracted data"""
    
    # Read temp data
    measurements = pd.read_parquet('/opt/airflow/data/temp_measurements.parquet')
    wells = pd.read_parquet('/opt/airflow/data/temp_wells.parquet')
    
    # Transform: Add anomaly detection
    mean_amp = measurements['amplitude'].mean()
    std_amp = measurements['amplitude'].std()
    measurements['is_anomaly'] = (
        (measurements['amplitude'] < mean_amp - 2*std_amp) |
        (measurements['amplitude'] > mean_amp + 2*std_amp)
    ).astype(int)
    
    # Transform: Aggregate by well
    well_summary = measurements.groupby('well_id').agg({
        'amplitude': ['mean', 'std', 'min', 'max'],
        'depth_ft': 'count',
        'is_anomaly': 'sum'
    }).reset_index()
    
    well_summary.columns = ['well_id', 'avg_amplitude', 'std_amplitude', 
                            'min_amplitude', 'max_amplitude', 
                            'total_readings', 'anomaly_count']
    
    # Merge with well info
    well_summary = well_summary.merge(wells, on='well_id', how='left')
    
    print(f"✓ Transformed {len(well_summary)} well summaries")
    print(f"✓ Total anomalies detected: {measurements['is_anomaly'].sum()}")
    
    # Save transformed data
    measurements.to_parquet('/opt/airflow/data/transformed_measurements.parquet')
    well_summary.to_parquet('/opt/airflow/data/transformed_well_summary.parquet')
    
    return {
        'transformed_measurements': len(measurements),
        'well_summaries': len(well_summary),
        'total_anomalies': int(measurements['is_anomaly'].sum())
    }

def load_to_postgresql(**context):
    """Load data to PostgreSQL"""
    from sqlalchemy import create_engine
    
    # Read transformed data
    well_summary = pd.read_parquet('/opt/airflow/data/transformed_well_summary.parquet')
    
    # Connect to PostgreSQL
    engine = create_engine('postgresql://airflow:airflow@postgres:5432/airflow')
    
    # Load to database
    well_summary.to_sql('seismic_well_summary', engine, if_exists='replace', index=False)
    
    print(f"✓ Loaded {len(well_summary)} records to PostgreSQL")
    
    return len(well_summary)

def load_to_mongodb(**context):
    """Load data to MongoDB (NoSQL)"""
    from pymongo import MongoClient
    
    # Read transformed data
    measurements = pd.read_parquet('/opt/airflow/data/transformed_measurements.parquet')
    
    # Connect to MongoDB
    client = MongoClient('mongodb://admin:admin123@mongodb:27017/')
    db = client['seismic_data']
    collection = db['measurements']
    
    # Convert to dict and insert
    records = measurements.head(1000).to_dict('records')  # Limit for demo
    collection.delete_many({})  # Clear old data
    collection.insert_many(records)
    
    print(f"✓ Loaded {len(records)} records to MongoDB")
    
    client.close()
    
    return len(records)

def load_to_json(**context):
    """Load data to JSON files"""
    
    well_summary = pd.read_parquet('/opt/airflow/data/transformed_well_summary.parquet')
    
    # Export to JSON
    output_file = '/opt/airflow/data/well_summary_export.json'
    well_summary.to_json(output_file, orient='records', indent=2)
    
    print(f"✓ Exported to {output_file}")
    
    return output_file

def quality_check(**context):
    """Data quality checks"""
    
    well_summary = pd.read_parquet('/opt/airflow/data/transformed_well_summary.parquet')
    
    checks = {
        'total_wells': len(well_summary),
        'wells_with_anomalies': (well_summary['anomaly_count'] > 0).sum(),
        'avg_readings_per_well': well_summary['total_readings'].mean(),
        'data_completeness': (well_summary['avg_amplitude'].notna().sum() / len(well_summary)) * 100
    }
    
    print("=" * 50)
    print("DATA QUALITY REPORT")
    print("=" * 50)
    for key, value in checks.items():
        print(f"{key}: {value}")
    print("=" * 50)
    
    return checks

# Define DAG
with DAG(
    'seismic_etl_pipeline',
    default_args=default_args,
    description='Complete ETL pipeline for seismic data',
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'seismic', 'socar'],
) as dag:
    
    extract_task = PythonOperator(
        task_id='extract_vault_data',
        python_callable=extract_vault_data,
    )
    
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )
    
    load_postgres_task = PythonOperator(
        task_id='load_to_postgresql',
        python_callable=load_to_postgresql,
    )
    
    load_mongo_task = PythonOperator(
        task_id='load_to_mongodb',
        python_callable=load_to_mongodb,
    )
    
    load_json_task = PythonOperator(
        task_id='load_to_json',
        python_callable=load_to_json,
    )
    
    quality_task = PythonOperator(
        task_id='quality_check',
        python_callable=quality_check,
    )
    
    # Define pipeline flow
    extract_task >> transform_task >> [load_postgres_task, load_mongo_task, load_json_task] >> quality_task
