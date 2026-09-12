import { createContext, useEffect, useState } from 'react'
export const ThemeCtx = createContext<{theme:string; toggle:()=>void}>({theme:'light', toggle:()=>{}})
export function ThemeProvider({children}:{children:any}){
  const [theme,setTheme]=useState(localStorage.getItem('f1-theme')||'light')
  useEffect(()=>{ document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('f1-theme', theme)},[theme])
  return <ThemeCtx.Provider value={{theme, toggle:()=> setTheme(theme==='dark'?'light':'dark')}}>{children}</ThemeCtx.Provider>
}
