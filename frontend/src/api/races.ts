import { api } from './client'
import type { Race } from '../types'
export const fetchRaces = () => api.get<Race[]>('/api/v1/races')
export const fetchRaceResult = (raceId:string) => api.get<any>(`/api/v1/race-result/${raceId}`).catch(()=> api.get<any>(`/dashboard/api/race-result/${raceId}`))
