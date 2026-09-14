export function HeroPanel({ race, weather, countdown }: any) {
  return <div className="card p-4"><div className="f1-display font-bold">{race?.name||'Select race'}</div><div className="fs-11 text-sub">{weather} · {countdown||''}</div></div>
}
