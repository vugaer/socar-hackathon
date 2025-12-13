#!/usr/bin/env python3
"""
Dimensional Model Builder
Creates star schema from Data Vault for analytics
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DimensionalModelBuilder:
    """Build star schema dimensional model from Data Vault"""
    
    def __init__(self, vault_dir: str, output_dir: str):
        self.vault_dir = Path(vault_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def build_dim_well(self):
        """Dimension: Wells"""
        print("\n" + "="*60)
        print("Building dim_well...")
        print("="*60)
        
        hub = pd.read_parquet(self.vault_dir / 'hub_well.parquet')
        sat = pd.read_parquet(self.vault_dir / 'sat_well_details.parquet')
        
        dim = hub.merge(sat, on='well_hash_key', suffixes=('', '_sat'))
        
        if 'location' in dim.columns:
            coords = dim['location'].str.extract(r'([\d.-]+),\s*([\d.-]+)')
            if len(coords.columns) == 2:
                dim['latitude'] = pd.to_numeric(coords[0], errors='coerce')
                dim['longitude'] = pd.to_numeric(coords[1], errors='coerce')
        
        possible_cols = ['well_hash_key', 'well_id', 'well_name', 'field', 'location', 
                        'latitude', 'longitude', 'operator', 'spud_date', 'completion_date']
        dim_cols = [col for col in possible_cols if col in dim.columns]
        dim = dim[dim_cols]
        
        self.save_table(dim, 'dim_well')
        print(f"✓ Created {len(dim)} well dimensions")
        return dim
    
    def build_dim_survey(self):
        """Dimension: Survey Types"""
        print("\n" + "="*60)
        print("Building dim_survey...")
        print("="*60)
        
        hub = pd.read_parquet(self.vault_dir / 'hub_survey.parquet')
        sat = pd.read_parquet(self.vault_dir / 'sat_survey_details.parquet')
        
        dim = hub.merge(sat, on='survey_hash_key', suffixes=('', '_sat'))
        
        possible_cols = ['survey_hash_key', 'survey_type_id', 'survey_name', 'description', 'methodology']
        dim_cols = [col for col in possible_cols if col in dim.columns]
        dim = dim[dim_cols]
        
        self.save_table(dim, 'dim_survey')
        print(f"✓ Created {len(dim)} survey dimensions")
        return dim
    
    def build_dim_sensor(self):
        """Dimension: Sensors"""
        print("\n" + "="*60)
        print("Building dim_sensor...")
        print("="*60)
        
        hub = pd.read_parquet(self.vault_dir / 'hub_sensor.parquet')
        sat = pd.read_parquet(self.vault_dir / 'sat_sensor_details.parquet')
        
        dim = hub.merge(sat, on='sensor_hash_key', suffixes=('', '_sat'))
        
        possible_cols = ['sensor_hash_key', 'sensor_id', 'sensor_type', 'manufacturer', 
                        'model', 'calibration_date', 'accuracy']
        dim_cols = [col for col in possible_cols if col in dim.columns]
        dim = dim[dim_cols]
        
        self.save_table(dim, 'dim_sensor')
        print(f"✓ Created {len(dim)} sensor dimensions")
        return dim
    
    def build_dim_time(self, measurements_df):
        """Dimension: Time"""
        print("\n" + "="*60)
        print("Building dim_time...")
        print("="*60)
        
        if 'timestamp' in measurements_df.columns:
            timestamps = pd.to_datetime(measurements_df['timestamp'], errors='coerce').dropna().unique()
        else:
            timestamps = pd.to_datetime(measurements_df['load_timestamp']).unique()
        
        dim = pd.DataFrame({'timestamp': timestamps})
        dim['date'] = dim['timestamp'].dt.date
        dim['year'] = dim['timestamp'].dt.year
        dim['month'] = dim['timestamp'].dt.month
        dim['day'] = dim['timestamp'].dt.day
        dim['hour'] = dim['timestamp'].dt.hour
        dim['minute'] = dim['timestamp'].dt.minute
        dim['quarter'] = dim['timestamp'].dt.quarter
        dim['day_of_week'] = dim['timestamp'].dt.dayofweek
        dim['day_name'] = dim['timestamp'].dt.day_name()
        dim['month_name'] = dim['timestamp'].dt.month_name()
        dim['is_weekend'] = dim['day_of_week'].isin([5, 6])
        
        self.save_table(dim, 'dim_time')
        print(f"✓ Created {len(dim)} time dimensions")
        return dim
    
    def build_fact_seismic_readings(self):
        """Fact Table: Seismic Readings"""
        print("\n" + "="*60)
        print("Building fact_seismic_readings...")
        print("="*60)
        
        link = pd.read_parquet(self.vault_dir / 'link_seismic_reading.parquet')
        sat = pd.read_parquet(self.vault_dir / 'sat_seismic_measurements.parquet')
        
        fact = sat.merge(link, on='link_hash_key', suffixes=('', '_link'))
        
        possible_cols = [
            'link_hash_key', 'well_hash_key', 'survey_hash_key', 'sensor_hash_key',
            'depth_ft', 'amplitude', 'quality_flag', 'trace_num', 'timestamp',
            'record_source', 'record_source_link', 'load_timestamp', 'source_file'
        ]
        
        fact_cols = [col for col in possible_cols if col in fact.columns]
        fact = fact[fact_cols]
        
        if 'record_source' in fact.columns:
            source_col = 'record_source'
        elif 'record_source_link' in fact.columns:
            source_col = 'record_source_link'
        elif 'source_file' in fact.columns:
            source_col = 'source_file'
        else:
            fact['source_col'] = 'UNKNOWN'
            source_col = 'source_col'
        
        fact['data_quality_score'] = fact['quality_flag'] / 255.0
        fact['is_anomaly'] = (fact['amplitude'].abs() > fact['amplitude'].abs().quantile(0.95)).astype(int)
        
        fact['source_format'] = fact[source_col].apply(
            lambda x: 'SGX' if 'legacy' in str(x).lower() else 
                     ('PARQUET_ARCHIVE' if 'archive' in str(x).lower() else 'UNKNOWN')
        )
        
        self.save_table(fact, 'fact_seismic_readings')
        print(f"✓ Created {len(fact)} fact records")
        return fact
    
    def save_table(self, df: pd.DataFrame, table_name: str):
        """Save table to output directory"""
        output_path = self.output_dir / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        print(f"  → Saved to: {output_path}")
    
    def build_all(self):
        """Build complete dimensional model"""
        print("\n" + "="*70)
        print("DIMENSIONAL MODEL BUILDER - STAR SCHEMA")
        print("="*70)
        
        dim_well = self.build_dim_well()
        dim_survey = self.build_dim_survey()
        dim_sensor = self.build_dim_sensor()
        fact = self.build_fact_seismic_readings()
        dim_time = self.build_dim_time(fact)
        
        print("\n" + "="*70)
        print("✓ DIMENSIONAL MODEL BUILD COMPLETE!")
        print("="*70)
        
        return {
            'dim_well': dim_well,
            'dim_survey': dim_survey,
            'dim_sensor': dim_sensor,
            'dim_time': dim_time,
            'fact_seismic_readings': fact
        }


if __name__ == '__main__':
    builder = DimensionalModelBuilder(
        vault_dir='track_2_data_vault/vault_data',
        output_dir='track_3_analytics/data_marts'
    )
    
    tables = builder.build_all()
    
    print("\n" + "="*70)
    print("DIMENSIONAL MODEL SUMMARY")
    print("="*70)
    for name, df in tables.items():
        print(f"  {name}: {len(df)} records")
