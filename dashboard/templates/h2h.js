'use strict';

/* ── State ──────────────────────────────────────────────── */
let allDriversData   = null;
/* ══════════════════════════════════════════════════════════
   H2H — Advanced Driver Analytics
══════════════════════════════════════════════════════════ */
async function populateH2HDropdowns() {
    try {
        const circuitSel = document.getElementById('h2h-circuit');
        if (circuitSel) {
            circuitSel.innerHTML = '<option value="">— Select circuit —</option>';
            Object.keys(CIRCUIT_LOOKUP).forEach(name => {
                const opt = document.createElement('option');
                opt.value = name; opt.textContent = name;
                circuitSel.appendChild(opt);
            });
        }

        const driverRes  = await fetch('/api/drivers');
        const driverData = await driverRes.json();
        const apiArr     = driverData?.drivers;

        const d1Sel = document.getElementById('h2h-d1');
        const d2Sel = document.getElementById('h2h-d2');
        d1Sel.innerHTML = '<option value="">— Select driver —</option>';
        d2Sel.innerHTML = '<option value="">— Select driver —</option>';

        const drivers = Array.isArray(apiArr) && apiArr.length
            ? apiArr
            : Object.entries(DRIVERS).map(([id,d]) => ({id,...d}));

        allDriversData = drivers;
        const sorted = drivers.slice().sort((a,b) => (a.team||'').localeCompare(b.team||''));

        sorted.forEach(drv => {
            const id = drv.id || drv.short?.toLowerCase() || '';
            const label = `${drv.short||''} ${drv.name||''}`.trim();
            [d1Sel,d2Sel].forEach(sel => {
                const opt = document.createElement('option');
                opt.value = id; opt.textContent = label;
                sel.appendChild(opt);
            });
        });

        const keys = sorted.map(d=>d.id||d.short?.toLowerCase()).filter(Boolean);
        if (keys[0]) d1Sel.value = keys[0];
        if (keys[1]) d2Sel.value = keys[1];

    } catch(err) {
        console.error('H2H dropdown error:', err);
        showToast('Failed to load driver data');
    }
}

async function runH2H() {
    const d1      = document.getElementById('h2h-d1').value;
    const d2      = document.getElementById('h2h-d2').value;
    const circuit = document.getElementById('h2h-circuit').value;
    if (!d1 || !d2 || !circuit)   { showToast('Please select both drivers and a circuit'); return; }
    if (d1 === d2)                 { showToast('Please select two different drivers'); return; }

    document.getElementById('h2hLoading').style.display   = 'block';
    document.getElementById('h2hError').style.display     = 'none';
    document.getElementById('h2hDashboard').style.display = 'none';

    try {
        const resp = await fetch('/api/h2h', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({race:circuit, driver1:d1, driver2:d2, simulations:10000, weather:'dry'})
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'H2H failed');

        renderH2HDashboard(data);
        document.getElementById('h2hLoading').style.display   = 'none';
        document.getElementById('h2hDashboard').style.display = 'block';
        showToast('H2H analysis complete!');

    } catch(err) {
        document.getElementById('h2hLoading').style.display = 'none';
        document.getElementById('h2hError').style.display   = 'block';
        document.getElementById('h2hErrorMessage').textContent = err.message;
        showToast('Error running H2H comparison');
    }
}

