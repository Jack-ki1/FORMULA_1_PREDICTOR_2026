import type { ChartData } from 'chart.js'
export function powerRankingsChart(teams:any[]): ChartData<'bar'> {
  return { labels: teams.map(t=>t.team||t.name), datasets:[{label:'Power', data:teams.map(t=>t.power||t.points||0), backgroundColor:'#E10600'}] }
}
