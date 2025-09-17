import React from 'react'
import { Search, Settings, Trash2, RefreshCw, Plus } from 'lucide-react'

import { useServers, useTestServer, useRemoveServer } from '@/hooks/useAPI'
import { ServerStatus } from '@/types'

const MCPServers: React.FC = () => {
  const { data: servers, isLoading, error } = useServers()
  const testServerMutation = useTestServer()
  const removeServerMutation = useRemoveServer()

  const getStatusColor = (status: ServerStatus) => {
    switch (status) {
      case ServerStatus.CONNECTED:
        return 'text-green-600'
      case ServerStatus.ERROR:
        return 'text-red-600'
      case ServerStatus.DISCONNECTED:
      default:
        return 'text-gray-600'
    }
  }

  const getStatusDotColor = (status: ServerStatus) => {
    switch (status) {
      case ServerStatus.CONNECTED:
        return 'bg-green-500'
      case ServerStatus.ERROR:
        return 'bg-red-500'
      case ServerStatus.DISCONNECTED:
      default:
        return 'bg-gray-400'
    }
  }

  const handleTestConnection = async (serverName: string) => {
    try {
      await testServerMutation.mutateAsync(serverName)
    } catch (error) {
      // Error is handled by the mutation
    }
  }

  const handleRemoveServer = async (serverName: string) => {
    if (window.confirm(`Are you sure you want to remove server "${serverName}"?`)) {
      try {
        await removeServerMutation.mutateAsync(serverName)
      } catch (error) {
        // Error is handled by the mutation
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
        <span className="ml-2 text-gray-600">Loading MCP servers...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Failed to load MCP servers</div>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    )
  }

  const serverList = servers || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">MCP Servers</h1>
        <div className="flex space-x-3">
          <button className="btn-outline">
            <Search className="w-4 h-4 mr-2" />
            Browse Catalog
          </button>
          <button className="btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            Add Server
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {serverList.map((server: any) => (
          <div key={server.id} className="card">
            <div className="card-body">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">{server.name}</h3>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      {server.server_type}
                    </span>
                    <span className={`text-sm font-medium flex items-center ${getStatusColor(server.status)}`}>
                      <div className={`w-2 h-2 rounded-full mr-2 ${getStatusDotColor(server.status)}`}></div>
                      {server.status}
                    </span>
                  </div>
                  <p className="text-gray-600 text-sm mt-1">{server.description}</p>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleTestConnection(server.name)}
                    disabled={testServerMutation.isPending}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Test Connection"
                  >
                    <RefreshCw className={`w-4 h-4 ${testServerMutation.isPending ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    className="p-2 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                    title="Settings"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleRemoveServer(server.name)}
                    disabled={removeServerMutation.isPending}
                    className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Remove Server"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="text-sm space-y-2">
                <div>
                  <span className="text-gray-600">Transport: </span>
                  <span className="font-mono text-gray-900">{server.transport}</span>
                </div>
                <div>
                  <span className="text-gray-600">Tools ({server.tools_count || 0}):</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {server.tools_count > 0 ? (
                      // This would normally come from the server data
                      <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs">
                        {server.tools_count} tools available
                      </span>
                    ) : (
                      <span className="text-gray-400">No tools</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {serverList.length === 0 && (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            <Search className="w-full h-full" />
          </div>
          <h3 className="text-sm font-medium text-gray-900">No MCP servers configured</h3>
          <p className="mt-1 text-sm text-gray-500 mb-4">
            Get started by adding servers from the catalog or creating a custom server.
          </p>
          <button className="btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Server
          </button>
        </div>
      )}
    </div>
  )
}

export default MCPServers