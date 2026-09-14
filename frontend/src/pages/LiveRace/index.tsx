import { useEffect, useState } from 'react';
import { liveApi } from '../../api/live';

export function LiveRacePage(){
  const [sessionKey, setSessionKey] = useState('latest');
  const [data, setData] = useState<any>(null);
  const [mode, setMode] = useState<string>('-');
  const [connected, setConnected] = useState(false);

  useEffect(()=>{
    let es: EventSource | null = null;
    let pollTimer: any = null;
    const start = async()=>{
      try{
        const snap = await liveApi.snapshot(sessionKey);
        setData(snap);
        setMode(snap.mode || 'historical_snapshot');
      }catch{}
      // try SSE
      try{
        es = new EventSource(liveApi.streamUrl(sessionKey));
        es.onopen = ()=> setConnected(true);
        es.onmessage = (e)=> {
          try{ const parsed = JSON.parse(e.data); setData(parsed); setMode(parsed.mode);}catch{}
        };
        es.onerror = ()=> { setConnected(false); es?.close(); };
      }catch{ setConnected(false); }
      // fallback poll if no SSE
      pollTimer = setInterval(async()=>{
        if (!es || es.readyState === 2) {
          try{ const s = await liveApi.snapshot(sessionKey); setData(s); setMode(s.mode);}catch{}
        }
      }, 5000);
    };
    start();
    return ()=> { es?.close(); clearInterval(pollTimer); };
  }, [sessionKey]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
      <div className="f1-hero mb-6 rounded-xl p-6 text-white" style={{background:'linear-gradient(135deg,#0a0a09,#16233F)'}}>
        <div className="flex items-center gap-3"><h1 className="text-2xl font-bold">Live Race</h1><span className="f1-live-pill">{connected?'LIVE':'SNAPSHOT'}</span><span className="text-xs opacity-70">{mode}</span></div>
        <p className="opacity-80 text-sm mt-1">OpenF1 live where subscription permits; otherwise latest historical snapshot — never pretending to be live.</p>
        <div className="mt-3 flex gap-2"><input value={sessionKey} onChange={e=>setSessionKey(e.target.value)} placeholder="session key (e.g. 2025-09-14 or latest)" className="f1-input flex-1 max-w-md"/><span className="text-xs opacity-60 self-center">{data?.timestamp?.slice(0,19)}</span></div>
        {mode==='historical_snapshot' && <div className="mt-2 text-xs bg-yellow-500/20 border border-yellow-500/30 rounded px-3 py-2">Using latest historical snapshot — not live. Live requires OpenF1 subscription.</div>}
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="card p-4">
          <h3 className="font-semibold mb-2">Pit Stops</h3>
          <div className="text-sm space-y-1 max-h-72 overflow-auto">
            {(data?.data?.pit_stops||[]).slice(0,10).map((p:any,i:number)=> <div key={i} className="flex justify-between border-b py-1"><span>Driver {p.driver_number||p.driver}</span><span>Lap {p.lap_number||'-'} {p.compound||''}</span></div>)}
            {(!data?.data?.pit_stops?.length) && <div className="opacity-60">No pit data in snapshot.</div>}
          </div>
          <div className="text-xs opacity-50 mt-2">Provenance: {data?.provenance?.pit?.provider || '-' } · {data?.provenance?.pit?.cache_status || '-'}</div>
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-2">Race Control</h3>
          <div className="text-sm space-y-1 max-h-72 overflow-auto">
            {(data?.data?.race_control||[]).slice(0,10).map((r:any,i:number)=> <div key={i} className="border-b py-1"><span className="font-mono text-xs">{r.category||r.flag||'INFO'}</span> <span>{r.message||r.scope||'-'}</span> <span className="opacity-60">Lap {r.lap_number||'-'}</span></div>)}
            {(!data?.data?.race_control?.length) && <div className="opacity-60">No race control in snapshot.</div>}
          </div>
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-2">Live Predictions (coming)</h3>
          <div className="text-sm opacity-70">Win prob, podium, DNF risk updated incrementally from pit + SC + telemetry. Shows delta lap-over-lap.</div>
          <div className="mt-3 p-3 bg-black text-white rounded text-xs">
            <div>VER win: 37% → 46% (pit + undercut)</div>
            <div className="opacity-60">Demo — wired to /predictions/scenario for what-if</div>
          </div>
          <div className="text-xs opacity-50 mt-2">Updates via SSE every 3s; fallback polling 5s.</div>
        </div>
      </div>
    </div>
  )
}
