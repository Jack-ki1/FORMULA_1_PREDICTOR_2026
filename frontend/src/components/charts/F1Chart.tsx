import { useMemo } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, RadialLinearScale,
  BarElement, PointElement, LineElement, ArcElement, Tooltip, Legend,
  type ChartData, type ChartOptions, type ChartType,
} from 'chart.js'
import { Chart } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale, LinearScale, RadialLinearScale,
  BarElement, PointElement, LineElement, ArcElement,
  Tooltip, Legend
)

export function F1Chart({
  type, data, options, height = 240,
}: { type: ChartType; data: ChartData<any>; options?: ChartOptions<any>; height?: number }) {
  const themed = useMemo<ChartOptions<any>>(() => {
    const style = typeof document !== 'undefined' ? getComputedStyle(document.documentElement) : null
    const text = style?.getPropertyValue('--text').trim() || '#1a1a1a'
    const sub = style?.getPropertyValue('--sub').trim() || '#6b7280'
    const border = style?.getPropertyValue('--border').trim() || '#e5e7eb'
    return {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: sub, font: { family: "'Inter', sans-serif", size: 11 } } },
        tooltip: { backgroundColor: text, titleColor: '#fff', bodyColor: '#fff', padding: 10, cornerRadius: 8, displayColors: false },
      },
      scales: type === 'radar'
        ? { r: { grid: { color: border }, angleLines: { color: border }, pointLabels: { color: sub, font: { size: 10 } }, ticks: { display: false } } }
        : type === 'doughnut' || type === 'pie' ? undefined
        : { x: { grid: { color: border }, ticks: { color: sub, font: { size: 10 } } }, y: { grid: { color: border }, ticks: { color: sub, font: { size: 10 } } } },
    }
  }, [type])
  return <div style={{ height }}><Chart type={type} data={data} options={{ ...themed, ...options } as any} /></div>
}
