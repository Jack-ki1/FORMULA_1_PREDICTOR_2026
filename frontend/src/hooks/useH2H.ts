import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchDrivers, compareDrivers } from '../api/h2h'
export const useDrivers = () => useQuery({ queryKey:['drivers'], queryFn: fetchDrivers })
export const useH2HCompare = () => useMutation({ mutationFn: ({a,b}:{a:string;b:string})=> compareDrivers(a,b) })
