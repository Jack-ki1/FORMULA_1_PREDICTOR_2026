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
        showToast('CSV export — use HTML report and copy the table.');
    }
}
function triggerDownload(blob, filename) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}