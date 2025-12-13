// Initialize map
let map;
let markers = [];

function initMap() {
    // Default center (Azerbaijan/Caspian Sea)
    map = L.map('map').setView([40.4093, 49.8671], 8);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    
    // Load well locations
    fetch('/api/wells_map')
        .then(response => response.json())
        .then(data => {
            data.forEach(well => {
                if (well.latitude && well.longitude) {
                    const marker = L.circleMarker([well.latitude, well.longitude], {
                        radius: 8,
                        fillColor: getWellColor(well.avg_quality),
                        color: '#000',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    }).addTo(map);
                    
                    marker.bindPopup(`
                        <div class="p-2">
                            <h3 class="font-bold text-lg">${well.well_id}</h3>
                            <p><strong>Readings:</strong> ${well.reading_count || 0}</p>
                            <p><strong>Avg Amplitude:</strong> ${(well.avg_amplitude || 0).toFixed(2)}</p>
                            <p><strong>Quality:</strong> ${((well.avg_quality || 0) * 100).toFixed(1)}%</p>
                        </div>
                    `);
                    
                    markers.push(marker);
                }
            });
            
            // Fit bounds if we have markers
            if (markers.length > 0) {
                const group = new L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        });
}

function getWellColor(quality) {
    if (!quality) return '#gray';
    if (quality > 0.8) return '#10b981'; // green
    if (quality > 0.6) return '#f59e0b'; // yellow
    return '#ef4444'; // red
}

// Load charts
function loadCharts() {
    // Amplitude distribution
    fetch('/api/amplitude_distribution')
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('amplitudeChart', data.data, data.layout, {responsive: true});
        });
    
    // Quality by source
    fetch('/api/quality_by_source')
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('qualityChart', data.data, data.layout, {responsive: true});
        });
    
    // Timeline
    fetch('/api/readings_timeline')
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('timelineChart', data.data, data.layout, {responsive: true});
        });
    
    // Scatter plot
    fetch('/api/depth_amplitude_scatter')
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('scatterChart', data.data, data.layout, {responsive: true});
        });
    
    // Heatmap
    fetch('/api/anomaly_heatmap')
        .then(response => response.json())
        .then(data => {
            Plotly.newPlot('heatmapChart', data.data, data.layout, {responsive: true});
        });
}

// Load tables
function loadTables() {
    // Well performance
    fetch('/api/well_performance')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('wellTableBody');
            tbody.innerHTML = data.map(row => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.well_id}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.source_format}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.total_readings}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.avg_amplitude.toFixed(2)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(row.avg_quality_score * 100).toFixed(1)}%</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(row.anomaly_rate * 100).toFixed(2)}%</td>
                </tr>
            `).join('');
        });
    
    // Sensor analysis
    fetch('/api/sensor_analysis')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('sensorTableBody');
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No sensor data available (SGX files)</td></tr>';
            } else {
                tbody.innerHTML = data.map(row => `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.sensor_id}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.sensor_type || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.total_readings}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.avg_amplitude.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(row.reliability_score * 100).toFixed(1)}%</td>
                    </tr>
                `).join('');
            }
        });
    
    // Survey summary
    fetch('/api/survey_summary')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('surveyTableBody');
            tbody.innerHTML = data.map(row => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${row.survey_type_id}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.source_format}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.wells_surveyed}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.total_readings}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.avg_amplitude.toFixed(2)}</td>
                </tr>
            `).join('');
        });
}

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`table-${tabName}`).classList.remove('hidden');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadCharts();
    loadTables();
});
