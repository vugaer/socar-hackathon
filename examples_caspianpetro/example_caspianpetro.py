from caspianpetro import SGXParser, ParquetRecovery, ForensicsTools
from pathlib import Path

# 1. Extract flags from corrupted files
forensics = ForensicsTools()
flags = forensics.extract_flags_from_directory('data/track_1_forensics')
print("Found flags:", flags)

# 2. Recover corrupted Parquet files
recovery = ParquetRecovery()
ParquetRecovery.recover_directory(
    'data/track_1_forensics',
    'solutions/tmp',
    pattern='*.parquet'
)

# 3. Parse all SGX files
df_legacy = SGXParser.parse_directory('data/track_1_forensics', combine=True)
df_legacy.to_parquet('solutions/tmp/all_surveys_combined.parquet')

# 4. Load recovered data
import pandas as pd
df1 = pd.read_parquet('solutions/tmp/archive_batch_seismic_readings.parquet')
df2 = pd.read_parquet('solutions/tmp/archive_batch_seismic_readings_2.parquet')

# 5. Combine all data
df_all = pd.concat([df_legacy, df1, df2], ignore_index=True)
print(f"Total records: {len(df_all)}")

