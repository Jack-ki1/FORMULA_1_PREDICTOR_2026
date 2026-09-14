import { api } from './client';
export const liveApi = {
  snapshot: (sessionKey:string)=> api.get<any>(`/api/v1/live/${sessionKey}`),
  // SSE helper — caller can `new EventSource('/api/v1/live/.../stream')` directly
  streamUrl: (sessionKey:string)=> `/api/v1/live/${sessionKey}/stream`,
};
