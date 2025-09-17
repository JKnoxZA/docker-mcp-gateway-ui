import { renderHook, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

import { useWebSocket } from '@/hooks/useWebSocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState: number = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null

  constructor(url: string) {
    this.url = url
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason, wasClean: true }))
    }
  }

  // Test helper methods
  simulateMessage(data: any) {
    if (this.onmessage) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data)
      this.onmessage(new MessageEvent('message', { data: messageData }))
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }

  simulateClose(wasClean = true, code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason, wasClean }))
    }
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const TEST_URL = 'ws://localhost:8000/test'

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useWebSocket(null))

    expect(result.current.isConnected).toBe(false)
    expect(result.current.isConnecting).toBe(false)
    expect(result.current.error).toBe(null)
    expect(result.current.connectionStatus).toBe('disconnected')
    expect(result.current.lastMessage).toBe(null)
  })

  it('connects automatically when autoConnect is true', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: true }))

    expect(result.current.isConnecting).toBe(true)
    expect(result.current.connectionStatus).toBe('connecting')

    // Fast-forward timers to simulate connection
    await act(async () => {
      vi.runAllTimers()
    })

    expect(result.current.isConnected).toBe(true)
    expect(result.current.isConnecting).toBe(false)
    expect(result.current.connectionStatus).toBe('connected')
  })

  it('does not connect automatically when autoConnect is false', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: false }))

    expect(result.current.isConnected).toBe(false)
    expect(result.current.isConnecting).toBe(false)
    expect(result.current.connectionStatus).toBe('disconnected')
  })

  it('connects manually when connect() is called', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: false }))

    act(() => {
      result.current.connect()
    })

    expect(result.current.isConnecting).toBe(true)
    expect(result.current.connectionStatus).toBe('connecting')

    // Fast-forward timers to simulate connection
    await act(async () => {
      vi.runAllTimers()
    })

    expect(result.current.isConnected).toBe(true)
    expect(result.current.connectionStatus).toBe('connected')
  })

  it('handles messages correctly', async () => {
    const onMessage = vi.fn()
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, onMessage })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    // Simulate receiving a message
    const mockMessage = { type: 'test', data: 'hello world' }
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || {
      simulateMessage: vi.fn()
    }

    act(() => {
      if (mockWs.simulateMessage) {
        mockWs.simulateMessage(mockMessage)
      }
    })

    expect(onMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'test',
        data: 'hello world',
      })
    )
    expect(result.current.lastMessage).toEqual(
      expect.objectContaining({
        type: 'test',
        data: 'hello world',
      })
    )
  })

  it('handles plain text messages', async () => {
    const onMessage = vi.fn()
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, onMessage })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    // Simulate receiving a plain text message
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || {
      simulateMessage: vi.fn()
    }

    act(() => {
      if (mockWs.simulateMessage) {
        mockWs.simulateMessage('plain text message')
      }
    })

    expect(onMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'message',
        data: 'plain text message',
      })
    )
  })

  it('sends messages when connected', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: true }))

    await act(async () => {
      vi.runAllTimers()
    })

    const mockSend = vi.fn()
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || { send: mockSend }
    if (!mockWs.send) {
      mockWs.send = mockSend
    }

    act(() => {
      result.current.sendMessage({ type: 'test', data: 'hello' })
    })

    expect(mockSend).toHaveBeenCalledWith('{"type":"test","data":"hello"}')
  })

  it('handles send errors when not connected', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: false }))

    act(() => {
      result.current.sendMessage({ type: 'test', data: 'hello' })
    })

    expect(result.current.error).toBe('Cannot send message: not connected')
  })

  it('disconnects properly', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL, { autoConnect: true }))

    await act(async () => {
      vi.runAllTimers()
    })

    expect(result.current.isConnected).toBe(true)

    act(() => {
      result.current.disconnect()
    })

    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus).toBe('disconnected')
  })

  it('handles connection errors', async () => {
    const onError = vi.fn()
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, onError })
    )

    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || {
      simulateError: vi.fn()
    }

    act(() => {
      if (mockWs.simulateError) {
        mockWs.simulateError()
      }
    })

    expect(result.current.connectionStatus).toBe('error')
    expect(result.current.error).toBeTruthy()
    expect(onError).toHaveBeenCalled()
  })

  it('handles unexpected disconnection and attempts reconnect', async () => {
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, reconnectAttempts: 2 })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    expect(result.current.isConnected).toBe(true)

    // Simulate unexpected disconnection
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || {
      simulateClose: vi.fn()
    }

    act(() => {
      if (mockWs.simulateClose) {
        mockWs.simulateClose(false, 1006, 'Connection lost') // wasClean = false
      }
    })

    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus).toBe('error')

    // Should attempt reconnection
    await act(async () => {
      vi.runAllTimers()
    })
  })

  it('handles clean disconnection without reconnect', async () => {
    const onClose = vi.fn()
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, onClose })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    expect(result.current.isConnected).toBe(true)

    // Simulate clean disconnection
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || {
      simulateClose: vi.fn()
    }

    act(() => {
      if (mockWs.simulateClose) {
        mockWs.simulateClose(true, 1000, 'Normal closure') // wasClean = true
      }
    })

    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus).toBe('disconnected')
    expect(onClose).toHaveBeenCalled()
  })

  it('respects reconnection attempt limits', async () => {
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true, reconnectAttempts: 1 })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    // Simulate multiple unexpected disconnections
    for (let i = 0; i < 3; i++) {
      const mockWs = (global.WebSocket as any).mock?.instances?.[i] || {
        simulateClose: vi.fn()
      }

      act(() => {
        if (mockWs.simulateClose) {
          mockWs.simulateClose(false, 1006, 'Connection lost')
        }
      })

      await act(async () => {
        vi.runAllTimers()
      })
    }

    // Should not reconnect after exceeding attempts
    expect(result.current.isConnected).toBe(false)
  })

  it('cleans up on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket(TEST_URL, { autoConnect: true })
    )

    await act(async () => {
      vi.runAllTimers()
    })

    const mockClose = vi.fn()
    const mockWs = (global.WebSocket as any).mock?.instances?.[0] || { close: mockClose }
    if (!mockWs.close) {
      mockWs.close = mockClose
    }

    unmount()

    expect(mockClose).toHaveBeenCalled()
  })

  it('handles null URL gracefully', () => {
    const { result } = renderHook(() => useWebSocket(null))

    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus).toBe('disconnected')

    // Should not crash when trying to connect with null URL
    act(() => {
      result.current.connect()
    })

    expect(result.current.isConnected).toBe(false)
  })
})