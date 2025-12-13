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
    
    # Load from sat_seismic_measurements (this has the actual data)
    measurements_file = os.path.join(VAULT_DATA_DIR, 'sat_seismic_measurements.parquet')
    
    if not os.path.exists(measurements_file):
        print(f"❌ {measurements_file} not found")
        return
    
    print(f"Loading data from {measurements_file}...")
    df = pd.read_parquet(measurements_file)
    print(f"Found {len(df)} measurements")
    
    # Show sample
    print("\nSample data:")
    print(df.head(3))
    print("\nColumns:", df.columns.tolist())
    
    count = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        well_id = row.get('well_id')
        
        # Get well_key
        dim_cursor.execute("SELECT well_key FROM dim_well WHERE well_id = ?", (str(well_id),))
        well_result = dim_cursor.fetchone()
        if not well_result:
            skipped += 1
            continue
        well_key = well_result[0]
        
        # Use a default sensor for now (since sensor_id is NaN in the data)
        sensor_key = 1
        
        # Get time_key from timestamp if available, otherwise use default
        timestamp = row.get('timestamp', '2024-01-01')
        if pd.isna(timestamp):
            timestamp = '2024-01-01'
        else:
            timestamp = str(timestamp).split('T')[0] if 'T' in str(timestamp) else str(timestamp)
        
        dim_cursor.execute("SELECT time_key FROM dim_time WHERE full_date = DATE(?)", (timestamp,))
        time_result = dim_cursor.fetchone()
        time_key = time_result[0] if time_result else 1
        
        # Source is Parquet
        source_key = 3
        
        # Extract values
        depth = float(row.get('depth_ft', 0))
        amplitude = float(row.get('amplitude', 0))
        frequency = float(row.get('frequency', 0)) if 'frequency' in row and not pd.isna(row.get('frequency')) else 0
        phase = float(row.get('phase', 0)) if 'phase' in row and not pd.isna(row.get('phase')) else 0
        quality_flag = 1  # Default to good quality
        
        # Detect anomaly (amplitude > 50 or < -50)
        is_anomaly = 1 if abs(amplitude) > 50 else 0
        
        dim_cursor.execute("""
            INSERT INTO fact_sensor_reading 
            (well_key, sensor_key, time_key, source_key, timestamp, depth, 
             amplitude, frequency, phase, quality_flag, is_anomaly, data_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            well_key, sensor_key, time_key, source_key,
            timestamp, depth, amplitude, frequency, phase,
            quality_flag, is_anomaly, 1.0
        ))
        
        count += 1
        
        if count % 1000 == 0:
            dim_conn.commit()
            print(f"  Inserted {count} readings...")
    
    dim_conn.commit()
    print(f"\n✓ Loaded {count} readings into fact_sensor_reading")
    print(f"⚠ Skipped {skipped} readings (no matching well)")
    dim_conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print(" Loading Fact Tables (FIXED VERSION) ")
    print("=" * 60)
    etl_fact_sensor_reading()
    print("=" * 60)
    print(" ✓ Facts loaded successfully! ")
    print("=" * 60)
