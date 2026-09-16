import { useQuery } from '@tanstack/react-query'
import { fetchDrivers } from '../api/drivers'
export const useDrivers = () => useQuery({ queryKey: ['drivers'], queryFn: fetchDrivers, staleTime: 60_000 })
