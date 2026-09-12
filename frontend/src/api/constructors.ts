import { api } from './client'
export const fetchTeams = () => api.get<any[]>('/api/v1/constructors/teams')
export const fetchPowerRankings = () => api.get<any[]>('/api/v1/constructors/power-rankings')
