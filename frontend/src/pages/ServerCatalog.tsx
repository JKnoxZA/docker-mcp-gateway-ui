import React from 'react'
import { Search, Plus, Key } from 'lucide-react'

import { useServerCatalog } from '@/hooks/useAPI'

const ServerCatalog: React.FC = () => {
  const { data: catalogData, isLoading, error } = useServerCatalog()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
        <span className="ml-2 text-gray-600">Loading server catalog...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Failed to load server catalog</div>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    )
  }

  const servers = catalogData?.servers || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Server Catalog</h1>
        <button className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          Add Custom Server
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search servers..."
          className="input pl-10"
        />
      </div>

      {/* Server Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {servers.map((server: any) => (
          <div key={server.name} className="card">
            <div className="card-body">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{server.name}</h3>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {server.type}
                  </span>
                </div>
                {server.requires_api_key && (
                  <Key className="h-4 w-4 text-yellow-600" title="Requires API Key" />
                )}
              </div>

              <p className="text-gray-600 text-sm mb-3">{server.description}</p>

              <div className="text-xs text-gray-500 mb-4">
                <strong>Tools:</strong> {server.tools?.join(', ') || 'None'}
              </div>

              <button className="w-full btn-success">
                Add Server
              </button>
            </div>
          </div>
        ))}
      </div>

      {servers.length === 0 && (
        <div className="text-center py-12">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No servers found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding a custom server or check your connection.
          </p>
        </div>
      )}
    </div>
  )
}

export default ServerCatalog