import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import *
import pandas as pd
from datetime import datetime

def etl_dim_well():
    """Load wells from master CSV and vault"""
    dim_conn = get_dimensional_connection()
    dim_cursor = dim_conn.cursor()
    
    # Load from master CSV
    wells_csv = os.path.join(BASE_DIR, '../../data/master_wells.csv')
    if os.path.exists(wells_csv):
        df_wells = pd.read_csv(wells_csv)
        
        for _, row in df_wells.iterrows():
            dim_cursor.execute("""
                INSERT OR REPLACE INTO dim_well 
                (well_id, well_name, latitude, longitude, basin, field, operator, 
                 spud_date, completion_date, well_status, total_depth, effective_date, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                row.get('well_id', ''),
                row.get('well_name', ''),
                row.get('latitude', 0),
                row.get('longitude', 0),
                row.get('basin', ''),
                row.get('field', ''),
                row.get('operator', ''),
                row.get('spud_date', ''),
                row.get('completion_date', ''),
                row.get('status', ''),
                row.get('total_depth', 0),
                datetime.now().strftime('%Y-%m-%d'),
            ))
        
        dim_conn.commit()
        print(f"✓ Loaded {len(df_wells)} wells into dim_well")
    
    # Load from vault parquet
    vault_well_file = os.path.join(VAULT_DATA_DIR, 'hub_well.parquet')
    if os.path.exists(vault_well_file):
        df_vault = pd.read_parquet(vault_well_file)
        for _, row in df_vault.iterrows():
            dim_cursor.execute("""
                INSERT OR IGNORE INTO dim_well 
                (well_id, well_name, effective_date, is_current)
                VALUES (?, ?, ?, 1)
            """, (
                row.get('well_id', ''),
                row.get('well_id', ''),  # Use ID as name if no name
                datetime.now().strftime('%Y-%m-%d'),
            ))
        dim_conn.commit()
        print(f"✓ Loaded {len(df_vault)} wells from vault")
    
    dim_conn.close()

def etl_dim_sensor():
    """Load sensors from master CSV and vault"""
    dim_conn = get_dimensional_connection()
    dim_cursor = dim_conn.cursor()
    
    # Load from master CSV
    sensors_csv = os.path.join(BASE_DIR, '../../data/master_sensors.csv')
    if os.path.exists(sensors_csv):
        df_sensors = pd.read_csv(sensors_csv)
        
        for _, row in df_sensors.iterrows():
            dim_cursor.execute("""
                INSERT OR REPLACE INTO dim_sensor 
                (sensor_id, sensor_type, manufacturer, model, installation_date, 
                 calibration_date, sensor_status, effective_date, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                row.get('sensor_id', ''),
                row.get('sensor_type', ''),
                row.get('manufacturer', ''),
                row.get('model', ''),
                row.get('installation_date', ''),
                row.get('calibration_date', ''),
                row.get('status', ''),
                datetime.now().strftime('%Y-%m-%d'),
            ))
        
        dim_conn.commit()
        print(f"✓ Loaded {len(df_sensors)} sensors into dim_sensor")
    
    # Load from vault
    vault_sensor_file = os.path.join(VAULT_DATA_DIR, 'hub_sensor.parquet')
    if os.path.exists(vault_sensor_file):
        df_vault = pd.read_parquet(vault_sensor_file)
        for _, row in df_vault.iterrows():
            dim_cursor.execute("""
                INSERT OR IGNORE INTO dim_sensor 
                (sensor_id, sensor_type, effective_date, is_current)
                VALUES (?, ?, ?, 1)
            """, (
                row.get('sensor_id', ''),
                row.get('sensor_type', 'Unknown'),
                datetime.now().strftime('%Y-%m-%d'),
            ))
        dim_conn.commit()
        print(f"✓ Loaded {len(df_vault)} sensors from vault")
    
    dim_conn.close()

def etl_dim_time():
    """Generate time dimension"""
    import pandas as pd
    
    dim_conn = get_dimensional_connection()
    dim_cursor = dim_conn.cursor()
    
    dates = pd.date_range('1990-01-01', '2030-12-31', freq='D')
    
    for date in dates:
        dim_cursor.execute("""
            INSERT OR IGNORE INTO dim_time 
            (full_date, year, quarter, month, day, day_of_week, week_of_year, is_weekend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date.strftime('%Y-%m-%d'),
            date.year,
            (date.month - 1) // 3 + 1,
            date.month,
            date.day,
            date.weekday(),
            date.isocalendar()[1],
            1 if date.weekday() >= 5 else 0
        ))
    
    dim_conn.commit()
    print(f"✓ Loaded {len(dates)} dates into dim_time")
    dim_conn.close()

def etl_dim_data_source():
    """Load data source dimension"""
    dim_conn = get_dimensional_connection()
    dim_cursor = dim_conn.cursor()
    
    sources = [
        ('CSV', 'Flat File', '.csv'),
        ('JSON', 'Structured', '.json'),
        ('Parquet', 'Columnar', '.parquet'),
        ('SEGY', 'Seismic', '.segy'),
        ('SGX', 'Legacy Seismic', '.sgx')
    ]
    
    for source in sources:
        dim_cursor.execute("""
            INSERT OR IGNORE INTO dim_data_source (source_format, source_type, file_extension)
            VALUES (?, ?, ?)
        """, source)
    
    dim_conn.commit()
    print(f"✓ Loaded {len(sources)} sources into dim_data_source")
    dim_conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Dimension ETL...")
    print("=" * 50)
    etl_dim_time()
    etl_dim_data_source()
    etl_dim_well()
    etl_dim_sensor()
    print("=" * 50)
    print("✓ All dimensions loaded successfully!")
    print("=" * 50)
