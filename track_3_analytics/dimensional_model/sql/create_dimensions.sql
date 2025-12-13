-- Dimension: Wells
CREATE TABLE IF NOT EXISTS dim_well (
    well_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id TEXT UNIQUE NOT NULL,
    well_name TEXT,
    latitude REAL,
    longitude REAL,
    basin TEXT,
    field TEXT,
    operator TEXT,
    spud_date TEXT,
    completion_date TEXT,
    well_status TEXT,
    total_depth REAL,
    effective_date TEXT,
    is_current INTEGER DEFAULT 1
);

-- Dimension: Sensors
CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_key INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT UNIQUE NOT NULL,
    sensor_type TEXT,
    manufacturer TEXT,
    model TEXT,
    installation_date TEXT,
    calibration_date TEXT,
    sensor_status TEXT,
    effective_date TEXT,
    is_current INTEGER DEFAULT 1
);

-- Dimension: Time
CREATE TABLE IF NOT EXISTS dim_time (
    time_key INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date TEXT UNIQUE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    week_of_year INTEGER,
    is_weekend INTEGER
);

-- Dimension: Data Source
CREATE TABLE IF NOT EXISTS dim_data_source (
    source_key INTEGER PRIMARY KEY AUTOINCREMENT,
    source_format TEXT UNIQUE NOT NULL,
    source_type TEXT,
    file_extension TEXT
);
