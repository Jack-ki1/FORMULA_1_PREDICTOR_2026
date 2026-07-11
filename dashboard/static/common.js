'use strict';

/* ── Constants ──────────────────────────────────────────── */
const TEAM_COLORS = {
    mercedes:'#00d2be', red_bull:'#0600ef', ferrari:'#dc0000',
    mclaren:'#ff8000', williams:'#005aff', alpine:'#0090ff',
    haas:'#b6babd', rb:'#6692ff', audi:'#e10600',
    aston_martin:'#006f62', cadillac:'#ff6900'
};

const DRIVERS = {
    antonelli: {name:'Kimi Antonelli',   short:'ANT', team:'mercedes',     num:'15'},
    russell:   {name:'George Russell',   short:'RUS', team:'mercedes',     num:'63'},
    hamilton:  {name:'Lewis Hamilton',   short:'HAM', team:'ferrari',      num:'44'},
    leclerc:   {name:'Charles Leclerc',  short:'LEC', team:'ferrari',      num:'16'},
    norris:    {name:'Lando Norris',     short:'NOR', team:'mclaren',      num:'4'},
    piastri:   {name:'Oscar Piastri',    short:'PIA', team:'mclaren',      num:'81'},
    verstappen:{name:'Max Verstappen',   short:'VER', team:'red_bull',     num:'1'},
    hadjar:    {name:'Isack Hadjar',     short:'HAD', team:'red_bull',     num:'6'},
    perez:     {name:'Sergio Pérez',     short:'PER', team:'cadillac',     num:'11'},
    bottas:    {name:'Valtteri Bottas',  short:'BOT', team:'cadillac',     num:'77'},
    sainz:     {name:'Carlos Sainz',     short:'SAI', team:'williams',     num:'55'},
    albon:     {name:'Alex Albon',       short:'ALB', team:'williams',     num:'23'},
    gasly:     {name:'Pierre Gasly',     short:'GAS', team:'alpine',       num:'10'},
    colapinto: {name:'Franco Colapinto', short:'COL', team:'alpine',       num:'43'},
    ocon:      {name:'Esteban Ocon',     short:'OCO', team:'haas',         num:'31'},
    bearman:   {name:'Oliver Bearman',   short:'BEA', team:'haas',         num:'87'},
    alonso:    {name:'Fernando Alonso',  short:'ALO', team:'aston_martin', num:'14'},
    stroll:    {name:'Lance Stroll',     short:'STR', team:'aston_martin', num:'18'},
    hulkenberg:{name:'Nico Hülkenberg',  short:'HUL', team:'audi',         num:'27'},
    bortoleto: {name:'Gabriel Bortoleto',short:'BOR', team:'audi',         num:'5'},
    lawson:    {name:'Liam Lawson',      short:'LAW', team:'rb',           num:'3'},
    lindblad:  {name:'Arvid Lindblad',   short:'LIN', team:'rb',           num:'41'},
};

const CIRCUIT_LOOKUP = {
    'Australian Grand Prix':     'australia',
    'Chinese Grand Prix':        'china',
    'Japanese Grand Prix':       'japan',
    'Bahrain Grand Prix':        'bahrain',
    'Saudi Arabian Grand Prix':  'saudi_arabia',
    'Miami Grand Prix':          'miami',
    'Emilia Romagna Grand Prix': 'imola',  // Fixed: Emilia Romagna should map to imola
    'Monaco Grand Prix':         'monaco',
    'Spanish Grand Prix (Barcelona)': 'spain',  // Fixed: Barcelona race
    'Spanish Grand Prix (Madrid)': 'madrid',  // Fixed: Madrid race
    'Canadian Grand Prix':       'canada',
    'Austrian Grand Prix':       'austria',
    'British Grand Prix':        'britain',
    'Belgian Grand Prix':        'belgium',
    'Hungarian Grand Prix':      'hungary',
    'Dutch Grand Prix':          'netherlands',
    'Italian Grand Prix':        'italy',
    'Azerbaijan Grand Prix':     'azerbaijan',
    'Singapore Grand Prix':      'singapore',
    'United States Grand Prix':  'usa',
    'Mexico City Grand Prix':    'mexico',
    'São Paulo Grand Prix':      'brazil',
    'Las Vegas Grand Prix':      'las_vegas',
    'Qatar Grand Prix':          'qatar',
    'Abu Dhabi Grand Prix':      'uae',
};

