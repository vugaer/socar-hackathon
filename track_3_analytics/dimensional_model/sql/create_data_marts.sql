-- Data Mart: Well Performance
CREATE VIEW IF NOT EXISTS mart_well_performance AS
SELECT 
    w.well_id,
    w.well_name,
    w.latitude,
    w.longitude,
    ds.source_format,
    COUNT(f.reading_key) as total_readings,
    AVG(f.amplitude) as avg_amplitude,
    AVG(CASE WHEN f.quality_flag = 1 THEN 1.0 ELSE 0.0 END) as data_quality_rate,
    SUM(CASE WHEN f.is_anomaly = 1 THEN 1 ELSE 0 END) as anomaly_count,
    MIN(f.timestamp) as first_reading,
    MAX(f.timestamp) as last_reading
FROM fact_sensor_reading f
JOIN dim_well w ON f.well_key = w.well_key
JOIN dim_data_source ds ON f.source_key = ds.source_key
WHERE w.is_current = 1
GROUP BY w.well_id, w.well_name, w.latitude, w.longitude, ds.source_format;

-- Data Mart: Sensor Analysis
CREATE VIEW IF NOT EXISTS mart_sensor_analysis AS
SELECT 
    s.sensor_id,
    s.sensor_type,
    s.manufacturer,
    COUNT(f.reading_key) as total_readings,
    AVG(CASE WHEN f.quality_flag = 1 THEN 1.0 ELSE 0.0 END) as data_quality_rate,
    AVG(f.amplitude) as avg_amplitude,
    MIN(f.timestamp) as first_reading,
    MAX(f.timestamp) as last_reading
FROM fact_sensor_reading f
JOIN dim_sensor s ON f.sensor_key = s.sensor_key
WHERE s.is_current = 1
GROUP BY s.sensor_id, s.sensor_type, s.manufacturer;

-- Data Mart: Survey Summary
CREATE VIEW IF NOT EXISTS mart_survey_summary AS
SELECT 
    se.survey_type,
    ds.source_format,
    COUNT(DISTINCT se.well_key) as wells_surveyed,
    SUM(se.total_readings) as total_readings,
    AVG(se.avg_amplitude) as avg_amplitude,
    AVG(se.data_quality_rate) as avg_data_quality_rate,
    MIN(se.survey_start_date) as earliest_survey,
    MAX(se.survey_end_date) as latest_survey
FROM fact_survey_event se
JOIN dim_data_source ds ON se.source_key = ds.source_key
GROUP BY se.survey_type, ds.source_format;
