let wellsData = [];
let performanceData = [];
let sensorData = [];
let surveyData = [];
let map = null;
let predictionChart = null;
let timeRange = { min: 0, max: 20, current: 20 };

document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
    initializeTimeTravel();
});

async function loadAllData() {
    try {
        const [stats, wells, performance, sensors, surveys] = await Promise.all([
            fetch('/api/stats').then(r => r.json()),
            fetch('/api/wells_map').then(r => r.json()),
            fetch('/api/well_performance').then(r => r.json()),
            fetch('/api/sensor_analysis').then(r => r.json()),
            fetch('/api/survey_summary').then(r => r.json())
        ]);
        
        wellsData = wells;
        performanceData = performance;
        sensorData = sensors;
        surveyData = surveys;
        
        updateStats(stats);
        renderCharts();
        renderTables();
        
        console.log('✓ Data loaded');
    } catch (error) {
        console.error('Error:', error);
    }
}

async function initializeTimeTravel() {
    try {
        const range = await fetch('/api/time_range').then(r => r.json());
        timeRange = range;
        
        const slider = document.getElementById('timeSlider');
        slider.min = range.min_time;
        slider.max = range.max_time;
        slider.value = range.current_time;
        
        slider.oninput = function() {
            document.getElementById('timeDisplay').textContent = `Time: ${this.value}`;
        };
        
        console.log('✓ Time travel initialized');
    } catch (error) {
        console.error('Time travel init error:', error);
    }
}

async function loadTimeTravel() {
    const timePoint = document.getElementById('timeSlider').value;
    
    try {
        const snapshot = await fetch(`/api/time_travel/${timePoint}`).then(r => r.json());
        
        document.getElementById('snapshotStats').innerHTML = `
            <div class="stat-box">
                <strong>Time Point:</strong> ${snapshot.time_point}
            </div>
            <div class="stat-box">
                <strong>Wells Active:</strong> ${snapshot.wells_at_time}
            </div>
            <div class="stat-box">
                <strong>Total Readings:</strong> ${snapshot.total_readings.toLocaleString()}
            </div>
            <div class="stat-box">
                <strong>Avg Amplitude:</strong> ${snapshot.avg_amplitude.toFixed(4)}
            </div>
            <div class="stat-box">
                <strong>Data Quality:</strong> ${(snapshot.avg_quality * 100).toFixed(1)}%
            </div>
            <h4>Wells at this time:</h4>
            <ul>
                ${snapshot.wells.slice(0, 10).map(w => `
                    <li>Well ${w.well_id} (${w.well_name}): ${w.avg_amplitude.toFixed(2)} amplitude, ${w.total_readings} readings</li>
                `).join('')}
            </ul>
        `;
        
        console.log('✓ Time travel snapshot loaded');
    } catch (error) {
        console.error('Time travel error:', error);
        document.getElementById('snapshotStats').innerHTML = `<p style="color: red;">Error: ${error}</p>`;
    }
}

async function runPrediction() {
    const model = document.getElementById('modelSelect').value;
    const periods = document.getElementById('periodsInput').value;
    
    document.getElementById('predictionStats').innerHTML = '<p>Predicting... Please wait...</p>';
    
    try {
        const result = await fetch(`/api/predict?model=${model}&periods=${periods}`).then(r => r.json());
        
        document.getElementById('predictionStats').innerHTML = `
            <div class="stat-box">
                <strong>Model:</strong> ${result.model === 'linear' ? 'Linear Regression' : 'Random Forest'}
            </div>
            <div class="stat-box">
                <strong>Periods:</strong> ${result.periods} future time points
            </div>
            <h4>Predictions:</h4>
            <ul>
                ${result.predictions.map(p => `
                    <li>Time ${p.time_index}: Amplitude = ${p.predicted_amplitude.toFixed(4)}</li>
                `).join('')}
            </ul>
        `;
        
        // Create prediction chart
        renderPredictionChart(result.predictions);
        
        console.log('✓ Prediction complete');
    } catch (error) {
        console.error('Prediction error:', error);
        document.getElementById('predictionStats').innerHTML = `<p style="color: red;">Error: ${error}</p>`;
    }
}

