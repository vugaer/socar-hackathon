from flask import Flask, render_template, jsonify
import pandas as pd
import os
import json
import numpy as np

app = Flask(__name__)

DATA_MARTS_DIR = 'data_marts'

def load_mart(filename):
    """Load data mart CSV and handle NaN values"""
    filepath = os.path.join(DATA_MARTS_DIR, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df = df.fillna({
            'well_name': 'Unknown',
            'sensor_type': 'Unknown',
            'manufacturer': 'Unknown',
            'latitude': 0,
            'longitude': 0,
            'total_readings': 0,
            'avg_amplitude': 0,
            'data_quality_rate': 0,
            'anomaly_count': 0
        })
        return df
    return pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/well_performance')
def api_well_performance():
    df = load_mart('mart_well_performance.csv')
    if df.empty:
        return jsonify([])
    return jsonify(df.to_dict('records'))

@app.route('/api/sensor_analysis')
def api_sensor_analysis():
    df = load_mart('mart_sensor_analysis.csv')
    if df.empty:
        return jsonify([])
    return jsonify(df.to_dict('records'))

@app.route('/api/survey_summary')
def api_survey_summary():
    df = load_mart('mart_survey_summary.csv')
    if df.empty:
        return jsonify([])
    return jsonify(df.to_dict('records'))

@app.route('/api/stats')
def api_stats():
    """API: Aggregated statistics with WEIGHTED average"""
    df_well = load_mart('mart_well_performance.csv')
    df_sensor = load_mart('mart_sensor_analysis.csv')
    
    if df_well.empty:
        return jsonify({
            'total_wells': 0,
            'total_readings': 0,
            'avg_data_quality': 0,
            'total_anomalies': 0,
            'total_sensors': 0,
            'avg_amplitude': 0
        })
    
    # FIXED: Calculate weighted average amplitude
    # (sum of all readings * their avg amplitude) / total readings
    weighted_amplitude = (df_well['total_readings'] * df_well['avg_amplitude']).sum() / df_well['total_readings'].sum()
    
    stats = {
        'total_wells': int(df_well['well_id'].nunique()),
        'total_readings': int(df_well['total_readings'].sum()),
        'avg_data_quality': float(df_well['data_quality_rate'].mean()),
        'total_anomalies': int(df_well['anomaly_count'].sum()),
        'total_sensors': int(df_sensor['sensor_id'].nunique()) if not df_sensor.empty else 1,
        'avg_amplitude': float(weighted_amplitude)  # WEIGHTED average
    }
    
    return jsonify(stats)

@app.route('/api/wells_map')
def api_wells_map():
    df = load_mart('mart_well_performance.csv')
    if df.empty:
        return jsonify([])
    
    wells = []
    for _, row in df.iterrows():
        lat = float(row.get('latitude', 0))
        lon = float(row.get('longitude', 0))
        
        if lat != 0 and lon != 0:
            wells.append({
                'well_id': int(row['well_id']),
                'well_name': str(row['well_name']),
                'lat': lat,
                'lon': lon,
                'total_readings': int(row['total_readings']),
                'avg_amplitude': float(row['avg_amplitude']),
                'data_quality_rate': float(row['data_quality_rate']),
                'anomaly_count': int(row['anomaly_count'])
            })
    
    return jsonify(wells)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
