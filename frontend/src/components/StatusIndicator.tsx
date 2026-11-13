import React from 'react'
import { useHealthCheck } from '../hooks/useHealthCheck'
import { Badge } from './ui/Badge'
import { Activity, AlertTriangle, XCircle } from 'lucide-react'

export const StatusIndicator: React.FC = () => {
  const { data: health, isLoading, isError } = useHealthCheck()

  if (isLoading) {
    return (
      <Badge variant="neutral" className="animate-pulse">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
        Connecting...
      </Badge>
    )
  }

  if (isError || !health) {
    return (
      <Badge variant="danger" title="Backend API unreachable">
        <XCircle className="w-3.5 h-3.5 text-red-600" />
        Backend Offline
      </Badge>
    )
  }

  if (!health.database_connected) {
    return (
      <Badge variant="warning" title="Database disconnected">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
        DB Degraded
      </Badge>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant="success" className="gap-1.5">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span className="font-semibold">Backend Live</span>
      </Badge>

      {health.database_latency_ms !== null && (
        <span className="hidden sm:inline-flex items-center text-xs text-slate-500 font-mono">
          <Activity className="w-3 h-3 mr-1 text-slate-400" />
          {health.database_latency_ms}ms
        </span>
      )}
    </div>
  )
}
