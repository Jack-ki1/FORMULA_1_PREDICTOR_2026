export const PROVIDERS = {
  google: { label: 'Google', icon: '●', color: '#4285F4', requiresKey: true, keyLabel: 'Google AI API Key (aistudio.google.com)' },
  openai: { label: 'OpenAI', icon: '●', color: '#10A37F', requiresKey: true, keyLabel: 'OpenAI API Key (platform.openai.com)' },
  claude: { label: 'Claude (Anthropic)', icon: '●', color: '#CC785C', requiresKey: true, keyLabel: 'Anthropic API Key (console.anthropic.com)' },
  free: { label: 'Free — Puter (No Key)', icon: '◆', color: '#8B5CF6', requiresKey: false, keyLabel: 'No API key needed — runs via Puter.js' },
} as const

export const MODEL_GROUPS: Record<string, string[]> = {
  google: [
    'gemini-3.8-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-pro-preview',
    'gemini-2.5-pro-preview',
    'gemini-2.5-flash',
    'gemini-2.0-flash-exp',
  ],
  openai: [
    'gpt-6-astra',
    'gpt-5.6-sol',
    'gpt-5.6-terra',
    'gpt-5.6-luna',
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-3.5-turbo',
    'o1',
  ],
  claude: [
    'claude-fable-5',
    'claude-opus-5',
    'claude-opus-4-8',
    'claude-sonnet-5',
    'claude-haiku-4-5',
    'claude-3-5-sonnet',
  ],
  free: [
    'puter:gemini-3.8-flash',
    'puter:gemini-3.6-flash',
    'puter:gpt-5.6-luna',
    'puter:gpt-4o-mini',
    'puter:claude-3-5-sonnet',
    'puter:deepseek-v3',
    'puter:llama-3.1-70b',
    'puter:mistral-medium-3.5',
    'puter:grok-4.5',
  ],
}

export function getProviderForModel(model: string): keyof typeof PROVIDERS {
  if (model.startsWith('puter:')) return 'free'
  if (model.startsWith('gemini')) return 'google'
  if (model.startsWith('gpt') || model.startsWith('o1')) return 'openai'
  if (model.startsWith('claude')) return 'claude'
  return 'openai'
}

export function AIModelSelect({ value, onChange, provider }: { value: string; onChange: (v:string)=>void; provider?: keyof typeof PROVIDERS }) {
  const groupsToShow = provider ? { [provider]: MODEL_GROUPS[provider] } : MODEL_GROUPS
  return (
    <select value={value} onChange={e=>onChange(e.target.value)} className="f1-select w-full">
      {Object.entries(groupsToShow).map(([group, models])=> (
        <optgroup key={group} label={PROVIDERS[group as keyof typeof PROVIDERS]?.label || group}>
          {models.map(m=> <option key={m} value={m}>{m}</option>)}
        </optgroup>
      ))}
    </select>
  )
}
