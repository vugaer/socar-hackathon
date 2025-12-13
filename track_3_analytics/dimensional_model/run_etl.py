#!/usr/bin/env python3
import os
import sys
from config.db_config import *

def initialize_database():
    """Initialize dimensional database"""
    print("Initializing dimensional database...")
    conn = get_dimensional_connection()
    
    # Execute all SQL files
    sql_files = ['create_dimensions.sql', 'create_facts.sql', 'create_data_marts.sql']
    for sql_file in sql_files:
        filepath = os.path.join(SQL_DIR, sql_file)
        if os.path.exists(filepath):
            print(f"  Executing {sql_file}...")
            execute_sql_file(conn, filepath)
        else:
            print(f"  ⚠ {sql_file} not found")
    
    conn.close()
    print("✓ Database initialized\n")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" SEISMIC DATA ANALYTICS - DIMENSIONAL MODEL ETL ")
    print("=" * 60 + "\n")
    
    # Step 1: Initialize database
    initialize_database()
    
    # Step 2: Load dimensions
    print("=" * 60)
    print(" STEP 1: Loading Dimensions ")
    print("=" * 60)
    os.system('python3 etl/etl_dimensions.py')
    
    # Step 3: Load facts
    print("\n" + "=" * 60)
    print(" STEP 2: Loading Facts ")
    print("=" * 60)
    os.system('python3 etl/etl_facts.py')
    
    # Step 4: Export data marts
    print("\n" + "=" * 60)
    print(" STEP 3: Exporting Data Marts ")
    print("=" * 60)
    os.system('python3 etl/etl_data_marts.py')
    
    print("\n" + "=" * 60)
    print(" ✓ ETL PIPELINE COMPLETED SUCCESSFULLY! ")
    print("=" * 60 + "\n")
