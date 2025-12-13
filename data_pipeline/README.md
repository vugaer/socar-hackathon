# SOCAR Hackathon - Data Pipeline

## Architecture

┌─────────────────┐
│ Data Sources │
│ (Data Vault) │
└────────┬────────┘
│
▼
┌─────────────────┐
│ Airflow │
│ Scheduler │
└────────┬────────┘
│
┌────┴────┐
│ DAGs │
└────┬────┘
│
┌────┴─────────────┬─────────────┐
▼ ▼ ▼
┌──────────┐ ┌──────────┐ ┌────────┐
│PostgreSQL│ │ MongoDB │ │ JSON │
│ (SQL) │ │ (NoSQL) │ │ Files │
└──────────┘ └──────────┘ └────────┘

text

## Components

1. **Apache Airflow** - Orchestration
2. **PostgreSQL** - SQL Database
3. **MongoDB** - NoSQL Database
4. **Redis** - Caching & Message Broker

## DAGs

### 1. seismic_etl_pipeline
- Extract from Data Vault
- Transform with anomaly detection
- Load to PostgreSQL, MongoDB, and JSON

### 2. realtime_monitoring
- Data freshness checks
- Anomaly monitoring
- Quality scoring
- Alert generation

### 3. ml_training_pipeline
- Prepare training data
- Train Linear Regression
- Train Random Forest
- Model selection
- Generate predictions

### 4. data_validation
- Schema validation
- Data type checks
- Range validation
- Report generation

## Usage

Start pipeline
./start_pipeline.sh

Access Airflow UI
http://localhost:8080
Username: airflow
Password: airflow

Stop pipeline
docker-compose down

View logs
docker-compose logs -f airflow-scheduler

text

## Scoring

- Docker setup: 100 pts ✅
- Airflow deployment: 75 pts ✅
- ETL DAGs (SQL/NoSQL): 25 pts ✅
- **Total: 200 pts**
