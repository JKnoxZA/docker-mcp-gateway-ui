import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import {
  projectAPI,
  serverAPI,
  clientAPI,
  permissionAPI,
  secretAPI,
  dockerAPI,
  gatewayAPI,
  authAPI,
  healthAPI,
} from '@/services/api'
import {
  MCPProjectCreate,
  MCPServerCreate,
  LLMClient,
  ToolPermissionCreate,
  SecretCreate,
} from '@/types'

// Query Keys
export const QueryKeys = {
  projects: ['projects'] as const,
  project: (id: number) => ['projects', id] as const,
  buildStatus: (buildId: string) => ['build', buildId] as const,

  servers: ['servers'] as const,
  server: (name: string) => ['servers', name] as const,
  serverCatalog: ['serverCatalog'] as const,

  clients: ['clients'] as const,

  permissions: ['permissions'] as const,
  tools: ['tools'] as const,

  secrets: ['secrets'] as const,

  containers: ['containers'] as const,
  containerLogs: (id: string) => ['containers', id, 'logs'] as const,
  images: ['images'] as const,
  systemInfo: ['systemInfo'] as const,

  gateway: ['gateway'] as const,
  gatewayLogs: ['gatewayLogs'] as const,

  currentUser: ['currentUser'] as const,
  health: ['health'] as const,
}

// Project Hooks
export const useProjects = () => {
  return useQuery({
    queryKey: QueryKeys.projects,
    queryFn: projectAPI.list,
  })
}

export const useProject = (id: number) => {
  return useQuery({
    queryKey: QueryKeys.project(id),
    queryFn: () => projectAPI.get(id),
    enabled: !!id,
  })
}

export const useBuildStatus = (buildId: string) => {
  return useQuery({
    queryKey: QueryKeys.buildStatus(buildId),
    queryFn: () => projectAPI.getBuildStatus(buildId),
    enabled: !!buildId,
    refetchInterval: 2000, // Poll every 2 seconds while building
  })
}

export const useCreateProject = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MCPProjectCreate) => projectAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.projects })
      toast.success('Project created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create project')
    },
  })
}

export const useBuildProject = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => projectAPI.build(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.projects })
      toast.success('Build started successfully')
      // Start polling build status
      queryClient.invalidateQueries({ queryKey: QueryKeys.buildStatus(data.build_id) })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to start build')
    },
  })
}

export const useDeployProject = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => projectAPI.deploy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.projects })
      queryClient.invalidateQueries({ queryKey: QueryKeys.servers })
      toast.success('Project deployed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to deploy project')
    },
  })
}

// Server Hooks
export const useServers = () => {
  return useQuery({
    queryKey: QueryKeys.servers,
    queryFn: serverAPI.list,
  })
}

export const useServer = (name: string) => {
  return useQuery({
    queryKey: QueryKeys.server(name),
    queryFn: () => serverAPI.get(name),
    enabled: !!name,
  })
}

export const useServerCatalog = () => {
  return useQuery({
    queryKey: QueryKeys.serverCatalog,
    queryFn: serverAPI.getCatalog,
  })
}

export const useAddServer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MCPServerCreate) => serverAPI.add(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.servers })
      toast.success('Server added successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to add server')
    },
  })
}

export const useRemoveServer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (name: string) => serverAPI.remove(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.servers })
      toast.success('Server removed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to remove server')
    },
  })
}

export const useTestServer = () => {
  return useMutation({
    mutationFn: (name: string) => serverAPI.test(name),
    onSuccess: (data) => {
      toast.success(data.message)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Connection test failed')
    },
  })
}

// Client Hooks
export const useClients = () => {
  return useQuery({
    queryKey: QueryKeys.clients,
    queryFn: clientAPI.list,
  })
}

export const useAddClient = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: LLMClient) => clientAPI.add(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.clients })
      toast.success('Client added successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to add client')
    },
  })
}

export const useConnectClient = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ clientName, serverNames }: { clientName: string; serverNames: string[] }) =>
      clientAPI.connect(clientName, serverNames),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.clients })
      toast.success('Client connected to servers')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to connect client')
    },
  })
}

// Permission Hooks
export const usePermissions = () => {
  return useQuery({
    queryKey: QueryKeys.permissions,
    queryFn: permissionAPI.list,
  })
}

