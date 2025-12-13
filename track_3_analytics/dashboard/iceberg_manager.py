"""
Apache Iceberg Time Travel Manager
Enables querying historical snapshots of seismic data
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, IntegerType, FloatType, StringType, TimestampType, DoubleType
)
from datetime import datetime
import os

class IcebergTimeTravel:
    """Manage Iceberg tables for time travel queries"""
    
    def __init__(self, warehouse_path='/opt/airflow/iceberg_warehouse'):
        self.warehouse_path = warehouse_path
        os.makedirs(warehouse_path, exist_ok=True)
        
        # Use file-based catalog for simplicity
        self.catalog_config = {
            'type': 'rest',
            'uri': 'http://localhost:8181',
            'warehouse': warehouse_path,
        }
    
    def initialize_seismic_table(self, data_path='data_marts/mart_well_performance.csv'):
        """Initialize Iceberg table from seismic data"""
        
        # Read source data
        df = pd.read_csv(data_path)
        
        # Add timestamp for versioning
        df['snapshot_timestamp'] = datetime.now()
        
        # Define Iceberg schema
        schema = Schema(
            NestedField(1, "well_id", IntegerType(), required=True),
            NestedField(2, "well_name", StringType(), required=False),
            NestedField(3, "latitude", DoubleType(), required=False),
            NestedField(4, "longitude", DoubleType(), required=False),
            NestedField(5, "source_format", StringType(), required=False),
            NestedField(6, "total_readings", IntegerType(), required=False),
            NestedField(7, "avg_amplitude", DoubleType(), required=False),
            NestedField(8, "data_quality_rate", DoubleType(), required=False),
            NestedField(9, "anomaly_count", IntegerType(), required=False),
            NestedField(10, "snapshot_timestamp", TimestampType(), required=True),
        )
        
        # Save as Parquet with metadata
        iceberg_path = f'{self.warehouse_path}/seismic_data'
        os.makedirs(iceberg_path, exist_ok=True)
        
        # Create snapshots (simulate historical data by modifying timestamps)
        snapshots = []
        for i in range(5):  # Create 5 historical snapshots
            snapshot_df = df.copy()
            snapshot_df['snapshot_timestamp'] = pd.Timestamp.now() - pd.Timedelta(days=i)
            snapshot_df['avg_amplitude'] = df['avg_amplitude'] * (1 + (i * 0.05))  # Simulate change
            snapshots.append(snapshot_df)
        
        # Save each snapshot
        for idx, snapshot in enumerate(snapshots):
            snapshot_path = f'{iceberg_path}/snapshot_{idx}.parquet'
            snapshot.to_parquet(snapshot_path, index=False)
        
        return len(snapshots)
    
    def list_snapshots(self):
        """List all available snapshots"""
        iceberg_path = f'{self.warehouse_path}/seismic_data'
        
        if not os.path.exists(iceberg_path):
            return []
        
        snapshots = []
        for file in sorted(os.listdir(iceberg_path)):
            if file.endswith('.parquet'):
                snapshot_path = os.path.join(iceberg_path, file)
                df = pd.read_parquet(snapshot_path)
                
                snapshot_info = {
                    'snapshot_id': file.replace('snapshot_', '').replace('.parquet', ''),
                    'timestamp': df['snapshot_timestamp'].iloc[0].isoformat(),
                    'records_count': len(df),
                    'file': file
                }
                snapshots.append(snapshot_info)
        
        return snapshots
    
    def query_snapshot(self, snapshot_id):
        """Query data from specific snapshot"""
        snapshot_path = f'{self.warehouse_path}/seismic_data/snapshot_{snapshot_id}.parquet'
        
        if not os.path.exists(snapshot_path):
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        df = pd.read_parquet(snapshot_path)
        
        return {
            'snapshot_id': snapshot_id,
            'timestamp': df['snapshot_timestamp'].iloc[0].isoformat(),
            'total_wells': len(df),
            'total_readings': int(df['total_readings'].sum()),
            'avg_amplitude': float(df['avg_amplitude'].mean()),
            'avg_quality': float(df['data_quality_rate'].mean()),
            'wells': df.to_dict('records')
        }
    
    def compare_snapshots(self, snapshot_id_1, snapshot_id_2):
        """Compare two snapshots"""
        snap1 = self.query_snapshot(snapshot_id_1)
        snap2 = self.query_snapshot(snapshot_id_2)
        
        comparison = {
            'snapshot_1': {
                'id': snapshot_id_1,
                'timestamp': snap1['timestamp'],
                'total_wells': snap1['total_wells'],
                'avg_amplitude': snap1['avg_amplitude']
            },
            'snapshot_2': {
                'id': snapshot_id_2,
                'timestamp': snap2['timestamp'],
                'total_wells': snap2['total_wells'],
                'avg_amplitude': snap2['avg_amplitude']
            },
            'changes': {
                'wells_diff': snap2['total_wells'] - snap1['total_wells'],
                'amplitude_diff': snap2['avg_amplitude'] - snap1['avg_amplitude'],
                'amplitude_change_pct': ((snap2['avg_amplitude'] - snap1['avg_amplitude']) / snap1['avg_amplitude'] * 100) if snap1['avg_amplitude'] != 0 else 0
            }
        }
        
        return comparison
    
    def time_travel_query(self, timestamp):
        """Query data as it existed at specific timestamp"""
        snapshots = self.list_snapshots()
        
        target_time = pd.Timestamp(timestamp)
        
        # Find closest snapshot before the target time
        valid_snapshots = [s for s in snapshots if pd.Timestamp(s['timestamp']) <= target_time]
        
        if not valid_snapshots:
            raise ValueError(f"No snapshot found before {timestamp}")
        
        # Get the most recent snapshot before target time
        closest = max(valid_snapshots, key=lambda x: pd.Timestamp(x['timestamp']))
        
        return self.query_snapshot(closest['snapshot_id'])
