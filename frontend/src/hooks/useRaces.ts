import { useQuery } from '@tanstack/react-query'
import { fetchRaces } from '../api/races'
export const useRaces = () => useQuery({ queryKey: ['races'], queryFn: fetchRaces, staleTime: 60_000 })
