#!/usr/bin/env python3
"""
Flask Dashboard for Seismic Data Analytics
Modern UI with Plotly charts and Leaflet maps
"""

from flask import Flask, render_template, jsonify
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

app = Flask(__name__)

# Load data
DATA_DIR = Path(__file__).parent.parent / 'data_marts'

def load_data():
    """Load all data marts and dimensions"""
    return {
        'dim_well': pd.read_parquet(DATA_DIR / 'dim_well.parquet'),
        'dim_survey': pd.read_parquet(DATA_DIR / 'dim_survey.parquet'),
        'dim_sensor': pd.read_parquet(DATA_DIR / 'dim_sensor.parquet'),
        'fact': pd.read_parquet(DATA_DIR / 'fact_seismic_readings.parquet'),
        'mart_well': pd.read_parquet(DATA_DIR / 'mart_well_performance.parquet'),
        'mart_sensor': pd.read_parquet(DATA_DIR / 'mart_sensor_analysis.parquet'),
        'mart_survey': pd.read_parquet(DATA_DIR / 'mart_survey_summary.parquet')
    }

@app.route('/')
def index():
    """Main dashboard page"""
    data = load_data()
    
    # Calculate summary statistics
    stats = {
        'total_wells': len(data['dim_well']),
        'total_readings': len(data['fact']),
        'total_surveys': len(data['dim_survey']),
        'avg_quality': f"{data['fact']['data_quality_score'].mean():.2%}",
        'anomaly_count': int(data['fact']['is_anomaly'].sum())
    }
    
    return render_template('index.html', stats=stats)

@app.route('/api/wells_map')
def wells_map():
    """Get well locations for map"""
    data = load_data()
    dim_well = data['dim_well']
    fact = data['fact']
    
    # Join with fact to get reading counts
    well_stats = fact.groupby('well_hash_key').agg({
        'link_hash_key': 'count',
        'amplitude': 'mean',
        'data_quality_score': 'mean'
    }).reset_index()
    
    well_stats.columns = ['well_hash_key', 'reading_count', 'avg_amplitude', 'avg_quality']
    
    wells = dim_well.merge(well_stats, on='well_hash_key', how='left')
    
    # Filter wells with valid coordinates
    wells = wells[wells['latitude'].notna() & wells['longitude'].notna()]
    
    wells_json = wells.to_dict('records')
    return jsonify(wells_json)

@app.route('/api/amplitude_distribution')
def amplitude_distribution():
    """Amplitude distribution histogram"""
    data = load_data()
    fact = data['fact']
    
    fig = px.histogram(
        fact, 
        x='amplitude',
        nbins=50,
        title='Amplitude Distribution',
        labels={'amplitude': 'Amplitude', 'count': 'Frequency'},
        color_discrete_sequence=['#3b82f6']
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400,
        showlegend=False
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/quality_by_source')
def quality_by_source():
    """Data quality by source format"""
    data = load_data()
    fact = data['fact']
    
    quality = fact.groupby('source_format').agg({
        'data_quality_score': 'mean',
        'link_hash_key': 'count'
    }).reset_index()
    
    quality.columns = ['source_format', 'avg_quality', 'count']
    quality['avg_quality'] = quality['avg_quality'] * 100
    
    fig = px.bar(
        quality,
        x='source_format',
        y='avg_quality',
        title='Data Quality by Source Format',
        labels={'avg_quality': 'Average Quality (%)', 'source_format': 'Source Format'},
        color='avg_quality',
        color_continuous_scale='RdYlGn',
        text='count'
    )
    
    fig.update_traces(texttemplate='%{text} readings', textposition='outside')
    fig.update_layout(template='plotly_white', height=400)
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/anomaly_heatmap')
def anomaly_heatmap():
    """Anomaly heatmap by well and depth"""
    data = load_data()
    fact = data['fact'].merge(data['dim_well'], on='well_hash_key')
    
    # Create depth bins
    fact['depth_bin'] = pd.cut(fact['depth_ft'], bins=10)
    
    # Count anomalies
    heatmap_data = fact.groupby(['well_id', 'depth_bin'])['is_anomaly'].sum().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='depth_bin', columns='well_id', values='is_anomaly').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=[str(interval) for interval in heatmap_pivot.index],
        colorscale='Reds',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title='Anomaly Heatmap (Well vs Depth)',
        xaxis_title='Well ID',
        yaxis_title='Depth Range (ft)',
        template='plotly_white',
        height=500
    )
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/readings_timeline')
def readings_timeline():
    """Timeline of readings by source"""
    data = load_data()
    fact = data['fact']
    
    if 'timestamp' in fact.columns:
        fact['date'] = pd.to_datetime(fact['timestamp']).dt.date
        timeline = fact.groupby(['date', 'source_format']).size().reset_index(name='count')
        
        fig = px.line(
            timeline,
            x='date',
            y='count',
            color='source_format',
            title='Readings Timeline',
            labels={'count': 'Number of Readings', 'date': 'Date'}
        )
    else:
        # Fallback: show by source format only
        timeline = fact.groupby('source_format').size().reset_index(name='count')
        fig = px.bar(
            timeline,
            x='source_format',
            y='count',
            title='Readings by Source Format'
        )
    
    fig.update_layout(template='plotly_white', height=400)
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/well_performance')
def well_performance_data():
    """Well performance mart data"""
    data = load_data()
    mart = data['mart_well'].to_dict('records')
    return jsonify(mart)

@app.route('/api/sensor_analysis')
def sensor_analysis_data():
    """Sensor analysis mart data"""
    data = load_data()
    mart = data['mart_sensor'].to_dict('records')
    return jsonify(mart)

@app.route('/api/survey_summary')
def survey_summary_data():
    """Survey summary mart data"""
    data = load_data()
    mart = data['mart_survey'].to_dict('records')
    return jsonify(mart)

@app.route('/api/depth_amplitude_scatter')
def depth_amplitude_scatter():
    """Scatter plot: Depth vs Amplitude"""
    data = load_data()
    fact = data['fact'].sample(min(5000, len(data['fact'])))  # Sample for performance
    
    fig = px.scatter(
        fact,
        x='depth_ft',
        y='amplitude',
        color='source_format',
        title='Depth vs Amplitude Relationship',
        labels={'depth_ft': 'Depth (ft)', 'amplitude': 'Amplitude'},
        opacity=0.6
    )
    
    fig.update_layout(template='plotly_white', height=500)
    
    return jsonify(json.loads(fig.to_json()))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
