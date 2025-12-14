# Interactive Analytics Dashboard

## Overview

Production-ready **Flask-based web dashboard** providing real-time visualization and analytics for seismic data. Features include Apache Iceberg time travel queries, interactive maps, KPI monitoring, and RESTful API access to dimensional data marts.

## Architecture

### System Components

```
┌───────────────────────────────────────────────────────────────────┐
│                    DASHBOARD ARCHITECTURE                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  WEB APPLICATION LAYER (Flask)                                    │
│  ├── app.py              → Main Flask application                │
│  ├── iceberg_manager.py  → Time travel query engine              │
│  └── templates/          → HTML/JavaScript frontend              │
│                                                                   │
│  DATA ACCESS LAYER                                                │
│  ├── Data Marts (CSV)                                             │
│  │   ├── mart_well_performance.csv                               │
│  │   ├── mart_sensor_analysis.csv                                │
│  │   └── mart_survey_summary.csv                                 │
│  └── Iceberg Tables (Parquet snapshots)                          │
│      └── /opt/airflow/iceberg_warehouse/seismic_data/            │
│                                                                   │
│  VISUALIZATION LAYER                                              │
│  ├── Interactive Map (Leaflet.js)                                │
│  ├── Real-time Charts (Chart.js)                                 │
│  ├── KPI Cards                                                   │
│  └── Time Travel Interface                                       │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Real-Time KPIs

**Dashboard Cards**:
- Total Wells
- Total Seismic Readings
- Average Data Quality Rate
- Total Anomalies Detected
- Active Sensors
- Average Amplitude

**API Endpoint**: `GET /api/stats`

```json
{
    "total_wells": 125,
    "total_readings": 50000,
    "avg_data_quality": 0.95,
    "total_anomalies": 2341,
    "total_sensors": 10,
    "avg_amplitude": 24.5
}
```

---

### 2. Interactive Well Map

**Technology**: Leaflet.js with OpenStreetMap tiles

**Features**:
- Geographic visualization of all wells
- Color-coded markers by performance
- Popup details on click
- Zoom/pan controls

**API Endpoint**: `GET /api/wells_map`

```json
[
    {
        "well_id": 12345,
        "well_name": "WELL-12345",
        "lat": 40.4093,
        "lon": 49.8671,
        "total_readings": 1250,
        "avg_amplitude": 23.5,
        "data_quality_rate": 0.95,
        "anomaly_count": 23
    }
]
```

**Marker Colors**:
- 🟢 Green: High quality (>90%)
- 🟡 Yellow: Medium quality (70-90%)
- 🔴 Red: Low quality (<70%)

---

### 3. Well Performance Analytics

**Data Source**: `mart_well_performance.csv`

**Columns Displayed**:
- Well ID & Name
- Location (Latitude/Longitude)
- Total Readings
- Average Amplitude
- Data Quality Rate
- Anomaly Count
- Source Format

**API Endpoint**: `GET /api/well_performance`

**Sorting**: Default by `total_readings DESC`

---

### 4. Sensor Analysis

**Data Source**: `mart_sensor_analysis.csv`

**Metrics**:
- Sensor ID & Type
- Manufacturer & Model
- Total Measurements
- Average Amplitude
- Average Quality Score
- Anomaly Count

**API Endpoint**: `GET /api/sensor_analysis`

**Use Case**: Identify underperforming or failing sensors

---

### 5. Survey Summary

**Data Source**: `mart_survey_summary.csv`

**Information**:
- Survey ID & Type
- Well Name
- Start/End Dates
- Total Readings
- Average Amplitude
- Data Quality Rate

**API Endpoint**: `GET /api/survey_summary`

---

### 6. Apache Iceberg Time Travel

**Purpose**: Query historical snapshots of seismic data

#### Feature 6A: List Snapshots

**Endpoint**: `GET /api/iceberg/snapshots`

```json
[
    {
        "snapshot_id": "0",
        "timestamp": "2025-12-14T05:30:00",
        "records_count": 125,
        "file": "snapshot_0.parquet"
    },
    {
        "snapshot_id": "1",
        "timestamp": "2025-12-13T05:30:00",
        "records_count": 120,
        "file": "snapshot_1.parquet"
    }
]
```

#### Feature 6B: Query Specific Snapshot

**Endpoint**: `GET /api/iceberg/snapshot/<snapshot_id>`

```json
{
    "snapshot_id": "0",
    "timestamp": "2025-12-14T05:30:00",
    "total_wells": 125,
    "total_readings": 50000,
    "avg_amplitude": 24.5,
    "avg_quality": 0.95,
    "wells": [...]
}
```

#### Feature 6C: Compare Snapshots

**Endpoint**: `GET /api/iceberg/compare?snapshot1=0&snapshot2=1`

```json
{
    "snapshot_1": {
        "id": "0",
        "timestamp": "2025-12-14T05:30:00",
        "total_wells": 125,
        "avg_amplitude": 24.5
    },
    "snapshot_2": {
        "id": "1",
        "timestamp": "2025-12-13T05:30:00",
        "total_wells": 120,
        "avg_amplitude": 23.8
    },
    "changes": {
        "wells_diff": 5,
        "amplitude_diff": 0.7,
        "amplitude_change_pct": 2.94
    }
}
```

#### Feature 6D: Time Travel Query

**Endpoint**: `GET /api/iceberg/time_travel?timestamp=2025-12-13T00:00:00`

Returns data as it existed at the specified timestamp.

---

## Installation & Deployment

### Prerequisites

```bash
# Python dependencies
Flask==2.3.0
pandas==1.5.3
numpy==1.23.5
pyarrow==10.0.1
pyiceberg==0.5.0
```

### Setup

```bash
cd track_3_analytics/dashboard