function renderPredictionChart(predictions) {
    const ctx = document.getElementById('predictionChart');
    
    if (predictionChart) {
        predictionChart.destroy();
    }
    
    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: predictions.map(p => `T${p.time_index}`),
            datasets: [{
                label: 'Predicted Amplitude',
                data: predictions.map(p => p.predicted_amplitude),
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Future Amplitude Predictions'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: { display: true, text: 'Amplitude' }
                },
                x: {
                    title: { display: true, text: 'Time Point' }
                }
            }
        }
    });
}

function updateStats(stats) {
    document.getElementById('total-wells').textContent = stats.total_wells.toLocaleString();
    document.getElementById('total-sensors').textContent = stats.total_sensors.toLocaleString();
    document.getElementById('total-readings').textContent = stats.total_readings.toLocaleString();
    document.getElementById('data-quality').textContent = (stats.avg_data_quality * 100).toFixed(1) + '%';
    document.getElementById('total-anomalies').textContent = stats.total_anomalies.toLocaleString();
    document.getElementById('avg-amplitude').textContent = stats.avg_amplitude.toFixed(4);
}

function renderCharts() {
    const amplitudes = performanceData.map(d => d.avg_amplitude);
    const wellNames = performanceData.map(d => d.well_name || d.well_id);
    
    new Chart(document.getElementById('amplitudeChart'), {
        type: 'bar',
        data: {
            labels: wellNames.slice(0, 10),
            datasets: [{
                label: 'Average Amplitude',
                data: amplitudes.slice(0, 10),
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
    
    const sourceFormats = [...new Set(performanceData.map(d => d.source_format))];
    const qualityBySource = sourceFormats.map(format => {
        const filtered = performanceData.filter(d => d.source_format === format);
        return (filtered.reduce((sum, d) => sum + d.data_quality_rate, 0) / filtered.length) * 100;
    });
    
    new Chart(document.getElementById('qualityChart'), {
        type: 'doughnut',
        data: {
            labels: sourceFormats,
            datasets: [{
                data: qualityBySource,
                backgroundColor: ['rgba(102,126,234,0.8)', 'rgba(118,75,162,0.8)', 'rgba(255,99,132,0.8)']
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
}

function renderTables() {
    document.getElementById('performanceBody').innerHTML = performanceData.map(row => `
        <tr>
            <td>${row.well_id}</td>
            <td>${row.well_name || 'N/A'}</td>
            <td>${row.source_format}</td>
            <td>${row.total_readings.toLocaleString()}</td>
            <td>${row.avg_amplitude.toFixed(2)}</td>
            <td>${(row.data_quality_rate * 100).toFixed(1)}%</td>
            <td>${row.anomaly_count}</td>
        </tr>
    `).join('');
    
    document.getElementById('sensorBody').innerHTML = sensorData.map(row => `
        <tr>
            <td>${row.sensor_id}</td>
            <td>${row.sensor_type || 'N/A'}</td>
            <td>${row.manufacturer || 'N/A'}</td>
            <td>${row.total_readings.toLocaleString()}</td>
            <td>${(row.data_quality_rate * 100).toFixed(1)}%</td>
            <td>${row.avg_amplitude.toFixed(2)}</td>
        </tr>
    `).join('');
    
    document.getElementById('surveyBody').innerHTML = surveyData.map(row => `
        <tr>
            <td>${row.survey_type || 'N/A'}</td>
            <td>${row.source_format}</td>
            <td>${row.wells_surveyed}</td>
            <td>${row.total_readings.toLocaleString()}</td>
            <td>${row.avg_amplitude.toFixed(4)}</td>
            <td>${(row.avg_data_quality_rate * 100).toFixed(1)}%</td>
        </tr>
    `).join('');
}

function showSection(sectionId) {
    document.querySelectorAll('.dashboard-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    event.target.classList.add('active');
    
    if (sectionId === 'map' && !map) {
        initMap();
    }
}

function initMap() {
    map = L.map('mapContainer').setView([40.4093, 49.8671], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);
    
    wellsData.forEach(well => {
        L.marker([well.lat, well.lon]).addTo(map)
            .bindPopup(`<h3>${well.well_name}</h3><p><b>ID:</b> ${well.well_id}</p><p><b>Readings:</b> ${well.total_readings}</p><p><b>Anomalies:</b> ${well.anomaly_count}</p>`);
    });
    
    if (wellsData.length > 0) {
        map.fitBounds(L.latLngBounds(wellsData.map(w => [w.lat, w.lon])), {padding: [50,50]});
    }
}
