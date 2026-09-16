import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode, useState } from 'react'

export function Providers({children}:{children:ReactNode}){
  const [client]=useState(()=> new QueryClient({
    defaultOptions:{
      queries:{
        // retry:1 doubled the user-visible wait on any slow/failed request —
        // 3s became 6s. The UI already renders a fallback, so a single retry is
        // not worth the latency. Retry only genuine network blips.
        retry: 0,
        // Lists like races/drivers/standings change at most once a weekend.
        // A 5-minute stale window means navigating between pages reuses the
        // cached payload instead of re-hitting the API every time.
        staleTime: 5 * 60_000,
        gcTime: 30 * 60_000,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
      },
      mutations:{ retry:0 }
    }
  }))
  return (
    <QueryClientProvider client={client}>
      {children}
    </QueryClientProvider>
  )
}
