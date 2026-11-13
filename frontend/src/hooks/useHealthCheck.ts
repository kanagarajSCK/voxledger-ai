import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../services/healthService'
import { HealthResponse } from '../types/health'

export function useHealthCheck(refetchInterval = 10000) {
  return useQuery<HealthResponse, Error>({
    queryKey: ['system-health'],
    queryFn: fetchHealth,
    refetchInterval,
    retry: 2,
    staleTime: 5000,
  })
}
