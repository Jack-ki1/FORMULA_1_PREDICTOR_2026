import { api } from './client';
export type ScenarioPayload = { race_id: string; session_type?: string; weather?: string; grid_positions?: Record<string,number>; scenario: Record<string,any>; simulation_count?: number; random_seed?: number };
export type ScenarioResult = { baseline:any; scenario:any; diff: Record<string,number>; scenario_params:any; explanation:string };
export const scenarioApi = {
  run: (p: ScenarioPayload) => api.post<ScenarioResult>('/api/v1/predictions/scenario', p),
  simulate: (p: ScenarioPayload) => api.post<ScenarioResult>('/api/v1/predictions/simulate', p),
};
