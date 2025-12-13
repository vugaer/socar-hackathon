#!/usr/bin/env python3
"""Data Marts Builder"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DataMartsBuilder:
    def __init__(self, dim_model_dir: str, output_dir: str):
        self.dim_model_dir = Path(dim_model_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.fact = pd.read_parquet(self.dim_model_dir / 'fact_seismic_readings.parquet')
        self.dim_well = pd.read_parquet(self.dim_model_dir / 'dim_well.parquet')
        self.dim_sensor = pd.read_parquet(self.dim_model_dir / 'dim_sensor.parquet')
        self.dim_survey = pd.read_parquet(self.dim_model_dir / 'dim_survey.parquet')
        
        print(f"Loaded fact table: {len(self.fact)} records")
        print(f"Fact columns: {self.fact.columns.tolist()}")
        print(f"Well columns: {self.dim_well.columns.tolist()}")
    
    def build_mart_well_performance(self):
        print("\n" + "="*60)
        print("Building mart_well_performance...")
        print("="*60)
        
        df = self.fact.merge(self.dim_well, on='well_hash_key')
        
        # Determine which groupby columns exist
        groupby_cols = ['well_id', 'source_format']
        optional_cols = ['well_name', 'field', 'operator']
        
        for col in optional_cols:
            if col in df.columns:
                groupby_cols.insert(-1, col)  # Insert before source_format
        
        print(f"Grouping by: {groupby_cols}")
        
        mart = df.groupby(groupby_cols).agg({
            'link_hash_key': 'count',
            'amplitude': ['mean', 'std', 'min', 'max'],
            'depth_ft': ['min', 'max'],
            'data_quality_score': 'mean',
            'is_anomaly': 'sum'
        }).reset_index()
        
        mart.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in mart.columns.values]
        
        mart.rename(columns={
            'link_hash_key_count': 'total_readings',
            'amplitude_mean': 'avg_amplitude',
            'amplitude_std': 'std_amplitude',
            'amplitude_min': 'min_amplitude',
            'amplitude_max': 'max_amplitude',
            'depth_ft_min': 'min_depth_ft',
            'depth_ft_max': 'max_depth_ft',
            'data_quality_score_mean': 'avg_quality_score',
            'is_anomaly_sum': 'anomaly_count'
        }, inplace=True)
        
        mart['anomaly_rate'] = mart['anomaly_count'] / mart['total_readings']
        mart['depth_range_ft'] = mart['max_depth_ft'] - mart['min_depth_ft']
        
        self.save_table(mart, 'mart_well_performance')
        print(f"✓ Created mart with {len(mart)} records")
        return mart
    
    def build_mart_sensor_analysis(self):
        print("\n" + "="*60)
        print("Building mart_sensor_analysis...")
        print("="*60)
        
        df = self.fact[self.fact['sensor_hash_key'].notna()].copy()
        
        if len(df) == 0:
            print("⚠ No sensor data available (SGX files don't have sensors)")
            empty_mart = pd.DataFrame(columns=[
                'sensor_id', 'sensor_type', 'manufacturer', 'total_readings',
                'avg_amplitude', 'std_amplitude', 'avg_quality_score',
                'anomaly_count', 'anomaly_rate', 'reliability_score'
            ])
            self.save_table(empty_mart, 'mart_sensor_analysis')
            return empty_mart
        
        df = df.merge(self.dim_sensor, on='sensor_hash_key')
        
        # Determine groupby columns
        groupby_cols = ['sensor_id']
        optional_cols = ['sensor_type', 'manufacturer', 'model']
        
        for col in optional_cols:
            if col in df.columns:
                groupby_cols.append(col)
        
        print(f"Grouping by: {groupby_cols}")
        
        mart = df.groupby(groupby_cols).agg({
            'link_hash_key': 'count',
            'amplitude': ['mean', 'std'],
            'data_quality_score': 'mean',
            'is_anomaly': ['sum', 'mean']
        }).reset_index()
        
        mart.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in mart.columns.values]
        
        mart.rename(columns={
            'link_hash_key_count': 'total_readings',
            'amplitude_mean': 'avg_amplitude',
            'amplitude_std': 'std_amplitude',
            'data_quality_score_mean': 'avg_quality_score',
            'is_anomaly_sum': 'anomaly_count',
            'is_anomaly_mean': 'anomaly_rate'
        }, inplace=True)
        
        mart['reliability_score'] = mart['avg_quality_score'] * (1 - mart['anomaly_rate'])
        
        self.save_table(mart, 'mart_sensor_analysis')
        print(f"✓ Created mart with {len(mart)} records")
        return mart
    
    def build_mart_survey_summary(self):
        print("\n" + "="*60)
        print("Building mart_survey_summary...")
        print("="*60)
        
        df = self.fact.merge(self.dim_survey, on='survey_hash_key')
        df = df.merge(self.dim_well[['well_hash_key', 'well_id']], on='well_hash_key')
        
        # Determine groupby columns
        groupby_cols = ['survey_type_id', 'source_format']
        optional_cols = ['survey_name', 'description']
        
        for col in optional_cols:
            if col in df.columns:
                groupby_cols.insert(-1, col)
        
        print(f"Grouping by: {groupby_cols}")
        
        # Check if timestamp exists
        has_timestamp = 'timestamp' in df.columns
        
        agg_dict = {
            'well_id': 'nunique',
            'link_hash_key': 'count',
            'amplitude': 'mean',
            'data_quality_score': 'mean'
        }
        
        if has_timestamp:
            agg_dict['timestamp'] = ['min', 'max']
        
        mart = df.groupby(groupby_cols).agg(agg_dict).reset_index()
        
        mart.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in mart.columns.values]
        
        rename_dict = {
            'well_id_nunique': 'wells_surveyed',
            'link_hash_key_count': 'total_readings',
            'amplitude_mean': 'avg_amplitude',
            'data_quality_score_mean': 'avg_quality_score'
        }
        
        if has_timestamp:
            rename_dict.update({
                'timestamp_min': 'first_reading',
                'timestamp_max': 'last_reading'
            })
        
        mart.rename(columns=rename_dict, inplace=True)
        
        if 'first_reading' in mart.columns and 'last_reading' in mart.columns:
            mart['survey_duration_days'] = (
                pd.to_datetime(mart['last_reading']) - pd.to_datetime(mart['first_reading'])
            ).dt.days
        
        self.save_table(mart, 'mart_survey_summary')
        print(f"✓ Created mart with {len(mart)} records")
        return mart
    
    def save_table(self, df: pd.DataFrame, table_name: str):
        output_path = self.output_dir / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        print(f"  → Saved to: {output_path}")
    
    def build_all(self):
        print("\n" + "="*70)
        print("DATA MARTS BUILDER")
        print("="*70)
        
        mart_well = self.build_mart_well_performance()
        mart_sensor = self.build_mart_sensor_analysis()
        mart_survey = self.build_mart_survey_summary()
        
        print("\n" + "="*70)
        print("✓ DATA MARTS BUILD COMPLETE!")
        print("="*70)
        
        return {
            'mart_well_performance': mart_well,
            'mart_sensor_analysis': mart_sensor,
            'mart_survey_summary': mart_survey
        }


if __name__ == '__main__':
    builder = DataMartsBuilder(
        dim_model_dir='track_3_analytics/data_marts',
        output_dir='track_3_analytics/data_marts'
    )
    
    marts = builder.build_all()
    
    print("\n" + "="*70)
    print("DATA MARTS SUMMARY")
    print("="*70)
    for name, df in marts.items():
        print(f"  {name}: {len(df)} records")
