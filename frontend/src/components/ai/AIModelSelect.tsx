const GROUPS = {
  Gemini: ['gemini-2.0-flash-exp','gemini-1.5-pro'],
  OpenAI: ['gpt-4o','gpt-4o-mini'],
  Anthropic: ['claude-3-5-sonnet'],
  Local: ['ollama/llama3','ollama/mistral'],
  Custom: ['custom'],
}
export function AIModelSelect({ value, onChange }: { value: string; onChange: (v:string)=>void }) {
  return (
    <select value={value} onChange={e=>onChange(e.target.value)} className="f1-select w-full">
      {Object.entries(GROUPS).map(([group, models])=> (
        <optgroup key={group} label={group}>
          {models.map(m=> <option key={m} value={m}>{m}</option>)}
        </optgroup>
      ))}
    </select>
  )
}
