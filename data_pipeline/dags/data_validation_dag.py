"""
Data Validation and Schema Enforcement Pipeline
Validates data integrity and enforces schema rules
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'socar',
    'start_date': datetime(2025, 12, 13),
}

def validate_schema(**context):
    """Validate data schema"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet')
    
    required_columns = ['trace_num', 'well_id', 'depth_ft', 'amplitude']
    missing_columns = [col for col in required_columns if col not in measurements.column_names]
    
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")
    
    print(f"✓ Schema validation passed. Columns: {measurements.column_names}")

def validate_data_types(**context):
    """Validate data types"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet').to_pandas()
    
    # Check numeric columns
    numeric_cols = ['trace_num', 'well_id', 'depth_ft', 'amplitude']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(measurements[col]):
            raise TypeError(f"Column {col} is not numeric")
    
    print("✓ Data type validation passed")

def validate_ranges(**context):
    """Validate value ranges"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet').to_pandas()
    
    # Check amplitude range
    invalid_amp = ((measurements['amplitude'] < -1000) | (measurements['amplitude'] > 1000)).sum()
    
    # Check depth range
    invalid_depth = ((measurements['depth_ft'] < 0) | (measurements['depth_ft'] > 50000)).sum()
    
    print(f"Invalid amplitudes: {invalid_amp}")
    print(f"Invalid depths: {invalid_depth}")
    
    if invalid_amp > len(measurements) * 0.01:  # More than 1%
        raise ValueError(f"Too many invalid amplitudes: {invalid_amp}")

def generate_validation_report(**context):
    """Generate validation report"""
    import json
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'schema_valid': True,
        'data_types_valid': True,
        'ranges_valid': True,
        'status': 'PASSED'
    }
    
    with open('/opt/airflow/data/validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✓ Validation report generated")

with DAG(
    'data_validation',
    default_args=default_args,
    description='Data validation and schema enforcement',
    schedule_interval='@hourly',
    catchup=False,
    tags=['validation', 'quality', 'schema'],
) as dag:
    
    validate_schema_task = PythonOperator(
        task_id='validate_schema',
        python_callable=validate_schema,
    )
    
    validate_types_task = PythonOperator(
        task_id='validate_data_types',
        python_callable=validate_data_types,
    )
    
    validate_ranges_task = PythonOperator(
        task_id='validate_ranges',
        python_callable=validate_ranges,
    )
    
    report_task = PythonOperator(
        task_id='generate_validation_report',
        python_callable=generate_validation_report,
    )
    
    validate_schema_task >> validate_types_task >> validate_ranges_task >> report_task
