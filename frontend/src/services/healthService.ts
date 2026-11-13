import { apiClient } from '../lib/api'
import { HealthResponse } from '../types/health'

export async function fetchHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/api/health')
}

export async function fetchVersionedHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/api/v1/health')
}
