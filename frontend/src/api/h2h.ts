import { api } from './client'
export const fetchDrivers = () => api.get<any[]>('/api/v1/h2h/drivers')
export const compareDrivers = (driver_a:string, driver_b:string) => api.post<any>('/api/v1/h2h/compare', { driver_a, driver_b })
