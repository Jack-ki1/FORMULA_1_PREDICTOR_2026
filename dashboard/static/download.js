'use strict';

/* ── Download ───────────────────────────────────────────── */
async function downloadReport(fmt) {
    const race = document.getElementById('dlRaceSelect').value;
    if (!race) { showToast('Please select a Grand Prix first.'); return; }
    if (fmt === 'html') {
        showToast('Generating HTML report…');
        window.open('/download-report/' + race, '_blank');
    } else if (fmt === 'json') {
        showLoading('Building JSON export…');
        try {
            const r = await fetch('/api/predict', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({race: Object.keys(CIRCUIT_LOOKUP).find(k=>CIRCUIT_LOOKUP[k]===race)||race, session_type:'RACE', simulations:10000})
            });
            const d = await r.json();
            hideLoading();
            triggerDownload(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}), race+'_prediction.json');
            showToast('JSON export downloaded');
        } catch(e) { hideLoading(); showToast('Error: '+e.message); }
    } else if (fmt === 'csv') {
        showLoading('Building CSV export…');
        try {
            const r = await fetch('/api/predict', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({race: Object.keys(CIRCUIT_LOOKUP).find(k=>CIRCUIT_LOOKUP[k]===race)||race, session_type:'RACE', simulations:10000})
            });
            const d = await r.json();
            hideLoading();
            const predictions = d.results?.predictions || d.prediction?.predictions || [];
            let csv = "Position,Driver,Team,Win_Pct,Top3_Pct,Top10_Pct,DNF_Pct,Expected_Points,Confidence\n";
            predictions.forEach((p, idx) => {
                const pos = p.predicted_position || (idx + 1);
                const name = `"${p.driver || p.driver_name || ''}"`;
                const team = `"${p.team || ''}"`;
                csv += `${pos},${name},${team},${p.win_pct || 0},${p.top3_pct || 0},${p.top10_pct || 0},${p.dnf_pct || 0},${p.expected_points || 0},${p.confidence || ''}\n`;
            });
            triggerDownload(new Blob([csv], {type:'text/csv;charset=utf-8;'}), race+'_prediction.csv');
            showToast('CSV export downloaded');
        } catch(e) { hideLoading(); showToast('Error: '+e.message); }
    }
}
function triggerDownload(blob, filename) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}