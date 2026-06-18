/**
 * Analytics & Settings Module - F1 Predictor Dashboard v3.1
 * 
 * All functions for:
 * - Database migration
 * - Race evaluation
 * - Backtesting
 * - Calibration
 * - Weight optimization
 * - Quality checks
 * - Benchmarking
 * - System initialization
 */

// ── Database Migration ────────────────────────────────────
async function migrateDatabase() {
    const statusDiv = document.getElementById('migrationStatus');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="spinner"></div><p>Migrating database...</p>';
    
    try {
        const response = await fetch('/api/database/migrate', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <strong>Database initialized!</strong><br>
                    Tables created: ${result.tables_created.join(', ')}<br>
                    Records migrated: ${result.records_migrated}
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Generate Results Template ─────────────────────────────
async function generateTemplate() {
    const circuit = document.getElementById('evalCircuit').value;
    if (!circuit) {
        showToast('Please select a circuit first');
        return;
    }
    
    try {
        const response = await fetch('/api/template/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({circuit_id: circuit})
        });
        
        const result = await response.json();
        
        // Auto-fill textarea with template
        document.getElementById('resultsJson').value = 
            JSON.stringify(result.template, null, 2);
        
        showToast('Template generated! Replace 0s with actual positions.');
    } catch (error) {
        showToast('Error: ' + error.message);
    }
}

// ── Evaluate Race ─────────────────────────────────────────
async function evaluateRace() {
    const circuit = document.getElementById('evalCircuit').value;
    const resultsText = document.getElementById('resultsJson').value;
    
    if (!circuit) {
        showToast('Please select a circuit');
        return;
    }
    
    let results;
    try {
        results = JSON.parse(resultsText);
    } catch (e) {
        showToast('Invalid JSON format');
        return;
    }
    
    const resultsDiv = document.getElementById('evaluationResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Evaluating...</p>';
    
    try {
        const response = await fetch('/api/evaluate/race', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                circuit_id: circuit,
                results: results
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const metrics = result.metrics;
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-check-circle"></i> Evaluation Complete</h4>
                    <table class="metrics-table">
                        <tr><td>Average Brier Score:</td><td><strong>${metrics.avg_brier_score.toFixed(4)}</strong></td></tr>
                        <tr><td>Predictions Evaluated:</td><td><strong>${metrics.predictions_evaluated}</strong></td></tr>
                        <tr><td>Circuit:</td><td><strong>${result.circuit}</strong></td></tr>
                    </table>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Backtesting ───────────────────────────────────────────
async function runBacktest() {
    const seasons = [];
    if (document.getElementById('season2024').checked) seasons.push(2024);
    if (document.getElementById('season2025').checked) seasons.push(2025);
    if (document.getElementById('season2026').checked) seasons.push(2026);
    
    const sims = parseInt(document.getElementById('backtestSims').value) || 10000;
    
    if (seasons.length === 0) {
        showToast('Please select at least one season');
        return;
    }
    
    const resultsDiv = document.getElementById('backtestResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Running backtest... This may take several minutes.</p>';
    
    try {
        const response = await fetch('/api/backtest/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ seasons, sims })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-check-circle"></i> Backtest Complete</h4>
                    <pre style="max-height: 400px; overflow-y: auto;">${result.output}</pre>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Calibration ───────────────────────────────────────────
async function runCalibration() {
    const season = document.getElementById('calibrationSeason').value;
    
    const resultsDiv = document.getElementById('calibrationResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Running calibration...</p>';
    
    try {
        const response = await fetch('/api/calibration/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ season: parseInt(season) })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-check-circle"></i> Calibration Complete</h4>
                    <pre style="max-height: 400px; overflow-y: auto;">${result.output}</pre>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Weight Optimization ───────────────────────────────────
async function optimizeWeights() {
    const trials = parseInt(document.getElementById('optTrials').value);
    
    const resultsDiv = document.getElementById('optimizationResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Optimizing weights... This may take 5-10 minutes.</p>';
    
    try {
        const response = await fetch('/api/optimize/weights', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ trials })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-check-circle"></i> Optimization Complete</h4>
                    <p>Trials completed: ${result.trials_completed}</p>
                    <pre style="max-height: 400px; overflow-y: auto;">${result.output}</pre>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Accuracy Report ───────────────────────────────────────
async function loadAccuracyReport() {
    const resultsDiv = document.getElementById('accuracyReport');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Loading accuracy report...</p>';
    
    try {
        const response = await fetch('/api/accuracy/report');
        const result = await response.json();
        
        if (result.status === 'success') {
            const report = result.report;
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <h4><i class="fas fa-chart-bar"></i> Accuracy Report</h4>
                    <pre style="max-height: 400px; overflow-y: auto;">${JSON.stringify(report, null, 2)}</pre>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── FastF1 Sync ───────────────────────────────────────────
async function syncFastF1() {
    const seasons = [];
    if (document.getElementById('sync2024').checked) seasons.push(2024);
    if (document.getElementById('sync2025').checked) seasons.push(2025);
    
    if (seasons.length === 0) {
        showToast('Please select at least one season');
        return;
    }
    
    const statusDiv = document.getElementById('syncStatus');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="spinner"></div><p>Syncing FastF1 data... This may take several minutes.</p>';
    
    try {
        const response = await fetch('/api/sync/fastf1', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ seasons })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <strong>Sync Complete</strong><br>
                    Seasons synced: ${result.seasons_synced.join(', ')}
                    <pre style="max-height: 200px; overflow-y: auto;">${result.output}</pre>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Quality Check ─────────────────────────────────────────
async function runQualityCheck() {
    const resultsDiv = document.getElementById('qualityResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Running quality checks...</p>';
    
    try {
        const response = await fetch('/api/quality/check');
        const result = await response.json();
        
        if (result.status === 'success') {
            const icon = result.passed ? 'fa-check-circle' : 'fa-exclamation-triangle';
            const color = result.passed ? 'alert-success' : 'alert-warning';
            
            resultsDiv.innerHTML = `
                <div class="alert ${color}">
                    <h4><i class="fas ${icon}"></i> Quality Check ${result.passed ? 'Passed' : 'Completed with Warnings'}</h4>
                    <pre style="max-height: 400px; overflow-y: auto;">${result.output}</pre>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── Benchmark ─────────────────────────────────────────────
async function runBenchmark() {
    const circuit = document.getElementById('benchmarkCircuit').value;
    const sims = parseInt(document.getElementById('benchmarkSims').value) || 5000;
    
    const resultsDiv = document.getElementById('benchmarkResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="spinner"></div><p>Running benchmark...</p>';
    
    try {
        const response = await fetch('/api/benchmark/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ circuit, sims })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            const bm = result.benchmark;
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-tachometer-alt"></i> Benchmark Results</h4>
                    <table class="metrics-table">
                        <tr><td>Vectorized Time:</td><td><strong>${bm.vectorized_time_ms.toFixed(2)} ms</strong></td></tr>
                        <tr><td>Original Time:</td><td><strong>${bm.original_time_ms.toFixed(2)} ms</strong></td></tr>
                        <tr><td>Speedup Factor:</td><td><strong>${bm.speedup_factor.toFixed(2)}x</strong></td></tr>
                        <tr><td>Max Probability Diff:</td><td><strong>${bm.max_prob_diff.toFixed(4)}</strong></td></tr>
                    </table>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Error:</strong> ${result.message}
                </div>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}

// ── System Initialization Wizard ──────────────────────────
async function initializeSystem() {
    const statusDiv = document.getElementById('setupStatus');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="spinner"></div><p>Initializing system... Please wait.</p>';
    
    try {
        const response = await fetch('/api/setup/initialize', { method: 'POST' });
        const result = await response.json();
        
        if (result.setup_complete) {
            let stepsHtml = result.steps.map(step => `
                <div style="margin: 0.5rem 0;">
                    <i class="fas fa-${step.status === 'success' ? 'check-circle' : 'times-circle'}" 
                       style="color: ${step.status === 'success' ? '#10b981' : '#ef4444'};"></i>
                    <strong>${step.step}:</strong> ${step.details}
                </div>
            `).join('');
            
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4><i class="fas fa-rocket"></i> Setup Complete!</h4>
                    ${stepsHtml}
                    <p style="margin-top: 1rem;"><strong>Next:</strong> Make your first prediction!</p>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Setup Failed</strong><br>
                    ${result.error}
                </div>
            `;
        }
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                <strong>Failed:</strong> ${error.message}
            </div>
        `;
    }
}