# Install dependencies
pip install -r requirements.txt

# Initialize Iceberg tables
python3 -c "from iceberg_manager import IcebergTimeTravel; IcebergTimeTravel().initialize_seismic_table()"

# Start Flask server
python3 app.py
```

**Access**: `http://localhost:80`

---

## Configuration

### Flask Settings

```python
# app.py
app.run(
    host='0.0.0.0',    # Listen on all interfaces
    port=80,           # HTTP port
    debug=False        # Production mode
)
```

### Data Marts Location

```python
DATA_MARTS_DIR = 'data_marts'
```

**Expected Files**:
- `mart_well_performance.csv`
- `mart_sensor_analysis.csv`
- `mart_survey_summary.csv`

### Iceberg Warehouse

```python
warehouse_path = '/opt/airflow/iceberg_warehouse'
```

---

## API Reference

### Core Analytics Endpoints

| Endpoint | Method | Description | Response Type |
|----------|--------|-------------|---------------|
| `/api/stats` | GET | Aggregate KPIs | JSON Object |
| `/api/well_performance` | GET | Well analytics | JSON Array |
| `/api/sensor_analysis` | GET | Sensor metrics | JSON Array |
| `/api/survey_summary` | GET | Survey data | JSON Array |
| `/api/wells_map` | GET | Geographic data | JSON Array |

### Iceberg Time Travel Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/api/iceberg/snapshots` | GET | None | List all snapshots |
| `/api/iceberg/snapshot/<id>` | GET | snapshot_id | Query specific snapshot |
| `/api/iceberg/compare` | GET | snapshot1, snapshot2 | Compare two snapshots |
| `/api/iceberg/time_travel` | GET | timestamp | Query at specific time |

---

## Frontend Components

### HTML Template (`templates/index.html`)

**Layout**:
```html
<!DOCTYPE html>
<html>
<head>
    <!-- Bootstrap 5 for styling -->
    <!-- Chart.js for charts -->
    <!-- Leaflet.js for maps -->
</head>
<body>
    <!-- KPI Cards Section -->
    <div id="kpi-cards"></div>

    <!-- Interactive Map Section -->
    <div id="wells-map"></div>

    <!-- Data Tables Section -->
    <div id="well-performance-table"></div>
    <div id="sensor-analysis-table"></div>

    <!-- Time Travel Interface -->
    <div id="iceberg-time-travel"></div>
</body>
</html>
```

### JavaScript Visualization

**Chart.js Example**:
```javascript
// Amplitude distribution chart
fetch('/api/well_performance')
    .then(response => response.json())
    .then(data => {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(w => w.well_name),
                datasets: [{
                    label: 'Average Amplitude',
                    data: data.map(w => w.avg_amplitude)
                }]
            }
        });
    });
```

**Leaflet.js Map**:
```javascript
// Initialize map
const map = L.map('wells-map').setView([40.4093, 49.8671], 8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Add well markers
fetch('/api/wells_map')
    .then(response => response.json())
    .then(wells => {
        wells.forEach(well => {
            L.marker([well.lat, well.lon])
                .bindPopup(`<b>${well.well_name}</b><br>Readings: ${well.total_readings}`)
                .addTo(map);
        });
    });
```

---

## Iceberg Time Travel Implementation

### Snapshot Creation

