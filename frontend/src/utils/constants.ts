// API Constants
export const API_ENDPOINTS = {
  CONTAINERS: '/api/containers',
  IMAGES: '/api/images',
  SERVERS: '/api/mcp/servers',
  CLIENTS: '/api/mcp/clients',
  PERMISSIONS: '/api/mcp/permissions',
  SECRETS: '/api/mcp/secrets',
  GATEWAY: '/api/mcp/gateway',
  PROJECTS: '/api/projects',
} as const

// Status Constants
export const STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  PENDING: 'pending',
} as const

// Default Values
export const DEFAULT_PAGE_SIZE = 20
export const DEFAULT_TIMEOUT = 5000

// Helper function
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}