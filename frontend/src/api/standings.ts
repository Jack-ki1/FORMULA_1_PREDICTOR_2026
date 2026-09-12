import { api } from './client'
export const fetchDriverStandings = () => api.get<any>('/api/v1/standings/drivers')
export const fetchConstructorStandings = () => api.get<any>('/api/v1/standings/constructors')
