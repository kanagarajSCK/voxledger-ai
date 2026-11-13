export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  app_name: string
  version: string
  environment: string
  database_connected: boolean
  database_latency_ms: number | null
  api_version: string
  websocket_endpoint: string
}
