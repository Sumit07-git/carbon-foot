// API Configuration
const API_BASE = 'http://localhost:5000/api';

// State
let state = {
    emissions: [],
    summary: {},
    predictions: {},
    recommendations: [],
    activityTypes: [],
    currentPeriod: 'all'
};

// Chart instances
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    setDefaultDate();
});

function initializeApp() {
    loadData();
}

function setupEventListeners() {
    // Tab Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = link.dataset.tab;
            switchTab(tabName);
        });
    });

    // Form Submission
    document.getElementById('emissionForm').addEventListener('submit', handleAddEmission);

    // Filter Buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.currentPeriod = e.target.dataset.period;
            loadEmissions();
        });
    });

    // Export Button
    document.getElementById('exportBtn')?.addEventListener('click', handleExportData);
}

function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date').value = today;
}

// Tab Switching
function switchTab(tabName) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.tab === tabName) {
            link.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Load data for specific tabs
    if (tabName === 'analytics') {
        setTimeout(() => initializeAnalyticsChart(), 100);
    }
}

// Loading
function showLoading() {
    document.getElementById('loading').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

// Data Loading
async function loadData() {
    showLoading();
    try {
        await Promise.all([
            loadActivityTypes(),
            loadSummary(),
            loadEmissions(),
            loadPredictions(),
            loadRecommendations()
        ]);
        updateDashboard();
    } catch (error) {
        console.error('Error loading data:', error);
        showNotification('Error loading data', 'error');
    } finally {
        hideLoading();
    }
}

async function loadActivityTypes() {
    try {
        const response = await fetch(`${API_BASE}/activity-types`);
        const data = await response.json();
        state.activityTypes = data.types || [];
        populateActivityTypes();
    } catch (error) {
        console.error('Error loading activity types:', error);
    }
}

function populateActivityTypes() {
    const select = document.getElementById('activityType');
    select.innerHTML = '<option value="">Select Activity Type</option>';
    state.activityTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        select.appendChild(option);
    });
}

