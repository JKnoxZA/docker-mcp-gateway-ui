import React from 'react'
import { Shield } from 'lucide-react'

const ToolPermissions: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tool Permissions</h1>

      <div className="text-center py-12">
        <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
          <Shield className="w-full h-full" />
        </div>
        <h3 className="text-sm font-medium text-gray-900">Tool Permissions Management</h3>
        <p className="mt-1 text-sm text-gray-500">
          This page will show tool permission approval workflows.
        </p>
      </div>
    </div>
  )
}

export default ToolPermissions