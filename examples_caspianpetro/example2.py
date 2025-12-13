#!/usr/bin/env python3
"""Example usage of CaspianPetro library"""

from caspianpetro import SGXParser, ParquetRecovery, ForensicsTools

# Extract the hidden flag
print("=" * 70)
print("TASK 1: Extract Hidden Flag")
print("=" * 70)
forensics = ForensicsTools()
flags = forensics.extract_flags('data/track_1_forensics/archive_batch_seismic_readings.parquet')
print(f"Found: {flags[0] if flags else 'No flags found'}")

# Recover corrupted Parquet files
print("\n" + "=" * 70)
print("TASK 2: Recover Corrupted Parquet Files")
print("=" * 70)
ParquetRecovery.recover_directory(
    'data/track_1_forensics',
    'solutions/tmp',
    pattern='archive*.parquet'
)

# Parse legacy SGX files
print("\n" + "=" * 70)
print("TASK 3: Parse Legacy SGX Files")
print("=" * 70)
df = SGXParser.parse_directory('data/track_1_forensics', combine=True)
parser = SGXParser()
stats = parser.get_statistics(df)
print(f"\nStatistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n✅ All tasks completed successfully!")

