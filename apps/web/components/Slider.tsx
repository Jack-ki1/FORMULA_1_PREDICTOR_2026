export function Slider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="block">
      <div className="mb-1 flex items-center justify-between text-xs text-paper-dim">
        <span>{label}</span>
        <span className="tabular">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-purple-fastest"
      />
    </label>
  );
}
