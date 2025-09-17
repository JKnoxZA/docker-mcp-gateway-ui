import axios, { AxiosResponse, AxiosError } from 'axios'
import toast from 'react-hot-toast'

import {
  APIResponse,
  ErrorResponse,
  MCPProject,
  MCPProjectCreate,
  MCPProjectResponse,
  MCPServer,
  MCPServerCreate,
  MCPServerResponse,
  LLMClient,
  LLMClientResponse,
  ToolPermission,
  ToolPermissionCreate,
  SecretCreate,
  SecretResponse,
  ContainerInfo,
  ImageInfo,
  BuildInfo,
  GatewayStatus,
} from '@/types'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError<ErrorResponse>) => {
    // Handle different error status codes
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token')
          toast.error('Session expired. Please log in again.')
          break
        case 403:
          toast.error('You do not have permission to perform this action.')
          break
        case 404:
          toast.error('Resource not found.')
          break
        case 422:
          // Validation error
          toast.error(data?.message || 'Validation error occurred.')
          break
        case 500:
          toast.error('Internal server error. Please try again later.')
          break
        default:
          toast.error(data?.message || 'An unexpected error occurred.')
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.')
    } else {
      toast.error('An unexpected error occurred.')
    }

    return Promise.reject(error)
  }
)

// Helper function to handle API responses
const handleResponse = <T>(response: AxiosResponse<T>): T => {
  return response.data
}

// Project API
export const projectAPI = {
  // List projects
  list: (): Promise<MCPProjectResponse[]> =>
    api.get('/api/projects/').then(handleResponse),

  // Get project details
  get: (id: number): Promise<MCPProject> =>
    api.get(`/api/projects/${id}`).then(handleResponse),

  // Create project
  create: (data: MCPProjectCreate): Promise<MCPProjectResponse> =>
    api.post('/api/projects/', data).then(handleResponse),

  // Update project
  update: (id: number, data: Partial<MCPProjectCreate>): Promise<MCPProjectResponse> =>
    api.put(`/api/projects/${id}`, data).then(handleResponse),

  // Delete project
  delete: (id: number): Promise<APIResponse> =>
    api.delete(`/api/projects/${id}`).then(handleResponse),

  // Build project
  build: (id: number): Promise<{ build_id: string; status: string }> =>
    api.post(`/api/projects/${id}/build`).then(handleResponse),

  // Deploy project
  deploy: (id: number): Promise<APIResponse> =>
    api.post(`/api/projects/${id}/deploy`).then(handleResponse),

  // Get build status
  getBuildStatus: (buildId: string): Promise<BuildInfo> =>
    api.get(`/api/builds/${buildId}`).then(handleResponse),
}

// MCP Server API
export const serverAPI = {
  // List servers
  list: (): Promise<MCPServerResponse[]> =>
    api.get('/api/mcp/servers/').then(handleResponse),

  // Get server details
  get: (name: string): Promise<MCPServer> =>
    api.get(`/api/mcp/servers/${name}`).then(handleResponse),

  // Add server
  add: (data: MCPServerCreate): Promise<MCPServerResponse> =>
    api.post('/api/mcp/servers/', data).then(handleResponse),

  // Update server
  update: (name: string, data: Partial<MCPServerCreate>): Promise<MCPServerResponse> =>
    api.put(`/api/mcp/servers/${name}`, data).then(handleResponse),

  // Remove server
  remove: (name: string): Promise<APIResponse> =>
    api.delete(`/api/mcp/servers/${name}`).then(handleResponse),

  // Test server connection
  test: (name: string): Promise<{ status: string; message: string }> =>
    api.post(`/api/mcp/servers/${name}/test`).then(handleResponse),

  // Get server catalog
  getCatalog: (): Promise<{ servers: any[] }> =>
    api.get('/api/mcp/catalog/').then(handleResponse),
}

// LLM Client API
export const clientAPI = {
  // List clients
  list: (): Promise<{ clients: LLMClientResponse[] }> =>
    api.get('/api/mcp/clients/').then(handleResponse),

  // Add custom client
  add: (data: LLMClient): Promise<APIResponse> =>
    api.post('/api/mcp/clients/', data).then(handleResponse),

  // Connect client to servers
  connect: (clientName: string, serverNames: string[]): Promise<APIResponse> =>
    api.post(`/api/mcp/clients/${clientName}/connect`, serverNames).then(handleResponse),
}

// Tool Permissions API
export const permissionAPI = {
  // List permissions
  list: (): Promise<{ permissions: ToolPermission[] }> =>
    api.get('/api/mcp/permissions/').then(handleResponse),

  // Create permission request
  create: (data: ToolPermissionCreate): Promise<APIResponse> =>
    api.post('/api/mcp/permissions/', data).then(handleResponse),

  // Update permission
  update: (id: number, action: 'allowed' | 'denied'): Promise<APIResponse> =>
    api.put(`/api/mcp/permissions/${id}`, { action }).then(handleResponse),

  // Execute tool
  executeTool: (
    toolName: string,
    serverName: string,
    clientName: string,
    parameters: Record<string, any> = {}
  ): Promise<any> =>
    api.post('/api/mcp/tools/execute', {
      tool_name: toolName,
      server_name: serverName,
      client_name: clientName,
      parameters,
    }).then(handleResponse),

  // List all tools
  listTools: (): Promise<{ tools: any[] }> =>
    api.get('/api/mcp/tools/').then(handleResponse),
}

