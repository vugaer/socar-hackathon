#!/bin/bash

echo "================================================"
echo " Debugging DAG Failure"
echo "================================================"

# Check if packages are installed
echo ""
echo "1. Checking Python packages in Airflow..."
sudo docker exec socar_airflow_scheduler pip list | grep -E "pyarrow|pandas|pymongo|sqlalchemy"

# Check DAG import errors
echo ""
echo "2. Checking DAG import errors..."
sudo docker exec socar_airflow_scheduler airflow dags list-import-errors

# Check last task failure
echo ""
echo "3. Getting last task failure log..."
LATEST_LOG=$(sudo docker exec socar_airflow_scheduler find /opt/airflow/logs/dag_id=socar_seismic_etl -name "*.log" -type f | tail -1)
if [ -n "$LATEST_LOG" ]; then
    echo "Latest log: $LATEST_LOG"
    sudo docker exec socar_airflow_scheduler tail -100 "$LATEST_LOG"
fi

# Test DAG manually
echo ""
echo "4. Testing DAG tasks manually..."
sudo docker exec socar_airflow_scheduler airflow tasks test socar_seismic_etl extract_from_vault 2025-12-13

