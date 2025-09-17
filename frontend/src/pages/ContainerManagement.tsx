import React, { useState, useEffect } from 'react'
import {
  Container,
  Play,
  Square,
  RotateCcw,
  Trash2,
  FileText,
  Search,
  Filter,
  RefreshCw,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Download,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { ContainerInfo } from '@/types'
import { dockerAPI } from '@/services/api'
import { Button, Input, StatusBadge, Modal, LogViewer } from '@/components/common'
import { useWebSocket } from '@/hooks/useWebSocket'

interface ContainerWithActions extends ContainerInfo {
  isLoading?: boolean
}

const ContainerManagement: React.FC = () => {
  const [containers, setContainers] = useState<ContainerWithActions[]>([])
  const [filteredContainers, setFilteredContainers] = useState<ContainerWithActions[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedContainer, setSelectedContainer] = useState<ContainerWithActions | null>(null)
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [containerLogs, setContainerLogs] = useState<string[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [showAllContainers, setShowAllContainers] = useState(true)
  const [isStreamingLogs, setIsStreamingLogs] = useState(false)

  // WebSocket for real-time log streaming
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const wsUrl = selectedContainer
    ? `${API_BASE_URL.replace('http', 'ws')}/api/ws/logs/${selectedContainer.id}`
    : null

  const {
    isConnected: wsConnected,
    lastMessage: wsMessage,
    connect: connectWs,
    disconnect: disconnectWs,
  } = useWebSocket(wsUrl, {
    autoConnect: false,
    onMessage: (message) => {
      if (message.type === 'log' && message.data.message) {
        setContainerLogs(prev => [...prev, message.data.message])
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
      toast.error('Lost connection to log stream')
    },
  })

  // Load containers
  const loadContainers = async () => {
    try {
      setLoading(true)
      const data = await dockerAPI.listContainers(showAllContainers)
      setContainers(data)
    } catch (error) {
      console.error('Failed to load containers:', error)
      toast.error('Failed to load containers')
    } finally {
      setLoading(false)
    }
  }

  // Filter containers based on search and status
  useEffect(() => {
    let filtered = containers

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (container) =>
          container.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          container.image.toLowerCase().includes(searchQuery.toLowerCase()) ||
          container.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((container) => container.status === statusFilter)
    }

    setFilteredContainers(filtered)
  }, [containers, searchQuery, statusFilter])

  // Container actions
  const handleContainerAction = async (
    containerId: string,
    action: 'start' | 'stop' | 'restart' | 'remove',
    force = false
  ) => {
    try {
      // Set loading state for this container
      setContainers((prev) =>
        prev.map((c) => (c.id === containerId ? { ...c, isLoading: true } : c))
      )

      let result
      switch (action) {
        case 'start':
          result = await dockerAPI.startContainer(containerId)
          toast.success(`Container ${result.container_id} started successfully`)
          break
        case 'stop':
          result = await dockerAPI.stopContainer(containerId)
          toast.success(`Container ${result.container_id} stopped successfully`)
          break
        case 'restart':
          result = await dockerAPI.restartContainer(containerId)
          toast.success(`Container ${result.container_id} restarted successfully`)
          break
        case 'remove':
          result = await dockerAPI.removeContainer(containerId, force)
          toast.success(`Container ${result.container_id} removed successfully`)
          break
      }

      // Reload containers to get updated status
      await loadContainers()
    } catch (error) {
      console.error(`Failed to ${action} container:`, error)
      toast.error(`Failed to ${action} container`)
    } finally {
      // Clear loading state
      setContainers((prev) =>
        prev.map((c) => (c.id === containerId ? { ...c, isLoading: false } : c))
      )
    }
  }

  // Load container logs
  const loadContainerLogs = async (containerId: string) => {
    try {
      setLogsLoading(true)
      const result = await dockerAPI.getContainerLogs(containerId, 200)
      setContainerLogs(result.logs)
    } catch (error) {
      console.error('Failed to load container logs:', error)
      toast.error('Failed to load container logs')
      setContainerLogs([])
    } finally {
      setLogsLoading(false)
    }
  }

  // Show logs modal
  const showLogs = async (container: ContainerWithActions) => {
    setSelectedContainer(container)
    setShowLogsModal(true)
    setIsStreamingLogs(false)
    await loadContainerLogs(container.id)
  }

  // Start log streaming
  const startLogStreaming = () => {
    if (selectedContainer) {
      setIsStreamingLogs(true)
      connectWs()
    }
  }

  // Stop log streaming
  const stopLogStreaming = () => {
    setIsStreamingLogs(false)
    disconnectWs()
  }

  // Handle modal close
  const handleLogsModalClose = () => {
    setShowLogsModal(false)
    stopLogStreaming()
    setSelectedContainer(null)
    setContainerLogs([])
  }

  // Get status icon and color
  const getStatusInfo = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-100', textColor: 'text-green-800' }
      case 'exited':
        return { icon: Square, color: 'text-gray-500', bgColor: 'bg-gray-100', textColor: 'text-gray-800' }
      case 'created':
        return { icon: Clock, color: 'text-blue-500', bgColor: 'bg-blue-100', textColor: 'text-blue-800' }
      case 'paused':
        return { icon: Clock, color: 'text-yellow-500', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800' }
      case 'restarting':
        return { icon: RotateCcw, color: 'text-orange-500', bgColor: 'bg-orange-100', textColor: 'text-orange-800' }
      default:
        return { icon: AlertCircle, color: 'text-red-500', bgColor: 'bg-red-100', textColor: 'text-red-800' }
    }
  }

  // Format created date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  // Get unique statuses for filter
  const uniqueStatuses = Array.from(new Set(containers.map((c) => c.status)))

  useEffect(() => {
    loadContainers()
  }, [showAllContainers])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Docker Containers</h1>
          <p className="text-gray-600">Manage your Docker containers</p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showAllContainers}
              onChange={(e) => setShowAllContainers(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Show all containers</span>
          </label>
          <Button
            onClick={loadContainers}
            disabled={loading}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search containers by name, image, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            {uniqueStatuses.map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Container List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Loading containers...</span>
        </div>
      ) : filteredContainers.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            <Container className="w-full h-full" />
          </div>
          <h3 className="text-sm font-medium text-gray-900">No containers found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {containers.length === 0
              ? 'No Docker containers are available.'
              : 'No containers match your current filters.'}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {filteredContainers.map((container) => {
              const statusInfo = getStatusInfo(container.status)
              const StatusIcon = statusInfo.icon

              return (
                <li key={container.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1 min-w-0">
                      <div className="flex-shrink-0">
                        <StatusIcon className={`w-5 h-5 ${statusInfo.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {container.name}
                          </p>
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.bgColor} ${statusInfo.textColor}`}
                          >
                            {container.status}
                          </span>
                        </div>
                        <div className="mt-1 space-y-1">
                          <p className="text-sm text-gray-500 truncate">
                            <span className="font-medium">Image:</span> {container.image}
                          </p>
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">ID:</span> {container.id}
                          </p>
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">Created:</span> {formatDate(container.created)}
                          </p>
                          {container.ports && Object.keys(container.ports).length > 0 && (
                            <p className="text-sm text-gray-500">
                              <span className="font-medium">Ports:</span>{' '}
                              {Object.entries(container.ports)
                                .map(([internal, external]) =>
                                  Array.isArray(external)
                                    ? external.map(e => `${e.HostPort}:${internal}`).join(', ')
                                    : `${internal}`
                                )
                                .join(', ')}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => showLogs(container)}
                        variant="outline"
                        size="sm"
                        className="flex items-center space-x-1"
                      >
                        <FileText className="w-4 h-4" />
                        <span>Logs</span>
                      </Button>

                      {container.status === 'running' ? (
                        <>
                          <Button
                            onClick={() => handleContainerAction(container.id, 'restart')}
                            disabled={container.isLoading}
                            variant="outline"
                            size="sm"
                            className="flex items-center space-x-1"
                          >
                            <RotateCcw className="w-4 h-4" />
                            <span>Restart</span>
                          </Button>
                          <Button
                            onClick={() => handleContainerAction(container.id, 'stop')}
                            disabled={container.isLoading}
                            variant="outline"
                            size="sm"
                            className="flex items-center space-x-1"
                          >
                            <Square className="w-4 h-4" />
                            <span>Stop</span>
                          </Button>
                        </>
                      ) : (
                        <Button
                          onClick={() => handleContainerAction(container.id, 'start')}
                          disabled={container.isLoading}
                          variant="outline"
                          size="sm"
                          className="flex items-center space-x-1"
                        >
                          <Play className="w-4 h-4" />
                          <span>Start</span>
                        </Button>
                      )}

                      <Button
                        onClick={() => handleContainerAction(container.id, 'remove', true)}
                        disabled={container.isLoading}
                        variant="outline"
                        size="sm"
                        className="flex items-center space-x-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Remove</span>
                      </Button>

                      {container.isLoading && (
                        <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
                      )}
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {/* Container Logs Modal */}
      <Modal
        isOpen={showLogsModal}
        onClose={handleLogsModalClose}
        title={`Container Logs - ${selectedContainer?.name}`}
        size="xl"
      >
        <LogViewer
          title={`Logs for ${selectedContainer?.name || 'Container'}`}
          logs={containerLogs}
          isStreaming={isStreamingLogs}
          onStartStreaming={startLogStreaming}
          onStopStreaming={stopLogStreaming}
          onRefresh={() => selectedContainer && loadContainerLogs(selectedContainer.id)}
          isLoading={logsLoading}
          maxHeight="max-h-96"
          showControls={true}
          showSearch={true}
          autoScroll={true}
          websocketUrl={wsUrl || undefined}
        />
      </Modal>
    </div>
  )
}

export default ContainerManagement