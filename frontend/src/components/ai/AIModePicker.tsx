export function AIModePicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex gap-2">
      <button onClick={() => onChange('normal')} className={`px-3 py-1.5 rounded text-sm ${value==='normal'?'bg-red text-white':'card'}`}>Normal</button>
      <button onClick={() => onChange('ai')} className={`px-3 py-1.5 rounded text-sm ${value==='ai'?'bg-red text-white':'card'}`}>AI-Enhanced</button>
    </div>
  )
}
