import { api } from './client'

export const settingsApi = {
  get: () => api.get<{ settings: Record<string, any>; overrides: Record<string, any>; timestamp: number; note: string }>('/api/v1/settings'),
  patch: (body: Record<string, any>, adminToken?: string) =>
    api.post<{ applied: Record<string, any>; rejected_sensitive: string[]; settings: Record<string, any> }>(
      '/api/v1/settings', body, adminToken ? { headers: { 'X-Admin-Token': adminToken } } : undefined,
    ),
}
