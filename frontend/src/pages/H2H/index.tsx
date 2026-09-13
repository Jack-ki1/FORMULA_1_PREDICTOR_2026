import { useState, useMemo } from 'react'
import { useDrivers, useH2HCompare } from '../../hooks/useH2H'
import { TeamStripe } from '../../components/shared/TeamStripe'
import { DuelRadar } from '../../components/h2h/DuelRadar'
export function H2HPage(){
  const {data:drivers}=useDrivers()
  const mut=useH2HCompare()
  const [a,setA]=useState(''); const [b,setB]=useState('')
  const driverMap = useMemo(()=> {
    const m: Record<string, any> = {}
    ;(drivers||[]).forEach((d:any)=> m[d.code]=d)
    return m
  }, [drivers])
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <h2 className="f1-display text-xl font-bold">Head-to-Head</h2>
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <select value={a} onChange={e=>setA(e.target.value)} className="f1-select"><option value="">Driver A</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select>
        <select value={b} onChange={e=>setB(e.target.value)} className="f1-select"><option value="">Driver B</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select>
        <button onClick={()=> mut.mutate({a,b})} disabled={!a||!b||mut.isPending} className="btn-primary">Compare</button>
      </div>
      {mut.data && (
        <>
          <div className="card p-4">
            <div className="font-bold flex items-center gap-2"><TeamStripe color={driverMap[mut.data.driver_a.code]?.team_color} />{mut.data.driver_a.code} vs <TeamStripe color={driverMap[mut.data.driver_b.code]?.team_color} />{mut.data.driver_b.code}</div>
            <div className="f1-mono text-2xl mt-2" style={{color:'var(--red)'}}>{(mut.data.win_probability*100).toFixed(1)}% vs {(mut.data.reverse_probability*100).toFixed(1)}%</div>
            <div className="fs-11 text-sub mt-1">Elo-based H2H probability via /api/v1/h2h/compare</div>
          </div>
          <DuelRadar
            a={{
              code: mut.data.driver_a.code,
              team_color: driverMap[mut.data.driver_a.code]?.team_color,
              strength: driverMap[mut.data.driver_a.code]?.strength ?? 50,
              wet_skill: driverMap[mut.data.driver_a.code]?.wet_skill ?? 0.5,
              consistency: driverMap[mut.data.driver_a.code]?.consistency ?? 0.5,
              reliability: driverMap[mut.data.driver_a.code]?.reliability ?? 0.9,
            }}
            b={{
              code: mut.data.driver_b.code,
              team_color: driverMap[mut.data.driver_b.code]?.team_color,
              strength: driverMap[mut.data.driver_b.code]?.strength ?? 50,
              wet_skill: driverMap[mut.data.driver_b.code]?.wet_skill ?? 0.5,
              consistency: driverMap[mut.data.driver_b.code]?.consistency ?? 0.5,
              reliability: driverMap[mut.data.driver_b.code]?.reliability ?? 0.9,
            }}
          />
        </>
      )}
      {mut.isError && <div className="card p-4 text-red">{(mut.error as any).message}</div>}
    </div>
  )
}
