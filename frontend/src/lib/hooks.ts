import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api, type SimParams } from "./api";

const M5 = 5 * 60_000;
export const useMeta = () => useQuery({ queryKey: ["meta"], queryFn: api.meta, staleTime: M5 });
export const useRaces = () => useQuery({ queryKey: ["races"], queryFn: api.races, staleTime: M5, refetchInterval: 10 * 60_000 });
export const useNextRace = () => useQuery({ queryKey: ["next"], queryFn: api.nextRace, staleTime: 60_000 });
export const usePrediction = (p: SimParams) => useQuery({ queryKey: ["pred", p], queryFn: () => api.predict(p), staleTime: M5, placeholderData: keepPreviousData });
export const useStandings = () => useQuery({ queryKey: ["standings"], queryFn: api.standings, staleTime: M5 });
export const useDrivers = () => useQuery({ queryKey: ["drivers"], queryFn: api.drivers, staleTime: 3_600_000 });
export const useH2H = (a?: string, b?: string, race?: string | null) =>
  useQuery({ queryKey: ["h2h", a, b, race], queryFn: () => api.h2h(a!, b!, race ?? null), enabled: !!a && !!b && a !== b, staleTime: M5, placeholderData: keepPreviousData });
export const useRecent = () => useQuery({ queryKey: ["recent"], queryFn: api.recent, staleTime: M5 });
export const useFantasy = (race: string | null) => useQuery({ queryKey: ["fantasy", race], queryFn: () => api.fantasy(race), staleTime: M5 });
export const useGridOptions = (race: string | null | undefined) => useQuery({ queryKey: ["grid", race], queryFn: () => api.grid(race!), enabled: !!race, staleTime: 60_000 });
export const useServerConfig = () => useQuery({ queryKey: ["config"], queryFn: api.config, staleTime: 30_000 });
export const useSearch = (q: string) => useQuery({ queryKey: ["search", q], queryFn: () => api.search(q), enabled: q.length > 0, staleTime: M5 });
