import type { ChartData } from 'chart.js'
export function attributeRadar(a:any,b:any): ChartData<'radar'> {
  return { labels:['Pace','Consistency','Wet','Overtaking','Tyre'], datasets:[
    {label:a?.code||'A', data:[a?.pace||0,a?.consistency||0,a?.wet||0,a?.overtaking||0,a?.tyre||0], backgroundColor:'rgba(225,6,0,0.2)', borderColor:'#E10600'},
    {label:b?.code||'B', data:[b?.pace||0,b?.consistency||0,b?.wet||0,b?.overtaking||0,b?.tyre||0], backgroundColor:'rgba(54,113,198,0.2)', borderColor:'#3671C6'},
  ]}
}
export function winProbabilityBar(p:number): ChartData<'bar'> {
  return { labels:['Win Prob'], datasets:[{label:'A', data:[p*100], backgroundColor:'#E10600'},{label:'B', data:[(1-p)*100], backgroundColor:'#3671C6'}]}
}
