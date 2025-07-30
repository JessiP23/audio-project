import { useState, useEffect, useRef, useCallback } from 'react'
import { useAudioStore } from '@/store/audioStore'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

export const useWebSocket = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const audioStore = useAudioStore()

  const connect = useCallback((sessionId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }

    setSessionId(sessionId)
    setError(null)

    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/audio/${sessionId}`)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        audioStore.setConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        audioStore.setConnected(false)
        console.log('WebSocket disconnected:', event.code, event.reason)
        
        // Attempt to reconnect after 3 seconds
        if (event.code !== 1000) { // Not a normal closure
          reconnectTimeoutRef.current = setTimeout(() => {
            if (sessionId) {
              connect(sessionId)
            }
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        setError('WebSocket connection error')
        console.error('WebSocket error:', error)
      }
    } catch (err) {
      setError('Failed to create WebSocket connection')
      console.error('Failed to create WebSocket:', err)
    }
  }, [audioStore])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected')
      wsRef.current = null
    }

    setIsConnected(false)
    audioStore.setConnected(false)
    setSessionId(null)
    setError(null)
  }, [audioStore])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'buffer_status':
        audioStore.setBufferStatus(message.status)
        break
        
      case 'processed_audio':
        // Handle processed audio data
        console.log('Received processed audio:', message.samples?.length, 'samples')
        break
        
      case 'effect_applied':
        audioStore.addProcessingHistory({
          id: Date.now().toString(),
          effect: message.effect,
          parameters: {},
          processed_at: new Date().toISOString(),
          samples_processed: message.processed_samples || 0,
          processing_time_ms: 0,
        })
        break
        
      case 'error':
        setError(message.error || 'Unknown error')
        break
        
      default:
        console.log('Unknown message type:', message.type)
    }
  }, [audioStore])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    sessionId,
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage,
  }
} 