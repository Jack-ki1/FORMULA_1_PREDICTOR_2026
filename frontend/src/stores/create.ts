import { useState, useSyncExternalStore } from 'react'
function createStore<T>(initializer:(set:(p:Partial<T>|((s:T)=>Partial<T>))=>void, get:()=>T)=>T){
  let state: T
  const listeners = new Set<()=>void>()
  const set = (partial:any)=> {
    const upd = typeof partial==='function'? partial(state): partial
    state = { ...state, ...upd }
    listeners.forEach(l=>l())
  }
  const get = ()=> state
  state = initializer(set as any, get)
  const subscribe = (cb:()=>void)=>{ listeners.add(cb); return ()=> listeners.delete(cb)}
  const useStore = (selector?: (s:T)=>any)=> {
    const snap = useSyncExternalStore(subscribe, get, get)
    return selector ? selector(snap) : snap
  }
  ;(useStore as any).getState=get; (useStore as any).setState=set
  return useStore as any
}
export const create = createStore as any
