'use strict';

/* ══════════════════════════════════════════════════════════
   CONSTRUCTORS — Live data
══════════════════════════════════════════════════════════ */
let constructorData = null;

async function loadConstructorData() {
    document.getElementById('constructorLoading').style.display = 'block';
    document.getElementById('constructorError').style.display = 'none';
    document.getElementById('constructorDashboard').style.display = 'none';
    try {
        const res  = await fetch('/api/constructors/live');
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Failed to fetch constructor data');
        constructorData = data;
        document.getElementById('constructorLastUpdate').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        renderConstructorSummary(data);
        renderConstructorTable(data);
        renderConstructorCharts(data);
        document.getElementById('constructorLoading').style.display = 'none';
        document.getElementById('constructorDashboard').style.display = 'block';
        showToast('Live constructor data loaded!');
    } catch(err) {
        document.getElementById('constructorLoading').style.display = 'none';
        document.getElementById('constructorError').style.display = 'block';
        document.getElementById('constructorErrorMessage').textContent = err.message;
    }
}

function renderConstructorSummary(data) {
    const cs = data.constructors || [];
    document.getElementById('totalTeams').textContent   = data.total_teams   || cs.length;
    document.getElementById('totalDrivers').textContent = data.total_drivers || (data.drivers||[]).length;
    document.getElementById('leaderPoints').textContent = cs.length ? Math.max(...cs.map(c=>c.points)).toFixed(0) : '—';
    document.getElementById('totalWins').textContent    = cs.reduce((s,c)=>s+(c.wins||0),0);
    document.getElementById('standingsRound').textContent = `After R${data.round||'—'} · ${data.season||'2026'}`;
}

