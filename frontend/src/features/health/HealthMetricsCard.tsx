import React from 'react'
import { useHealthCheck } from '../../hooks/useHealthCheck'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ErrorAlert } from '../../components/ui/ErrorAlert'
import { Database, Server, Clock, GitBranch } from 'lucide-react'

export const HealthMetricsCard: React.FC = () => {
  const { data: health, isLoading, isError, error, refetch } = useHealthCheck()

  return (
    <Card className="border-slate-200 shadow-sm" id="health-section">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-slate-900">
            <Server className="w-5 h-5 text-emerald-600" />
            Backend System Health
          </CardTitle>
          <CardDescription>
            Live connectivity metrics and database status from FastAPI
          </CardDescription>
        </div>
        {health && (
          <Badge variant={health.status === 'healthy' ? 'success' : 'warning'}>
            {health.status.toUpperCase()}
          </Badge>
        )}
      </CardHeader>

      <CardContent>
        {isLoading && (
          <LoadingSpinner size="md" label="Querying backend health endpoint..." />
        )}

        {isError && (
          <ErrorAlert
            title="Backend Service Unreachable"
            message={error?.message || 'Unable to establish connection with the FastAPI backend at http://localhost:8000.'}
            onRetry={() => refetch()}
          />
        )}

        {health && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Database Status */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-3">
              <div className="p-2 rounded-md bg-emerald-100/70 text-emerald-700">
                <Database className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Database (SQLite/aiosqlite)</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-sm font-semibold text-slate-800">
                    {health.database_connected ? 'Connected' : 'Disconnected'}
                  </span>
                  {health.database_latency_ms !== null && (
                    <span className="text-xs text-slate-400 font-mono">
                      ({health.database_latency_ms} ms)
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* API Version & Environment */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-3">
              <div className="p-2 rounded-md bg-blue-100/70 text-blue-700">
                <GitBranch className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">API Version & Env</p>
                <p className="text-sm font-semibold text-slate-800 mt-0.5">
                  {health.version} • {health.environment}
                </p>
              </div>
            </div>

            {/* Active API Prefix */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-3 sm:col-span-2 lg:col-span-1">
              <div className="p-2 rounded-md bg-purple-100/70 text-purple-700">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Server Timestamp (UTC)</p>
                <p className="text-xs font-mono text-slate-700 mt-0.5 truncate">
                  {new Date(health.timestamp).toLocaleTimeString()} ({new Date(health.timestamp).toLocaleDateString()})
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
