from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
import numpy as np
from ml_predictor import SeismicPredictor

app = Flask(__name__)

DATA_MARTS_DIR = 'data_marts'
predictor = SeismicPredictor(DATA_MARTS_DIR)

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
    
    weighted_amplitude = (df_well['total_readings'] * df_well['avg_amplitude']).sum() / df_well['total_readings'].sum()
    
    stats = {
        'total_wells': int(df_well['well_id'].nunique()),
        'total_readings': int(df_well['total_readings'].sum()),
        'avg_data_quality': float(df_well['data_quality_rate'].mean()),
        'total_anomalies': int(df_well['anomaly_count'].sum()),
        'total_sensors': int(df_sensor['sensor_id'].nunique()) if not df_sensor.empty else 1,
        'avg_amplitude': float(weighted_amplitude)
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

# NEW: Time Travel & Prediction Endpoints
@app.route('/api/time_travel/<int:time_point>')
def api_time_travel(time_point):
    """Time travel: Get historical snapshot"""
    try:
        snapshot = predictor.get_historical_snapshot(time_point)
        return jsonify(snapshot)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/predict')
def api_predict():
    """ML Prediction endpoint"""
    model_type = request.args.get('model', 'linear')  # linear or random_forest
    periods = int(request.args.get('periods', 5))
    
    try:
        predictions = predictor.predict_future(model_type, periods)
        return jsonify({
            'model': model_type,
            'periods': periods,
            'predictions': predictions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/time_range')
def api_time_range():
    """Get available time range for time travel"""
    df = predictor.prepare_time_series_data()
    return jsonify({
        'min_time': int(df['time_index'].min()),
        'max_time': int(df['time_index'].max()),
        'current_time': int(df['time_index'].max())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
