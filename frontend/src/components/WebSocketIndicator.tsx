import React from 'react'
import { useVoiceWebSocket } from '../hooks/useVoiceWebSocket'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { Radio, Send } from 'lucide-react'

export const WebSocketIndicator: React.FC = () => {
  const { status, latencyMs, connect, disconnect, ping } = useVoiceWebSocket()

  const statusVariant = {
    connected: 'success',
    connecting: 'warning',
    disconnected: 'neutral',
    error: 'danger',
  } as const

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
      <div className="flex items-center gap-2.5">
        <Radio className={`w-4 h-4 ${status === 'connected' ? 'text-emerald-600 animate-pulse' : 'text-slate-400'}`} />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-800">Voice Stream Gateway</span>
            <Badge variant={statusVariant[status]}>
              {status.toUpperCase()}
            </Badge>
          </div>
          <p className="text-[11px] text-slate-500 font-mono mt-0.5">
            Endpoint: /api/v1/ws/voice {latencyMs !== null && `• Ping: ${latencyMs}ms`}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto">
        {status === 'disconnected' || status === 'error' ? (
          <Button size="sm" variant="outline" onClick={connect} className="text-xs h-8">
            Connect Socket
          </Button>
        ) : (
          <>
            <Button size="sm" variant="outline" onClick={ping} className="text-xs h-8 gap-1">
              <Send className="w-3 h-3" />
              Ping
            </Button>
            <Button size="sm" variant="ghost" onClick={disconnect} className="text-xs h-8 text-red-600 hover:text-red-700">
              Disconnect
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
