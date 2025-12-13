#!/bin/bash
echo "============================================"
echo " SOCAR Hackathon - Data Pipeline Startup"
echo "============================================"

# Create necessary directories
mkdir -p logs plugins config scripts

# Set permissions
echo "Setting permissions..."
chmod -R 777 logs plugins config dags scripts

# Start Docker Compose
echo "Starting Airflow cluster..."
sudo docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 30

echo ""
echo "============================================"
echo "✅ Pipeline Started Successfully!"
echo "============================================"
echo "Airflow UI: http://localhost:8080"
echo "Username: airflow"
echo "Password: airflow"
echo ""
echo "PostgreSQL: localhost:5432"
echo "MongoDB: localhost:27017"
echo "============================================"
echo ""
echo "Available DAGs:"
echo "  1. seismic_etl_pipeline - Main ETL (SQL + NoSQL + JSON)"
echo "  2. realtime_monitoring - Data quality monitoring"
echo "  3. ml_training_pipeline - ML model training"
echo "  4. data_validation - Schema validation"
echo "============================================"
