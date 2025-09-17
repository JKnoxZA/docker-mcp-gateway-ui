import React from 'react'
import { Monitor, Server, Users, Clock, Link } from 'lucide-react'

import { useGatewayStatus } from '@/hooks/useAPI'

const GatewayMonitoring: React.FC = () => {
  const { data: gatewayStatus, isLoading } = useGatewayStatus()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
        <span className="ml-2 text-gray-600">Loading gateway status...</span>
      </div>
    )
  }

  const status = gatewayStatus || {
    status: 'unknown',
    uptime: '0',
    connected_servers: 0,
    active_clients: 0,
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">MCP Gateway Status</h1>

      {/* Status Overview */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Gateway Status</p>
                <p className={`text-lg font-semibold ${
                  status.status === 'running' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {status.status}
                </p>
              </div>
              <Server className={status.status === 'running' ? 'text-green-600' : 'text-red-600'} size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Connected Servers</p>
                <p className="text-lg font-semibold text-gray-900">{status.connected_servers}</p>
              </div>
              <Link className="text-blue-600" size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Clients</p>
                <p className="text-lg font-semibold text-gray-900">{status.active_clients}</p>
              </div>
              <Users className="text-purple-600" size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Uptime</p>
                <p className="text-lg font-semibold text-gray-900">{status.uptime}</p>
              </div>
              <Clock className="text-orange-600" size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Gateway Logs */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Gateway Logs</h3>
        </div>
        <div className="card-body">
          <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm h-64 overflow-y-auto custom-scrollbar">
            <div>[2024-01-15 10:30:15] MCP Gateway started</div>
            <div>[2024-01-15 10:30:16] Connected to server: obsidian-vault</div>
            <div>[2024-01-15 10:30:17] Connected to server: weather-api</div>
            <div>[2024-01-15 10:30:18] Client 'Claude' connected</div>
            <div>[2024-01-15 10:31:22] Tool execution: append_to_note (allowed)</div>
            <div>[2024-01-15 10:32:05] Tool execution: get_weather (success)</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GatewayMonitoring