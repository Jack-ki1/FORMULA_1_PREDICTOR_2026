import { create } from './create'
type Draft = { raceId:string; weather:string; simCount:number }
export type DashboardState = {
  draft: Draft; session: string; subSession: string; targetId: string;
  manualGrid: Record<string,number>|null; gridPositions: Record<string,number>|null; gridSource: string|null;
  aiMode:string; aiModel:string; aiWeight:number; aiTemperature:number;
  setDraft:(d:Partial<Draft>)=>void; setSession:(s:string)=>void; setSubSession:(v:string)=>void; setTarget:(v:string)=>void;
  setManualGrid:(g:any)=>void; setGridPositions:(g:any, src:string)=>void; setAI:(p:any)=>void
}
export const useDashboardStore = (create as any)((set:any)=>({
  draft:{ raceId:'', weather:'dry', simCount:10000 },
  session:'race', subSession:'Race', targetId:'podium',
  manualGrid:null, gridPositions:null, gridSource:null,
  aiMode: localStorage.getItem('f1-ai-mode')||'normal',
  aiModel: localStorage.getItem('f1-ai-model')||'gemini-2.0-flash-exp',
  aiWeight: parseInt(localStorage.getItem('f1-ai-weight')||'30'),
  aiTemperature: parseFloat(localStorage.getItem('f1-ai-temperature')||'0.7'),
  setDraft:(d:any)=> set((s:any)=> ({ draft:{...s.draft, ...d}})),
  setSession:(s:string)=> set({session:s}),
  setSubSession:(v:string)=> set({subSession:v}),
  setTarget:(v:string)=> set({targetId:v}),
  setManualGrid:(g:any)=> set({manualGrid:g}),
  setGridPositions:(g:any,src:string)=> set({gridPositions:g, gridSource:src}),
  setAI:(p:any)=> {
    const upd:any={}; if(p.aiMode!==undefined) upd.aiMode=p.aiMode; if(p.aiModel!==undefined) upd.aiModel=p.aiModel; if(p.aiWeight!==undefined) upd.aiWeight=p.aiWeight; if(p.aiTemperature!==undefined) upd.aiTemperature=p.aiTemperature;
    set(upd as any);
    if(p.aiMode) localStorage.setItem('f1-ai-mode', p.aiMode);
    if(p.aiModel) localStorage.setItem('f1-ai-model', p.aiModel);
    if(p.aiWeight!==undefined) localStorage.setItem('f1-ai-weight', String(p.aiWeight));
    if(p.aiTemperature!==undefined) localStorage.setItem('f1-ai-temperature', String(p.aiTemperature));
  }
}))