// Secrets API
export const secretAPI = {
  // List secrets
  list: (): Promise<{ secrets: SecretResponse[] }> =>
    api.get('/api/mcp/secrets/').then(handleResponse),

  // Create secret
  create: (data: SecretCreate): Promise<APIResponse> =>
    api.post('/api/mcp/secrets/', null, { params: data }).then(handleResponse),

  // Delete secret
  delete: (key: string): Promise<APIResponse> =>
    api.delete(`/api/mcp/secrets/${key}`).then(handleResponse),
}

// Docker API
export const dockerAPI = {
  // List containers
  listContainers: (all?: boolean): Promise<ContainerInfo[]> =>
    api.get('/api/docker/containers/', { params: { all_containers: all ?? true } }).then(handleResponse),

  // Get container details
  getContainer: (id: string): Promise<ContainerInfo & {
    started?: string;
    environment?: string[];
    network_settings?: Record<string, any>;
    logs_path?: string;
  }> =>
    api.get(`/api/docker/containers/${id}`).then(handleResponse),

  // Start container
  startContainer: (id: string): Promise<{ container_id: string; status: string; message: string }> =>
    api.post(`/api/docker/containers/${id}/start`).then(handleResponse),

  // Stop container
  stopContainer: (id: string, timeout?: number): Promise<{ container_id: string; status: string; message: string }> =>
    api.post(`/api/docker/containers/${id}/stop`, { timeout: timeout ?? 10 }).then(handleResponse),

  // Restart container
  restartContainer: (id: string, timeout?: number): Promise<{ container_id: string; status: string; message: string }> =>
    api.post(`/api/docker/containers/${id}/restart`, { timeout: timeout ?? 10 }).then(handleResponse),

  // Remove container
  removeContainer: (id: string, force?: boolean): Promise<{ container_id: string; status: string; message: string }> =>
    api.delete(`/api/docker/containers/${id}`, { data: { force: force ?? false } }).then(handleResponse),

  // Get container logs
  getContainerLogs: (id: string, tail?: number): Promise<{ logs: string[] }> =>
    api.get(`/api/docker/containers/${id}/logs`, { params: { tail: tail ?? 100, follow: false } }).then(handleResponse),

  // List images
  listImages: (): Promise<ImageInfo[]> =>
    api.get('/api/docker/images/').then(handleResponse),

  // Remove image
  removeImage: (id: string, force?: boolean): Promise<{ image_id: string; status: string; message: string }> =>
    api.delete(`/api/docker/images/${id}`, { params: { force: force ?? false } }).then(handleResponse),

  // List networks
  listNetworks: (): Promise<{ id: string; name: string; driver: string; scope: string; created: string; containers: string[] }[]> =>
    api.get('/api/docker/networks/').then(handleResponse),

  // List volumes
  listVolumes: (): Promise<{ name: string; driver: string; mountpoint: string; created: string; labels: Record<string, string>; scope: string }[]> =>
    api.get('/api/docker/volumes/').then(handleResponse),

  // Get system info
  getSystemInfo: (): Promise<{
    containers: number;
    containers_running: number;
    containers_paused: number;
    containers_stopped: number;
    images: number;
    server_version: string;
    architecture: string;
    os: string;
    total_memory: number;
    cpu_count: number;
    storage_driver: string;
  }> =>
    api.get('/api/docker/system/info').then(handleResponse),

  // Check Docker health
  checkHealth: (): Promise<{ status: string; message: string }> =>
    api.get('/api/docker/health').then(handleResponse),
}

// Gateway API
export const gatewayAPI = {
  // Get gateway status
  getStatus: (): Promise<GatewayStatus> =>
    api.get('/api/mcp/gateway/status').then(handleResponse),

  // Get gateway logs
  getLogs: (): Promise<{ logs: string[] }> =>
    api.get('/api/mcp/gateway/logs').then(handleResponse),

  // Restart gateway
  restart: (): Promise<APIResponse> =>
    api.post('/api/mcp/gateway/restart').then(handleResponse),
}

// Auth API
export const authAPI = {
  // Login
  login: (credentials: { username: string; password: string }): Promise<{
    access_token: string;
    token_type: string;
  }> =>
    api.post('/api/auth/login', credentials).then(handleResponse),

  // Logout
  logout: (): Promise<APIResponse> =>
    api.post('/api/auth/logout').then(handleResponse),

  // Get current user
  getCurrentUser: (): Promise<{
    user_id: number;
    username: string;
    role: string;
  }> =>
    api.get('/api/auth/me').then(handleResponse),
}

// Health check
export const healthAPI = {
  check: (): Promise<{ status: string; service: string }> =>
    api.get('/health').then(handleResponse),
}

export default api