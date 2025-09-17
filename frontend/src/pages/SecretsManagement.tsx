import React from 'react'
import { Key, Plus } from 'lucide-react'

const SecretsManagement: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Secrets Management</h1>
        <button className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          Add Secret
        </button>
      </div>

      <div className="text-center py-12">
        <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
          <Key className="w-full h-full" />
        </div>
        <h3 className="text-sm font-medium text-gray-900">Secrets Management</h3>
        <p className="mt-1 text-sm text-gray-500">
          This page will show secure API key and secret management.
        </p>
      </div>
    </div>
  )
}

export default SecretsManagement