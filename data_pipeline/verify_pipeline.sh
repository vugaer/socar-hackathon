#!/bin/bash
echo "=========================================="
echo " SOCAR Data Pipeline Verification"
echo "=========================================="

# Check PostgreSQL
echo ""
echo "1. PostgreSQL (SQL):"
sudo docker exec data_pipeline_postgres_1 psql -U airflow -d airflow -c "SELECT COUNT(*) FROM seismic_well_summary;" 2>/dev/null || echo "  ⚠ Table not created yet"

# Check MongoDB
echo ""
echo "2. MongoDB (NoSQL):"
sudo docker exec data_pipeline_mongodb_1 mongosh --quiet --username admin --password admin123 --eval "db.getSiblingDB('seismic_data').measurements.countDocuments()" 2>/dev/null || echo "  ⚠ Collection not created yet"

# Check JSON exports
echo ""
echo "3. JSON Exports:"
sudo docker exec data_pipeline_airflow-scheduler_1 ls -lh /opt/airflow/data/exports/ 2>/dev/null || echo "  ⚠ No exports yet"

echo ""
echo "=========================================="
echo " Access Airflow UI: http://localhost:8080"
echo " Username: airflow | Password: airflow"
echo "=========================================="
