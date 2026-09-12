export async function exportReport(payload:any): Promise<void> {
  const res = await fetch('/api/v1/reports/export', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
  if (!res.ok) throw new Error('export failed')
  const ct = res.headers.get('content-type')||''
  if (ct.includes('application/json')) {
    const data = await res.json(); const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`f1_${payload.race_id}_${payload.format}.json`; a.click(); URL.revokeObjectURL(url); return;
  }
  const blob=await res.blob(); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; const ext=payload.format==='pdf'?'pdf':payload.format==='csv'?'csv':'bin'; a.download=`f1_${payload.race_id}.${ext}`; a.click(); URL.revokeObjectURL(url);
}