export const useTools = () => {
  return useQuery({
    queryKey: QueryKeys.tools,
    queryFn: permissionAPI.listTools,
  })
}

export const useCreatePermission = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ToolPermissionCreate) => permissionAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.permissions })
      toast.success('Permission request created')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create permission request')
    },
  })
}

export const useUpdatePermission = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'allowed' | 'denied' }) =>
      permissionAPI.update(id, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.permissions })
      toast.success('Permission updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update permission')
    },
  })
}

export const useExecuteTool = () => {
  return useMutation({
    mutationFn: ({
      toolName,
      serverName,
      clientName,
      parameters = {},
    }: {
      toolName: string
      serverName: string
      clientName: string
      parameters?: Record<string, any>
    }) => permissionAPI.executeTool(toolName, serverName, clientName, parameters),
    onSuccess: (data) => {
      if (data.status === 'permission_required') {
        toast.error(data.message)
      } else {
        toast.success('Tool executed successfully')
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Tool execution failed')
    },
  })
}

// Secret Hooks
export const useSecrets = () => {
  return useQuery({
    queryKey: QueryKeys.secrets,
    queryFn: secretAPI.list,
  })
}

export const useCreateSecret = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SecretCreate) => secretAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.secrets })
      toast.success('Secret created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create secret')
    },
  })
}

export const useDeleteSecret = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (key: string) => secretAPI.delete(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.secrets })
      toast.success('Secret deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to delete secret')
    },
  })
}

// Docker Hooks
export const useContainers = () => {
  return useQuery({
    queryKey: QueryKeys.containers,
    queryFn: dockerAPI.listContainers,
    refetchInterval: 5000, // Refresh every 5 seconds
  })
}

export const useContainerLogs = (id: string) => {
  return useQuery({
    queryKey: QueryKeys.containerLogs(id),
    queryFn: () => dockerAPI.getContainerLogs(id),
    enabled: !!id,
  })
}

export const useImages = () => {
  return useQuery({
    queryKey: QueryKeys.images,
    queryFn: dockerAPI.listImages,
  })
}

export const useSystemInfo = () => {
  return useQuery({
    queryKey: QueryKeys.systemInfo,
    queryFn: dockerAPI.getSystemInfo,
  })
}

export const useStartContainer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => dockerAPI.startContainer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.containers })
      toast.success('Container started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to start container')
    },
  })
}

export const useStopContainer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => dockerAPI.stopContainer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.containers })
      toast.success('Container stopped')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to stop container')
    },
  })
}

export const useRemoveContainer = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => dockerAPI.removeContainer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.containers })
      toast.success('Container removed')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to remove container')
    },
  })
}

// Gateway Hooks
export const useGatewayStatus = () => {
  return useQuery({
    queryKey: QueryKeys.gateway,
    queryFn: gatewayAPI.getStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

export const useGatewayLogs = () => {
  return useQuery({
    queryKey: QueryKeys.gatewayLogs,
    queryFn: gatewayAPI.getLogs,
  })
}

export const useRestartGateway = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gatewayAPI.restart,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.gateway })
      toast.success('Gateway restarted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to restart gateway')
    },
  })
}

// Auth Hooks
export const useCurrentUser = () => {
  return useQuery({
    queryKey: QueryKeys.currentUser,
    queryFn: authAPI.getCurrentUser,
    retry: false,
  })
}

export const useLogin = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      authAPI.login(credentials),
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token)
      queryClient.invalidateQueries({ queryKey: QueryKeys.currentUser })
      toast.success('Logged in successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Login failed')
    },
  })
}

export const useLogout = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authAPI.logout,
    onSuccess: () => {
      localStorage.removeItem('auth_token')
      queryClient.clear()
      toast.success('Logged out successfully')
    },
    onError: (error: any) => {
      // Still clear local state even if API call fails
      localStorage.removeItem('auth_token')
      queryClient.clear()
      toast.error(error.response?.data?.message || 'Logout failed')
    },
  })
}

// Health Check Hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: QueryKeys.health,
    queryFn: healthAPI.check,
    refetchInterval: 30000, // Check every 30 seconds
    retry: false,
  })
}