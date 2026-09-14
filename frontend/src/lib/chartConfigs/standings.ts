import type { ChartData } from 'chart.js'
const TEAM_COLORS: Record<string,string> = { mclaren:'#FF8000', ferrari:'#E8002D', redbull:'#3671C6', mercedes:'#00A19B', astonmartin:'#229971', williams:'#1E6FCE', audi:'#BB0A30', alpine:'#0090FF', haas:'#9198A1', racingbulls:'#3F5FCC', cadillac:'#9C7A19' }
const tc=(t:string)=>TEAM_COLORS[(t||'').toLowerCase().replace(/[^a-z]/g,'')]||'#9AA0AC'
export function driverPointsChart(drivers:any[]): ChartData<'bar'> {
  return { labels: drivers.map(d=>d.driver_code||d.driver_name), datasets:[{label:'Points', data:drivers.map(d=>d.points??0), backgroundColor: drivers.map(d=>tc(d.team)), borderRadius:4}]}
}
export function constructorShareChart(constructors:any[]): ChartData<'doughnut'> {
  return { labels: constructors.map(t=>t.team||t.name), datasets:[{data:constructors.map(t=>t.points??0), backgroundColor:constructors.map(t=>tc(t.team||t.name)), borderWidth:0}]}
}