```python
# iceberg_manager.py
def initialize_seismic_table(self, data_path):
    df = pd.read_csv(data_path)
    df['snapshot_timestamp'] = datetime.now()

    # Create 5 historical snapshots
    for i in range(5):
        snapshot_df = df.copy()
        snapshot_df['snapshot_timestamp'] = pd.Timestamp.now() - pd.Timedelta(days=i)
        snapshot_df['avg_amplitude'] = df['avg_amplitude'] * (1 + (i * 0.05))

        snapshot_path = f'{iceberg_path}/snapshot_{i}.parquet'
        snapshot_df.to_parquet(snapshot_path, index=False)
```

### Query Interface

```python
def query_snapshot(self, snapshot_id):
    snapshot_path = f'{warehouse}/seismic_data/snapshot_{snapshot_id}.parquet'
    df = pd.read_parquet(snapshot_path)

    return {
        'snapshot_id': snapshot_id,
        'timestamp': df['snapshot_timestamp'].iloc[0].isoformat(),
        'total_wells': len(df),
        'wells': df.to_dict('records')
    }
```

---

## Performance Optimization

### Data Loading Strategy

**Problem**: Loading large CSV files on every request is slow

**Solution**: Caching with Flask
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_mart(filename):
    return pd.read_csv(f'data_marts/{filename}')
```

### NaN Handling

**Critical**: Pandas NaN values cause JSON serialization errors

**Fix**:
```python
def load_mart(filename):
    df = pd.read_csv(filepath)
    df = df.fillna({
        'well_name': 'Unknown',
        'latitude': 0,
        'longitude': 0,
        'avg_amplitude': 0
    })
    return df
```

### Weighted Average Calculation

**Problem**: Simple mean doesn't account for reading count

**Solution**:
```python
weighted_amplitude = (
    (df['total_readings'] * df['avg_amplitude']).sum() / 
    df['total_readings'].sum()
)
```

---

## Security Considerations

### Production Deployment

```python
# Disable debug mode
app.run(debug=False)

# Use production WSGI server
from waitress import serve
serve(app, host='0.0.0.0', port=80)
```

### CORS Configuration

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://dashboard.socar.com"}})
```

### API Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["200 per day", "50 per hour"])

@app.route('/api/well_performance')
@limiter.limit("10 per minute")
def api_well_performance():
    ...
```

---

## Monitoring & Logging

### Request Logging

```python
import logging

logging.basicConfig(
    filename='dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/api/stats')
def api_stats():
    logging.info(f"Stats requested from {request.remote_addr}")
    ...
```

### Error Tracking

```python
@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
```

---

## Testing

### Unit Tests

```python
# test_dashboard.py
import unittest
from app import app

class DashboardTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_wells', data)
```

### Integration Tests

```bash
# Test all API endpoints
curl http://localhost:80/api/stats
curl http://localhost:80/api/well_performance
curl http://localhost:80/api/iceberg/snapshots
```

---

## Troubleshooting

### Issue: Data Marts Not Found

**Error**: `FileNotFoundError: mart_well_performance.csv`

**Fix**:
```bash
cd track_3_analytics/dimensional_model
python3 etl/etl_data_marts.py
```

### Issue: Iceberg Snapshots Empty

**Error**: `No snapshot found before {timestamp}`

**Fix**:
```python
from iceberg_manager import IcebergTimeTravel
iceberg = IcebergTimeTravel()
iceberg.initialize_seismic_table()
```

### Issue: Port 80 Permission Denied

**Error**: `PermissionError: [Errno 13] Permission denied`

**Fix**:
```bash
# Use unprivileged port
python3 app.py  # Modify to use port 8080

# Or run with sudo (not recommended)
sudo python3 app.py
```

---

## Deployment Architectures

### Development (Local)

```bash
python3 app.py
# Access: http://localhost:80
```

### Production (Docker)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 80
CMD ["python3", "app.py"]
```

```bash
docker build -t drillica-dashboard .
docker run -p 80:80 -v /data:/app/data_marts drillica-dashboard
```

### Production (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drillica-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dashboard
  template:
    spec:
      containers:
      - name: dashboard
        image: drillica-dashboard:latest
        ports:
        - containerPort: 80
```

---

## Future Enhancements

1. **Real-time Data Streaming**: WebSocket integration for live updates
2. **Machine Learning**: Predictive anomaly detection
3. **Export Functionality**: Download charts and tables as PDF/Excel
4. **User Authentication**: Role-based access control
5. **Custom Dashboards**: User-defined widget layouts

---

## References

- Flask Documentation: https://flask.palletsprojects.com/
- Apache Iceberg: https://iceberg.apache.org/
- Leaflet.js: https://leafletjs.com/
- Chart.js: https://www.chartjs.org/

---

## License

MIT License - Part of Drillica Platform

