import { useState } from 'react'
import { RaceSelector } from '../../components/dashboard/RaceSelector'
import { SessionSelector } from '../../components/dashboard/SessionSelector'
import { WeatherSelector } from '../../components/dashboard/WeatherSelector'
import { PredictionControls } from '../../components/dashboard/PredictionControls'
import { PredictionResults } from '../../components/prediction/PredictionResults'
import { GridEditor } from '../../features/manual-grid/GridEditor'
import { AISidebar } from '../../features/ai-assistant/AISidebar'
import { PredictionCharts } from '../../components/charts/PredictionCharts'
import { useDashboardStore } from '../../stores/dashboardStore'
import { exportReport } from '../../api/reports'
export function DashboardPage(){
  const [result,setResult]=useState<any>(null)
  const setManual=useDashboardStore(s=>s.setManualGrid) as any
  const manualGrid=useDashboardStore(s=>s.manualGrid) as any
  const draft=useDashboardStore(s=>s.draft) as any
  const session=useDashboardStore(s=>s.session) as any
  const subSession=useDashboardStore(s=>s.subSession) as any
  const targetId=useDashboardStore(s=>s.targetId) as any
  const saveResult = (r:any)=> {
    setResult(r)
    try{
      localStorage.setItem('f1-last-prediction', JSON.stringify({ raceId: r.race_id || draft.raceId, predictions: r.predictions }))
      window.dispatchEvent(new Event('f1-prediction'))
    } catch{}
  }
  return (
    <div className="px-4 sm:px-8 py-6 space-y-4">
      <RaceSelector />
      <SessionSelector />
      <WeatherSelector />
      <PredictionControls onResult={saveResult} />
      {session==='race' && (
        <div className="card p-4 flex items-center gap-2">
          <span>Grid source: {result?.grid_positions? 'auto (Q3 model)': 'none'}</span>
          <button onClick={()=> document.getElementById('grid-editor')?.scrollIntoView()} className="btn-ghost text-sm">Edit Grid Manually</button>
        </div>
      )}
      <div id="grid-editor"><GridEditor value={manualGrid} onChange={setManual} /></div>
      <PredictionCharts result={result} />
      <PredictionResults result={result} />
      {result && (
        <div className="card p-4 flex items-center gap-2">
          <select id="export-format" defaultValue="csv" className="f1-select" style={{maxWidth:'160px'}}><option value="csv">CSV</option><option value="json">JSON</option><option value="pdf">PDF</option></select>
          <button onClick={()=>{
            const fmt=(document.getElementById('export-format') as HTMLSelectElement).value
            exportReport({race_id:draft.raceId, session, sub_session:subSession, target_id:targetId, format:fmt, predictions: result.predictions})
          }} className="btn-ghost">Export</button>
          <span className="fs-11 text-sub">Exports via /api/v1/reports/export</span>
        </div>
      )}
      <AISidebar />
    </div>
  )
}
