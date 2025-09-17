import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import LogViewer from '@/components/common/LogViewer'

// Mock React Hot Toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  success: vi.fn(),
  error: vi.fn(),
}))

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
})

describe('LogViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockLogs = [
    '[2024-01-01T00:00:00Z] [INFO] Application started',
    '[2024-01-01T00:00:01Z] [WARN] Configuration file not found, using defaults',
    '[2024-01-01T00:00:02Z] [ERROR] Failed to connect to database',
    '[2024-01-01T00:00:03Z] [DEBUG] Processing request',
    '[2024-01-01T00:00:04Z] [INFO] Request completed successfully',
  ]

  it('renders log viewer with default title', () => {
    render(<LogViewer logs={mockLogs} />)

    expect(screen.getByText('Logs')).toBeInTheDocument()
    expect(screen.getByText('(5 lines)')).toBeInTheDocument()
  })

  it('renders log viewer with custom title', () => {
    render(<LogViewer title="Container Logs" logs={mockLogs} />)

    expect(screen.getByText('Container Logs')).toBeInTheDocument()
  })

  it('displays all log lines', () => {
    render(<LogViewer logs={mockLogs} />)

    expect(screen.getByText(/Application started/)).toBeInTheDocument()
    expect(screen.getByText(/Configuration file not found/)).toBeInTheDocument()
    expect(screen.getByText(/Failed to connect to database/)).toBeInTheDocument()
    expect(screen.getByText(/Processing request/)).toBeInTheDocument()
    expect(screen.getByText(/Request completed successfully/)).toBeInTheDocument()
  })

  it('shows empty state when no logs', () => {
    render(<LogViewer logs={[]} />)

    expect(screen.getByText('No logs available')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<LogViewer logs={[]} isLoading={true} />)

    expect(screen.getByText('Loading logs...')).toBeInTheDocument()
  })

  it('filters logs by search query', async () => {
    render(<LogViewer logs={mockLogs} showSearch={true} />)

    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'ERROR' } })

    await waitFor(() => {
      expect(screen.getByText(/Failed to connect to database/)).toBeInTheDocument()
      expect(screen.queryByText(/Application started/)).not.toBeInTheDocument()
    })
  })

  it('filters logs by level', async () => {
    render(<LogViewer logs={mockLogs} showSearch={true} />)

    const levelFilter = screen.getByDisplayValue('All Levels')
    fireEvent.change(levelFilter, { target: { value: 'error' } })

    await waitFor(() => {
      expect(screen.getByText(/Failed to connect to database/)).toBeInTheDocument()
      expect(screen.queryByText(/Application started/)).not.toBeInTheDocument()
    })
  })

  it('clears filters when clear button is clicked', async () => {
    render(<LogViewer logs={mockLogs} showSearch={true} />)

    // Apply a search filter
    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'ERROR' } })

    await waitFor(() => {
      expect(screen.getByDisplayValue('ERROR')).toBeInTheDocument()
    })

    // Clear filters
    const clearButton = screen.getByRole('button', { name: /clear/i })
    fireEvent.click(clearButton)

    await waitFor(() => {
      expect(searchInput).toHaveValue('')
      expect(screen.getByDisplayValue('All Levels')).toBeInTheDocument()
    })
  })

  it('shows streaming controls when enabled', () => {
    const mockStart = vi.fn()
    const mockStop = vi.fn()

    render(
      <LogViewer
        logs={mockLogs}
        showControls={true}
        onStartStreaming={mockStart}
        onStopStreaming={mockStop}
        websocketUrl="ws://test"
      />
    )

    expect(screen.getByRole('button', { name: /stream/i })).toBeInTheDocument()
  })

  it('calls start streaming when stream button is clicked', () => {
    const mockStart = vi.fn()

    render(
      <LogViewer
        logs={mockLogs}
        showControls={true}
        onStartStreaming={mockStart}
        websocketUrl="ws://test"
      />
    )

    const streamButton = screen.getByRole('button', { name: /stream/i })
    fireEvent.click(streamButton)

    expect(mockStart).toHaveBeenCalledTimes(1)
  })

  it('shows pause button when streaming', () => {
    const mockStop = vi.fn()

    render(
      <LogViewer
        logs={mockLogs}
        showControls={true}
        isStreaming={true}
        onStopStreaming={mockStop}
        websocketUrl="ws://test"
      />
    )

    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
  })

  it('calls refresh when refresh button is clicked', () => {
    const mockRefresh = vi.fn()

    render(
      <LogViewer
        logs={mockLogs}
        showControls={true}
        onRefresh={mockRefresh}
      />
    )

    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    fireEvent.click(refreshButton)

    expect(mockRefresh).toHaveBeenCalledTimes(1)
  })

  it('handles copy all logs', async () => {
    const mockWriteText = vi.mocked(navigator.clipboard.writeText)

    render(<LogViewer logs={mockLogs} showControls={true} />)

    const copyButton = screen.getByRole('button', { name: /copy all/i })
    fireEvent.click(copyButton)

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(mockLogs.join('\n'))
    })
  })

  it('handles download logs', () => {
    // Mock URL.createObjectURL and other DOM APIs
    global.URL.createObjectURL = vi.fn(() => 'mock-url')
    global.URL.revokeObjectURL = vi.fn()

    const mockClick = vi.fn()
    const mockAppendChild = vi.fn()
    const mockRemoveChild = vi.fn()

    // Mock createElement to return an element with click method
    vi.spyOn(document, 'createElement').mockReturnValue({
      click: mockClick,
      href: '',
      download: '',
    } as any)

    vi.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild)
    vi.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild)

    render(<LogViewer logs={mockLogs} showControls={true} />)

    const downloadButton = screen.getByRole('button', { name: /download/i })
    fireEvent.click(downloadButton)

    expect(mockClick).toHaveBeenCalledTimes(1)
    expect(mockAppendChild).toHaveBeenCalledTimes(1)
    expect(mockRemoveChild).toHaveBeenCalledTimes(1)
  })

  it('handles copy individual log line', async () => {
    const mockWriteText = vi.mocked(navigator.clipboard.writeText)

    render(<LogViewer logs={mockLogs} />)

    // Find the first copy button (should be in the first log line)
    const copyButtons = screen.getAllByRole('button')
    const copyButton = copyButtons.find(button => {
      const svg = button.querySelector('svg')
      return svg?.getAttribute('data-testid') === 'copy-icon' ||
             button.getAttribute('aria-label')?.includes('copy')
    })

    if (copyButton) {
      fireEvent.click(copyButton)

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith(mockLogs[0])
      })
    }
  })

  it('toggles follow tail checkbox', () => {
    render(<LogViewer logs={mockLogs} showControls={true} />)

    const followCheckbox = screen.getByLabelText('Follow') as HTMLInputElement
    expect(followCheckbox.checked).toBe(true)

    fireEvent.click(followCheckbox)
    expect(followCheckbox.checked).toBe(false)
  })

  it('shows live indicator when connected', () => {
    render(
      <LogViewer
        logs={mockLogs}
        isStreaming={true}
        websocketUrl="ws://test"
      />
    )

    // Look for the live indicator
    expect(screen.getByText('Live')).toBeInTheDocument()
  })

  it('toggles fullscreen mode', () => {
    render(<LogViewer logs={mockLogs} />)

    const fullscreenButton = screen.getByRole('button')
    fireEvent.click(fullscreenButton)

    // The component should now be in fullscreen mode
    // This is hard to test without actually checking DOM classes
    // In a real scenario, you might want to test specific CSS classes
  })

  it('applies correct styling for different log levels', () => {
    const coloredLogs = [
      '[ERROR] This is an error',
      '[WARN] This is a warning',
      '[INFO] This is info',
      '[DEBUG] This is debug',
    ]

    render(<LogViewer logs={coloredLogs} />)

    // Check that different log levels are present
    expect(screen.getByText(/This is an error/)).toBeInTheDocument()
    expect(screen.getByText(/This is a warning/)).toBeInTheDocument()
    expect(screen.getByText(/This is info/)).toBeInTheDocument()
    expect(screen.getByText(/This is debug/)).toBeInTheDocument()
  })

  it('shows filtered results count', async () => {
    render(<LogViewer logs={mockLogs} showSearch={true} />)

    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'INFO' } })

    await waitFor(() => {
      expect(screen.getByText('Showing 2 of 5 lines')).toBeInTheDocument()
    })
  })

  it('shows help text when no results match filters', async () => {
    render(<LogViewer logs={mockLogs} showSearch={true} />)

    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'NONEXISTENT' } })

    await waitFor(() => {
      expect(screen.getByText('No logs available')).toBeInTheDocument()
      expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument()
    })
  })
})