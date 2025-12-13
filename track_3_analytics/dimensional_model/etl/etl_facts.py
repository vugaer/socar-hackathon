import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import *
import pandas as pd
import numpy as np

def etl_fact_sensor_reading():
    """Load sensor readings from vault parquet files"""
    dim_conn = get_dimensional_connection()
    dim_cursor = dim_conn.cursor()
    
    # Load readings from vault
    readings_file = os.path.join(VAULT_DATA_DIR, 'link_seismic_reading.parquet')
    measurements_file = os.path.join(VAULT_DATA_DIR, 'sat_seismic_measurements.parquet')
    
    if not os.path.exists(readings_file):
        print("⚠ No seismic readings found in vault")
        return
    
    df_readings = pd.read_parquet(readings_file)
    print(f"Loaded {len(df_readings)} readings from vault")
    
    if os.path.exists(measurements_file):
        df_measurements = pd.read_parquet(measurements_file)
        df_readings = df_readings.merge(df_measurements, on='link_key', how='left')
    
    count = 0
    for _, row in df_readings.iterrows():
        # Get foreign keys
        dim_cursor.execute("SELECT well_key FROM dim_well WHERE well_id = ?", (row.get('well_id', ''),))
        well_result = dim_cursor.fetchone()
        if not well_result:
            continue
        well_key = well_result[0]
        
        dim_cursor.execute("SELECT sensor_key FROM dim_sensor WHERE sensor_id = ?", (row.get('sensor_id', ''),))
        sensor_result = dim_cursor.fetchone()
        if not sensor_result:
            continue
        sensor_key = sensor_result[0]
        
        timestamp = row.get('timestamp', '2024-01-01')
        dim_cursor.execute("SELECT time_key FROM dim_time WHERE full_date = DATE(?)", (timestamp,))
        time_result = dim_cursor.fetchone()
        if not time_result:
            time_key = 1
        else:
            time_key = time_result[0]
        
        source_key = 1  # Default to Parquet
        
        amplitude = float(row.get('amplitude', 0))
        quality_flag = int(row.get('quality_flag', 1))
        is_anomaly = 1 if abs(amplitude) > 100 else 0
        
        dim_cursor.execute("""
            INSERT INTO fact_sensor_reading 
            (well_key, sensor_key, time_key, source_key, timestamp, depth, 
             amplitude, frequency, phase, quality_flag, is_anomaly, data_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            well_key, sensor_key, time_key, source_key,
            timestamp,
            float(row.get('depth', 0)),
            amplitude,
            float(row.get('frequency', 0)),
            float(row.get('phase', 0)),
            quality_flag,
            is_anomaly,
            1.0 if quality_flag == 1 else 0.5
        ))
        count += 1
        
        if count % 1000 == 0:
            dim_conn.commit()
            print(f"  Processed {count} readings...")
    
    dim_conn.commit()
    print(f"✓ Loaded {count} readings into fact_sensor_reading")
    dim_conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Fact ETL...")
    print("=" * 50)
    etl_fact_sensor_reading()
    print("=" * 50)
    print("✓ All facts loaded successfully!")
    print("=" * 50)