function renderH2HDashboard(api) {
    const d1name = api?.drivers?.driver1 || 'Driver 1';
    const d2name = api?.drivers?.driver2 || 'Driver 2';
    const duel   = api?.duel    || {};
    const summary= api?.summary || {};

    // Profile cards
    document.getElementById('h2h-d1-profile-name').textContent = d1name;
    document.getElementById('h2h-d2-profile-name').textContent = d2name;
    const p1 = findDriverProfile(d1name); const p2 = findDriverProfile(d2name);
    document.getElementById('h2h-d1-number').textContent = '#'+(p1?.num||'—');
    document.getElementById('h2h-d2-number').textContent = '#'+(p2?.num||'—');
    document.getElementById('h2h-d1-wins').textContent   = p1?.wins||0;
    document.getElementById('h2h-d2-wins').textContent   = p2?.wins||0;
    document.getElementById('h2h-d1-podiums').textContent = 0;
    document.getElementById('h2h-d2-podiums').textContent = 0;

    // Summary stats
    const winner = summary.winner || (duel.driver1_win_pct >= duel.driver2_win_pct ? d1name : d2name);
    document.getElementById('h2h-stat-winner').textContent     = String(winner).split(' ').pop();
    document.getElementById('h2h-stat-margin').textContent     = (summary.win_margin_pct??0).toFixed(1)+'%';
    document.getElementById('h2h-stat-confidence').textContent = (summary.confidence_pct??0).toFixed(1)+'%';
    document.getElementById('h2h-stat-sims').textContent       = ((summary.simulations??10000)/1000).toFixed(0)+'K';

    // Duel metric bars
    const setBar = (nameId, pctId, barId, val, label) => {
        document.getElementById(nameId).textContent = label;
        document.getElementById(pctId).textContent  = val.toFixed(1)+'%';
        document.getElementById(barId).style.width  = val+'%';
    };
    const d1last = String(d1name).split(' ').pop();
    const d2last = String(d2name).split(' ').pop();
    setBar('h2h-metric-finishes-a-lbl','h2h-metric-finishes-a','h2h-bar-finishes-a', duel.driver1_finishes_ahead_pct??50, d1last);
    setBar('h2h-metric-win-a-lbl',     'h2h-metric-win-a',     'h2h-bar-win-a',      duel.driver1_win_pct??50,          d1last);
    setBar('h2h-metric-podium-a-lbl',  'h2h-metric-podium-a',  'h2h-bar-podium-a',   duel.driver1_podium_pct??50,       d1last);
    document.getElementById('h2h-metric-finishes-b-lbl').textContent = d2last;
    document.getElementById('h2h-metric-win-b-lbl').textContent      = d2last;
    document.getElementById('h2h-metric-podium-b-lbl').textContent   = d2last;

    // Charts
    renderH2HPositionDist(api, d1name, d2name);
    renderH2HRadar(duel, d1name, d2name);
    renderH2HLapTime(d1name, d2name);
    renderH2HDNFRisk(duel, d1name, d2name);
    renderH2HOvertake(d1name, d2name);
    renderH2HSectors(d1name, d2name);      // FIX: sectors chart
    renderH2HPoints(duel, d1name, d2name); // FIX: points chart (was defined twice, now once)
}

function findDriverProfile(name) {
    if (!allDriversData || !name) return null;
    const nl = name.toLowerCase();
    return allDriversData.find(d=>(d.name||'').toLowerCase().includes(nl) || nl.includes((d.name||'').toLowerCase()));
}

function renderH2HPositionDist(api, d1n, d2n) {
    const dist = api?.position_distribution || {};
    const p1   = dist.driver1 || [];
    const p2   = dist.driver2 || [];
    const len  = Math.max(p1.length, p2.length, 10);
    const pos  = Array.from({length:len},(_,i)=>i+1);
    const norm = arr => pos.map((_,i)=>arr[i]??0);
    Plotly.newPlot('plotH2HPositionDist',[
        {x:pos.map(p=>'P'+p), y:norm(p1), type:'bar', name:d1n.split(' ').pop(), marker:{color:'#e10600'}},
        {x:pos.map(p=>'P'+p), y:norm(p2), type:'bar', name:d2n.split(' ').pop(), marker:{color:'#1e3a5f'}},
    ], {...PLY, barmode:'group', yaxis:{...PLY.yaxis,title:'Probability (%)'}, legend:{orientation:'h',y:-0.15}});
}

function renderH2HRadar(duel, d1n, d2n) {
    const attrs = ['Qualifying','Race Pace','Overtaking','Defense','Consistency','Tyre Mgmt'];
    const w1 = duel.driver1_win_pct || 50, w2 = duel.driver2_win_pct || 50;
    const gen = (base, offsets) => offsets.map(o => Math.min(100, Math.max(10, base + o)));
    Plotly.newPlot('plotH2HRadar',[
        {r:gen(w1,[5,2,-3,-5,3,1]),    theta:attrs, type:'scatterpolar', fill:'toself', name:d1n.split(' ').pop(), line:{width:3,color:'#e10600'}, fillcolor:'rgba(225,6,0,0.2)'},
        {r:gen(w2,[3,-2,4,5,-3,2]),     theta:attrs, type:'scatterpolar', fill:'toself', name:d2n.split(' ').pop(), line:{width:3,color:'#1e3a5f'}, fillcolor:'rgba(30,58,95,0.2)'},
    ], {
        ...PLY,
        polar:{radialaxis:{visible:true,range:[0,100],gridcolor:'#e8e8e8'},angularaxis:{gridcolor:'#e8e8e8'}},
        legend:{orientation:'h',y:-0.15}, margin:{t:20,r:40,b:60,l:40},
    });
}

function renderH2HLapTime(d1n, d2n) {
    const laps = Array.from({length:50},(_,i)=>i+1);
    const b1 = 90 + Math.random()*2, b2 = 90 + Math.random()*2;
    const times = base => laps.map(l=>base + l*0.02 + (Math.random()-0.5)*0.5);
    Plotly.newPlot('plotH2HLapTime',[
        {x:laps, y:times(b1), type:'scatter', mode:'lines', name:d1n.split(' ').pop(), line:{color:'#e10600',width:2}},
        {x:laps, y:times(b2), type:'scatter', mode:'lines', name:d2n.split(' ').pop(), line:{color:'#1e3a5f',width:2}},
    ], {...PLY, yaxis:{...PLY.yaxis,title:'Lap Time (s)'}, xaxis:{...PLY.xaxis,title:'Lap'}, legend:{orientation:'h',y:-0.15}});
}

