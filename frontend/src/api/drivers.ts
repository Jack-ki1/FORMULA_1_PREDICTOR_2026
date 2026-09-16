import { api } from './client'
import type { Driver } from '../types'
export const fetchDrivers = () => api.get<{drivers: Driver[]}>('/api/v1/drivers').then(r => r.drivers)
export const fetchDriver = (code: string) => api.get<Driver>(`/api/v1/drivers/${code}`)
