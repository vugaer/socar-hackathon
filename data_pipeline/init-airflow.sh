#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL ready!"

echo "Installing dependencies..."
pip install --no-warn-script-location pandas pyarrow psycopg2-binary sqlalchemy pymongo redis scikit-learn joblib

echo "Initializing Airflow database..."
airflow db init

echo "Creating admin user..."
airflow users create \
    --username airflow \
    --password airflow \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || true

echo "Starting $1..."
exec airflow $1
