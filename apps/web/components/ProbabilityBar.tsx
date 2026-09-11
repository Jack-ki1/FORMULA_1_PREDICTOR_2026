interface Props {
  driverCode: string;
  driverName?: string;
  teamColor?: string;
  probability: number; // 0..1
  rank: number;
}

export function ProbabilityBar({ driverCode, driverName, teamColor, probability, rank }: Props) {
  const pct = Math.round(probability * 1000) / 10;
  const color = teamColor ?? "#5a6072";

  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-5 shrink-0 tabular text-sm text-paper-dim">{rank}</span>
      <span className="w-14 shrink-0 font-medium tabular">{driverCode}</span>
      <div className="relative h-6 flex-1 overflow-hidden rounded-sm bg-graphite-800">
        <div
          className="absolute inset-y-0 left-0 rounded-sm transition-[width] duration-500"
          style={{ width: `${Math.max(pct, 1.5)}%`, backgroundColor: color }}
        />
      </div>
      <span className="w-16 shrink-0 text-right tabular text-sm">{pct.toFixed(1)}%</span>
      {driverName && <span className="hidden w-32 shrink-0 truncate text-sm text-paper-dim md:block">{driverName}</span>}
    </div>
  );
}
