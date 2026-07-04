'use strict';

/* ══════════════════════════════════════════════════════════
   SETTINGS — All functions now implemented
   FIX: migrateDatabase, syncFastF1, runQualityCheck,
        runBenchmark, initializeSystem were all called
        but never defined.
══════════════════════════════════════════════════════════ */
async function settingsCall(endpoint, body, resultElId, loadingMsg) {
    showLoading(loadingMsg);
    try {
        const resp = await fetch(endpoint, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: body ? JSON.stringify(body) : undefined
        });
        const data = await resp.json();
        hideLoading();
        // FIX: Check for 'status' field instead of 'success'
        if (data.status === 'success') {
            renderResult(resultElId, `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> ${data.message||'Operation complete'}</div>
                ${data.output ? `<pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:300px;white-space:pre-wrap;">${data.output}</pre>` : ''}
                ${data.details ? `<pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:200px;">${JSON.stringify(data.details,null,2)}</pre>` : ''}`);
        } else {
            renderResult(resultElId, `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||data.error||'Operation failed'}</div>`);
        }
    } catch(e) {
        hideLoading();
        renderResult(resultElId, `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`);
    }
}

function migrateDatabase() {
    // FIX: Updated endpoint path to match backend
    settingsCall('/api/database/migrate', {}, 'migrationStatus', 'Initialising database…');
}

function syncFastF1() {
    const seasons = [];
    if (document.getElementById('sync2024').checked) seasons.push(2024);
    if (document.getElementById('sync2025').checked) seasons.push(2025);
    if (!seasons.length) { showToast('Select at least one season to sync'); return; }
    // FIX: Updated endpoint path to match backend
    settingsCall('/api/sync/fastf1', {seasons}, 'syncStatus', 'Syncing FastF1 data…');
}

function runQualityCheck() {
    showLoading('Running quality checks…');
    try {
        // FIX: Updated endpoint path and method to match backend (GET instead of POST)
        fetch('/api/quality/check')
            .then(resp => resp.json())
            .then(data => {
                hideLoading();
                if (data.status === 'success') {
                    renderResult('qualityResults', `
                        <div class="alert alert-${data.passed ? 'success' : 'warning'}">
                            <i class="fas fa-${data.passed ? 'check-circle' : 'exclamation-triangle'}"></i> 
                            ${data.passed ? 'All quality checks passed' : 'Some warnings detected'}
                        </div>
                        <pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:300px;white-space:pre-wrap;">${data.output||''}</pre>
                        ${data.errors ? `<div class="alert alert-error" style="margin-top:1rem;"><pre>${data.errors}</pre></div>` : ''}`);
                } else {
                    renderResult('qualityResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Quality check failed'}</div>`);
                }
            })
            .catch(e => {
                hideLoading();
                renderResult('qualityResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`);
            });
    } catch(e) {
        hideLoading();
        renderResult('qualityResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`);
    }
}

function runBenchmark() {
    const circuit = document.getElementById('benchmarkCircuit').value;
    const sims    = parseInt(document.getElementById('benchmarkSims').value)||5000;
    // FIX: Updated endpoint path to match backend
    settingsCall('/api/benchmark/run', {circuit, sims}, 'benchmarkResults', 'Benchmarking engine…');
}

function initializeSystem() {
    // FIX: Updated endpoint path to match backend
    settingsCall('/api/setup/initialize', {}, 'setupStatus', 'Initialising all systems…');
}