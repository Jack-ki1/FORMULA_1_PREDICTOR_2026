import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { scenarioApi } from '../../api/scenario';
import { api } from '../../api/client';

type Race = { id:string; name:string; circuit:string };

export function ScenarioLabPage(){
  const { data: races } = useQuery({ queryKey:['races'], queryFn: ()=> api.get<Race[]>('/api/v1/races'), staleTime: 300000 });
  const [raceId, setRaceId] = useState('au');
  const [weather, setWeather] = useState('dry');
  const [gridVer, setGridVer] = useState('1');
  const [safety, setSafety] = useState('normal');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string|null>(null);

  const run = async()=>{
    setLoading(true); setErr(null);
    try{
      // simple grid scenario: if gridVer === 'verstappen p14'
      const scenario:any = {};
      if (weather !== 'dry') scenario.weather = weather;
      if (gridVer === 'p14') scenario.grid_positions = { VER:14 };
      if (safety === 'high') scenario.safety_car_boost = 1.5;
      const r = await scenarioApi.run({ race_id: raceId, weather:'dry', scenario, simulation_count:5000 });
      setResult(r);
    }catch(e:any){ setErr(e.message || String(e)); }
    finally{ setLoading(false); }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
      <div className="f1-hero mb-6 rounded-xl p-6 text-white" style={{background:'linear-gradient(135deg,#0a0a09,#16233F)'}}>
        <h1 className="text-2xl font-bold">Scenario Lab</h1>
        <p className="opacity-80 text-sm mt-1">What happens if conditions change? Baseline vs scenario — model vs simulation.</p>
        <div className="mt-2 text-xs opacity-60">Baseline vs scenario uses the same calibrated ensemble + Monte Carlo; deltas are deterministic.</div>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <label className="card p-4">Race
          <select value={raceId} onChange={e=>setRaceId(e.target.value)} className="f1-select w-full mt-2">
            {(races||[]).map(r=> <option key={r.id} value={r.id}>{r.name}</option>)}
            {!races?.length && <><option value="au">Australia</option><option value="mc">Monaco</option><option value="sg">Singapore</option></>}
          </select>
        </label>
        <label className="card p-4">Weather scenario
          <select value={weather} onChange={e=>setWeather(e.target.value)} className="f1-select w-full mt-2">
            <option value="dry">Dry</option><option value="wet">Wet</option><option value="mixed">Mixed</option>
          </select>
        </label>
        <label className="card p-4">Grid scenario
          <select value={gridVer} onChange={e=>setGridVer(e.target.value)} className="f1-select w-full mt-2">
            <option value="1">Default</option><option value="p14">VER P14 (what-if)</option>
          </select>
        </label>
      </div>
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <label className="card p-4">Safety car
          <select value={safety} onChange={e=>setSafety(e.target.value)} className="f1-select w-full mt-2">
            <option value="normal">Normal</option><option value="high">High SC risk</option>
          </select>
        </label>
        <div className="card p-4 flex items-end"><button onClick={run} disabled={loading} className="btn btn-primary w-full">{loading?'Simulating…':'Run scenario — baseline vs scenario'}</button></div>
        <div className="card p-4 text-xs opacity-70">Examples:<br/>• Heavy rain: wet<br/>• VER P14<br/>• Safety car lap 45: high</div>
      </div>

      {err && <div className="card p-4 border-red-200 text-red-600 mb-4">{err}</div>}
      {result && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card p-4">
            <h3 className="font-semibold mb-2">Baseline — win prob</h3>
            <div className="space-y-1 text-sm">
              {Object.entries(result.baseline.winner_probabilities).sort((a:any,b:any)=>b[1]-a[1]).slice(0,8).map(([code,p]:any)=>(
                <div key={code} className="flex justify-between"><span>{code}</span><span>{(Number(p)*100).toFixed(1)}%</span></div>
              ))}
            </div>
          </div>
          <div className="card p-4">
            <h3 className="font-semibold mb-2">Scenario — win prob + delta</h3>
            <div className="space-y-1 text-sm">
              {Object.entries(result.scenario.winner_probabilities).sort((a:any,b:any)=>b[1]-a[1]).slice(0,8).map(([code,p]:any)=>{
                const d = result.diff[code]||0;
                return <div key={code} className="flex justify-between"><span>{code}</span><span>{(Number(p)*100).toFixed(1)}% <span className={d>0?'text-green-600':'text-red-600'}>({d>0?'+':''}{(d*100).toFixed(1)}pp)</span></span></div>
              })}
            </div>
          </div>
        </div>
      )}
      {!result && <div className="card p-8 text-center opacity-60">Run a scenario to see baseline vs scenario probability shifts.</div>}
    </div>
  )
}
