'use strict';

/* ── State ──────────────────────────────────────────────── */
let currentSession   = 'practice';
let lastPrediction   = null;
let currentCircuitId = null;
let currentRaceStatus = null;  // Track current race completion status

/* ── Race Status Management ────────────────────────────── */
async function checkAndDisplayRaceStatus(circuitId) {
    if (!circuitId) return;
    
    try {
        console.log('[Race Status] Checking status for circuit:', circuitId);
        const resp = await fetch(`/api/check-race-status/${circuitId}`);
        const data = await resp.json();
        
        console.log('[Race Status] Response:', data);
        
        if (!data.success) {
            console.warn('Failed to check race status:', data.error);
            showToast('Could not load race status');
            return;
        }
        
        currentRaceStatus = data;
        
        // Update weekend status banner with new message
        renderWeekendStatusBanner(
            { 
                strategy: data.completed ? 'post_race_analysis' : 'full_data',
                message: data.banner_message || ''
            },
            {}
        );
        
        // Update Run Prediction button based on race status
        updatePredictionButton(data);
        
        // If race is completed, show actual results instead of predictions
        if (data.completed) {
            console.log('[Race Status] Race completed - displaying actual results');
            displayActualResults(data);
        } else {
            console.log('[Race Status] Race upcoming - hiding actual results');
            hideActualResults();
        }
        
    } catch(err) {
        console.error('Error checking race status:', err);
        showToast('Error loading race status');
    }
}

function updatePredictionButton(statusData) {
    const btn = document.getElementById('runPredictionBtn');
    const btnText = document.getElementById('runPredictionBtnText');
    
    if (!btn || !btnText) return;
    
    // Remove all button classes
    btn.classList.remove('btn-primary', 'btn-success', 'btn-warning');
    
    // Set appropriate state
    if (statusData.button_state === 'completed') {
        btn.classList.add('btn-success');
        btnText.textContent = statusData.button_text || 'Race Complete - View Results';
        btn.disabled = false;  // Keep button enabled so user can click to view results
        btn.style.cursor = 'pointer';
        btn.style.opacity = '1';
        // Store race status for click handler
        btn.dataset.raceCompleted = 'true';
    } else {
        btn.classList.add('btn-primary');
        btnText.textContent = statusData.button_text || 'Run Prediction';
        btn.disabled = false;
        btn.style.cursor = 'pointer';
        btn.style.opacity = '1';
        btn.dataset.raceCompleted = 'false';
    }
}

function displayActualResults(statusData) {
    console.log('[Display Results] Called with statusData:', statusData);
    
    const panel = document.getElementById('panel-actual-results');
    if (!panel) {
        console.error('[Display Results] panel-actual-results not found!');
        return;
    }
    
    // Show the actual results panel
    panel.style.display = 'block';
    console.log('[Display Results] Showing actual results panel');
    
    // Hide prediction panels
    ['panel-practice', 'panel-qualifying', 'panel-sprint', 'panel-race'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    
    // Display race results if available
    const sessions = statusData.sessions || {};
    const highlightSession = statusData.highlight_session;
    
    console.log('[Display Results] Available sessions:', Object.keys(sessions));
    console.log('[Display Results] Highlight session:', highlightSession);
    
    // Reset session cycle index
    currentSessionIndex = -1;  // Will be incremented to 0 on first click
    
    // Auto-display the highlighted session or default to race
    let defaultSession = highlightSession || 'race';
    if (!sessions[defaultSession] || !sessions[defaultSession].results) {
        console.warn('[Display Results] Default session not available, finding fallback');
        // Fallback to first available session
        const availableSessions = sessionOrder.filter(s => sessions[s] && sessions[s].results);
        console.log('[Display Results] Available sessions in order:', availableSessions);
        if (availableSessions.length > 0) {
            defaultSession = availableSessions[0];
        } else {
            console.error('[Display Results] No sessions with results available!');
            showToast('No session results available for this race yet');
            return;
        }
    }
    
    console.log('[Display Results] Rendering session:', defaultSession);
    
    if (sessions[defaultSession] && sessions[defaultSession].results) {
        console.log('[Display Results] Session has', sessions[defaultSession].results.length, 'results');
        displaySessionResults(defaultSession, sessions[defaultSession]);
        
        // Update button text to show what's being displayed
        const btnText = document.getElementById('runPredictionBtnText');
        if (btnText) {
            const sessionNames = {
                'race': 'Race Results',
                'qualifying': 'Qualifying Results',
                'sprint': 'Sprint Race Results',
                'fp3': 'FP3 Results',
                'fp2': 'FP2 Results',
                'fp1': 'FP1 Results'
            };
            btnText.textContent = `Viewing: ${sessionNames[defaultSession] || defaultSession}`;
        }
    } else {
        // No results available
        console.error('[Display Results] Session exists but no results array');
        showToast('No session results available for this race yet');
    }
}

function renderActualRaceResults(raceData) {
    const tbody = document.getElementById('actualResultsBody');
    if (!tbody || !raceData.results) return;
    
    const results = Array.isArray(raceData.results) ? raceData.results : [];
    
    tbody.innerHTML = results.map((row, idx) => {
        const pos = row.Position || idx + 1;
        const driver = row.Abbreviation || row.Driver || '—';
        const team = row.TeamName || row.Constructor || '—';
        const grid = row.GridPosition || '—';
        const time = row.Time || row.Status || 'Finished';
        const points = row.Points || 0;
        const status = row.Status || 'Finished';
        
        const posClass = pos <= 3 ? `pos-${pos}` : 'pos-n';
        const statusClass = status.includes('Finished') || /^\+/.test(time) ? 'finished' : 'dnf';
        
        return `<tr>
            <td><span class="pos-badge ${posClass}">${pos}</span></td>
            <td class="driver-cell"><strong>${driver}</strong></td>
            <td style="font-size:0.85rem;color:var(--text-2);">${team}</td>
            <td>${grid}</td>
            <td>${time}</td>
            <td style="font-weight:700;">${points}</td>
            <td><span class="badge bg-${statusClass === 'finished' ? 'success' : 'secondary'}">${status}</span></td>
        </tr>`;
    }).join('');
}

function renderQualifyingResults(qualData) {
    const tbody = document.getElementById('qualifyingResultsBody');
    if (!tbody || !qualData.results) return;
    
    const results = Array.isArray(qualData.results) ? qualData.results : [];
    
    tbody.innerHTML = results.map((row, idx) => {
        const pos = row.Position || idx + 1;
        const driver = row.Abbreviation || row.Driver || '—';
        const team = row.TeamName || row.Constructor || '—';
        const q1 = row.Q1 || '—';
        const q2 = row.Q2 || '—';
        const q3 = row.Q3 || '—';
        
        return `<tr>
            <td><span class="pos-badge pos-${pos <= 3 ? pos : 'n'}">${pos}</span></td>
            <td class="driver-cell"><strong>${driver}</strong></td>
            <td style="font-size:0.85rem;color:var(--text-2);">${team}</td>
            <td>${q1 !== '—' ? q1 : ''}</td>
            <td>${q2 !== '—' ? q2 : ''}</td>
            <td>${q3 !== '—' ? q3 : ''}</td>
        </tr>`;
    }).join('');
}

function renderPracticeResults(sessions, sessionKeys) {
    const tbody = document.getElementById('practiceResultsBody');
    if (!tbody) return;
    
    let rows = [];
    
    sessionKeys.forEach(key => {
        const session = sessions[key];
        if (!session || !session.results) return;
        
        const sessionLabel = key.toUpperCase();
        const results = Array.isArray(session.results) ? session.results : [];
        
        results.slice(0, 10).forEach((row, idx) => {
            const pos = row.Position || idx + 1;
            const driver = row.Abbreviation || row.Driver || '—';
            const team = row.TeamName || row.Constructor || '—';
            const bestTime = row.BestLapTime || row.Time || '—';
            const laps = row.Laps || '—';
            
            rows.push(`<tr>
                <td><span class="badge bg-info">${sessionLabel}</span></td>
                <td><span class="pos-badge pos-${pos <= 3 ? pos : 'n'}">${pos}</span></td>
                <td class="driver-cell"><strong>${driver}</strong></td>
                <td style="font-size:0.85rem;color:var(--text-2);">${team}</td>
                <td>${bestTime}</td>
                <td>${laps}</td>
            </tr>`);
        });
    });
    
    tbody.innerHTML = rows.join('');
}

function hideActualResults() {
    const panel = document.getElementById('panel-actual-results');
    if (panel) panel.style.display = 'none';
    
    // Show prediction panels again
    ['panel-practice', 'panel-qualifying', 'panel-sprint', 'panel-race'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = '';
    });
}

