import { useState, useEffect, useRef, useCallback } from 'react'

export type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

export function useVoiceWebSocket(endpoint = '/api/v1/ws/voice') {
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

          if (data.type === 'pong' && pingTimestampRef.current) {
            const diff = performance.now() - pingTimestampRef.current
            setLatencyMs(Math.round(diff))
            pingTimestampRef.current = null
          }
        } catch {
          // Non-JSON message
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
  }, [endpoint])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setStatus('disconnected')
    }
  }, [])

  const sendMessage = useCallback((msg: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (msg.type === 'ping') {
        pingTimestampRef.current = performance.now()
      }
      wsRef.current.send(JSON.stringify(msg))
      return true
    }
    return false
  }, [])

  const ping = useCallback(() => {
    return sendMessage({ type: 'ping' })
  }, [sendMessage])

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return {
    status,
    lastMessage,
    latencyMs,
    connect,
    disconnect,
    sendMessage,
    ping,
  }
}
