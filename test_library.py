#!/usr/bin/env python3
"""Test CaspianPetro Library"""

from caspianpetro import SGXParser, ParquetRecovery, ForensicsTools

print("=" * 70)
print("Testing CaspianPetro Library")
print("=" * 70)

# Test 1: Extract flags
print("\n1. Extracting flags...")
forensics = ForensicsTools()
flags = forensics.extract_flags('data/track_1_forensics/archive_batch_seismic_readings.parquet')
if flags:
    print(f"   ✓ Found: {flags[0]}")
else:
    print("   ✗ No flags found")

# Test 2: Recover Parquet
print("\n2. Recovering Parquet files...")
try:
    ParquetRecovery.recover_directory(
        'data/track_1_forensics',
        'solutions/tmp',
        pattern='archive*.parquet'
    )
    print("   ✓ Parquet files recovered")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Parse SGX
print("\n3. Parsing SGX files...")
try:
    df = SGXParser.parse_directory('data/track_1_forensics', combine=True)
    print(f"   ✓ Parsed {len(df)} total traces")
    df.to_parquet('solutions/tmp/all_legacy_combined.parquet', index=False)
    print("   ✓ Saved to solutions/tmp/all_legacy_combined.parquet")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