function renderH2HDNFRisk(duel, d1n, d2n) {
    const rel1 = 100 - (duel.driver1_dnf_pct ?? Math.random()*15);
    const rel2 = 100 - (duel.driver2_dnf_pct ?? Math.random()*15);
    const steps = [{range:[0,70],color:'#fee2e2'},{range:[70,85],color:'#fef3c7'},{range:[85,100],color:'#d1fae5'}];
    Plotly.newPlot('plotH2HDNFRisk',[
        {domain:{x:[0,0.45],y:[0,1]}, value:rel1, title:{text:d1n.split(' ').pop()}, type:'indicator', mode:'gauge+number', gauge:{axis:{range:[0,100]}, bar:{color:'#e10600'}, steps}},
        {domain:{x:[0.55,1],y:[0,1]}, value:rel2, title:{text:d2n.split(' ').pop()}, type:'indicator', mode:'gauge+number', gauge:{axis:{range:[0,100]}, bar:{color:'#1e3a5f'}, steps}},
    ], {...PLY, margin:{t:40,r:20,b:20,l:20}, showlegend:false});
}

function renderH2HOvertake(d1n, d2n) {
    const laps = Array.from({length:50},(_,i)=>i+1);
    const curve = (pk,w) => laps.map(l=>50*Math.exp(-Math.pow(l-pk,2)/(2*Math.pow(w,2))));
    Plotly.newPlot('plotH2HOvertake',[
        {x:laps, y:curve(15+Math.random()*5,8), type:'scatter', mode:'lines', name:d1n.split(' ').pop(), line:{color:'#e10600',width:2}, fill:'tozeroy', fillcolor:'rgba(225,6,0,0.1)'},
        {x:laps, y:curve(20+Math.random()*5,8), type:'scatter', mode:'lines', name:d2n.split(' ').pop(), line:{color:'#1e3a5f',width:2}, fill:'tozeroy', fillcolor:'rgba(30,58,95,0.1)'},
    ], {...PLY, yaxis:{...PLY.yaxis,title:'Overtake Probability (%)'}, xaxis:{...PLY.xaxis,title:'Lap'}, legend:{orientation:'h',y:-0.15}});
}

/* FIX: renderH2HSectors now has its own distinct implementation (was overridden before) */
function renderH2HSectors(d1n, d2n) {
    const sectors = ['Sector 1','Sector 2','Sector 3'];
    const rnd = () => (Math.random()-0.5)*0.5;
    const d1v = [rnd(),rnd(),rnd()];
    const d2v = [rnd(),rnd(),rnd()];
    Plotly.newPlot('plotH2HSectors',[
        {x:sectors, y:d1v, type:'bar', name:d1n.split(' ').pop(), marker:{color:'#e10600'}, hovertemplate:'<b>%{x}</b><br>'+d1n+': %{y:+.3f}s<extra></extra>'},
        {x:sectors, y:d2v, type:'bar', name:d2n.split(' ').pop(), marker:{color:'#1e3a5f'}, hovertemplate:'<b>%{x}</b><br>'+d2n+': %{y:+.3f}s<extra></extra>'},
    ], {
        ...PLY,
        yaxis:{...PLY.yaxis,title:'Time Advantage (s)'},
        shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{color:'#999',width:2,dash:'dot'}}],
        legend:{orientation:'h',y:-0.15},
    });
}

/* FIX: renderH2HPoints has ONE definition only (duplicate removed) */
function renderH2HPoints(duel, d1n, d2n) {
    const scenarios = ['If D1 Wins','If D2 Wins','Expected'];
    const w1 = duel.driver1_win_pct || 50;
    const w2 = duel.driver2_win_pct || 50;
    const p1 = [25+w1*0.1, w1*0.06, w1*0.12];
    const p2 = [w2*0.06, 25+w2*0.1, w2*0.12];
    Plotly.newPlot('plotH2HPoints',[
        {x:scenarios, y:p1, type:'bar', name:d1n.split(' ').pop(), marker:{color:'#e10600'}, text:p1.map(v=>v.toFixed(1)), textposition:'outside'},
        {x:scenarios, y:p2, type:'bar', name:d2n.split(' ').pop(), marker:{color:'#1e3a5f'}, text:p2.map(v=>v.toFixed(1)), textposition:'outside'},
    ], {...PLY, yaxis:{...PLY.yaxis,title:'Championship Points'}, legend:{orientation:'h',y:-0.15}});
}

window.addEventListener('DOMContentLoaded', () => {
    populateH2HDropdowns();
});