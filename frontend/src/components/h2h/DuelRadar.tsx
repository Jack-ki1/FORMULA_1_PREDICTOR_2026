import { Radar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

type DriverRadar = {
  code: string
  name?: string
  team_color?: string
  strength: number
  wet_skill: number
  consistency: number
  reliability: number
}

export function DuelRadar({ a, b }: { a: DriverRadar; b: DriverRadar }) {
  const labels = ['Strength', 'Wet Skill', 'Consistency', 'Reliability']
  // Normalize to 0-100 for radar (strength is 0-100, others 0-1 or 0-100 depending on source)
  const norm = (v: number) => (v > 1 ? v : v * 100)
  const data = {
    labels,
    datasets: [
      {
        label: a.code,
        data: [norm(a.strength), norm(a.wet_skill), norm(a.consistency), norm(a.reliability)],
        borderColor: a.team_color || '#E10600',
        backgroundColor: (a.team_color || '#E10600') + '33',
        pointBackgroundColor: a.team_color || '#E10600',
      },
      {
        label: b.code,
        data: [norm(b.strength), norm(b.wet_skill), norm(b.consistency), norm(b.reliability)],
        borderColor: b.team_color || '#16233F',
        backgroundColor: (b.team_color || '#16233F') + '33',
        pointBackgroundColor: b.team_color || '#16233F',
      },
    ],
  }
  const options = {
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: { stepSize: 20, backdropColor: 'transparent' },
        grid: { color: 'rgba(0,0,0,0.08)' },
        angleLines: { color: 'rgba(0,0,0,0.08)' },
      },
    },
    plugins: { legend: { position: 'bottom' as const } },
    maintainAspectRatio: false as const,
  }
  return (
    <div className="card p-4">
      <div className="f1-display font-bold mb-2">Duel Radar — explains the Elo</div>
      <div className="fs-11 text-sub mb-3">Strength, wet, consistency, reliability — the inputs behind the win prob.</div>
      <div style={{ height: 280 }}>
        <Radar data={data} options={options as any} />
      </div>
    </div>
  )
}
