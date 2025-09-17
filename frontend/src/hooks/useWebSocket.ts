import { useState, useEffect, useRef, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface UseWebSocketOptions {
  onOpen?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onClose?: (event: CloseEvent) => void
  reconnectAttempts?: number
  reconnectInterval?: number
  autoConnect?: boolean
}

export interface UseWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
  lastMessage: WebSocketMessage | null
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
}

export const useWebSocket = (
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    onOpen,
    onMessage,
    onError,
    onClose,
    reconnectAttempts = 3,
    reconnectInterval = 3000,
    autoConnect = true,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')

  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectCountRef = useRef(0)
  const isMountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!url || ws.current?.readyState === WebSocket.CONNECTING || ws.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setIsConnecting(true)
      setConnectionStatus('connecting')
      setError(null)

      ws.current = new WebSocket(url)

      ws.current.onopen = (event) => {
        if (!isMountedRef.current) return

        setIsConnected(true)
        setIsConnecting(false)
        setConnectionStatus('connected')
        setError(null)
        reconnectCountRef.current = 0

        onOpen?.(event)
        console.log('WebSocket connected:', url)
      }

      ws.current.onmessage = (event) => {
        if (!isMountedRef.current) return

        try {
          let messageData
          try {
            messageData = JSON.parse(event.data)
          } catch {
            // If not JSON, create a simple message structure
            messageData = {
              type: 'message',
              data: event.data,
              timestamp: new Date().toISOString(),
            }
          }

          const message: WebSocketMessage = {
            type: messageData.type || 'message',
            data: messageData.data || messageData,
            timestamp: messageData.timestamp || new Date().toISOString(),
          }

          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Error processing WebSocket message:', error)
        }
      }

      ws.current.onerror = (event) => {
        if (!isMountedRef.current) return

        const errorMessage = 'WebSocket connection error'
        setError(errorMessage)
        setConnectionStatus('error')
        setIsConnecting(false)

        onError?.(event)
        console.error('WebSocket error:', event)
      }

      ws.current.onclose = (event) => {
        if (!isMountedRef.current) return

        setIsConnected(false)
        setIsConnecting(false)

        if (event.wasClean) {
          setConnectionStatus('disconnected')
        } else {
          setConnectionStatus('error')
          setError('Connection lost unexpectedly')
        }

        onClose?.(event)
        console.log('WebSocket disconnected:', event.code, event.reason)

        // Attempt to reconnect if not a clean close and we haven't exceeded max attempts
        if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1
          console.log(`Attempting to reconnect (${reconnectCountRef.current}/${reconnectAttempts})...`)

          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connect()
            }
          }, reconnectInterval)
        }
      }
    } catch (error) {
      if (!isMountedRef.current) return

      setError('Failed to create WebSocket connection')
      setConnectionStatus('error')
      setIsConnecting(false)
      console.error('WebSocket creation error:', error)
    }
  }, [url, onOpen, onMessage, onError, onClose, reconnectAttempts, reconnectInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (ws.current) {
      ws.current.close(1000, 'Intentional disconnect')
      ws.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
    setConnectionStatus('disconnected')
    setError(null)
    reconnectCountRef.current = 0
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        const messageString = typeof message === 'string' ? message : JSON.stringify(message)
        ws.current.send(messageString)
      } catch (error) {
        console.error('Error sending WebSocket message:', error)
        setError('Failed to send message')
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message.')
      setError('Cannot send message: not connected')
    }
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && url) {
      connect()
    }

    return () => {
      isMountedRef.current = false
      disconnect()
    }
  }, [url, autoConnect, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  return {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    sendMessage,
    lastMessage,
    connectionStatus,
  }
}