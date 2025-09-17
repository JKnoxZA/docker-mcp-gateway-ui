import React, { useState, useEffect, useRef } from 'react'
import {
  Play,
  Pause,
  Square,
  Download,
  RefreshCw,
  Search,
  FilterX,
  Copy,
  CheckCircle,
  Terminal,
  Maximize2,
  Minimize2,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { Button, Input } from '@/components/common'

export interface LogEntry {
  id: string
  timestamp: string
  level?: 'info' | 'warn' | 'error' | 'debug'
  message: string
  source?: string
}

interface LogViewerProps {
  title?: string
  logs?: string[]
  isStreaming?: boolean
  onStartStreaming?: () => void
  onStopStreaming?: () => void
  onRefresh?: () => void
  isLoading?: boolean
  className?: string
  maxHeight?: string
  showControls?: boolean
  showSearch?: boolean
  autoScroll?: boolean
  websocketUrl?: string
}

const LogViewer: React.FC<LogViewerProps> = ({
  title = 'Logs',
  logs = [],
  isStreaming = false,
  onStartStreaming,
  onStopStreaming,
  onRefresh,
  isLoading = false,
  className = '',
  maxHeight = 'max-h-96',
  showControls = true,
  showSearch = true,
  autoScroll = true,
  websocketUrl,
}) => {
  const [filteredLogs, setFilteredLogs] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [followTail, setFollowTail] = useState(autoScroll)
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const logContainerRef = useRef<HTMLDivElement>(null)
  const [copiedLines, setCopiedLines] = useState<Set<number>>(new Set())

  // Parse log entry to extract level and format
  const parseLogEntry = (log: string, index: number): LogEntry => {
    const timestamp = new Date().toISOString()
    let level: LogEntry['level'] = 'info'
    let message = log

    // Try to extract log level from common formats
    const levelMatches = log.match(/\[(error|warn|info|debug)\]/i) ||
                        log.match(/(error|warn|info|debug):/i) ||
                        log.match(/level=(error|warn|info|debug)/i)

    if (levelMatches) {
      level = levelMatches[1].toLowerCase() as LogEntry['level']
    }

    // Extract timestamp if present
    const timestampMatch = log.match(/(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)/)
    const extractedTimestamp = timestampMatch ? timestampMatch[1] : timestamp

    return {
      id: `log-${index}`,
      timestamp: extractedTimestamp,
      level,
      message,
      source: 'container',
    }
  }

  // WebSocket connection for real-time streaming
  useEffect(() => {
    if (websocketUrl && isStreaming) {
      const ws = new WebSocket(websocketUrl)

      ws.onopen = () => {
        setConnectionStatus('connected')
        setWsConnection(ws)
        console.log('WebSocket connected for log streaming')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'log' && data.message) {
            // Add new log to the logs array
            setFilteredLogs(prev => [...prev, data.message])
          }
        } catch (error) {
          // If not JSON, treat as plain log message
          setFilteredLogs(prev => [...prev, event.data])
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('disconnected')
        toast.error('WebSocket connection error')
      }

      ws.onclose = () => {
        setConnectionStatus('disconnected')
        setWsConnection(null)
        console.log('WebSocket disconnected')
      }

      return () => {
        ws.close()
      }
    }
  }, [websocketUrl, isStreaming])

  // Filter logs based on search and level
  useEffect(() => {
    let filtered = logs

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(log =>
        log.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Level filter
    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => {
        const entry = parseLogEntry(log, 0)
        return entry.level === levelFilter
      })
    }

    setFilteredLogs(filtered)
  }, [logs, searchQuery, levelFilter])

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (followTail && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [filteredLogs, followTail])

  // Get log level styling
  const getLogLevelStyle = (log: string) => {
    const entry = parseLogEntry(log, 0)
    switch (entry.level) {
      case 'error':
        return 'text-red-400'
      case 'warn':
        return 'text-yellow-400'
      case 'debug':
        return 'text-blue-400'
      default:
        return 'text-gray-100'
    }
  }

  // Copy log line to clipboard
  const copyLogLine = async (log: string, index: number) => {
    try {
      await navigator.clipboard.writeText(log)
      setCopiedLines(prev => new Set([...prev, index]))
      toast.success('Log line copied to clipboard')

      // Clear the copied state after 2 seconds
      setTimeout(() => {
        setCopiedLines(prev => {
          const newSet = new Set(prev)
          newSet.delete(index)
          return newSet
        })
      }, 2000)
    } catch (error) {
      toast.error('Failed to copy log line')
    }
  }

  // Copy all visible logs
  const copyAllLogs = async () => {
    try {
      await navigator.clipboard.writeText(filteredLogs.join('\n'))
      toast.success('All logs copied to clipboard')
    } catch (error) {
      toast.error('Failed to copy logs')
    }
  }

  // Download logs as file
  const downloadLogs = () => {
    const blob = new Blob([filteredLogs.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${new Date().toISOString().slice(0, 19)}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Logs downloaded')
  }

  // Clear search and filters
  const clearFilters = () => {
    setSearchQuery('')
    setLevelFilter('all')
  }

  const containerClasses = isFullscreen
    ? 'fixed inset-0 z-50 bg-gray-900 p-6'
    : `${className} bg-white border border-gray-300 rounded-lg`

  const logContainerClasses = isFullscreen
    ? 'h-full'
    : maxHeight

  return (
    <div className={containerClasses}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Terminal className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
          {connectionStatus === 'connected' && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600">Live</span>
            </div>
          )}
          {filteredLogs.length > 0 && (
            <span className="text-sm text-gray-500">({filteredLogs.length} lines)</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <Button
            onClick={() => setIsFullscreen(!isFullscreen)}
            variant="outline"
            size="sm"
            className="flex items-center space-x-1"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Controls */}
      {showControls && (
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mb-4">
          {/* Streaming Controls */}
          <div className="flex items-center space-x-2">
            {websocketUrl && (
              <>
                {!isStreaming ? (
                  <Button
                    onClick={onStartStreaming}
                    variant="outline"
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <Play className="w-4 h-4" />
                    <span>Stream</span>
                  </Button>
                ) : (
                  <Button
                    onClick={onStopStreaming}
                    variant="outline"
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <Pause className="w-4 h-4" />
                    <span>Pause</span>
                  </Button>
                )}
              </>
            )}

            <Button
              onClick={onRefresh}
              disabled={isLoading}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </Button>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={followTail}
                onChange={(e) => setFollowTail(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Follow</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Button
              onClick={copyAllLogs}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1"
            >
              <Copy className="w-4 h-4" />
              <span>Copy All</span>
            </Button>

            <Button
              onClick={downloadLogs}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </Button>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      {showSearch && (
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mb-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>

            {(searchQuery || levelFilter !== 'all') && (
              <Button
                onClick={clearFilters}
                variant="outline"
                size="sm"
                className="flex items-center space-x-1"
              >
                <FilterX className="w-4 h-4" />
                <span>Clear</span>
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Log Container */}
      <div
        ref={logContainerRef}
        className={`bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-y-auto ${logContainerClasses}`}
      >
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-5 h-5 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-400">Loading logs...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8">
            <Terminal className="w-8 h-8 text-gray-600 mx-auto mb-2" />
            <p className="text-gray-400">No logs available</p>
            {(searchQuery || levelFilter !== 'all') && (
              <p className="text-gray-500 text-xs mt-1">Try adjusting your filters</p>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={index}
                className="group flex items-start space-x-2 hover:bg-gray-800 px-2 py-1 rounded"
              >
                <span className="text-gray-500 text-xs leading-5 mt-0.5 w-12 flex-shrink-0">
                  {String(index + 1).padStart(3, '0')}
                </span>
                <div className="flex-1 min-w-0">
                  <pre className={`whitespace-pre-wrap break-words text-sm leading-5 ${getLogLevelStyle(log)}`}>
                    {log}
                  </pre>
                </div>
                <Button
                  onClick={() => copyLogLine(log, index)}
                  variant="ghost"
                  size="sm"
                  className="opacity-0 group-hover:opacity-100 p-1 h-auto text-gray-400 hover:text-gray-200"
                >
                  {copiedLines.has(index) ? (
                    <CheckCircle className="w-3 h-3 text-green-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {filteredLogs.length > 0 && (
        <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
          <div>
            {searchQuery && (
              <span>
                Showing {filteredLogs.length} of {logs.length} lines
                {levelFilter !== 'all' && ` (${levelFilter} level)`}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-4">
            {isStreaming && connectionStatus === 'connected' && (
              <span className="text-green-600">● Live streaming</span>
            )}
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default LogViewer