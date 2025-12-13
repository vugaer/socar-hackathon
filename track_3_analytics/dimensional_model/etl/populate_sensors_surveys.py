import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import *
import pandas as pd

def populate_sensor_data():
    """Update fact table with proper sensor mappings"""
    conn = get_dimensional_connection()
    cursor = conn.cursor()
    
    # Get all sensors
    cursor.execute("SELECT sensor_key, sensor_id FROM dim_sensor ORDER BY sensor_key")
    sensors = cursor.fetchall()
    print(f"Found {len(sensors)} sensors")
    
    # Update readings to distribute across sensors
    cursor.execute("SELECT COUNT(*) FROM fact_sensor_reading")
    total_readings = cursor.fetchone()[0]
    print(f"Distributing {total_readings} readings across sensors...")
    
    readings_per_sensor = total_readings // len(sensors)
    
    for idx, (sensor_key, sensor_id) in enumerate(sensors):
        offset = idx * readings_per_sensor
        limit = readings_per_sensor
        
        cursor.execute("""
            UPDATE fact_sensor_reading 
            SET sensor_key = ?
            WHERE reading_key IN (
                SELECT reading_key FROM fact_sensor_reading 
                ORDER BY reading_key 
                LIMIT ? OFFSET ?
            )
        """, (sensor_key, limit, offset))
    
    conn.commit()
    print(f"✓ Updated sensor mappings")
    conn.close()

def populate_survey_events():
    """Create survey event facts"""
    conn = get_dimensional_connection()
    cursor = conn.cursor()
    
    # Aggregate readings by well and source
    query = """
    INSERT INTO fact_survey_event (
        well_key, time_key, source_key, survey_id, survey_type,
        survey_start_date, survey_end_date, total_readings, 
        avg_amplitude, data_quality_rate
    )
    SELECT 
        f.well_key,
        MIN(f.time_key) as time_key,
        f.source_key,
        'SURVEY-' || w.well_id as survey_id,
        'Seismic Survey' as survey_type,
        MIN(f.timestamp) as survey_start_date,
        MAX(f.timestamp) as survey_end_date,
        COUNT(*) as total_readings,
        AVG(f.amplitude) as avg_amplitude,
        AVG(CASE WHEN f.quality_flag = 1 THEN 1.0 ELSE 0.0 END) as data_quality_rate
    FROM fact_sensor_reading f
    JOIN dim_well w ON f.well_key = w.well_key
    GROUP BY f.well_key, f.source_key, w.well_id
    """
    
    cursor.execute(query)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM fact_survey_event")
    count = cursor.fetchone()[0]
    print(f"✓ Created {count} survey events")
    
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print(" Populating Sensors and Surveys ")
    print("=" * 60)
    populate_sensor_data()
    populate_survey_events()
    print("=" * 60)
    print(" ✓ Complete! ")
    print("=" * 60)
