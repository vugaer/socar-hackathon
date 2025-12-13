import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIMENSIONAL_DB = os.path.join(BASE_DIR, 'dimensional_model.db')
SQL_DIR = os.path.join(BASE_DIR, 'sql')

# FIXED PATH - go up two levels, not one!
VAULT_DATA_DIR = '/home/hackathon/socar-hackathon/track_2_data_vault/vault_data'

def get_dimensional_connection():
    """Connect to Dimensional Model database"""
    return sqlite3.connect(DIMENSIONAL_DB)

def execute_sql_file(conn, filepath):
    """Execute SQL from file"""
    with open(filepath, 'r') as f:
        sql = f.read()
    cursor = conn.cursor()
    cursor.executescript(sql)
    conn.commit()
