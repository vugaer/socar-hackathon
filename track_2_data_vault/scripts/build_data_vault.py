#!/usr/bin/env python3
"""
Data Vault Builder for Seismic Data
Implements Data Vault 2.0 methodology
"""

import pandas as pd
import hashlib
from datetime import datetime
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DataVaultBuilder:
    """Build Data Vault 2.0 structure from source data"""
    
    def __init__(self, source_dir: str, vault_dir: str):
        self.project_root = Path(__file__).parent.parent.parent
        self.source_dir = self.project_root / source_dir
        self.vault_dir = self.project_root / vault_dir
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.load_timestamp = datetime.now().isoformat()
        
        print(f"Project root: {self.project_root}")
        print(f"Source dir: {self.source_dir}")
        print(f"Vault dir: {self.vault_dir}")
        
    def generate_hash_key(self, *values) -> str:
        """Generate hash key for Hub/Link"""
        combined = '|'.join(str(v) for v in values)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def add_metadata(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """Add Data Vault metadata columns"""
        df['load_timestamp'] = self.load_timestamp
        df['record_source'] = source_file
        return df
    
    def build_hub_well(self, master_wells: pd.DataFrame) -> pd.DataFrame:
        """Build Hub_Well"""
        print("\n" + "="*60)
        print("Building Hub_Well...")
        print("="*60)
        
        hub = pd.DataFrame()
        hub['well_hash_key'] = master_wells['well_id'].apply(
            lambda x: self.generate_hash_key('WELL', x)
        )
        hub['well_id'] = master_wells['well_id']
        hub = self.add_metadata(hub, 'master_wells.csv')
        
        hub = hub.drop_duplicates(subset=['well_hash_key'], keep='first')
        
        print(f"✓ Created {len(hub)} wells")
        return hub
    
    def build_hub_survey(self, master_surveys: pd.DataFrame) -> pd.DataFrame:
        """Build Hub_Survey"""
        print("\n" + "="*60)
        print("Building Hub_Survey...")
        print("="*60)
        
        hub = pd.DataFrame()
        hub['survey_hash_key'] = master_surveys['survey_type_id'].apply(
            lambda x: self.generate_hash_key('SURVEY', x)
        )
        hub['survey_type_id'] = master_surveys['survey_type_id']
        hub = self.add_metadata(hub, 'master_surveys.csv')
        
        hub = hub.drop_duplicates(subset=['survey_hash_key'], keep='first')
        
        print(f"✓ Created {len(hub)} surveys")
        return hub
    
    def build_hub_sensor(self, master_sensors: pd.DataFrame) -> pd.DataFrame:
        """Build Hub_Sensor"""
        print("\n" + "="*60)
        print("Building Hub_Sensor...")
        print("="*60)
        
        hub = pd.DataFrame()
        hub['sensor_hash_key'] = master_sensors['sensor_id'].apply(
            lambda x: self.generate_hash_key('SENSOR', x)
        )
        hub['sensor_id'] = master_sensors['sensor_id']
        hub = self.add_metadata(hub, 'master_sensors.csv')
        
        hub = hub.drop_duplicates(subset=['sensor_hash_key'], keep='first')
        
        print(f"✓ Created {len(hub)} sensors")
        return hub
    
    def build_sat_well_details(self, master_wells: pd.DataFrame, hub_well: pd.DataFrame) -> pd.DataFrame:
        """Build Satellite with Well details"""
        print("\n" + "="*60)
        print("Building Sat_Well_Details...")
        print("="*60)
        
        sat = master_wells.copy()
        
        sat['well_hash_key'] = sat['well_id'].apply(
            lambda x: self.generate_hash_key('WELL', x)
        )
        
        sat = self.add_metadata(sat, 'master_wells.csv')
        
        sat['hash_diff'] = sat.apply(
            lambda row: hashlib.md5(
                ''.join(str(row[col]) for col in sat.columns if col not in ['well_hash_key', 'load_timestamp', 'record_source']).encode()
            ).hexdigest(),
            axis=1
        )
        
        print(f"✓ Created {len(sat)} well detail records")
        return sat
    
    def build_sat_survey_details(self, master_surveys: pd.DataFrame) -> pd.DataFrame:
        """Build Satellite with Survey details"""
        print("\n" + "="*60)
        print("Building Sat_Survey_Details...")
        print("="*60)
        
        sat = master_surveys.copy()
        
        sat['survey_hash_key'] = sat['survey_type_id'].apply(
            lambda x: self.generate_hash_key('SURVEY', x)
        )
        
        sat = self.add_metadata(sat, 'master_surveys.csv')
        
        sat['hash_diff'] = sat.apply(
            lambda row: hashlib.md5(
                ''.join(str(row[col]) for col in sat.columns if col not in ['survey_hash_key', 'load_timestamp', 'record_source']).encode()
            ).hexdigest(),
            axis=1
        )
        
        print(f"✓ Created {len(sat)} survey detail records")
        return sat
    
    def build_sat_sensor_details(self, master_sensors: pd.DataFrame) -> pd.DataFrame:
        """Build Satellite with Sensor details"""
        print("\n" + "="*60)
        print("Building Sat_Sensor_Details...")
        print("="*60)
        
        sat = master_sensors.copy()
        
        sat['sensor_hash_key'] = sat['sensor_id'].apply(
            lambda x: self.generate_hash_key('SENSOR', x)
        )
        
        sat = self.add_metadata(sat, 'master_sensors.csv')
        
        sat['hash_diff'] = sat.apply(
            lambda row: hashlib.md5(
                ''.join(str(row[col]) for col in sat.columns if col not in ['sensor_hash_key', 'load_timestamp', 'record_source']).encode()
            ).hexdigest(),
            axis=1
        )
        
        print(f"✓ Created {len(sat)} sensor detail records")
        return sat
    
    def build_link_seismic_reading(self, seismic_data: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """Build Link connecting Well, Survey, Sensor (or Well+Survey if no sensor)"""
        print("\n" + "="*60)
        print(f"Building Link_Seismic_Reading from {source_file}...")
        print("="*60)
        
        link = pd.DataFrame()
        
        # Check if sensor_id exists (archive files have it, SGX files don't)
        has_sensor = 'sensor_id' in seismic_data.columns
        
        # Generate hash keys
        link['well_hash_key'] = seismic_data['well_id'].apply(
            lambda x: self.generate_hash_key('WELL', x)
        )
        link['survey_hash_key'] = seismic_data['survey_type_id'].apply(
            lambda x: self.generate_hash_key('SURVEY', x)
        )
        
        if has_sensor:
            link['sensor_hash_key'] = seismic_data['sensor_id'].apply(
                lambda x: self.generate_hash_key('SENSOR', x)
            )
            # Generate link hash key with sensor
            link['link_hash_key'] = seismic_data.apply(
                lambda row: self.generate_hash_key(
                    'READING', row['well_id'], row['survey_type_id'], 
                    row['sensor_id'], row.get('timestamp', row.get('trace_num', ''))
                ),
                axis=1
            )
        else:
            # No sensor - use null/default
            link['sensor_hash_key'] = None
            # Generate link hash key without sensor
            link['link_hash_key'] = seismic_data.apply(
                lambda row: self.generate_hash_key(
                    'READING', row['well_id'], row['survey_type_id'],
                    'NO_SENSOR', row.get('trace_num', '')
                ),
                axis=1
            )
        
        link = self.add_metadata(link, source_file)
        link = link.drop_duplicates(subset=['link_hash_key'], keep='first')
        
        print(f"✓ Created {len(link)} seismic reading links (sensor: {has_sensor})")
        return link
    
    def build_sat_seismic_measurements(self, seismic_data: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """Build Satellite with actual measurements"""
        print("\n" + "="*60)
        print(f"Building Sat_Seismic_Measurements from {source_file}...")
        print("="*60)
        
        sat = seismic_data.copy()
        
        # Check if sensor_id exists
        has_sensor = 'sensor_id' in seismic_data.columns
        
        # Generate link hash key
        if has_sensor:
            sat['link_hash_key'] = sat.apply(
                lambda row: self.generate_hash_key(
                    'READING', row['well_id'], row['survey_type_id'],
                    row['sensor_id'], row.get('timestamp', row.get('trace_num', ''))
                ),
                axis=1
            )
        else:
            sat['link_hash_key'] = sat.apply(
                lambda row: self.generate_hash_key(
                    'READING', row['well_id'], row['survey_type_id'],
                    'NO_SENSOR', row.get('trace_num', '')
                ),
                axis=1
            )
        
        sat = self.add_metadata(sat, source_file)
        
        # Hash diff for measurements
        sat['hash_diff'] = sat.apply(
            lambda row: hashlib.md5(
                f"{row['depth_ft']}{row['amplitude']}{row['quality_flag']}".encode()
            ).hexdigest(),
            axis=1
        )
        
        print(f"✓ Created {len(sat)} measurement records")
        return sat
    
    def save_vault_table(self, df: pd.DataFrame, table_name: str):
        """Save table to vault"""
        output_path = self.vault_dir / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        print(f"  → Saved to: {output_path}")
    
    def build_vault(self):
        """Main method to build entire vault"""
        print("\n" + "="*70)
        print("DATA VAULT 2.0 BUILDER")
        print("="*70)
        
        # Load master data
        print(f"\nLoading master data from: {self.source_dir}")
        master_wells = pd.read_csv(self.source_dir / 'master_wells.csv')
        master_surveys = pd.read_csv(self.source_dir / 'master_surveys.csv')
        master_sensors = pd.read_csv(self.source_dir / 'master_sensors.csv')
        
        print(f"✓ Loaded {len(master_wells)} wells")
        print(f"✓ Loaded {len(master_surveys)} surveys")
        print(f"✓ Loaded {len(master_sensors)} sensors")
        
        # Build Hubs
        hub_well = self.build_hub_well(master_wells)
        self.save_vault_table(hub_well, 'hub_well')
        
        hub_survey = self.build_hub_survey(master_surveys)
        self.save_vault_table(hub_survey, 'hub_survey')
        
        hub_sensor = self.build_hub_sensor(master_sensors)
        self.save_vault_table(hub_sensor, 'hub_sensor')
        
        # Build Satellites for master data
        sat_well = self.build_sat_well_details(master_wells, hub_well)
        self.save_vault_table(sat_well, 'sat_well_details')
        
        sat_survey = self.build_sat_survey_details(master_surveys)
        self.save_vault_table(sat_survey, 'sat_survey_details')
        
        sat_sensor = self.build_sat_sensor_details(master_sensors)
        self.save_vault_table(sat_sensor, 'sat_sensor_details')
        
        # Load and process seismic data
        seismic_dir = self.project_root / 'solutions' / 'tmp'
        print(f"\nLoading seismic data from: {seismic_dir}")
        
        all_links = []
        all_measurements = []
        
        for parquet_file in sorted(seismic_dir.glob('*.parquet')):
            print(f"\n  Processing: {parquet_file.name}")
            seismic_data = pd.read_parquet(parquet_file)
            
            # Build link and satellite
            link = self.build_link_seismic_reading(seismic_data, parquet_file.name)
            sat = self.build_sat_seismic_measurements(seismic_data, parquet_file.name)
            
            all_links.append(link)
            all_measurements.append(sat)
        
        # Combine all links and satellites
        if all_links:
            combined_links = pd.concat(all_links, ignore_index=True)
            combined_links = combined_links.drop_duplicates(subset=['link_hash_key'], keep='first')
            self.save_vault_table(combined_links, 'link_seismic_reading')
        
        if all_measurements:
            combined_measurements = pd.concat(all_measurements, ignore_index=True)
            self.save_vault_table(combined_measurements, 'sat_seismic_measurements')
        
        print("\n" + "="*70)
        print("✓ DATA VAULT BUILD COMPLETE!")
        print("="*70)
        
        return {
            'hub_well': hub_well,
            'hub_survey': hub_survey,
            'hub_sensor': hub_sensor,
            'link_seismic_reading': combined_links if all_links else None,
            'sat_seismic_measurements': combined_measurements if all_measurements else None
        }


if __name__ == '__main__':
    builder = DataVaultBuilder(
        source_dir='data',
        vault_dir='track_2_data_vault/vault_data'
    )
    
    vault_tables = builder.build_vault()
    
    print("\n" + "="*70)
    print("VAULT SUMMARY")
    print("="*70)
    for table_name, df in vault_tables.items():
        if df is not None:
            print(f"  {table_name}: {len(df)} records")
