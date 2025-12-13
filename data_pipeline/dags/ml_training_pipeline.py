"""
ML Model Training and Prediction Pipeline
Trains ML models for seismic amplitude prediction
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

default_args = {
    'owner': 'socar',
    'start_date': datetime(2025, 12, 13),
    'retries': 1,
}

def prepare_training_data(**context):
    """Prepare data for ML training"""
    import pyarrow.parquet as pq
    
    measurements = pq.read_table('/opt/airflow/vault_data/sat_seismic_measurements.parquet').to_pandas()
    
    # Feature engineering
    measurements['amplitude_abs'] = measurements['amplitude'].abs()
    measurements['depth_km'] = measurements['depth_ft'] * 0.0003048
    
    # Create features
    features = measurements[['depth_km', 'trace_num', 'amplitude_abs']].dropna()
    
    print(f"✓ Prepared {len(features)} training samples")
    
    features.to_parquet('/opt/airflow/data/ml_training_data.parquet')
    
    return len(features)

def train_linear_model(**context):
    """Train Linear Regression model"""
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    import joblib
    
    data = pd.read_parquet('/opt/airflow/data/ml_training_data.parquet')
    
    X = data[['depth_km', 'trace_num']]
    y = data['amplitude_abs']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Linear Regression - MSE: {mse:.4f}, R²: {r2:.4f}")
    
    # Save model
    joblib.dump(model, '/opt/airflow/data/linear_model.pkl')
    
    context['task_instance'].xcom_push(key='linear_mse', value=mse)
    context['task_instance'].xcom_push(key='linear_r2', value=r2)

def train_random_forest(**context):
    """Train Random Forest model"""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    import joblib
    
    data = pd.read_parquet('/opt/airflow/data/ml_training_data.parquet')
    
    X = data[['depth_km', 'trace_num']]
    y = data['amplitude_abs']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Random Forest - MSE: {mse:.4f}, R²: {r2:.4f}")
    
    # Save model
    joblib.dump(model, '/opt/airflow/data/rf_model.pkl')
    
    context['task_instance'].xcom_push(key='rf_mse', value=mse)
    context['task_instance'].xcom_push(key='rf_r2', value=r2)

def select_best_model(**context):
    """Select best performing model"""
    ti = context['task_instance']
    
    linear_r2 = ti.xcom_pull(task_ids='train_linear_model', key='linear_r2')
    rf_r2 = ti.xcom_pull(task_ids='train_random_forest', key='rf_r2')
    
    best_model = 'Random Forest' if rf_r2 > linear_r2 else 'Linear Regression'
    
    print("=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)
    print(f"Linear Regression R²: {linear_r2:.4f}")
    print(f"Random Forest R²: {rf_r2:.4f}")
    print(f"Best Model: {best_model}")
    print("=" * 60)
    
    # Save model metadata
    import json
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'best_model': best_model,
        'linear_r2': linear_r2,
        'rf_r2': rf_r2
    }
    
    with open('/opt/airflow/data/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

def generate_predictions(**context):
    """Generate predictions using best model"""
    import joblib
    
    # Load best model (using RF for demo)
    model = joblib.load('/opt/airflow/data/rf_model.pkl')
    
    # Generate predictions for new data
    new_data = pd.DataFrame({
        'depth_km': np.linspace(1, 5, 100),
        'trace_num': np.arange(1, 101)
    })
    
    predictions = model.predict(new_data)
    new_data['predicted_amplitude'] = predictions
    
    # Save predictions
    new_data.to_csv('/opt/airflow/data/predictions.csv', index=False)
    
    print(f"✓ Generated {len(predictions)} predictions")

with DAG(
    'ml_training_pipeline',
    default_args=default_args,
    description='ML model training and prediction',
    schedule_interval='@weekly',
    catchup=False,
    tags=['ml', 'training', 'prediction'],
) as dag:
    
    prepare = PythonOperator(
        task_id='prepare_training_data',
        python_callable=prepare_training_data,
    )
    
    train_linear = PythonOperator(
        task_id='train_linear_model',
        python_callable=train_linear_model,
    )
    
    train_rf = PythonOperator(
        task_id='train_random_forest',
        python_callable=train_random_forest,
    )
    
    select = PythonOperator(
        task_id='select_best_model',
        python_callable=select_best_model,
    )
    
    predict = PythonOperator(
        task_id='generate_predictions',
        python_callable=generate_predictions,
    )
    
    prepare >> [train_linear, train_rf] >> select >> predict
