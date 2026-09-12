import { api } from './client'
export const fetchAccuracy = () => api.get<any>('/api/v1/analytics/accuracy')
export const fetchWeights = () => api.get<any>('/api/v1/analytics/feature-weights')
export const updateWeights = (weights:any) => api.post<any>('/api/v1/analytics/feature-weights', weights)
export const fetchTargets = () => api.get<any[]>('/api/v1/analytics/targets')
