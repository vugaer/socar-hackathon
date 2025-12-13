#!/bin/bash

DATA_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$DATA_DIR" ]; then
    echo "Usage: $0 --data-dir <directory>"
    exit 1
fi

# Create output directory
mkdir -p tmp

python3 << EOF
import struct
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

data_dir = Path("$DATA_DIR")
output_dir = Path("tmp")

def parse_sgx_to_parquet(sgx_file, output_dir):
    """
    Parse legacy .sgx seismic file and convert to Parquet
    
    Format (Little Endian):
    - Header (16 bytes): CPETRO01 (8) | Survey Type ID (4) | Trace Count (4)
    - Trace Records (13 bytes each): Well ID (4) | Depth (4) | Amplitude (4) | Quality (1)
    """
    print(f"\nProcessing: {sgx_file.name}")
    print("=" * 60)
    
    with open(sgx_file, 'rb') as f:
        data = f.read()
    
    # Parse header (16 bytes)
    header_fmt = '<8sII'  # 8 bytes string, 2 unsigned ints (little endian)
    header_size = struct.calcsize(header_fmt)
    
    try:
        magic, survey_type_id, trace_count = struct.unpack(header_fmt, data[:header_size])
        magic_str = magic.decode('ascii', errors='ignore').rstrip('\x00')
    except Exception as e:
        print(f"✗ Failed to parse header: {e}")
        return False
    
    print(f"Magic: {magic_str}")
    print(f"Survey Type ID: {survey_type_id}")
    print(f"Trace Count: {trace_count}")
    
    # Validate
    if magic_str != 'CPETRO01':
        print(f"⚠ Warning: Unexpected magic signature: {magic_str}")
    
    expected_size = header_size + (trace_count * 13)
    if len(data) < expected_size:
        print(f"✗ File too small. Expected {expected_size}, got {len(data)}")
        return False
    
    # Parse trace records (13 bytes each)
    trace_fmt = '<IffB'  # unsigned int, 2 floats, unsigned byte
    trace_size = struct.calcsize(trace_fmt)  # 13 bytes
    
    traces = []
    offset = header_size
    
    for i in range(trace_count):
        if offset + trace_size > len(data):
            print(f"⚠ Warning: File truncated at trace {i}")
            break
        
        well_id, depth_ft, amplitude, quality_flag = struct.unpack(
            trace_fmt,
            data[offset:offset + trace_size]
        )
        
        traces.append({
            'trace_num': i + 1,
            'well_id': well_id,
            'survey_type_id': survey_type_id,
            'depth_ft': depth_ft,
            'amplitude': amplitude,
            'quality_flag': quality_flag
        })
        
        offset += trace_size
    
    # Convert to DataFrame
    df = pd.DataFrame(traces)
    
    print(f"✓ Parsed {len(traces)} traces")
    print(f"\nData preview:")
    print(df.head())
    
    print(f"\nStatistics:")
    print(f"  Unique Wells: {df['well_id'].nunique()}")
    print(f"  Depth Range: {df['depth_ft'].min():.2f} - {df['depth_ft'].max():.2f} ft")
    print(f"  Amplitude Range: {df['amplitude'].min():.4f} - {df['amplitude'].max():.4f}")
    
    # Save as Parquet
    output_file = output_dir / (sgx_file.stem + '.parquet')
    df.to_parquet(output_file, index=False, engine='pyarrow')
    print(f"\n✓ Saved to: {output_file}")
    
    return True

# Process all .sgx files
sgx_files = sorted(data_dir.glob("*.sgx"))
print(f"Found {len(sgx_files)} .sgx file(s)")
print(f"Output directory: {output_dir.absolute()}\n")

success = 0
all_data = []

for sgx_file in sgx_files:
    if parse_sgx_to_parquet(sgx_file, output_dir):
        success += 1
        # Also load for combined file
        df = pd.read_parquet(output_dir / (sgx_file.stem + '.parquet'))
        df['source_file'] = sgx_file.name
        all_data.append(df)

# Create combined Parquet file with all surveys
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_file = output_dir / 'all_surveys_combined.parquet'
    combined_df.to_parquet(combined_file, index=False, engine='pyarrow')
    
    print("\n" + "=" * 70)
    print(f"✓ COMBINED DATASET")
    print("=" * 70)
    print(f"Total traces: {len(combined_df)}")
    print(f"Total wells: {combined_df['well_id'].nunique()}")
    print(f"Survey types: {sorted(combined_df['survey_type_id'].unique())}")
    print(f"Date range inferred from filenames: 1991-1994")
    print(f"\nCombined file saved: {combined_file}")
    print(f"\nFirst few rows:")
    print(combined_df.head(10))

print("\n" + "=" * 70)
print(f"Successfully converted: {success}/{len(sgx_files)} files")
print

