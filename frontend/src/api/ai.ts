import { api } from './client'
export const aiApi = {
  chat: (payload: { message:string; model:string; api_key:string; temperature:number }) => api.post<{response:string}>('/api/v1/ai/chat', { body: JSON.stringify(payload) } as any),
}