function renderConstructorTable(data) {
    const cs   = data.constructors || [];
    const tbody = document.getElementById('constructorTableBody');
    if (!cs.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;">No data available</td></tr>'; return; }
    tbody.innerHTML = cs.map((c,idx) => {
        const pos     = c.position || idx+1;
        const posClass= pos<=3 ? `pos-${pos}` : 'pos-n';
        const color   = getTeamColor(c.team_id || c.name);
        let tier='tier-back', tierTxt='Back Marker';
        if (c.tier==='Top Tier' || pos<=3) { tier='tier-top'; tierTxt='Top Tier'; }
        else if (c.tier==='Mid Field' || pos<=6) { tier='tier-mid'; tierTxt='Mid Field'; }
        const drivers = (c.drivers||[]).map(d=>d.code||d.family_name?.substring(0,3).toUpperCase()||'—').join(' · ') || '—';
        return `<tr>
            <td><span class="pos-badge ${posClass}">${pos}</span></td>
            <td><strong style="color:${color};">${c.name}</strong><div style="font-size:0.75rem;color:var(--text-3);margin-top:0.2rem;">${c.nationality||''}</div></td>
            <td style="font-family:var(--font-head);font-weight:700;font-size:1.1rem;">${(c.points||0).toFixed(1)}</td>
            <td style="font-weight:600;">${c.wins||0}</td>
            <td style="font-size:0.85rem;">${drivers}</td>
            <td><span class="tier-badge ${tier}">${tierTxt}</span></td>
        </tr>`;
    }).join('');
}

function renderConstructorCharts(data) {
    const cs = data.constructors || [];
    const an = data.analytics    || {};
    renderConstrPointsPie(cs);
    renderConstrRadar(an.team_radar_data || []);
    renderConstrWins(an.win_distribution || [], cs);
    renderConstrDriverContrib(an.driver_contributions || []);
    renderConstrGaps(an.points_gaps || []);
    renderConstrTiers(an.performance_tiers || []);
    renderConstrAvgByPos(an.avg_by_position || []);
}

function renderConstrPointsPie(cs) {
    const top = cs.slice(0,8);
    Plotly.newPlot('plotConstructorPointsPie', [{
        labels:top.map(c=>c.name), values:top.map(c=>c.points), type:'pie',
        marker:{colors:top.map(c=>getTeamColor(c.team_id||c.name))},
        textinfo:'label+percent', textposition:'outside', pull:0.05, hole:0.4,
    }], {...PLY, margin:{t:20,r:20,b:20,l:20}, showlegend:false});
}

function renderConstrRadar(rd) {
    if (!rd.length) return;
    const traces = rd.map(t => ({
        r:Object.values(t.metrics), theta:Object.keys(t.metrics),
        type:'scatterpolar', fill:'toself', name:t.team,
        line:{width:2, color:getTeamColor(t.team_id||t.team)},
        fillcolor:getTeamColor(t.team_id||t.team)+'30',
    }));
    Plotly.newPlot('plotTeamRadar', traces, {
        ...PLY,
        polar:{radialaxis:{visible:true,range:[0,100],gridcolor:'#e8e8e8'},angularaxis:{gridcolor:'#e8e8e8'}},
        legend:{orientation:'h',y:-0.15}, margin:{t:20,r:40,b:80,l:40},
    });
}

function renderConstrWins(wd, cs) {
    if (!wd.length && !cs.length) return;
    const src = wd.length ? wd : cs.map(c=>({team:c.name, wins:c.wins||0, percentage:0}));
    Plotly.newPlot('plotWinDistribution', [{
        x:src.map(w=>w.team), y:src.map(w=>w.wins), type:'bar',
        marker:{color:src.map(w=>getTeamColor(normalizeTeamKey(w.team)))},
        text:src.map(w=>(w.percentage||0).toFixed(1)+'%'), textposition:'outside',
    }], {...PLY, yaxis:{...PLY.yaxis,title:'Number of Wins'}, margin:{t:20,r:20,b:80,l:60}});
}

function renderConstrDriverContrib(cd) {
    if (!cd.length) return;
    Plotly.newPlot('plotDriverContribution', [
        {x:cd.map(c=>c.team), y:cd.map(c=>c.driver1_pct), type:'bar', name:'Driver 1', marker:{color:'#e10600'}, text:cd.map((c,i)=>`${c.driver1}: ${c.driver1_pct.toFixed(1)}%`), textposition:'inside', insidetextanchor:'middle', textfont:{color:'#fff',size:11}},
        {x:cd.map(c=>c.team), y:cd.map(c=>c.driver2_pct), type:'bar', name:'Driver 2', marker:{color:'#1e3a5f'}, text:cd.map((c,i)=>`${c.driver2}: ${c.driver2_pct.toFixed(1)}%`), textposition:'inside', insidetextanchor:'middle', textfont:{color:'#fff',size:11}},
    ], {...PLY, barmode:'stack', yaxis:{...PLY.yaxis,title:'Points Contribution (%)',range:[0,100]}, legend:{orientation:'h',y:-0.15}, margin:{t:20,r:20,b:100,l:60}});
}

function renderConstrGaps(gaps) {
    if (!gaps.length) return;
    Plotly.newPlot('plotPointsGaps', [{
        x:gaps.map(g=>g.position), y:gaps.map(g=>g.gap), type:'bar',
        marker:{color:gaps.map(g=>g.gap>50?'#ef4444':g.gap>20?'#f59e0b':'#10b981')},
        text:gaps.map(g=>g.gap.toFixed(1)+' pts'), textposition:'outside',
    }], {...PLY, yaxis:{...PLY.yaxis,title:'Points Gap'}, margin:{t:20,r:20,b:80,l:60}});
}

function renderConstrTiers(tiers) {
    if (!tiers.length) return;
    Plotly.newPlot('plotPerformanceTiers', [{
        x:tiers.map(t=>t.points), y:tiers.map(t=>t.team), mode:'markers', type:'scatter',
        marker:{size:tiers.map(t=>Math.max(20,t.points/5)), color:tiers.map(t=>t.color), sizemode:'diameter', opacity:0.7, line:{width:2,color:'#fff'}},
        text:tiers.map(t=>`${t.team}<br>${t.tier}<br>${t.points.toFixed(1)} pts`), hovertemplate:'%{text}<extra></extra>',
    }], {...PLY, xaxis:{...PLY.xaxis,title:'Championship Points'}, margin:{t:20,r:20,b:50,l:120}, showlegend:false});
}

function renderConstrAvgByPos(avg) {
    if (!avg.length) return;
    Plotly.newPlot('plotAvgByPosition', [{
        x:avg.map(a=>a.position_range), y:avg.map(a=>a.avg_points), type:'scatter',
        mode:'lines+markers', line:{color:'#e10600',width:3,shape:'spline'}, marker:{size:10,color:'#e10600'},
        fill:'tozeroy', fillcolor:'rgba(225,6,0,0.1)',
    }], {...PLY, yaxis:{...PLY.yaxis,title:'Average Points'}, margin:{t:20,r:20,b:60,l:60}});
}

/* FIX: backward compatibility alias */
function renderConstructors() { loadConstructorData(); }

window.addEventListener('DOMContentLoaded', () => {
    loadConstructorData();
});