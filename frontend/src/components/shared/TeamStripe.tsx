export function TeamStripe({ color, size = 'default' }: { color?: string; size?: 'small' | 'default' }) {
  const style: React.CSSProperties = {
    background: color || 'var(--muted)',
    width: size === 'small' ? 3 : 4,
    height: size === 'small' ? 16 : 22,
  }
  return <span className="team-bar" style={style} />
}
