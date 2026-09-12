import { Bar, Doughnut } from 'react-chartjs-2'
import { Chart as C, CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend } from 'chart.js'
C.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)
export function PredictionCharts({result}:{result:any}){
  if(!result) return null
  const firstKey = Object.keys(result.predictions||{})[0]
  const preds = result.predictions?.[firstKey]?.predictions?.slice(0,8) || []
  const labels = preds.map((p:any)=>p.driver_code)
  const data = preds.map((p:any)=>p.percentage)
  const colors = preds.map((_:any,i:number)=> `hsl(${0 + i*12}, 80%, 50%)`)
  return (
    <div className="charts-grid">
      <div className="card p-4"><div className="f1-display font-bold mb-2">Top 8 — {firstKey}</div><Bar data={{labels, datasets:[{label:'%', data, backgroundColor: colors}]}} options={{responsive:true, plugins:{legend:{display:false}}}}/></div>
      <div className="card p-4"><div className="f1-display font-bold mb-2">Distribution</div><Doughnut data={{labels, datasets:[{data, backgroundColor: colors}]}} options={{responsive:true}}/></div>
    </div>
  )
}
