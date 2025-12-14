#!/bin/bash

echo "================================================"
echo " SOCAR Pipeline - Fix & Deploy Script"
echo "================================================"

# Step 1: Stop everything
echo ""
echo "Step 1: Cleaning old containers..."
sudo docker-compose down -v
sudo docker rm -f socar_airflow_init socar_postgres socar_mongodb 2>/dev/null || true

# Step 2: Fix docker-compose.yml
echo ""
echo "Step 2: Fixing docker-compose.yml..."

cat > docker-compose.yml << 'EOF'
version: '3.8'

x-airflow-common: &airflow-common
  image: apache/airflow:2.10.4-python3.11
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'false'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG: 'true'
    _PIP_ADDITIONAL_REQUIREMENTS: 'pymongo pyarrow pandas sqlalchemy psycopg2-binary'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./data:/opt/airflow/data
    - ../track_2_data_vault/vault_data:/opt/airflow/vault_data:ro
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15-alpine
    container_name: socar_postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always
    networks:
      - socar_network

  mongodb:
    image: mongo:7.0
    container_name: socar_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin123
    volumes:
      - mongo-db-volume:/data/db
    ports:
      - "27017:27017"
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 20s
    restart: always
    networks:
      - socar_network

  airflow-webserver:
    <<: *airflow-common
    container_name: socar_airflow_webserver
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
    networks:
      - socar_network

  airflow-scheduler:
    <<: *airflow-common
    container_name: socar_airflow_scheduler
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
    networks:
      - socar_network

  airflow-init:
    <<: *airflow-common
    container_name: socar_airflow_init
    entrypoint: /bin/bash
    command:
      - -c
      - |
        echo "Initializing Airflow DB and creating admin user..."
        airflow db migrate
        airflow users create \
          --username airflow \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@socar.com \
          --password airflow || echo "User already exists"
        echo "Init complete!"
    environment:
      <<: *airflow-common-env
    user: "0:0"
    volumes:
      - ./:/sources
    networks:
      - socar_network

volumes:
  postgres-db-volume:
  mongo-db-volume:

networks:
  socar_network:
    driver: bridge
EOF

echo "✅ docker-compose.yml fixed"

# Step 3: Set Airflow UID
echo ""
echo "Step 3: Setting Airflow UID..."
echo "AIRFLOW_UID=$(id -u)" > .env
cat .env

# Step 4: Run init
echo ""
echo "Step 4: Running airflow-init..."
sudo docker-compose up airflow-init

# Wait for init to complete
sleep 5

# Step 5: Start all services
echo ""
echo "Step 5: Starting all services..."
sudo docker-compose up -d postgres mongodb airflow-webserver airflow-scheduler

# Wait for services to stabilize
echo ""
echo "⏳ Waiting 50 seconds for services to start..."
sleep 50

# Step 6: Check status
echo ""
echo "================================================"
echo " Service Status"
echo "================================================"
sudo docker-compose ps

echo ""
echo "================================================"
echo " Checking Airflow Health"
echo "================================================"
curl -s http://localhost:8080/health | grep -q "healthy" && echo "✅ Airflow Webserver is healthy!" || echo "⚠ Webserver still starting..."

echo ""
echo "================================================"
echo " ✅ DEPLOYMENT COMPLETE"
echo "================================================"
echo ""
echo "🌐 Airflow UI: http://localhost:8080"
echo "👤 Username: airflow"
echo "🔑 Password: airflow"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8080 in browser"
echo "  2. Login with airflow/airflow"
echo "  3. Check if DAG 'socar_seismic_etl' appears"
echo ""
echo "If DAG is not there yet, run:"
echo "  sudo docker-compose restart airflow-scheduler"
echo ""