let currentSessionIndex = 0;
const sessionOrder = ['race', 'qualifying', 'sprint', 'fp3', 'fp2', 'fp1'];

function cycleThroughSessionResults() {
    if (!currentRaceStatus || !currentRaceStatus.completed) return;
    
    const sessions = currentRaceStatus.sessions || {};
    const availableSessions = sessionOrder.filter(s => sessions[s] && sessions[s].results);
    
    if (availableSessions.length === 0) {
        showToast('No session results available for this race');
        return;
    }
    
    // Cycle to next session
    currentSessionIndex = (currentSessionIndex + 1) % availableSessions.length;
    const sessionType = availableSessions[currentSessionIndex];
    
    // Display the selected session
    displaySessionResults(sessionType, sessions[sessionType]);
    
    // Update button text to show what's being displayed
    const btnText = document.getElementById('runPredictionBtnText');
    if (btnText) {
        const sessionNames = {
            'race': 'Race Results',
            'qualifying': 'Qualifying Results',
            'sprint': 'Sprint Race Results',
            'fp3': 'FP3 Results',
            'fp2': 'FP2 Results',
            'fp1': 'FP1 Results'
        };
        btnText.textContent = `Viewing: ${sessionNames[sessionType] || sessionType}`;
    }
    
    showToast(`Showing ${sessionNames[sessionType] || sessionType}`);
}

