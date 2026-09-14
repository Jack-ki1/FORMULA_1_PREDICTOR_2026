export function AISettingsPanel({ weight, temp, onWeight, onTemp }: { weight:number; temp:number; onWeight:(n:number)=>void; onTemp:(n:number)=>void }) {
  return (
    <div className="space-y-3">
      <label className="block"><span className="fs-11 text-sub">AI Weight {weight.toFixed(2)}</span><input type="range" min={0} max={1} step={0.05} value={weight} onChange={e=>onWeight(parseFloat(e.target.value))} className="w-full" /></label>
      <label className="block"><span className="fs-11 text-sub">Temperature {temp.toFixed(2)}</span><input type="range" min={0} max={1} step={0.05} value={temp} onChange={e=>onTemp(parseFloat(e.target.value))} className="w-full" /></label>
    </div>
  )
}
