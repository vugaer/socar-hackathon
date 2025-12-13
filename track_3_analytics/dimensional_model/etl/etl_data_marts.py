import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import *
import pandas as pd

def export_data_marts():
    """Export data marts to CSV for dashboard"""
    dim_conn = get_dimensional_connection()
    
    output_dir = os.path.join(BASE_DIR, '../dashboard/data_marts')
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Export mart_well_performance
        df_well = pd.read_sql_query("SELECT * FROM mart_well_performance", dim_conn)
        df_well.to_csv(os.path.join(output_dir, 'mart_well_performance.csv'), index=False)
        print(f"✓ Exported mart_well_performance: {len(df_well)} rows")
        
        # Export mart_sensor_analysis
        df_sensor = pd.read_sql_query("SELECT * FROM mart_sensor_analysis", dim_conn)
        df_sensor.to_csv(os.path.join(output_dir, 'mart_sensor_analysis.csv'), index=False)
        print(f"✓ Exported mart_sensor_analysis: {len(df_sensor)} rows")
        
        # Export mart_survey_summary
        df_survey = pd.read_sql_query("SELECT * FROM mart_survey_summary", dim_conn)
        df_survey.to_csv(os.path.join(output_dir, 'mart_survey_summary.csv'), index=False)
        print(f"✓ Exported mart_survey_summary: {len(df_survey)} rows")
        
    except Exception as e:
        print(f"⚠ Error exporting data marts: {e}")
    
    dim_conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Exporting data marts...")
    print("=" * 50)
    export_data_marts()
    print("=" * 50)
    print("✓ All data marts exported!")
    print("=" * 50)
