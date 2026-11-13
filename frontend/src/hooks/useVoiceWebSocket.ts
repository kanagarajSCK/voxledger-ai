import { useState, useRef, useCallback } from 'react'

export type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

export interface UseVoiceWebSocketOptions {
  endpoint?: string
  onMessage?: (message: WebSocketMessage) => void
}

export function useVoiceWebSocket(options: UseVoiceWebSocketOptions = {}) {
  const { endpoint = '/api/v1/ws/voice', onMessage } = options

  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const pingTimestampRef = useRef<number | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      setStatus('connecting')
      const wsUrl = `${WS_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`
      const socket = new WebSocket(wsUrl)
      wsRef.current = socket

      socket.onopen = () => {
        setStatus('connected')
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(data)
          onMessage?.(data)

          if (data.type === 'pong' && pingTimestampRef.current) {
            const diff = performance.now() - pingTimestampRef.current
            setLatencyMs(Math.round(diff))
            pingTimestampRef.current = null
          }
        } catch {
          // Non-JSON frame
        }
      }

      socket.onerror = () => {
        setStatus('error')
      }

      socket.onclose = () => {
        setStatus('disconnected')
        wsRef.current = null
      }
    } catch {
      setStatus('error')
    }
  }, [endpoint, onMessage])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setStatus('disconnected')
    }
  }, [])

  const sendMessage = useCallback((msg: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendBinary = useCallback((data: ArrayBuffer | Uint8Array) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  const ping = useCallback(() => {
    pingTimestampRef.current = performance.now()
    sendMessage({ type: 'ping' })
  }, [sendMessage])

  return {
    status,
    lastMessage,
    latencyMs,
    connect,
    disconnect,
    sendMessage,
    sendBinary,
    ping,
  }
}
