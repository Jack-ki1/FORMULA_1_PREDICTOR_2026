export function DriverChip({ code, team, color }: { code:string; team?:string; color?:string }) {
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold" style={{background: color||'#eee', color:'#fff'}}>{code}{team?` · ${team}`:''}</span>
}
