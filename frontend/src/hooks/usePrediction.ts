import { useMutation } from '@tanstack/react-query'
import { predictSession, PredictPayload } from '../api/predictions'
export const usePrediction = () => useMutation({ mutationFn: (p: PredictPayload)=> predictSession(p) })
