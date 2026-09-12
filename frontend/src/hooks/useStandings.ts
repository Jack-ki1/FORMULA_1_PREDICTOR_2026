import { useQuery } from '@tanstack/react-query'
import { fetchDriverStandings, fetchConstructorStandings } from '../api/standings'
export const useDriverStandings = () => useQuery({ queryKey:['standings','drivers',2026], queryFn: fetchDriverStandings })
export const useConstructorStandings = () => useQuery({ queryKey:['standings','constructors',2026], queryFn: fetchConstructorStandings })