const CIRCUIT_META = {
    australia:   {len:'5.303 km', corners:16, drs:2, sc:'35%', type:'Street/Balanced'},
    china:       {len:'5.451 km', corners:16, drs:2, sc:'28%', type:'Permanent/Technical'},
    japan:       {len:'5.807 km', corners:18, drs:2, sc:'32%', type:'Permanent/High-Speed'},
    bahrain:     {len:'5.412 km', corners:15, drs:2, sc:'25%', type:'Permanent/Balanced'},
    saudi_arabia:{len:'6.175 km', corners:27, drs:2, sc:'40%', type:'Street/High-Speed'},
    miami:       {len:'5.436 km', corners:19, drs:2, sc:'38%', type:'Street/High-Downforce'},
    italy:       {len:'5.793 km', corners:11, drs:2, sc:'25%', type:'Permanent/High-Speed'},
    monaco:      {len:'3.337 km', corners:19, drs:1, sc:'55%', type:'Street/Technical'},
    spain:       {len:'4.655 km', corners:16, drs:2, sc:'22%', type:'Permanent/Balanced'},
    canada:      {len:'4.361 km', corners:14, drs:2, sc:'45%', type:'Street/Power'},
    austria:     {len:'4.318 km', corners:10, drs:2, sc:'30%', type:'Permanent/High-Speed'},
    britain:     {len:'5.891 km', corners:18, drs:2, sc:'38%', type:'Permanent/High-Speed'},
    belgium:     {len:'7.004 km', corners:19, drs:2, sc:'48%', type:'Permanent/High-Speed'},
    netherlands: {len:'4.259 km', corners:14, drs:2, sc:'35%', type:'Permanent/Technical'},
    madrid:      {len:'5.474 km', corners:21, drs:2, sc:'32%', type:'Street/Balanced'},
    azerbaijan:  {len:'6.003 km', corners:20, drs:2, sc:'35%', type:'Street/High-Speed'},
    singapore:   {len:'5.063 km', corners:23, drs:2, sc:'42%', type:'Street/High-Downforce'},
    usa:         {len:'5.513 km', corners:20, drs:2, sc:'28%', type:'Permanent/Balanced'},
    mexico:      {len:'4.304 km', corners:17, drs:2, sc:'30%', type:'Permanent/High-Altitude'},
    brazil:      {len:'4.309 km', corners:15, drs:2, sc:'40%', type:'Permanent/Technical'},
    las_vegas:   {len:'6.201 km', corners:17, drs:2, sc:'25%', type:'Street/High-Speed'},
    qatar:       {len:'5.380 km', corners:16, drs:2, sc:'22%', type:'Permanent/Balanced'},
    uae:         {len:'5.281 km', corners:16, drs:2, sc:'20%', type:'Permanent/Balanced'},
    imola:       {len:'4.909 km', corners:19, drs:2, sc:'35%', type:'Permanent/High-Speed'},  // Added: Imola circuit
};
/* ── Plotly layout defaults ─────────────────────────────── */
const PLY = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor:  'rgba(0,0,0,0)',
    font:   {color:'#444', family:'Inter, sans-serif', size:12},
    margin: {t:20, r:20, b:60, l:60},
    xaxis:  {gridcolor:'#e8e8e8', zerolinecolor:'#e8e8e8'},
    yaxis:  {gridcolor:'#e8e8e8', zerolinecolor:'#e8e8e8'},
};

/* ── Helpers ────────────────────────────────────────────── */
function normalizeTeamKey(t) {
    return String(t || '').toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');
}
function getTeamColor(team) {
    return TEAM_COLORS[normalizeTeamKey(team)] || '#e10600';
}
function showToast(msg) {
    const t = document.getElementById('toast');
    document.getElementById('toastMsg').textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3500);
}

/* ── Loading helpers ────────────────────────────────────── */
const SIM_MSGS = [
    'Computing ELO ratings…',
    'Modelling tire degradation…',
    'Running Monte Carlo engine…',
    'Applying Platt calibration…',
    'Ranking probability distributions…',
    'Finishing up…',
];
let _simInterval = null;

function showLoading(msg) {
    // FIX: clear any existing interval to prevent stale state
    if (_simInterval) { clearInterval(_simInterval); _simInterval = null; }
    document.getElementById('simProgress').textContent = msg || 'Processing…';
    document.getElementById('loadingOverlay').classList.add('active');
    let idx = 0;
    const el = document.getElementById('simProgress');
    _simInterval = setInterval(() => {
        idx++;
        if (idx >= SIM_MSGS.length) { clearInterval(_simInterval); _simInterval = null; return; }
        if (el) el.textContent = SIM_MSGS[idx];
    }, 700);
}
function hideLoading() {
    if (_simInterval) { clearInterval(_simInterval); _simInterval = null; }
    document.getElementById('loadingOverlay').classList.remove('active');
}
/* ── Shared result renderer (used by Analytics & Settings) ── */
function renderResult(elId, html) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.style.display = 'block';
    el.innerHTML = html;
}

/* NOTE: no global onclick/eval interception here on purpose. Native inline
   onclick="..." attributes already execute fine on their own — no JS needed
   to make them work — and this app's Content-Security-Policy (script-src
   has no 'unsafe-eval') blocks window.eval() outright, so any handler that
   re-dispatches onclick via eval() would silently disable every button. */