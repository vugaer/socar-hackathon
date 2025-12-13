import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import os

class SeismicPredictor:
    """ML models for seismic data prediction"""
    
    def __init__(self, data_marts_dir='data_marts'):
        self.data_marts_dir = data_marts_dir
        self.models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        self.scaler = StandardScaler()
        
    def prepare_time_series_data(self):
        """Prepare historical time series data"""
        df = pd.read_csv(os.path.join(self.data_marts_dir, 'mart_well_performance.csv'))
        
        # Create synthetic time series
        df['time_index'] = range(len(df))
        df = df.sort_values('time_index')
        
        return df
    
    def train_model(self, model_type='linear'):
        """Train prediction model"""
        df = self.prepare_time_series_data()
        
        # Features: time_index, total_readings, data_quality_rate
        X = df[['time_index', 'total_readings', 'data_quality_rate']].values
        y = df['avg_amplitude'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        model = self.models[model_type]
        model.fit(X_scaled, y)
        
        return model
    
    def predict_future(self, model_type='linear', periods=5):
        """Predict future values"""
        df = self.prepare_time_series_data()
        model = self.train_model(model_type)
        
        # Generate future time points
        last_index = df['time_index'].max()
        future_indices = range(last_index + 1, last_index + periods + 1)
        
        # Use average values for other features
        avg_readings = df['total_readings'].mean()
        avg_quality = df['data_quality_rate'].mean()
        
        predictions = []
        for idx in future_indices:
            X_future = np.array([[idx, avg_readings, avg_quality]])
            X_future_scaled = self.scaler.transform(X_future)
            pred = model.predict(X_future_scaled)[0]
            
            predictions.append({
                'time_index': int(idx),
                'predicted_amplitude': float(pred),
                'model': model_type
            })
        
        return predictions
    
    def get_historical_snapshot(self, time_point):
        """Get data snapshot at specific time point (time travel)"""
        df = self.prepare_time_series_data()
        
        # Filter data up to time point
        snapshot = df[df['time_index'] <= time_point]
        
        return {
            'time_point': time_point,
            'wells_at_time': len(snapshot),
            'total_readings': int(snapshot['total_readings'].sum()),
            'avg_amplitude': float(snapshot['avg_amplitude'].mean()),
            'avg_quality': float(snapshot['data_quality_rate'].mean()),
            'wells': snapshot[['well_id', 'well_name', 'avg_amplitude', 'total_readings']].to_dict('records')
        }
