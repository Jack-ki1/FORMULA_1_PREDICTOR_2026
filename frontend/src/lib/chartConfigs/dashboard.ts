// Pure (data) => ChartData functions for dashboard — unit-testable, no React/DOM
import type { ChartData } from 'chart.js'
export function podiumDistribution(result:any): ChartData<'bar'> {
  const preds = result?.predictions ? Object.values(result.predictions as any)[0] as any : null
  const top = preds?.predictions?.slice(0,8) || []
  return { labels: top.map((p:any)=>p.driver_code), datasets:[{label:'Win %', data: top.map((p:any)=>p.percentage||0), backgroundColor:'#E10600'}] }
}
export function confidenceGauge(result:any): ChartData<'doughnut'> {
  const c = result?.confidence ?? 0
  return { labels:['Confidence','Remaining'], datasets:[{data:[c,100-c], backgroundColor:['#E10600','#e5e7eb'], borderWidth:0}] }
}
export function dnfRisk(result:any): ChartData<'bar'> {
  const preds = result?.predictions ? Object.values(result.predictions as any)[0] as any : null
  const top = preds?.predictions?.slice(0,8) || []
  return { labels: top.map((p:any)=>p.driver_code), datasets:[{label:'DNF %', data: top.map((p:any)=> (p.dnf_probability||0)*100), backgroundColor:'#6b7280'}] }
}
