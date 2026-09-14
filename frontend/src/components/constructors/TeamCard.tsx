export function TeamCard({ team }:any){ return <div className="card p-4"><div className="font-bold">{team?.name||team?.team}</div><div className="fs-11 text-sub">{team?.points ?? 0} pts</div></div>}
