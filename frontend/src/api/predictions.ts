import { api } from './client'
import type { PredictionResult } from '../types'
export type PredictPayload = {
  race_id: string; session_type: string; sub_session?: string; weather?: string;
  grid_positions?: Record<string,number>; feature_weights?: Record<string,number>;
  simulation_count?: number; ai_mode?: string; ai_model?: string; ai_api_key?: string; ai_weight?: number; ai_temperature?: number;
}
export const predictSession = (payload: PredictPayload) => api.post<PredictionResult>('/api/v1/predictions', payload)
export const aiChat = (payload:{message:string; model:string; api_key:string; temperature:number}) => api.post<{response:string; provider:string; model:string}>('/api/v1/ai/chat', payload)
