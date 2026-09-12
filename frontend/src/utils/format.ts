export const pct = (p:number)=> (p*100).toFixed(2)+'%'
export const escapeHtml = (s:string)=> s.replace(/[&<>"']/g, m=> ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]!))
export const teamColor = (team:string)=> ({ 'Red Bull':'#0600EF','Ferrari':'#DC0000','Mercedes':'#00D2BE','McLaren':'#FF8700','Aston Martin':'#006F62','Alpine':'#0090FF','Williams':'#005AFF','RB':'#2B4562','Kick Sauber':'#52E252','Haas':'#FFFFFF'}[team]||'#6B7280')
export const compoundForWeather = (w:string)=> w==='wet'? 'FULL_WET': w==='mixed'? 'INTERMEDIATE':'SOFT'
export const tyreChipHtml = (c:string)=> `<span class="tyre-dot" style="background:${{SOFT:'#E10600',MEDIUM:'#FFD700',HARD:'#FFFFFF',INTERMEDIATE:'#00D2BE',FULL_WET:'#0066FF'}[c]||'#ccc'};width:10px;height:10px;display:inline-block;border-radius:999px;border:1px solid rgba(0,0,0,.15)"></span> ${c}`
