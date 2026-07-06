'use strict';

/* ══════════════════════════════════════════════════════════
   ANALYTICS — All functions now implemented
   FIX: evaluateRace, generateTemplate, runBacktest,
        runCalibration, optimizeWeights, loadAccuracyReport
        were all called but never defined.
══════════════════════════════════════════════════════════ */
function generateTemplate() {
    const circuit = document.getElementById('evalCircuit').value;
    if (!circuit) { showToast('Select a circuit first'); return; }
    const template = Object.entries(DRIVERS)
        .slice(0,20)
        .reduce((acc,[id],i) => { acc[id]=i+1; return acc; }, {});
    document.getElementById('resultsJson').value = JSON.stringify(template, null, 2);
    showToast('Template generated — fill in actual finishing positions');
}

async function evaluateRace() {
    const circuit  = document.getElementById('evalCircuit').value;
    const rawJson  = document.getElementById('resultsJson').value;
    if (!circuit) { showToast('Select a circuit first'); return; }
    let actual;
    try { actual = JSON.parse(rawJson); }
    catch { showToast('Invalid JSON — check your results data'); return; }

    showLoading('Evaluating race accuracy…');
    try {
        // FIX: Updated endpoint path to match backend
        const resp = await fetch('/api/evaluate/race', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({circuit_id: circuit, results: actual})
        });
        const data = await resp.json();
        hideLoading();
        if (data.status === 'success') {
            const metrics = data.metrics || {};
            renderResult('evaluationResults', `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> Evaluation complete for ${circuit}</div>
                <div class="metric-row"><span class="metric-lbl">Position MAE</span><span class="metric-val">${(metrics.mae||0).toFixed(2)}</span></div>
                <div class="metric-row"><span class="metric-lbl">Top-3 Accuracy</span><div class="metric-bar-wrap"><div class="metric-bar"><div class="metric-bar-fill" style="width:${(metrics.top3_accuracy||0)*100}%"></div></div></div><span class="metric-val">${((metrics.top3_accuracy||0)*100).toFixed(1)}%</span></div>
                <div class="metric-row"><span class="metric-lbl">Winner Correct</span><span class="metric-val">${metrics.winner_correct ? '✅ Yes' : '❌ No'}</span></div>
                <pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:200px;">${JSON.stringify(metrics, null, 2)}</pre>`);
        } else {
            renderResult('evaluationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Evaluation failed'}</div>`);
        }
    } catch(e) { hideLoading(); renderResult('evaluationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`); }
}

async function runBacktest() {
    const seasons = [];
    if (document.getElementById('season2024').checked) seasons.push(2024);
    if (document.getElementById('season2025').checked) seasons.push(2025);
    if (document.getElementById('season2026').checked) seasons.push(2026);
    if (!seasons.length) { showToast('Select at least one season'); return; }
    const sims = parseInt(document.getElementById('backtestSims').value)||10000;
    showLoading('Running historical backtest…');
    try {
        // FIX: Updated endpoint path to match backend
        const resp = await fetch('/api/backtest/run', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({seasons, sims})
        });
        const data = await resp.json();
        hideLoading();
        if (data.status === 'success') {
            renderResult('backtestResults', `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> Backtest complete across ${seasons.join(', ')}</div>
                <pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:300px;white-space:pre-wrap;">${data.output||'Backtest completed successfully'}</pre>`);
        } else {
            renderResult('backtestResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Backtest failed'}</div>`);
        }
    } catch(e) { hideLoading(); renderResult('backtestResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`); }
}

async function runCalibration() {
    const season = document.getElementById('calibrationSeason').value;
    showLoading('Running Platt calibration…');
    try {
        // FIX: Updated endpoint path to match backend
        const resp = await fetch('/api/calibration/run', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({season: parseInt(season)})
        });
        const data = await resp.json();
        hideLoading();
        if (data.status === 'success') {
            renderResult('calibrationResults', `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> Calibration complete for ${season}</div>
                <pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:300px;white-space:pre-wrap;">${data.output||'Calibration completed successfully'}</pre>`);
        } else {
            renderResult('calibrationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Calibration failed'}</div>`);
        }
    } catch(e) { hideLoading(); renderResult('calibrationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`); }
}

async function optimizeWeights() {
    const trials = parseInt(document.getElementById('optTrials').value)||100;
    showLoading('Running Bayesian optimization…');
    try {
        // FIX: Updated endpoint path to match backend
        const resp = await fetch('/api/optimize/weights', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({trials})
        });
        const data = await resp.json();
        hideLoading();
        if (data.status === 'success') {
            renderResult('optimizationResults', `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> Optimization complete — ${trials} trials</div>
                <pre style="margin-top:1rem;font-size:0.8rem;overflow:auto;max-height:300px;white-space:pre-wrap;">${data.output||'Optimization completed successfully'}</pre>`);
        } else {
            renderResult('optimizationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Optimization failed'}</div>`);
        }
    } catch(e) { hideLoading(); renderResult('optimizationResults', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`); }
}

async function loadAccuracyReport() {
    showLoading('Loading accuracy report…');
    try {
        // FIX: Updated endpoint path to match backend
        const resp = await fetch('/api/accuracy/report');
        const data = await resp.json();
        hideLoading();
        if (data.status === 'success') {
            const report = data.report || {};
            renderResult('accuracyReport', `
                <div class="alert alert-success"><i class="fas fa-check-circle"></i> Report loaded — ${(report.total_races||0)} races evaluated</div>
                <div class="metric-row"><span class="metric-lbl">Overall Accuracy</span><div class="metric-bar-wrap"><div class="metric-bar"><div class="metric-bar-fill" style="width:${(report.overall_accuracy||0)*100}%"></div></div></div><span class="metric-val">${((report.overall_accuracy||0)*100).toFixed(1)}%</span></div>
                <div class="metric-row"><span class="metric-lbl">Winner Prediction Rate</span><span class="metric-val">${((report.winner_accuracy||0)*100).toFixed(1)}%</span></div>
                <div class="metric-row"><span class="metric-lbl">Mean Position Error</span><span class="metric-val">${(report.mean_position_error||0).toFixed(2)}</span></div>
                <div class="metric-row"><span class="metric-lbl">Podium Accuracy</span><span class="metric-val">${((report.podium_accuracy||0)*100).toFixed(1)}%</span></div>`);
        } else {
            renderResult('accuracyReport', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${data.message||'Failed to load report'}</div>`);
        }
    } catch(e) { hideLoading(); renderResult('accuracyReport', `<div class="alert alert-error"><i class="fas fa-times-circle"></i> ${e.message}</div>`); }
}