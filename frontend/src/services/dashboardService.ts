import { apiClient } from '../lib/api'
import { DashboardSummary } from '../types/dashboard'

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return apiClient<DashboardSummary>('/api/v1/dashboard/summary')
}
