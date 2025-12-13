"""SGX Parser - Legacy CPETRO01 Format"""

import struct
from pathlib import Path
from typing import Union, List, Dict
import pandas as pd


class SGXParser:
    """Parser for Caspian Petrochemical Legacy Seismic Format (.sgx)"""
    
    MAGIC_SIGNATURE = b'CPETRO01'
    HEADER_SIZE = 16
    TRACE_SIZE = 13
    HEADER_FORMAT = '<8sII'
    TRACE_FORMAT = '<IffB'
    
    def __init__(self):
        self.current_file = None
        self.header = None
        self.traces = []
    
    def parse_file(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Parse a single .sgx file"""
        filepath = Path(filepath)
        self.current_file = filepath.name
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        self.header = self._parse_header(data[:self.HEADER_SIZE])
        
        expected_size = self.HEADER_SIZE + (self.header['trace_count'] * self.TRACE_SIZE)
        if len(data) < expected_size:
            raise ValueError(f"File too small. Expected {expected_size}, got {len(data)}")
        
        self.traces = self._parse_traces(
            data[self.HEADER_SIZE:],
            self.header['trace_count'],
            self.header['survey_type_id']
        )
        
        df = pd.DataFrame(self.traces)
        df['source_file'] = filepath.name
        return df
    
    def _parse_header(self, header_data: bytes) -> Dict:
        """Parse 16-byte header"""
        magic, survey_type_id, trace_count = struct.unpack(self.HEADER_FORMAT, header_data)
        magic_str = magic.decode('ascii', errors='ignore').rstrip('\x00')
        
        if magic_str != 'CPETRO01':
            raise ValueError(f"Invalid magic signature: {magic_str}")
        
        return {
            'magic': magic_str,
            'survey_type_id': survey_type_id,
            'trace_count': trace_count
        }
    
    def _parse_traces(self, trace_data: bytes, trace_count: int, survey_type_id: int) -> List[Dict]:
        """Parse trace records"""
        traces = []
        offset = 0
        
        for i in range(trace_count):
            if offset + self.TRACE_SIZE > len(trace_data):
                break
            
            well_id, depth_ft, amplitude, quality_flag = struct.unpack(
                self.TRACE_FORMAT,
                trace_data[offset:offset + self.TRACE_SIZE]
            )
            
            traces.append({
                'trace_num': i + 1,
                'well_id': well_id,
                'survey_type_id': survey_type_id,
                'depth_ft': depth_ft,
                'amplitude': amplitude,
                'quality_flag': quality_flag
            })
            
            offset += self.TRACE_SIZE
        
        return traces
    
    @classmethod
    def parse_directory(cls, directory: Union[str, Path], pattern: str = "*.sgx", combine: bool = True):
        """Parse all .sgx files in a directory"""
        directory = Path(directory)
        parser = cls()
        
        sgx_files = sorted(directory.glob(pattern))
        if not sgx_files:
            raise FileNotFoundError(f"No .sgx files found in {directory}")
        
        dataframes = []
        print(f"Found {len(sgx_files)} .sgx file(s)\n")
        
        for sgx_file in sgx_files:
            try:
                df = parser.parse_file(sgx_file)
                dataframes.append(df)
                print(f"✓ {sgx_file.name}: {len(df)} traces")
            except Exception as e:
                print(f"✗ {sgx_file.name}: {e}")
        
        if combine and dataframes:
            combined = pd.concat(dataframes, ignore_index=True)
            print(f"\n✓ Combined: {len(combined)} total traces")
            return combined
        
        return dataframes
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """Get statistics from parsed data"""
        return {
            'total_traces': len(df),
            'unique_wells': df['well_id'].nunique(),
            'survey_types': sorted(df['survey_type_id'].unique().tolist()),
            'depth_range_ft': (float(df['depth_ft'].min()), float(df['depth_ft'].max())),
            'amplitude_range': (float(df['amplitude'].min()), float(df['amplitude'].max())),
        }
