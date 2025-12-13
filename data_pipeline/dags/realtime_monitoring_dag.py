"""
Real-time Data Monitoring and Alerting Pipeline
Monitors data quality, anomalies, and system health
"""
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

default_args = {
    'owner': 'socar',
    'start_date': datetime(2025, 12, 13),
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

def check_data_freshness(**context):
    """Check if data is up to date"""
    import os
    from datetime import datetime
    
    vault_dir = '/opt/airflow/vault_data'
    measurements_file = f'{vault_dir}/sat_seismic_measurements.parquet'
    
    if not os.path.exists(measurements_file):
        print("❌ Data file not found!")
        return 'send_alert'
    
    # Check file modification time
    mod_time = os.path.getmtime(measurements_file)
    age_hours = (datetime.now().timestamp() - mod_time) / 3600
    
    print(f"Data age: {age_hours:.2f} hours")
    
    if age_hours > 24:
        return 'send_alert'
    return 'monitor_anomalies'

def monitor_anomalies(**context):
    """Monitor for critical anomalies"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet').to_pandas()
    
    # Detect severe anomalies
    mean_amp = measurements['amplitude'].mean()
    std_amp = measurements['amplitude'].std()
    severe_anomalies = measurements[
        (measurements['amplitude'] < mean_amp - 3*std_amp) |
        (measurements['amplitude'] > mean_amp + 3*std_amp)
    ]
    
    anomaly_rate = len(severe_anomalies) / len(measurements) * 100
    
    print(f"Severe anomaly rate: {anomaly_rate:.2f}%")
    print(f"Total severe anomalies: {len(severe_anomalies)}")
    
    context['task_instance'].xcom_push(key='anomaly_rate', value=anomaly_rate)
    context['task_instance'].xcom_push(key='anomaly_count', value=len(severe_anomalies))
    
    if anomaly_rate > 5:
        return 'send_alert'
    return 'check_data_quality'

def check_data_quality(**context):
    """Validate data quality metrics"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet').to_pandas()
    
    # Quality checks
    missing_values = measurements.isnull().sum().sum()
    duplicate_rows = measurements.duplicated().sum()
    invalid_amplitudes = ((measurements['amplitude'] < -1000) | (measurements['amplitude'] > 1000)).sum()
    
    quality_score = 100 - (
        (missing_values / len(measurements)) * 30 +
        (duplicate_rows / len(measurements)) * 30 +
        (invalid_amplitudes / len(measurements)) * 40
    )
    
    print(f"Data Quality Score: {quality_score:.2f}%")
    print(f"Missing values: {missing_values}")
    print(f"Duplicates: {duplicate_rows}")
    print(f"Invalid amplitudes: {invalid_amplitudes}")
    
    context['task_instance'].xcom_push(key='quality_score', value=quality_score)
    
    return quality_score

def send_alert(**context):
    """Send alert (simulated)"""
    print("=" * 60)
    print("⚠️  ALERT: DATA QUALITY ISSUE DETECTED")
    print("=" * 60)
    
    # Get metrics from previous tasks
    ti = context['task_instance']
    anomaly_rate = ti.xcom_pull(task_ids='monitor_anomalies', key='anomaly_rate')
    quality_score = ti.xcom_pull(task_ids='check_data_quality', key='quality_score')
    
    print(f"Anomaly Rate: {anomaly_rate}%")
    print(f"Quality Score: {quality_score}%")
    print("=" * 60)

def generate_report(**context):
    """Generate monitoring report"""
    import json
    
    ti = context['task_instance']
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'anomaly_rate': ti.xcom_pull(task_ids='monitor_anomalies', key='anomaly_rate'),
        'anomaly_count': ti.xcom_pull(task_ids='monitor_anomalies', key='anomaly_count'),
        'quality_score': ti.xcom_pull(task_ids='check_data_quality', key='quality_score'),
        'status': 'healthy'
    }
    
    # Save report
    with open('/opt/airflow/data/monitoring_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✓ Monitoring report generated")

with DAG(
    'realtime_monitoring',
    default_args=default_args,
    description='Real-time data monitoring and alerting',
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False,
    tags=['monitoring', 'quality', 'alerts'],
) as dag:
    
    check_freshness = BranchPythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness,
    )
    
    monitor = BranchPythonOperator(
        task_id='monitor_anomalies',
        python_callable=monitor_anomalies,
    )
    
    quality = PythonOperator(
        task_id='check_data_quality',
        python_callable=check_data_quality,
    )
    
    alert = PythonOperator(
        task_id='send_alert',
        python_callable=send_alert,
        trigger_rule='none_failed',
    )
    
    report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
        trigger_rule='all_done',
    )
    
    check_freshness >> monitor >> quality >> report
    check_freshness >> alert >> report
    monitor >> alert