function displaySessionResults(sessionType, sessionData) {
    // Hide all result cards first
    document.getElementById('qualifyingResultsCard').style.display = 'none';
    document.getElementById('practiceResultsCard').style.display = 'none';
    
    // Show the actual results panel
    const panel = document.getElementById('panel-actual-results');
    if (panel) panel.style.display = 'block';
    
    // Hide prediction panels
    ['panel-practice', 'panel-qualifying', 'panel-sprint', 'panel-race'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    
    // Display based on session type
    switch(sessionType) {
        case 'race':
            renderActualRaceResults(sessionData);
            document.getElementById('actualResultsDate').textContent = sessionData.date || '';
            break;
        case 'qualifying':
            renderQualifyingResults(sessionData);
            document.getElementById('qualifyingResultsCard').style.display = 'block';
            document.getElementById('actualResultsDate').textContent = sessionData.date || '';
            break;
        case 'sprint':
            renderActualRaceResults(sessionData); // Use same renderer as race
            document.getElementById('actualResultsDate').textContent = sessionData.date || '';
            break;
        case 'fp1':
        case 'fp2':
        case 'fp3':
            renderPracticeResults({[sessionType]: sessionData}, [sessionType]);
            document.getElementById('practiceResultsCard').style.display = 'block';
            document.getElementById('actualResultsDate').textContent = sessionData.date || '';
            break;
    }
}

/* ── Session switching ──────────────────────────────────── */
function selectSession(sess, el) {
    currentSession = sess;
    document.querySelectorAll('.session-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.session-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-' + sess).classList.add('active');
    const map = {practice:'PRACTICE', qualifying:'QUALIFYING', sprint:'SPRINT_QUALIFYING', race:'RACE'};
    document.getElementById('sessionTypeSelect').value = map[sess];
    showToast('Switched to ' + el.querySelector('.tab-day').textContent);
}

/* ── Sprint sub-tabs (Shootout / Sprint Race, inside the Sprint panel) ──── */
function selectSprintSubTab(which) {
    document.querySelectorAll('#panel-sprint .sub-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#panel-sprint .sub-panel').forEach(p => { p.classList.remove('active'); p.style.display = 'none'; });
    document.getElementById('subtab-' + which).classList.add('active');
    const panel = document.getElementById('subpanel-' + which);
    panel.classList.add('active');
    panel.style.display = 'block';
    document.getElementById('sessionTypeSelect').value = which === 'shootout' ? 'SPRINT_QUALIFYING' : 'SPRINT';
}

/* ── Weekend status banner: "has this race already happened" ────────────
   Renders the message/strategy computed server-side by get_weekend_phase(),
   and — when available — the already-computed data_confidence reasons list. */
function renderWeekendStatusBanner(phaseData, confidenceData) {
    const banner = document.getElementById('weekendStatusBanner');
    if (!banner || !phaseData) return;
    banner.setAttribute('data-strategy', phaseData.strategy || 'historical_only');
    const msgEl = document.getElementById('wsbMessage');
    if (msgEl) msgEl.textContent = phaseData.message || '';

    const reasons = (confidenceData && confidenceData.reasons) || [];
    const toggle = document.getElementById('wsbToggle');
    const reasonsEl = document.getElementById('wsbReasons');
    if (toggle && reasonsEl) {
        if (reasons.length) {
            toggle.style.display = 'inline-flex';
            reasonsEl.innerHTML = '<ul>' + reasons.map(r => `<li>${r}</li>`).join('') + '</ul>';
        } else {
            toggle.style.display = 'none';
            reasonsEl.style.display = 'none';
            reasonsEl.innerHTML = '';
        }
    }
}

function toggleConfidenceReasons() {
    const el = document.getElementById('wsbReasons');
    if (!el) return;
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

/* ── Sprint tab visibility: shown only for circuits flagged sprint_weekend ─
   SPRINT_CIRCUITS (circuit_id -> bool) and CIRCUIT_LOOKUP (race name -> circuit_id)
   both come from the server, so this stays correct without hardcoding a calendar. */
function updateSprintTabVisibility() {
    const race = document.getElementById('raceSelect')?.value;
    const circuitId = CIRCUIT_LOOKUP[race];
    const isSprint = !!(circuitId && window.SPRINT_CIRCUITS && window.SPRINT_CIRCUITS[circuitId]);
    const tab = document.getElementById('tab-sprint');
    const tabs = document.querySelector('.session-tabs');
    if (tab) tab.style.display = isSprint ? '' : 'none';
    if (tabs) tabs.classList.toggle('has-sprint', isSprint);
    // If Sprint was selected but the newly-picked race isn't a sprint weekend, bounce back to Qualifying.
    if (!isSprint && currentSession === 'sprint') {
        const qualTab = document.getElementById('tab-qualifying');
        if (qualTab) selectSession('qualifying', qualTab);
    }
}

/* ── Weather widget ─────────────────────────────────────── */
function updateWeatherWidget(weather) {
    const cfg = {
        dry:   {temp:'24°C', desc:'Sunny & Clear',       icon:'fa-sun',                bg:'linear-gradient(135deg,#1e3a5f,#1a2d4f)'},
        mixed: {temp:'21°C', desc:'Partly Cloudy',       icon:'fa-cloud-sun',          bg:'linear-gradient(135deg,#2d3748,#4a5568)'},
        wet:   {temp:'19°C', desc:'Heavy Rain',          icon:'fa-cloud-showers-heavy',bg:'linear-gradient(135deg,#1a365d,#2c5282)'},
    };
    const w = cfg[weather] || cfg.dry;
    const ww = document.getElementById('weatherWidget');
    if (!ww) return;
    ww.style.background = w.bg;
    ww.querySelector('.weather-icon').className = 'fas ' + w.icon + ' weather-icon';
    ww.querySelector('.weather-temp').textContent = w.temp;
    ww.querySelector('.weather-desc').textContent = w.desc;
}

/* ── Run Prediction ─────────────────────────────────────── */
async function runPrediction() {
    const race        = document.getElementById('raceSelect').value;
    const weather     = document.getElementById('weatherSelect').value;
    const sims        = parseInt(document.getElementById('simsInput').value) || 10000;
    const sessionType = document.getElementById('sessionTypeSelect').value;

    if (!race) { showToast('Please select a Grand Prix first.'); return; }
    
    // Check if this is a completed race - if so, show actual results instead
    const btn = document.getElementById('runPredictionBtn');
    if (btn && btn.dataset.raceCompleted === 'true') {
        // User clicked the green "Race Complete" button - cycle through available results
        cycleThroughSessionResults();
        return;
    }
    
    showLoading('Running ' + sims.toLocaleString() + ' simulations…');

    const payload = {race, session_type: sessionType, simulations: sims, weather};

    // Manual starting grid (P1-P22) only applies to sessions with a grid to override —
    // the Grand Prix race and the Sprint Race. getStartingGridOverrides() returns null
    // if there's a validation conflict (e.g. duplicate positions), in which case we
    // send nothing and let the model/auto-fetched grid be used instead.
    if (sessionType === 'RACE' || sessionType === 'SPRINT') {
        const overrides = getStartingGridOverrides();
        if (overrides && Object.keys(overrides).length) payload.grid_overrides = overrides;
    }

    try {
        const resp = await fetch('/api/predict', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        hideLoading();

        if (!data.success) { showToast('Error: ' + (data.error || 'Prediction failed')); return; }

        lastPrediction   = data;
        currentCircuitId = CIRCUIT_LOOKUP[race] || null;

        updateHero(race, data.results);
        updateCircuitInfo(currentCircuitId);
        updateSimBadge(sims);
        if (data.results.weekend_phase) {
            renderWeekendStatusBanner(data.results.weekend_phase, data.results.data_confidence);
        }

        const sess = sessionType.toLowerCase();
        if (sess === 'practice')           renderPractice(data.results);
        if (sess === 'qualifying')         renderQualifying(data.results);
        if (sess === 'sprint_qualifying')  renderSprintQualifying(data.results);
        if (sess === 'sprint')             renderSprintRace(data.results);
        if (sess === 'race')               renderRace(data.results);

        showToast('Prediction complete — ' + sims.toLocaleString() + ' sims');

    } catch(err) {
        hideLoading();
        showToast('Network error: ' + err.message);
        console.error(err);
    }
}

/* ── Hero update ────────────────────────────────────────── */
function updateHero(race, res) {
    const city = race.replace(' Grand Prix','').replace(' City','');
    document.getElementById('heroTitle').innerHTML = city.toUpperCase() + ' <span class="accent">GRAND PRIX</span>';
    document.getElementById('heroSub').textContent  = race;
    const m = res.meta || {};
    document.getElementById('kpi-sc').textContent   = m.safety_car_probability   != null ? Math.round(m.safety_car_probability*100)+'%'   : '—';
    document.getElementById('kpi-rain').textContent = m.rain_probability           != null ? Math.round(m.rain_probability*100)+'%'         : '—';
    document.getElementById('kpi-sims').textContent = m.n_simulations              != null ? (m.n_simulations/1000)+'k'                     : '—';
    document.getElementById('kpi-conf').textContent = m.overall_model_confidence   != null ? Math.round(m.overall_model_confidence*100)+'%' : '—';
}

function updateCircuitInfo(id) {
    const m = CIRCUIT_META[id]; if (!m) return;
    document.getElementById('circuitInfoBlock').innerHTML = `
        <div class="track-info">
            <div class="track-row"><span>Track Length</span><span>${m.len}</span></div>
            <div class="track-row"><span>Corners</span><span>${m.corners}</span></div>
            <div class="track-row"><span>DRS Zones</span><span>${m.drs}</span></div>
            <div class="track-row"><span>Safety Car Prob</span><span style="color:var(--red);font-weight:700;">${m.sc}</span></div>
            <div class="track-row"><span>Circuit Type</span><span>${m.type}</span></div>
        </div>`;
    document.getElementById('trackInfoBlock').innerHTML = `
        <div class="track-row"><span>Circuit Type</span><span style="font-weight:700;">${m.type}</span></div>
        <div class="track-row"><span>Safety Car Prob</span><span style="color:var(--red);font-weight:700;">${m.sc}</span></div>
        <div class="track-row"><span>DRS Zones</span><span>${m.drs}</span></div>`;
}

function updateSimBadge(n) {
    const el = document.getElementById('raceSimBadge');
    if (el) el.textContent = (n/1000).toFixed(0) + 'k sims';
}

/* ── Practice render ────────────────────────────────────── */
function renderPractice(res) {
    const top3 = (res.chart_data?.lap_time_comparison || []).slice(0,3);
    const pl   = document.getElementById('practicePodium');
    const cls  = ['p1','p2','p3'];
    const emj  = ['🥇','🥈','🥉'];
    if (top3.length) {
        pl.innerHTML = top3.map((d,i) => `
            <div class="podium-item ${cls[i]}">
                <div class="podium-pos">${emj[i]}</div>
                <div class="podium-info">
                    <div class="podium-name">${d.driver}</div>
                    <div class="podium-team">${(d.team||'').replace(/_/g,' ')}</div>
                </div>
                <div class="podium-metric">+${(d.gap_to_fastest||0).toFixed(3)}s</div>
            </div>`).join('');
    }
    const lt = (res.chart_data?.lap_time_comparison || []).slice(0,12);
    if (lt.length) {
        document.getElementById('practiceCharts').style.display = 'grid';
        Plotly.newPlot('plotPracticeLap', [{
            x: lt.map(d=>d.driver), y: lt.map(d=>d.gap_to_fastest||0), type:'bar',
            marker:{color: lt.map((_,i)=>i===0?'#e10600':i<3?'#ff6666':'#cccccc')},
            text: lt.map(d=>'+'+(d.gap_to_fastest||0).toFixed(3)+'s'), textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Gap to Fastest (s)'}});

        const cons = (res.chart_data?.consistency_ratings || []).slice(0,12);
        if (cons.length) {
            Plotly.newPlot('plotPracticeConsistency', [
                {r:cons.map(d=>d.consistency||70), theta:cons.map(d=>d.driver), type:'scatterpolar', fill:'toself', line:{color:'#e10600',width:2}, fillcolor:'rgba(225,6,0,0.12)', name:'Consistency'},
                {r:cons.map(d=>d.reliability||60),  theta:cons.map(d=>d.driver), type:'scatterpolar', fill:'toself', line:{color:'#1e3a5f',width:2}, fillcolor:'rgba(30,58,95,0.12)', name:'Reliability'},
            ], {
                paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
                font:{color:'#444',family:'Inter,sans-serif'},
                polar:{radialaxis:{visible:true,range:[0,100],gridcolor:'#e8e8e8'},angularaxis:{gridcolor:'#e8e8e8'}},
                showlegend:true, legend:{orientation:'h',y:-0.15}, margin:{t:20,r:40,b:60,l:40},
            });
        }
    }
}

/* ── Qualifying render ──────────────────────────────────── */
function renderQualifying(res) {
    const pos = (res.chart_data?.qualifying_positions || []).slice(0,5);
    const qg  = document.getElementById('qualifyingGrid');
    const cls = ['p1','p2','p3'];
    const emj = ['P1','P2','P3','P4','P5'];
    if (pos.length) {
        qg.innerHTML = pos.map((d,i) => `
            <div class="podium-item ${cls[i]||''}">
                <div class="podium-pos" style="${i>=3?'color:var(--text-3);font-size:1.4rem;':''}">${emj[i]}</div>
                <div class="podium-info">
                    <div class="podium-name">${d.driver}</div>
                    <div class="podium-team">${(d.team||'').replace(/_/g,' ')}</div>
                </div>
                <div class="podium-metric" style="${i>=3?'font-size:1.2rem;':''}">${(d.probability||0).toFixed(1)}%</div>
            </div>`).join('');
    }
    document.getElementById('q1Time').textContent = res.pole_time ? subtractMs(res.pole_time, 1200) : '—';
    document.getElementById('q2Time').textContent = res.pole_time ? subtractMs(res.pole_time, 600)  : '—';
    document.getElementById('q3Time').textContent = res.pole_time || '1:18.234';

    const posArr = (res.chart_data?.qualifying_positions || []).slice(0,15);
    if (posArr.length) {
        document.getElementById('qualCharts').style.display = 'grid';
        Plotly.newPlot('plotQualLine', [{
            x:posArr.map(d=>d.driver), y:posArr.map(d=>d.probability||0), type:'scatter',
            mode:'lines+markers', line:{color:'#e10600',width:3}, marker:{size:8,color:'#e10600'},
            fill:'tozeroy', fillcolor:'rgba(225,6,0,0.08)',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Probability (%)'}});

        const risk = res.chart_data?.elimination_risk || {};
        Plotly.newPlot('plotElim', [{
            x:['Q1 At Risk','Q2 At Risk','Safe in Q3'],
            y:[(risk.q1_at_risk||[]).length,(risk.q2_at_risk||[]).length,(risk.safe_in_q3||[]).length],
            type:'bar', marker:{color:['#ef4444','#f59e0b','#10b981']}, textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Drivers'}});
    }
}

function subtractMs(timeStr, ms) {
    try {
        const [m, rest] = timeStr.split(':');
        const s = parseFloat(rest) + ms/1000;
        return m + ':' + s.toFixed(3).padStart(6,'0');
    } catch { return '—'; }
}

/* ── Sprint Shootout render (sets tomorrow's Sprint grid, no points) ────── */
function renderSprintQualifying(res) {
    const pos = (res.chart_data?.qualifying_positions || []).slice(0,5);
    const qg  = document.getElementById('sprintQualGrid');
    const cls = ['p1','p2','p3'];
    const emj = ['P1','P2','P3','P4','P5'];
    if (qg && pos.length) {
        qg.innerHTML = pos.map((d,i) => `
            <div class="podium-item ${cls[i]||''}">
                <div class="podium-pos" style="${i>=3?'color:var(--text-3);font-size:1.4rem;':''}">${emj[i]}</div>
                <div class="podium-info">
                    <div class="podium-name">${d.driver}</div>
                    <div class="podium-team">${(d.team||'').replace(/_/g,' ')}</div>
                </div>
                <div class="podium-metric" style="${i>=3?'font-size:1.2rem;':''}">${(d.probability||0).toFixed(1)}%</div>
            </div>`).join('');
    }
    document.getElementById('sq1Time').textContent = res.pole_time ? subtractMs(res.pole_time, 900) : '—';
    document.getElementById('sq2Time').textContent = res.pole_time ? subtractMs(res.pole_time, 450) : '—';
    document.getElementById('sq3Time').textContent = res.pole_time || '1:19.500';
}

/* ── Sprint Race render (~100km, points for top 8 only) ─────────────────── */
function renderSprintRace(res) {
    const podSrc = (res.chart_data?.podium_probabilities || res.chart_data?.win_probabilities || []).slice(0,3);
    const rp     = document.getElementById('sprintRacePodium');
    const cls    = ['p1','p2','p3'];
    const emj    = ['🥇','🥈','🥉'];
    if (rp && podSrc.length) {
        rp.innerHTML = podSrc.map((d,i) => `
            <div class="podium-item ${cls[i]}">
                <div class="podium-pos">${emj[i]}</div>
                <div class="podium-info">
                    <div class="podium-name">${d.driver}</div>
                    <div class="podium-team">${(d.team||'').replace(/_/g,' ')}</div>
                </div>
                <div class="podium-metric">${(d.podium_chance||d.probability||0).toFixed(1)}%</div>
            </div>`).join('');
    }

    const dnfNote = document.getElementById('sprintDnfNote');
    const avgDnf = (res.chart_data?.dnf_risk_analysis || []).slice(0,20);
    if (dnfNote && avgDnf.length) {
        const avg = avgDnf.reduce((s,d) => s + (d.dnf_probability||0), 0) / avgDnf.length;
        dnfNote.textContent = `Average sprint DNF risk across the field: ${avg.toFixed(1)}% — noticeably lower than a full Grand Prix given the shorter distance.`;
    }

    ['sprintRaceCharts','sprintRaceTableWrap'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = id === 'sprintRaceTableWrap' ? 'block' : 'grid';
    });

    const wp = (res.chart_data?.win_probabilities || []).slice(0,8);
    if (wp.length) {
        Plotly.newPlot('plotSprintWinProb', [{
            x:wp.map(d=>d.driver), y:wp.map(d=>d.probability||0), type:'bar',
            marker:{color:wp.map(d=>getTeamColor(d.team))},
            text:wp.map(d=>(d.probability||0).toFixed(1)+'%'), textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Sprint Win Probability (%)'}});
    }

    const pp = (res.chart_data?.podium_probabilities || []).slice(0,8);
    if (pp.length) {
        Plotly.newPlot('plotSprintPodiumProb', [{
            y:pp.map(d=>d.driver), x:pp.map(d=>d.podium_chance||0), type:'bar', orientation:'h',
            marker:{color:pp.map(d=>getTeamColor(d.team))},
            text:pp.map(d=>(d.podium_chance||0).toFixed(1)+'%'), textposition:'outside',
        }], {...PLY, margin:{t:20,r:80,b:50,l:120}, xaxis:{...PLY.xaxis,title:'Sprint Podium Probability (%)'}, yaxis:{...PLY.yaxis,autorange:'reversed'}});
    }

    // Sprint scores points for the top 8 only — expected_points here already reflects
    // the sprint points table (8-7-6-5-4-3-2-1), computed server-side in predictor.py.
    const pts  = (res.points_finishers || res.chart_data?.win_probabilities || []).slice(0,8);
    const body = document.getElementById('sprintRaceTableBody');
    if (body && pts.length) {
        body.innerHTML = pts.map((p,i) => {
            const pos  = i + 1;
            const pb   = pos<=3 ? `<span class="pos-badge pos-${pos}">${pos}</span>` : `<span class="pos-badge pos-n">${pos}</span>`;
            const conf = (p.confidence||'medium').toLowerCase();
            const cb   = `<span class="conf-badge conf-${conf}">${conf.charAt(0).toUpperCase()+conf.slice(1)}</span>`;
            const winP = p.win_pct || p.probability || 0;
            return `<tr>
                <td>${pb}</td>
                <td class="driver-cell"><strong>${p.driver||p.driver_name||'—'}</strong><span>${(p.team||'').replace(/_/g,' ')}</span></td>
                <td style="font-size:0.85rem;color:var(--text-2);">${(p.team||'').replace(/_/g,' ')}</td>
                <td>${winP.toFixed(1)}%</td>
                <td>${(p.top3_pct||0).toFixed(1)}%</td>
                <td style="color:${(p.dnf_pct||0)>10?'var(--red)':'inherit'}">${(p.dnf_pct||0).toFixed(1)}%</td>
                <td style="font-weight:700;">${(p.expected_points||0).toFixed(1)}</td>
                <td>${cb}</td>
            </tr>`;
        }).join('');
    }
}

/* ── Race render ────────────────────────────────────────── */
function renderRace(res) {
    // Podium
    const podSrc = (res.chart_data?.podium_probabilities || res.chart_data?.win_probabilities || []).slice(0,3);
    const rp     = document.getElementById('racePodium');
    const cls    = ['p1','p2','p3'];
    const emj    = ['🥇','🥈','🥉'];
    if (podSrc.length) {
        rp.innerHTML = podSrc.map((d,i) => `
            <div class="podium-item ${cls[i]}">
                <div class="podium-pos">${emj[i]}</div>
                <div class="podium-info">
                    <div class="podium-name">${d.driver}</div>
                    <div class="podium-team">${(d.team||'').replace(/_/g,' ')}</div>
                </div>
                <div class="podium-metric">${(d.podium_chance||d.probability||0).toFixed(1)}%</div>
            </div>`).join('');
    }

    // Tire strategy
    document.getElementById('tireStratBlock').innerHTML = `
        <div class="tire-stint"><div class="tire-dot tire-S">S</div><div><div class="tire-label">Soft Compound</div><div class="tire-laps">Stint 1 · Laps 1–18</div></div></div>
        <div class="tire-stint"><div class="tire-dot tire-M">M</div><div><div class="tire-label">Medium Compound</div><div class="tire-laps">Stint 2 · Laps 19–40</div></div></div>
        <div class="tire-stint"><div class="tire-dot tire-H">H</div><div><div class="tire-label">Hard Compound</div><div class="tire-laps">Stint 3 · Laps 41–finish</div></div></div>
        <div style="margin-top:1rem;padding:1rem;background:var(--bg-2);border-radius:8px;font-size:0.85rem;color:var(--text-2);">
            Optimal: 2-stop strategy. Conservative runners gain track position under Safety Car.
        </div>`;

    // Model metrics
    const model = res.chart_data?.model_performance || {};
    document.getElementById('modelMetricsBlock').innerHTML = `
        <div class="metric-row"><span class="metric-lbl">Model Confidence</span><div class="metric-bar-wrap"><div class="metric-bar"><div class="metric-bar-fill" style="width:${model.overall_confidence||75}%"></div></div></div><span class="metric-val">${(model.overall_confidence||75).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="metric-lbl">Convergence Rate</span><div class="metric-bar-wrap"><div class="metric-bar"><div class="metric-bar-fill" style="width:${model.convergence_rate||85}%"></div></div></div><span class="metric-val">${(model.convergence_rate||85).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="metric-lbl">Historical Accuracy</span><div class="metric-bar-wrap"><div class="metric-bar"><div class="metric-bar-fill" style="width:${model.historical_accuracy||78}%"></div></div></div><span class="metric-val">${(model.historical_accuracy||78).toFixed(1)}%</span></div>
        <div class="metric-row"><span class="metric-lbl">Simulations</span><span class="metric-val">${((model.simulation_count||10000)/1000).toFixed(0)}k</span></div>`;

    // Show chart containers
    ['raceCharts1','raceTableWrap','raceCharts2','raceCharts3'].forEach(id => {
        document.getElementById(id).style.display = id === 'raceTableWrap' ? 'block' : 'grid';
    });

    // Win probability
    const wp = (res.chart_data?.win_probabilities || []).slice(0,10);
    if (wp.length) {
        Plotly.newPlot('plotWinProb', [{
            x:wp.map(d=>d.driver), y:wp.map(d=>d.probability||0), type:'bar',
            marker:{color:wp.map(d=>getTeamColor(d.team))},
            text:wp.map(d=>(d.probability||0).toFixed(1)+'%'), textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Win Probability (%)',range:[0,Math.max(...wp.map(d=>d.probability||0))*1.25]}});
    }

    // Podium probability
    const pp = (res.chart_data?.podium_probabilities || []).slice(0,10);
    if (pp.length) {
        Plotly.newPlot('plotPodiumProb', [{
            y:pp.map(d=>d.driver), x:pp.map(d=>d.podium_chance||0), type:'bar', orientation:'h',
            marker:{color:pp.map(d=>getTeamColor(d.team))},
            text:pp.map(d=>(d.podium_chance||0).toFixed(1)+'%'), textposition:'outside',
        }], {...PLY, margin:{t:20,r:80,b:50,l:120}, xaxis:{...PLY.xaxis,title:'Podium Probability (%)'}, yaxis:{...PLY.yaxis,autorange:'reversed'}});
    }

    // Results table
    const pts  = res.points_finishers || [];
    const all  = res.chart_data?.win_probabilities || [];
    const rows = pts.length ? pts : all.slice(0,20);
    
    // Qualifying grid source indicator (from changes.md)
    const gridSource = res.qualifying_grid_source;
    if (gridSource) {
        const badgeHTML = `<div style="margin-bottom:1rem;padding:0.75rem;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:8px;font-size:0.85rem;color:var(--text-2);">
            <i class="fas fa-info-circle" style="color:var(--green);"></i> 
            Starting grid auto-filled from <span class="grid-source-badge">${gridSource}</span>
        </div>`;
        document.getElementById('raceTableWrap').insertAdjacentHTML('afterbegin', badgeHTML);
    }
    
    if (rows.length) {
        document.getElementById('raceTableBody').innerHTML = rows.map((p,i) => {
            const pos  = i + 1;
            const pb   = pos<=3 ? `<span class="pos-badge pos-${pos}">${pos}</span>` : `<span class="pos-badge pos-n">${pos}</span>`;
            const conf = (p.confidence||'medium').toLowerCase();
            const cb   = `<span class="conf-badge conf-${conf}">${conf.charAt(0).toUpperCase()+conf.slice(1)}</span>`;
            const winP = p.win_pct || p.probability || 0;
            const driverId = p.driver_id || p.driver?.toLowerCase().replace(/\s+/g, '_') || '';
            return `<tr data-driver-id="${driverId}">
                <td>${pb}</td>
                <td class="driver-cell"><strong>${p.driver||p.driver_name||'—'}</strong><span>${(p.team||'').replace(/_/g,' ')}</span></td>
                <td style="font-size:0.85rem;color:var(--text-2);">${(p.team||'').replace(/_/g,' ')}</td>
                <td class="prob-bar-cell"><div class="prob-bar-wrap"><div class="prob-bar"><div class="prob-bar-fill" style="width:${Math.min(winP*3,100)}%"></div></div><div class="prob-val">${winP.toFixed(1)}%</div></div></td>
                <td>${(p.top3_pct||0).toFixed(1)}%</td>
                <td>${(p.top10_pct||0).toFixed(1)}%</td>
                <td style="color:${(p.dnf_pct||0)>20?'var(--red)':'inherit'}">${(p.dnf_pct||0).toFixed(1)}%</td>
                <td>${cb}</td>
                <td><button class="telemetry-btn" onclick="showTelemetry('${driverId}', '${p.driver||p.driver_name||''}')" title="View Live Telemetry"><i class="fas fa-activity"></i></button></td>
            </tr>`;
        }).join('');
    }

    // DNF chart
    const dnf = (res.chart_data?.dnf_risk_analysis || []).slice(0,12);
    if (dnf.length) {
        Plotly.newPlot('plotDNF', [{
            x:dnf.map(d=>d.driver), y:dnf.map(d=>d.dnf_probability||0), type:'bar',
            marker:{color:dnf.map(d=>d.dnf_probability>20?'#ef4444':d.dnf_probability>12?'#f59e0b':'#10b981')},
            text:dnf.map(d=>(d.dnf_probability||0).toFixed(1)+'%'), textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'DNF Probability (%)'}});
    }

    // Constructor chart
    const cst = res.chart_data?.constructor_standings || [];
    if (cst.length) {
        Plotly.newPlot('plotConstructorRace', [{
            x:cst.map(d=>d.team), y:cst.map(d=>d.points||0), type:'bar',
            marker:{color:cst.map(d=>getTeamColor(d.team))},
            text:cst.map(d=>(d.points||0).toFixed(1)+' pts'), textposition:'outside',
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Expected Points'}});
    }

    // Expected points
    const ep = (res.chart_data?.points_distribution || pts).slice(0,10);
    if (ep.length) {
        Plotly.newPlot('plotPoints', [{
            x:ep.map(d=>d.driver||d.driver_name||'—'), y:ep.map(d=>d.expected_points||0), type:'bar',
            marker:{color:ep.map(d=>d.expected_points>15?'#e10600':d.expected_points>8?'#f59e0b':'#94a3b8')},
        }], {...PLY, yaxis:{...PLY.yaxis,title:'Expected Championship Points'}});
    }

    // Heatmap
    const hm = res.chart_data?.position_heatmap || [];
    if (hm.length) {
        Plotly.newPlot('plotHeatmap', [{
            z:    hm.slice(0,10).map(d=>d.probabilities||[]),
            x:    (hm[0]?.positions||[]).map(p=>'P'+p),
            y:    hm.slice(0,10).map(d=>d.driver),
            type:'heatmap',
            colorscale:[[0,'rgba(225,6,0,0)'],[0.5,'rgba(225,6,0,0.5)'],[1,'rgba(225,6,0,1)']],
            showscale:false,
        }], {...PLY, margin:{t:20,r:20,b:50,l:100}});
    }
}

/* ══════════════════════════════════════════════════════════
   STARTING GRID WIDGET (P1-P22 manual override)
   One row per driver with a single position number input, rather than 22
   separate "P1: [driver dropdown]" selects — this makes picking the same
   driver twice structurally impossible instead of something to validate
   after the fact. Positions are optional; fill in as many as you know.
══════════════════════════════════════════════════════════ */

function buildStartingGridRows() {
    const table = document.getElementById('gridInputTable');
    if (!table) return;
    const entries = Object.entries(DRIVERS || {});
    if (!entries.length) return;
    table.innerHTML = entries.map(([id, d]) => `
        <div class="grid-input-row" data-driver-id="${id}">
            <span class="grid-input-swatch" style="background:${getTeamColor(d.team)}"></span>
            <span class="grid-input-name">${d.name}</span>
            <span class="grid-input-team">${(d.team||'').replace(/_/g,' ')}</span>
            <input type="number" class="grid-input-pos" min="1" max="22" placeholder="—"
                   aria-label="Grid position for ${d.name}"
                   oninput="validateStartingGrid()">
        </div>`).join('');
}

function validateStartingGrid() {
    const rows = Array.from(document.querySelectorAll('#gridInputTable .grid-input-row'));
    const errorEl = document.getElementById('gridInputError');
    const badge = document.getElementById('gridStatusBadge');
    const seen = {};
    let filled = 0;
    let conflict = false;

    rows.forEach(row => row.classList.remove('grid-input-conflict'));

    rows.forEach(row => {
        const input = row.querySelector('.grid-input-pos');
        const val = input.value ? parseInt(input.value, 10) : null;
        if (val) {
            filled++;
            if (seen[val]) {
                conflict = true;
                row.classList.add('grid-input-conflict');
                seen[val].classList.add('grid-input-conflict');
            } else {
                seen[val] = row;
            }
        }
    });

    if (conflict) {
        errorEl.textContent = 'Two drivers can\u2019t share a grid position — fix the highlighted rows.';
        badge.textContent = '⚠ Conflict';
        badge.style.color = 'var(--red)';
    } else if (filled === 0) {
        errorEl.textContent = '';
        badge.textContent = 'Auto';
        badge.style.color = '';
    } else if (filled === rows.length) {
        errorEl.textContent = '';
        badge.textContent = 'Complete (22/22)';
        badge.style.color = 'var(--green)';
    } else {
        errorEl.textContent = '';
        badge.textContent = `Partial (${filled}/${rows.length})`;
        badge.style.color = 'var(--gold)';
    }
    return !conflict;
}

function getStartingGridOverrides() {
    if (!validateStartingGrid()) return null;
    const overrides = {};
    document.querySelectorAll('#gridInputTable .grid-input-row').forEach(row => {
        const val = row.querySelector('.grid-input-pos').value;
        if (val) overrides[row.getAttribute('data-driver-id')] = parseInt(val, 10);
    });
    return overrides;
}

function clearStartingGrid() {
    document.querySelectorAll('#gridInputTable .grid-input-pos').forEach(input => input.value = '');
    validateStartingGrid();
    showToast('Starting grid cleared — using auto-fetched / model grid.');
}

/* ══════════════════════════════════════════════════════════
   LIVE DATA INTEGRATION (from changes.md - safe additions)
══════════════════════════════════════════════════════════ */

// Live data polling state
let livePollInterval = null;
// CIRCUIT_ID, IS_LIVE_ACTIVE, WEEKEND_PHASE, IS_SPRINT_WEEKEND, INITIAL_PREDICTIONS,
// INITIAL_META, and HAS_INITIAL_PREDICTION are NOT declared here. This file is served
// as a static asset — Flask/Jinja never processes it, so it can't contain "{{ }}"
// template expressions. Instead, dashboard.html (the actual Jinja template) sets
// these as window.* globals, via Jinja, in an inline <script> block that runs before
// this file loads. The bare names below resolve to those globals automatically.

// Update weekend phase badge
function updateWeekendPhaseBadge() {
    const badgeEl = document.getElementById('weekendPhaseBadge');
    const sprintEl = document.getElementById('sprintWeekendBadge');
    
    if (!badgeEl || !sprintEl) {
        console.warn('[Live Data] Badge elements not found in DOM');
        return;
    }
    
    console.log('[Live Data] Weekend phase:', WEEKEND_PHASE);
    console.log('[Live Data] Sprint weekend:', IS_SPRINT_WEEKEND);
    
    // Weekend phase badge - ALWAYS show if we have phase info
    if (WEEKEND_PHASE && WEEKEND_PHASE !== 'unknown' && WEEKEND_PHASE !== '') {
        // FIX: this dictionary previously used 'friday'/'saturday'/'sunday' keys, but
        // get_weekend_phase() on the backend actually returns 'practice'/'qualifying'/
        // 'sprint'/'race'/'pre_weekend'/'post_race'/'completed' — so every phase except
        // pre_weekend/post_race/completed fell through to the raw, unstyled backend string.
        const phaseNames = {
            'pre_weekend': 'Pre-Weekend',
            'practice':    'Practice (Friday)',
            'qualifying':  'Qualifying (Saturday)',
            'sprint':      'Sprint Weekend (Saturday)',
            'race':        'Race Day (Sunday)',
            'post_race':   'Post-Race',
            'completed':   'Completed',
        };
        const phaseClass = `phase-${WEEKEND_PHASE}`;
        badgeEl.innerHTML = `<span class="weekend-phase-badge ${phaseClass}">${phaseNames[WEEKEND_PHASE] || WEEKEND_PHASE}</span>`;
        console.log('[Live Data] Phase badge rendered:', phaseNames[WEEKEND_PHASE]);
    } else {
        console.log('[Live Data] No valid weekend phase to display');
    }
    
    // Sprint weekend badge
    if (IS_SPRINT_WEEKEND) {
        sprintEl.innerHTML = `<span class="sprint-weekend-badge"><i class="fas fa-bolt"></i> Sprint</span>`;
        console.log('[Live Data] Sprint badge rendered');
    } else {
        console.log('[Live Data] Not a sprint weekend');
    }
}

// Update live data banner
function updateLiveDataBanner(data) {
    const banner = document.getElementById('liveDataBanner');
    
    console.log('[Live Data] Banner update called, active:', data?.active);
    
    if (!banner || !data.active) {
        if (banner) {
            banner.style.display = 'none';
            console.log('[Live Data] Banner hidden (no active session)');
        }
        return;
    }
    
    banner.style.display = 'block';
    console.log('[Live Data] Banner shown');
    
    // Update session name
    const sessionNameEl = document.getElementById('liveSessionName');
    if (sessionNameEl) {
        sessionNameEl.textContent = data.session?.name || 'Live Session';
    }
    
    // Update weather metrics
    if (data.weather) {
        const airTempEl = document.getElementById('liveAirTemp');
        const trackTempEl = document.getElementById('liveTrackTemp');
        const rainProbEl = document.getElementById('liveRainProb');
        const rcEl = document.getElementById('liveRaceControl');
        
        if (airTempEl) airTempEl.textContent = `${data.weather.air_temp || '—'}°C`;
        if (trackTempEl) trackTempEl.textContent = `${data.weather.track_temp || '—'}°C`;
        if (rainProbEl) rainProbEl.textContent = `${data.weather.rain_probability || 0}%`;
        
        // Race control status
        if (rcEl) {
            if (data.safety_car_deployed) {
                rcEl.textContent = 'SC DEPLOYED';
                rcEl.style.color = '#f59e0b';
            } else {
                rcEl.textContent = 'GREEN';
                rcEl.style.color = 'var(--green)';
            }
        }
    }
    
    // Update timer
    const timerEl = document.getElementById('liveUpdateTimer');
    if (timerEl) {
        timerEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }
}

// Poll live data endpoint
function pollLiveData() {
    if (!CIRCUIT_ID || CIRCUIT_ID === '') return;
    
    fetch(`/api/live-data/${CIRCUIT_ID}`)
        .then(r => r.json())
        .then(data => {
            updateLiveDataBanner(data);
            
            // Auto-adjust rain probability if rain detected
            if (data.weather && data.weather.rained && data.weather.rain_probability > 30) {
                const rainInput = document.getElementById('rainInput');
                if (rainInput && !rainInput.value) {
                    rainInput.value = Math.round(data.weather.rain_probability);
                }
            }
        })
        .catch(err => console.warn('Live data poll error:', err));
}

// Start/stop live polling
function startLivePolling() {
    if (livePollInterval) clearInterval(livePollInterval);
    livePollInterval = setInterval(pollLiveData, 30000); // 30 seconds
    pollLiveData(); // Initial call
}

function stopLivePolling() {
    if (livePollInterval) {
        clearInterval(livePollInterval);
        livePollInterval = null;
    }
}

// Telemetry modal (from changes.md - simplified version)
function showTelemetry(driverId, driverName) {
    if (!driverId) {
        showToast('Driver ID not available');
        return;
    }
    
    // For now, just show a toast with driver info
    // Full telemetry modal would require additional HTML/CSS
    showToast(`Telemetry for ${driverName} — Feature coming soon`);
    
    // TODO: Implement full telemetry modal with Plotly charts
    // This would fetch from /api/telemetry/<circuit_id>/<driver_number>
}

function bindSessionTabInteractions() {
    document.querySelectorAll('.session-tab[data-session]').forEach(tab => {
        tab.addEventListener('click', () => {
            const session = tab.getAttribute('data-session');
            if (session) selectSession(session, tab);
        });
    });
}

window.addEventListener('DOMContentLoaded', () => {
    bindSessionTabInteractions();

    // Weather init
    try {
        const w = document.getElementById('weatherSelect')?.value || 'dry';
        updateWeatherWidget(w);
    } catch(e) { console.warn('Weather init skip:', e); }

    // Weather live update
    document.getElementById('weatherSelect')?.addEventListener('change', e => updateWeatherWidget(e.target.value));

    // NEW: Weekend status banner ("has this race already happened") — render the
    // server-computed status for the initially-loaded race immediately.
    renderWeekendStatusBanner(window.WEEKEND_PHASE_DATA, window.DATA_CONFIDENCE);

    // NEW: Starting grid (P1-P22) widget — build the 22 rows once on load.
    buildStartingGridRows();

    // NEW: Sprint tab only shows for sprint-weekend circuits. Check on load, and
    // again whenever the user picks a different race — plus refresh the banner for
    // whichever circuit is now selected via the lightweight weekend-phase endpoint,
    // so the notification is accurate before the user even clicks "Run Prediction".
    updateSprintTabVisibility();
    
    // NEW: Check race completion status on load and when switching races
    const initialRace = document.getElementById('raceSelect')?.value;
    if (initialRace) {
        const initialCircuitId = CIRCUIT_LOOKUP[initialRace];
        if (initialCircuitId) {
            checkAndDisplayRaceStatus(initialCircuitId);
        }
    }
    
    document.getElementById('raceSelect')?.addEventListener('change', e => {
        updateSprintTabVisibility();
        const circuitId = CIRCUIT_LOOKUP[e.target.value];
        if (!circuitId) return;
        
        // Check race completion status first
        checkAndDisplayRaceStatus(circuitId);
        
        // Also fetch weekend phase for additional context
        fetch(`/api/weekend-phase/${circuitId}`)
            .then(r => r.json())
            .then(data => { if (data.success) renderWeekendStatusBanner(data.weekend_phase); })
            .catch(err => console.warn('Weekend phase refresh failed:', err));
    });

    // Initialize live data features
    updateWeekendPhaseBadge();
    if (IS_LIVE_ACTIVE) {
        startLivePolling();
    }

    // Auto-render initial predictions if available from server
    if (HAS_INITIAL_PREDICTION && INITIAL_PREDICTIONS.length > 0) {
        console.log('[Init] Rendering initial predictions from server...');
        try {
            // Build result object in the format expected by renderRace
            const resultObj = {
                chart_data: {
                    win_probabilities: INITIAL_PREDICTIONS.map(p => ({
                        driver: p.driver || p.driver_name,
                        team: p.team,
                        probability: p.win_pct || 0
                    })),
                    podium_probabilities: INITIAL_PREDICTIONS.map(p => ({
                        driver: p.driver || p.driver_name,
                        team: p.team,
                        podium_chance: p.top3_pct || 0
                    })),
                    model_performance: INITIAL_META || {}
                },
                points_finishers: INITIAL_PREDICTIONS.slice(0, 10),
                qualifying_grid_source: null
            };

            // Render based on current session type
            const sessionType = WEEKEND_PHASE || 'race';
            if (sessionType.includes('practice')) {
                renderPractice(resultObj);
            } else if (sessionType.includes('qualifying')) {
                renderQualifying(resultObj);
            } else {
                renderRace(resultObj);
            }

            showToast('Predictions loaded for current race');
        } catch(e) {
            console.error('[Init] Failed to render initial predictions:', e);
        }
    }
});