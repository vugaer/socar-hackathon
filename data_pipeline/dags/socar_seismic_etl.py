"""
SOCAR Seismic Data - Production ETL Pipeline (FIXED)
=====================================================
Extract: Data Vault → Transform: Anomaly Detection → Load: SQL + NoSQL + JSON
Idempotent design (safe to re-run without duplicates)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import json
import os

default_args = {
    'owner': 'socar-hackathon',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 13),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_from_vault(**context):
    """EXTRACT: Read from Data Vault parquet files"""
    import pyarrow.parquet as pq
    
    vault_dir = '/opt/airflow/vault_data'
    temp_dir = '/opt/airflow/data/temp'
    os.makedirs(temp_dir, exist_ok=True)
    
    print("=" * 70)
    print("EXTRACT: Loading from Data Vault")
    print("=" * 70)
    
    measurements = pq.read_table(f'{vault_dir}/sat_seismic_measurements.parquet').to_pandas()
    wells = pq.read_table(f'{vault_dir}/hub_well.parquet').to_pandas()
    
    print(f"✓ Loaded {len(measurements):,} measurements")
    print(f"✓ Loaded {len(wells):,} wells")
    
    measurements.to_parquet(f'{temp_dir}/measurements_stage.parquet', index=False)
    wells.to_parquet(f'{temp_dir}/wells_stage.parquet', index=False)
    
    print("=" * 70)
    
    return {'measurements': len(measurements), 'wells': len(wells)}

def transform_data(**context):
    """TRANSFORM: Clean, enrich, detect anomalies"""
    
    temp_dir = '/opt/airflow/data/temp'
    
    print("=" * 70)
    print("TRANSFORM: Processing Data")
    print("=" * 70)
    
    measurements = pd.read_parquet(f'{temp_dir}/measurements_stage.parquet')
    wells = pd.read_parquet(f'{temp_dir}/wells_stage.parquet')
    
    # Anomaly Detection (statistical)
    mean_amp = measurements['amplitude'].mean()
    std_amp = measurements['amplitude'].std()
    measurements['is_anomaly'] = (
        (measurements['amplitude'] < mean_amp - 2*std_amp) |
        (measurements['amplitude'] > mean_amp + 2*std_amp)
    ).astype(int)
    
    anomalies = measurements['is_anomaly'].sum()
    print(f"✓ Detected {anomalies:,} anomalies ({anomalies/len(measurements)*100:.2f}%)")
    
    # Aggregate by well
    well_analytics = measurements.groupby('well_id').agg({
        'amplitude': ['mean', 'std', 'min', 'max', 'count'],
        'is_anomaly': 'sum',
        'quality_flag': lambda x: (x == 1).mean()
    }).reset_index()
    
    well_analytics.columns = [
        'well_id', 'avg_amplitude', 'std_amplitude', 'min_amplitude',
        'max_amplitude', 'reading_count', 'anomaly_count', 'quality_score'
    ]
    
    # Enrich with metadata
    if 'well_id' in wells.columns:
        well_analytics = well_analytics.merge(
            wells[['well_id']], on='well_id', how='left'
        )
    
    well_analytics['well_name'] = well_analytics['well_id'].apply(lambda x: f'WELL-{x}')
    well_analytics['processed_at'] = datetime.now()
    
    print(f"✓ Processed {len(well_analytics)} wells")
    
    well_analytics.to_parquet(f'{temp_dir}/well_analytics.parquet', index=False)
    measurements.to_parquet(f'{temp_dir}/measurements_final.parquet', index=False)
    
    print("=" * 70)
    
    return {'wells_processed': len(well_analytics), 'anomalies_found': int(anomalies)}

def load_to_sql(**context):
    """LOAD: PostgreSQL (SQL Database)"""
    from sqlalchemy import create_engine
    
    temp_dir = '/opt/airflow/data/temp'
    
    print("=" * 70)
    print("LOAD: PostgreSQL")
    print("=" * 70)
    
    well_analytics = pd.read_parquet(f'{temp_dir}/well_analytics.parquet')
    
    engine = create_engine('postgresql://airflow:airflow@postgres:5432/airflow')
    
    # IDEMPOTENT: Replace existing data
    well_analytics.to_sql('seismic_well_analytics', engine, if_exists='replace', index=False)
    
    print(f"✓ Loaded {len(well_analytics)} records to PostgreSQL")
    print(f"  Table: seismic_well_analytics")
    print("=" * 70)
    
    engine.dispose()
    return len(well_analytics)

def load_to_nosql(**context):
    """LOAD: MongoDB (NoSQL Database) - FIXED for NaT values"""
    from pymongo import MongoClient
    import numpy as np
    
    temp_dir = '/opt/airflow/data/temp'
    
    print("=" * 70)
    print("LOAD: MongoDB")
    print("=" * 70)
    
    measurements = pd.read_parquet(f'{temp_dir}/measurements_final.parquet')
    
    # FIX: Convert pandas types to Python native types for MongoDB
    # Replace NaT/NaN with None, convert timestamps to ISO strings
    for col in measurements.columns:
        if pd.api.types.is_datetime64_any_dtype(measurements[col]):
            # Convert datetime to ISO string, NaT becomes None
            measurements[col] = measurements[col].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
        elif pd.api.types.is_numeric_dtype(measurements[col]):
            # Replace NaN with None
            measurements[col] = measurements[col].replace({np.nan: None})
    
    client = MongoClient('mongodb://admin:admin123@mongodb:27017/')
    db = client['socar_seismic']
    collection = db['measurements']
    
    # IDEMPOTENT: Clear old data
    deleted = collection.delete_many({})
    print(f"✓ Cleared {deleted.deleted_count} old records")
    
    # Insert sample (10K records)
    sample_size = min(10000, len(measurements))
    records = measurements.head(sample_size).to_dict('records')
    
    print(f"✓ Inserting {len(records):,} documents...")
    result = collection.insert_many(records)
    
    print(f"✓ Inserted {len(result.inserted_ids):,} documents to MongoDB")
    print(f"  Database: socar_seismic")
    print(f"  Collection: measurements")
    print("=" * 70)
    
    client.close()
    return len(result.inserted_ids)

def load_to_json(**context):
    """LOAD: JSON Export"""
    
    temp_dir = '/opt/airflow/data/temp'
    export_dir = '/opt/airflow/data/exports'
    os.makedirs(export_dir, exist_ok=True)
    
    print("=" * 70)
    print("LOAD: JSON Export")
    print("=" * 70)
    
    well_analytics = pd.read_parquet(f'{temp_dir}/well_analytics.parquet')
    
    export_file = f'{export_dir}/well_analytics_{datetime.now().strftime("%Y%m%d")}.json'
    well_analytics.to_json(export_file, orient='records', indent=2, date_format='iso')
    
    print(f"✓ Exported {len(well_analytics)} wells")
    print(f"  File: {export_file}")
    print("=" * 70)
    
    return export_file

def generate_report(**context):
    """Generate pipeline execution report"""
    
    ti = context['task_instance']
    
    print("=" * 70)
    print("ETL PIPELINE REPORT")
    print("=" * 70)
    
    extract_metrics = ti.xcom_pull(task_ids='extract_from_vault')
    transform_metrics = ti.xcom_pull(task_ids='transform_data')
    sql_count = ti.xcom_pull(task_ids='load_to_sql')
    nosql_count = ti.xcom_pull(task_ids='load_to_nosql')
    json_file = ti.xcom_pull(task_ids='load_to_json')
    
    report = {
        'pipeline_run': context['run_id'],
        'execution_time': datetime.now().isoformat(),
        'extract': extract_metrics,
        'transform': transform_metrics,
        'load': {
            'postgresql': sql_count,
            'mongodb': nosql_count,
            'json': json_file
        }
    }
    
    # Save report
    report_dir = '/opt/airflow/data/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f'{report_dir}/etl_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"  Extracted: {extract_metrics['measurements']:,} measurements")
    print(f"  Transformed: {transform_metrics['wells_processed']} wells")
    print(f"  Anomalies: {transform_metrics['anomalies_found']:,}")
    print(f"  PostgreSQL: {sql_count} records")
    print(f"  MongoDB: {nosql_count:,} documents")
    print(f"  JSON: {json_file}")
    print(f"\n✅ Report saved: {report_file}")
    print("=" * 70)

with DAG(
    dag_id='socar_seismic_etl',
    default_args=default_args,
    description='SOCAR ETL: Vault → PostgreSQL + MongoDB + JSON',
    schedule_interval='@daily',
    catchup=False,
    tags=['production', 'etl', 'socar'],
    max_active_runs=1,
) as dag:
    
    extract_task = PythonOperator(
        task_id='extract_from_vault',
        python_callable=extract_from_vault,
    )
    
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )
    
    load_sql_task = PythonOperator(
        task_id='load_to_sql',
        python_callable=load_to_sql,
    )
    
    load_nosql_task = PythonOperator(
        task_id='load_to_nosql',
        python_callable=load_to_nosql,
    )
    
    load_json_task = PythonOperator(
        task_id='load_to_json',
        python_callable=load_to_json,
    )
    
    report_task = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
    )
    
    # Pipeline: Extract → Transform → [3 loads in parallel] → Report
    extract_task >> transform_task >> [load_sql_task, load_nosql_task, load_json_task] >> report_task
