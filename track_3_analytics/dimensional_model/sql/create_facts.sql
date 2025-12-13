-- Fact: Sensor Readings
CREATE TABLE IF NOT EXISTS fact_sensor_reading (
    reading_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_key INTEGER,
    sensor_key INTEGER,
    time_key INTEGER,
    source_key INTEGER,
    timestamp TEXT,
    depth REAL,
    amplitude REAL,
    frequency REAL,
    phase REAL,
    quality_flag INTEGER,
    is_anomaly INTEGER DEFAULT 0,
    data_quality_score REAL,
    FOREIGN KEY (well_key) REFERENCES dim_well(well_key),
    FOREIGN KEY (sensor_key) REFERENCES dim_sensor(sensor_key),
    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (source_key) REFERENCES dim_data_source(source_key)
);

-- Fact: Survey Events
CREATE TABLE IF NOT EXISTS fact_survey_event (
    survey_key INTEGER PRIMARY KEY AUTOINCREMENT,
    well_key INTEGER,
    time_key INTEGER,
    source_key INTEGER,
    survey_id TEXT,
    survey_type TEXT,
    survey_start_date TEXT,
    survey_end_date TEXT,
    total_readings INTEGER,
    avg_amplitude REAL,
    data_quality_rate REAL,
    FOREIGN KEY (well_key) REFERENCES dim_well(well_key),
    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (source_key) REFERENCES dim_data_source(source_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_reading_well ON fact_sensor_reading(well_key);
CREATE INDEX IF NOT EXISTS idx_fact_reading_time ON fact_sensor_reading(time_key);
