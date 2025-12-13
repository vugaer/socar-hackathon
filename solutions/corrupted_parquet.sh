#!/bin/bash

DATA_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir)
            DATA_DIR="$1"
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

mkdir -p tmp

python3 << EOF
import struct
from pathlib import Path
import pandas as pd

data_dir = Path("$DATA_DIR")
output_dir = Path("tmp")

def fix_parquet(filepath, output_dir):
    """Fix corrupted Parquet file"""
    print(f"\nProcessing: {filepath.name}")
    print("=" * 60)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    file_size = len(data)
    print(f"Original file size: {file_size} bytes")
    
    # Check if hex-encoded
    if data[:2] in [b'50', b'35']:
        print("Detected hex-encoded file - decoding...")
        try:
            hex_string = data.decode('ascii').strip().replace('\n', '').replace(' ', '')
            data = bytes.fromhex(hex_string)
            print(f"✓ Decoded to {len(data)} binary bytes")
        except Exception as e:
            print(f"✗ Hex decoding failed: {e}")
            return False
    
    # Now process the binary data (whether originally binary or decoded)
    par1_positions = [i for i in range(len(data)-3) if data[i:i+4] == b'PAR1']
    print(f"PAR1 positions: {par1_positions}")
    
    if not par1_positions:
        print("✗ No PAR1 found")
        return False
    
    # If has multiple PAR1, truncate at the last one (removes appended data like flags)
    if len(par1_positions) >= 2 and par1_positions[0] == 0:
        cleaned_data = data[:par1_positions[-1] + 4]
        print(f"✓ Truncated to {len(cleaned_data)} bytes (removed appended data)")
    elif len(par1_positions) == 1:
        cleaned_data = data
        print("✓ Single PAR1 found, using as-is")
    else:
        cleaned_data = data
        print("⚠ Unexpected PAR1 structure, using as-is")
    
    # Save and verify
    output_file = output_dir / filepath.name
    with open(output_file, 'wb') as f:
        f.write(cleaned_data)
    
    try:
        df = pd.read_parquet(output_file)
        print(f"\n✓ SUCCESS!")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nData summary:")
        print(df.describe())
        print(f"\n✓ Saved to: {output_file}")
        return True
    except Exception as e:
        print(f"✗ Load failed: {e}")
        if output_file.exists():
            output_file.unlink()
        return False

# Process files
parquet_files = sorted(data_dir.glob("*.parquet"))
print(f"Found {len(parquet_files)} Parquet file(s)\n")

success = 0
for pf in parquet_files:
    if fix_parquet(pf, output_dir):
        success += 1

print("\n" + "=" * 70)
print(f"✓✓✓ FINAL RESULT: {success}/{len(parquet_files)} files recovered ✓✓✓")
print(f"Recovered files saved to: tmp/")
print("=" * 70)

EOF

