let wellsData = [];
let performanceData = [];
let sensorData = [];
let surveyData = [];
let map = null;
let snapshots = [];

document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
    loadSnapshots();
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

// Iceberg Time Travel Functions
async function loadSnapshots() {
    try {
        const response = await fetch('/api/iceberg/snapshots');
        snapshots = await response.json();
        
        // Update snapshot list
        const listHtml = snapshots.map(s => `
            <div class="snapshot-item">
                <strong>Snapshot ${s.snapshot_id}</strong><br>
                📅 ${new Date(s.timestamp).toLocaleString()}<br>
                📊 ${s.records_count} records
            </div>
        `).join('');
        
        document.getElementById('snapshotList').innerHTML = listHtml || '<p>No snapshots available</p>';
        
        // Populate dropdowns
        const options = snapshots.map(s => 
            `<option value="${s.snapshot_id}">Snapshot ${s.snapshot_id} (${new Date(s.timestamp).toLocaleString()})</option>`
        ).join('');
        
        document.getElementById('snapshotSelect').innerHTML = '<option value="">-- Select Snapshot --</option>' + options;
        document.getElementById('compareSnap1').innerHTML = '<option value="">-- Select --</option>' + options;
        document.getElementById('compareSnap2').innerHTML = '<option value="">-- Select --</option>' + options;
        
        console.log('✓ Loaded', snapshots.length, 'snapshots');
    } catch (error) {
        console.error('Error loading snapshots:', error);
        document.getElementById('snapshotList').innerHTML = '<p style="color: red;">Error loading snapshots</p>';
    }
}

async function querySnapshot() {
    const snapshotId = document.getElementById('snapshotSelect').value;
    
    if (!snapshotId) {
        alert('Please select a snapshot');
        return;
    }
    
    try {
        const response = await fetch(`/api/iceberg/snapshot/${snapshotId}`);
        const data = await response.json();
        
        document.getElementById('snapshotResult').innerHTML = `
            <div class="stat-box">
                <strong>Snapshot ID:</strong> ${data.snapshot_id}
            </div>
            <div class="stat-box">
                <strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}
            </div>
            <div class="stat-box">
                <strong>Total Wells:</strong> ${data.total_wells}
            </div>
            <div class="stat-box">
                <strong>Total Readings:</strong> ${data.total_readings.toLocaleString()}
            </div>
            <div class="stat-box">
                <strong>Avg Amplitude:</strong> ${data.avg_amplitude.toFixed(4)}
            </div>
            <div class="stat-box">
                <strong>Avg Quality:</strong> ${(data.avg_quality * 100).toFixed(1)}%
            </div>
        `;
        
        // Display data in table
        renderSnapshotTable(data.wells);
        
        console.log('✓ Snapshot queried');
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('snapshotResult').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

async function timeTravelQuery() {
    const timestamp = document.getElementById('timestampInput').value;
    
    if (!timestamp) {
        alert('Please select a timestamp');
        return;
    }
    
    try {
        const response = await fetch(`/api/iceberg/time_travel?timestamp=${timestamp}`);
        const data = await response.json();
        
        document.getElementById('snapshotResult').innerHTML = `
            <div class="stat-box">
                <strong>Time Travel To:</strong> ${new Date(timestamp).toLocaleString()}
            </div>
            <div class="stat-box">
                <strong>Snapshot Found:</strong> ${data.snapshot_id}
            </div>
            <div class="stat-box">
                <strong>Actual Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}
            </div>
            <div class="stat-box">
                <strong>Total Wells:</strong> ${data.total_wells}
            </div>
            <div class="stat-box">
                <strong>Avg Amplitude:</strong> ${data.avg_amplitude.toFixed(4)}
            </div>
        `;
        
        renderSnapshotTable(data.wells);
        
        console.log('✓ Time travel query complete');
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('snapshotResult').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

async function compareSnapshots() {
    const snap1 = document.getElementById('compareSnap1').value;
    const snap2 = document.getElementById('compareSnap2').value;
    
    if (!snap1 || !snap2) {
        alert('Please select two snapshots to compare');
        return;
    }
    
    try {
        const response = await fetch(`/api/iceberg/compare?snapshot1=${snap1}&snapshot2=${snap2}`);
        const data = await response.json();
        
        const changeIcon = data.changes.amplitude_diff > 0 ? '📈' : '📉';
        const changeColor = data.changes.amplitude_diff > 0 ? 'green' : 'red';
        
        document.getElementById('comparisonResult').innerHTML = `
            <h4>Snapshot ${snap1} vs ${snap2}</h4>
            
            <div class="comparison-grid">
                <div class="comparison-col">
                    <h5>Snapshot ${snap1}</h5>
                    <div class="stat-box">
                        <strong>Time:</strong> ${new Date(data.snapshot_1.timestamp).toLocaleString()}
                    </div>
                    <div class="stat-box">
                        <strong>Wells:</strong> ${data.snapshot_1.total_wells}
                    </div>
                    <div class="stat-box">
                        <strong>Amplitude:</strong> ${data.snapshot_1.avg_amplitude.toFixed(4)}
                    </div>
                </div>
                
                <div class="comparison-col">
                    <h5>Snapshot ${snap2}</h5>
                    <div class="stat-box">
                        <strong>Time:</strong> ${new Date(data.snapshot_2.timestamp).toLocaleString()}
                    </div>
                    <div class="stat-box">
                        <strong>Wells:</strong> ${data.snapshot_2.total_wells}
                    </div>
                    <div class="stat-box">
                        <strong>Amplitude:</strong> ${data.snapshot_2.avg_amplitude.toFixed(4)}
                    </div>
                </div>
            </div>
            
            <div class="stat-box" style="background: #f0f7ff; margin-top: 1rem;">
                <h5>${changeIcon} Changes</h5>
                <p><strong>Wells Difference:</strong> ${data.changes.wells_diff}</p>
                <p><strong>Amplitude Difference:</strong> <span style="color: ${changeColor}">${data.changes.amplitude_diff.toFixed(4)}</span></p>
                <p><strong>Change:</strong> <span style="color: ${changeColor}">${data.changes.amplitude_change_pct.toFixed(2)}%</span></p>
            </div>
        `;
        
        console.log('✓ Snapshot comparison complete');
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('comparisonResult').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

function renderSnapshotTable(wells) {
    const tbody = document.getElementById('snapshotDataBody');
    
    if (!wells || wells.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">No data</td></tr>';
        return;
    }
    
    tbody.innerHTML = wells.slice(0, 20).map(w => `
        <tr>
            <td>${w.well_id}</td>
            <td>${w.well_name || 'N/A'}</td>
            <td>${w.total_readings.toLocaleString()}</td>
            <td>${w.avg_amplitude.toFixed(2)}</td>
            <td>${(w.data_quality_rate * 100).toFixed(1)}%</td>
            <td>${w.anomaly_count}</td>
        </tr>
    `).join('');
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
