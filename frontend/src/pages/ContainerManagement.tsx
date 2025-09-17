import React from 'react'
import { Container } from 'lucide-react'

const ContainerManagement: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Docker Containers</h1>

      <div className="text-center py-12">
        <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
          <Container className="w-full h-full" />
        </div>
        <h3 className="text-sm font-medium text-gray-900">Container Management</h3>
        <p className="mt-1 text-sm text-gray-500">
          This page will show Docker container management functionality.
        </p>
      </div>
    </div>
  )
}

export default ContainerManagement