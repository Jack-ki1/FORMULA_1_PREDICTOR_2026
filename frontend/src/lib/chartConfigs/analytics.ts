import type { ChartData } from 'chart.js'
export function accuracyChart(data:any): ChartData<'bar'> {
  return { labels: Object.keys(data||{}), datasets:[{label:'Accuracy %', data:Object.values(data||{}).map((v:any)=> (v?.accuracy||0)*100), backgroundColor:'#229971'}] }
}
