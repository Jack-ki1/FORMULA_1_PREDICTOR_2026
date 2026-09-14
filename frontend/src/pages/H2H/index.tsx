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
  const racerImg = (code:string, fallback:string) => {
    // Use racer images creatively — cycle through 3 racer images
    const idx = (code.charCodeAt(0) + (code.charCodeAt(1)||0)) % 3
    return ['/media/racer1.png','/media/racer2.png','/media/racer3.png'][idx] || fallback
  }
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <div className="card p-0 overflow-hidden">
        <div className="grid md:grid-cols-2 gap-0">
          <img src="/media/racer1.png" alt="Racers" loading="lazy" className="w-full h-40 object-cover" />
          <div className="p-6">
            <h2 className="f1-display text-xl font-bold">Head-to-Head — Elo Battle</h2>
            <p className="fs-11 text-sub mt-1">Any two drivers, any era. Elo-derived win probability with wet-skill & consistency. 2026 active aero makes every duel closer.</p>
          </div>
        </div>
      </div>
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <select value={a} onChange={e=>setA(e.target.value)} className="f1-select"><option value="">Driver A</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select>
        <select value={b} onChange={e=>setB(e.target.value)} className="f1-select"><option value="">Driver B</option>{(drivers||[]).map((d:any)=><option key={d.code} value={d.code}>{d.code} — {d.name}</option>)}</select>
        <button onClick={()=> mut.mutate({a,b})} disabled={!a||!b||mut.isPending} className="btn-primary">Compare</button>
      </div>
      {mut.data && (
        <>
          <div className="card p-0 overflow-hidden">
            <div className="grid grid-cols-3 gap-0 items-center">
              <div className="p-4 text-center">
                <img src={racerImg(mut.data.driver_a.code, '/media/racer1.png')} alt={mut.data.driver_a.code} className="w-24 h-24 mx-auto rounded-full object-cover border-4 shadow-md" style={{ borderColor: driverMap[mut.data.driver_a.code]?.team_color||'#ccc' }} loading="lazy" />
                <div className="f1-display font-bold mt-2 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_a.code]?.team_color} />{mut.data.driver_a.code}</div>
                <div className="fs-11 text-sub">{mut.data.driver_a.name}</div>
              </div>
              <div className="text-center p-4">
                <div className="f1-display text-2xl font-black" style={{ color: 'var(--red)' }}>VS</div>
                <div className="f1-mono text-lg font-bold mt-1">{(mut.data.win_probability*100).toFixed(1)}% — {(mut.data.reverse_probability*100).toFixed(1)}%</div>
                <div className="fs-11 text-sub mt-1">Elo probability</div>
              </div>
              <div className="p-4 text-center">
                <img src={racerImg(mut.data.driver_b.code, '/media/racer2.png')} alt={mut.data.driver_b.code} className="w-24 h-24 mx-auto rounded-full object-cover border-4 shadow-md" style={{ borderColor: driverMap[mut.data.driver_b.code]?.team_color||'#ccc' }} loading="lazy" />
                <div className="f1-display font-bold mt-2 flex items-center justify-center gap-2"><TeamStripe color={driverMap[mut.data.driver_b.code]?.team_color} />{mut.data.driver_b.code}</div>
                <div className="fs-11 text-sub">{mut.data.driver_b.name}</div>
              </div>
            </div>
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
