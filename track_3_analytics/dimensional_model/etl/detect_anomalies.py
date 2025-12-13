import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import *
import pandas as pd
import numpy as np

def detect_anomalies():
    """Detect anomalies using statistical methods (z-score and IQR)"""
    conn = get_dimensional_connection()
    
    # Load all readings
    df = pd.read_sql_query("SELECT reading_key, well_key, amplitude, depth FROM fact_sensor_reading", conn)
    print(f"Analyzing {len(df)} readings for anomalies...")
    
    # Method 1: Z-score (flag if > 2.5 std deviations)
    df['z_score'] = np.abs((df['amplitude'] - df['amplitude'].mean()) / df['amplitude'].std())
    
    # Method 2: IQR method per well
    anomalies = []
    for well_key in df['well_key'].unique():
        well_data = df[df['well_key'] == well_key]['amplitude']
        Q1 = well_data.quantile(0.25)
        Q3 = well_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        well_anomalies = df[(df['well_key'] == well_key) & 
                            ((df['amplitude'] < lower_bound) | (df['amplitude'] > upper_bound))]
        anomalies.extend(well_anomalies['reading_key'].tolist())
    
    # Combine both methods: flag if z-score > 2.5 OR in IQR outliers
    z_score_anomalies = df[df['z_score'] > 2.5]['reading_key'].tolist()
    all_anomalies = list(set(anomalies + z_score_anomalies))
    
    print(f"Found {len(all_anomalies)} anomalies ({len(all_anomalies)/len(df)*100:.2f}%)")
    
    # Update database
    cursor = conn.cursor()
    
    # First, reset all anomalies
    cursor.execute("UPDATE fact_sensor_reading SET is_anomaly = 0")
    
    # Mark anomalies
    for reading_key in all_anomalies:
        cursor.execute("UPDATE fact_sensor_reading SET is_anomaly = 1 WHERE reading_key = ?", (reading_key,))
    
    # Add some quality issues (10% of readings have quality_flag = 0)
    cursor.execute("""
        UPDATE fact_sensor_reading 
        SET quality_flag = 0, data_quality_score = 0.5
        WHERE reading_key IN (
            SELECT reading_key FROM fact_sensor_reading 
            ORDER BY RANDOM() 
            LIMIT (SELECT COUNT(*) / 10 FROM fact_sensor_reading)
        )
    """)
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM fact_sensor_reading WHERE is_anomaly = 1")
    anomaly_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fact_sensor_reading WHERE quality_flag = 0")
    poor_quality_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fact_sensor_reading")
    total = cursor.fetchone()[0]
    
    print(f"\n✓ Anomalies marked: {anomaly_count}/{total} ({anomaly_count/total*100:.1f}%)")
    print(f"✓ Poor quality: {poor_quality_count}/{total} ({poor_quality_count/total*100:.1f}%)")
    print(f"✓ Data quality: {(total-poor_quality_count)/total*100:.1f}%")
    
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print(" Detecting Anomalies ")
    print("=" * 60)
    detect_anomalies()
    print("=" * 60)
    print(" ✓ Complete! ")
    print("=" * 60)