async function loadSummary() {
    try {
        const response = await fetch(`${API_BASE}/get-summary`);
        state.summary = await response.json();
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

async function loadEmissions() {
    try {
        const response = await fetch(`${API_BASE}/get-emissions?period=${state.currentPeriod}`);
        const data = await response.json();
        state.emissions = data.records || [];
        displayActivities();
    } catch (error) {
        console.error('Error loading emissions:', error);
    }
}

async function loadPredictions() {
    try {
        const response = await fetch(`${API_BASE}/predict-emissions?days=30`);
        state.predictions = await response.json();
    } catch (error) {
        console.error('Error loading predictions:', error);
    }
}

async function loadRecommendations() {
    try {
        const response = await fetch(`${API_BASE}/get-recommendations`);
        const data = await response.json();
        state.recommendations = data.recommendations || [];
        displayRecommendations();
    } catch (error) {
        console.error('Error loading recommendations:', error);
    }
}

// Update Dashboard
function updateDashboard() {
    // Summary Cards
    document.getElementById('totalEmissions').textContent = 
        (state.summary.total_emissions_kg || 0).toFixed(2);
    document.getElementById('monthlyAverage').textContent = 
        (state.summary.monthly_average_kg || 0).toFixed(2);
    document.getElementById('topContributor').textContent = 
        (state.summary.top_contributor || 'N/A').toUpperCase();
    document.getElementById('totalRecords').textContent = 
        state.summary.total_records || 0;

    // Initialize Charts
    initializeCategoryChart();
    initializeTypeChart();
    initializePredictionChart();
}

// Charts
function initializeCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    if (charts.category) charts.category.destroy();

    const byCategory = state.summary.by_category || {};
    const labels = Object.keys(byCategory);
    const data = Object.values(byCategory);

    charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#10b981',
                    '#3b82f6',
                    '#f59e0b',
                    '#ef4444',
                    '#8b5cf6'
                ],
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function initializeTypeChart() {
    const ctx = document.getElementById('typeChart');
    if (!ctx) return;

    if (charts.type) charts.type.destroy();

    const byType = state.summary.by_type || {};
    const labels = Object.keys(byType);
    const data = Object.values(byType);

    charts.type = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Emissions (kg CO₂)',
                data: data,
                backgroundColor: '#10b981',
                borderColor: '#059669',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

function initializePredictionChart() {
    const ctx = document.getElementById('predictionChart');
    if (!ctx) return;

    if (charts.prediction) charts.prediction.destroy();

    const predictions = state.predictions.predictions || [];
    const labels = predictions.map(p => new Date(p.date).toLocaleDateString());
    const data = predictions.map(p => p.predicted_emissions_kg);

    charts.prediction = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted Emissions (kg CO₂)',
                data: data,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

function initializeAnalyticsChart() {
    const ctx = document.getElementById('analyticsChart');
    if (!ctx) return;

    if (charts.analytics) charts.analytics.destroy();

    const byType = state.summary.by_type || {};
    const labels = Object.keys(byType);
    const data = Object.values(byType);

    charts.analytics = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Emissions (kg CO₂)',
                data: data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });

    // Display Statistics
    displayStatistics();
}

function displayStatistics() {
    const table = document.getElementById('statisticsTable');
    if (!table) return;

    const stats = state.summary;
    table.innerHTML = `
        <div class="stat-row">
            <span class="stat-row-label">Total Records:</span>
            <span class="stat-row-value">${stats.total_records || 0}</span>
        </div>
        <div class="stat-row">
            <span class="stat-row-label">Total Emissions:</span>
            <span class="stat-row-value">${(stats.total_emissions_kg || 0).toFixed(2)} kg CO₂</span>
        </div>
        <div class="stat-row">
            <span class="stat-row-label">Monthly Average:</span>
            <span class="stat-row-value">${(stats.monthly_average_kg || 0).toFixed(2)} kg CO₂</span>
        </div>
        <div class="stat-row">
            <span class="stat-row-label">Top Contributor:</span>
            <span class="stat-row-value">${stats.top_contributor || 'N/A'}</span>
        </div>
    `;
}

// Display Activities
function displayActivities() {
    const list = document.getElementById('activitiesList');
    if (!list) return;

    if (state.emissions.length === 0) {
        list.innerHTML = '<p class="no-data">No activities logged yet</p>';
        return;
    }

    list.innerHTML = state.emissions.map(emission => `
        <div class="activity-item">
            <div class="activity-info">
                <h4>${emission.type}</h4>
                <p class="activity-meta">
                    ${emission.value} • 
                    ${new Date(emission.date).toLocaleDateString()} • 
                    ${emission.category}
                </p>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="activity-emissions">${emission.emissions.toFixed(2)} kg</span>
                <button class="btn btn-danger" onclick="deleteEmission('${emission.id}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Display Recommendations
function displayRecommendations() {
    const container = document.getElementById('recommendationsList');
    if (!container) return;

    if (state.recommendations.length === 0) {
        container.innerHTML = '<p class="no-data">No recommendations available. Log some activities first!</p>';
        return;
    }

    container.innerHTML = state.recommendations.map(rec => `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <div class="recommendation-icon">
                    <i class="fas fa-leaf"></i>
                </div>
                <div>
                    <p class="recommendation-title">
                        Switch from ${rec.current_activity} to ${rec.alternative}
                    </p>
                </div>
            </div>
            <p class="recommendation-description">${rec.description}</p>
            <div class="recommendation-stats">
                <div class="stat-box">
                    <p class="stat-label">Current Emissions</p>
                    <p class="stat-value">${rec.current_emissions_kg} kg</p>
                </div>
                <div class="stat-box">
                    <p class="stat-label">Potential Savings</p>
                    <p class="stat-value savings">${rec.potential_savings_kg} kg</p>
                </div>
                <div class="stat-box">
                    <p class="stat-label">Reduction</p>
                    <p class="stat-value">${rec.reduction_percent}%</p>
                </div>
                <div class="stat-box">
                    <p class="stat-label">Cost Benefit</p>
                    <p class="stat-value">${rec.cost_benefit}</p>
                </div>
            </div>
        </div>
    `).join('');
}

// Add Emission
async function handleAddEmission(e) {
    e.preventDefault();

    const formData = {
        type: document.getElementById('activityType').value,
        category: document.getElementById('category').value,
        value: parseFloat(document.getElementById('value').value),
        date: document.getElementById('date').value,
        notes: document.getElementById('notes').value
    };

    if (!formData.type || !formData.value) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    try {
        showLoading();
        const response = await fetch(`${API_BASE}/log-emission`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(`Activity logged! ${result.emissions_kg_co2} kg CO₂ added.`, 'success');
            document.getElementById('emissionForm').reset();
            setDefaultDate();
            loadData();
        } else {
            showNotification('Error logging activity', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error logging activity', 'error');
    } finally {
        hideLoading();
    }
}

// Delete Emission
async function deleteEmission(id) {
    if (!confirm('Are you sure you want to delete this activity?')) return;

    try {
        const response = await fetch(`${API_BASE}/delete-emission/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Activity deleted', 'success');
            loadData();
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error deleting activity', 'error');
    }
}

// Export Data
async function handleExportData() {
    try {
        const response = await fetch(`${API_BASE}/export-data`);
        const result = await response.json();
        
        const dataStr = JSON.stringify(result.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `carbon-emissions-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        showNotification('Data exported successfully', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error exporting data', 'error');
    }
}

// Notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);