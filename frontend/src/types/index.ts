export type Race = {
  id: string; round: number; name: string; circuit: string; location: string; country: string; flag: string;
  date: string; laps: number; length_km: number; drs_zones: number; overtaking: string;
  base_rain: number; base_sc: number; base_temp: number; status: 'completed'|'upcoming'|'cancelled'; sprint: boolean;
}
export type Driver = { code: string; name: string; team: string; team_name: string; team_color: string; number: number; strength: number; wet_skill: number; consistency: number; reliability: number; nationality?: string; }
export type PredictionEntry = { driver_code: string; probability: number; percentage: number; }
export type PredictionSummary = { target_id: string; target_label: string; predictions: PredictionEntry[]; confidence: number; source: string; top_prediction?: [string, number]; target_info?: any; }
export type PredictionResult = {
  race_id: string; session_type: string; sub_session?: string; weather: string;
  grid_positions: Record<string,number>; predictions: Record<string, PredictionSummary>;
  winner_probabilities: Record<string,number>; confidence_intervals: Record<string,any>;
  model_drift_score: number; timestamp: string; status: string;
}
export type StandingDriver = { position: number; driver_code: string; driver_name: string; team: string; points: number; wins: number; }
export type Team = { id: string; name: string; color: string; color_hex?: string; power?: number; drivers?: string[]; }
