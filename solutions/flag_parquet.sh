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

# Use Python for reliable extraction
python3 << EOF
import re
from pathlib import Path

data_dir = Path("$DATA_DIR")

for parquet_file in data_dir.glob("*.parquet"):
    with open(parquet_file, 'rb') as f:
        data = f.read()
    
    # Search for FLAG{...} pattern
    match = re.search(rb'FLAG\{[A-Z0-9_]+\}', data)
    
    if match:
        print(match.group(0).decode('ascii'))
        break
EOF

