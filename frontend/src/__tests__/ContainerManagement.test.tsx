import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'

import ContainerManagement from '@/pages/ContainerManagement'
import { dockerAPI } from '@/services/api'

// Mock the API
vi.mock('@/services/api', () => ({
  dockerAPI: {
    listContainers: vi.fn(),
    getContainer: vi.fn(),
    startContainer: vi.fn(),
    stopContainer: vi.fn(),
    restartContainer: vi.fn(),
    removeContainer: vi.fn(),
    getContainerLogs: vi.fn(),
  },
}))

// Mock React Hot Toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  success: vi.fn(),
  error: vi.fn(),
}))

// Mock WebSocket hook
vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: false,
    lastMessage: null,
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
}))

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('ContainerManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockContainers = [
    {
      id: 'abc123',
      name: 'test-container-1',
      image: 'nginx:latest',
      status: 'running',
      created: '2024-01-01T00:00:00Z',
      ports: { '80/tcp': [{ HostPort: '8080' }] },
      labels: { app: 'test' },
      state: { Status: 'running' },
      mounts: [],
    },
    {
      id: 'def456',
      name: 'test-container-2',
      image: 'redis:alpine',
      status: 'exited',
      created: '2024-01-01T01:00:00Z',
      ports: {},
      labels: {},
      state: { Status: 'exited' },
      mounts: [],
    },
  ]

  it('renders container management page', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    expect(screen.getByText('Docker Containers')).toBeInTheDocument()
    expect(screen.getByText('Manage your Docker containers')).toBeInTheDocument()
  })

  it('displays containers after loading', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
      expect(screen.getByText('test-container-2')).toBeInTheDocument()
    })

    expect(screen.getByText('nginx:latest')).toBeInTheDocument()
    expect(screen.getByText('redis:alpine')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    vi.mocked(dockerAPI.listContainers).mockReturnValue(new Promise(() => {})) // Never resolves

    renderWithProviders(<ContainerManagement />)

    expect(screen.getByText('Loading containers...')).toBeInTheDocument()
  })

  it('shows empty state when no containers', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue([])

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('No containers found')).toBeInTheDocument()
      expect(screen.getByText('No Docker containers are available.')).toBeInTheDocument()
    })
  })

  it('filters containers by search query', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search containers by name, image, or ID...')
    fireEvent.change(searchInput, { target: { value: 'nginx' } })

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
      expect(screen.queryByText('test-container-2')).not.toBeInTheDocument()
    })
  })

  it('filters containers by status', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    const statusFilter = screen.getByDisplayValue('All Status')
    fireEvent.change(statusFilter, { target: { value: 'running' } })

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
      expect(screen.queryByText('test-container-2')).not.toBeInTheDocument()
    })
  })

  it('handles container start action', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)
    vi.mocked(dockerAPI.startContainer).mockResolvedValue({
      container_id: 'def456',
      status: 'started',
      message: 'Container def456 started successfully',
    })

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-2')).toBeInTheDocument()
    })

    // Find the start button for the stopped container
    const startButtons = screen.getAllByText('Start')
    fireEvent.click(startButtons[0])

    await waitFor(() => {
      expect(dockerAPI.startContainer).toHaveBeenCalledWith('def456')
    })
  })

  it('handles container stop action', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)
    vi.mocked(dockerAPI.stopContainer).mockResolvedValue({
      container_id: 'abc123',
      status: 'stopped',
      message: 'Container abc123 stopped successfully',
    })

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    // Find the stop button for the running container
    const stopButtons = screen.getAllByText('Stop')
    fireEvent.click(stopButtons[0])

    await waitFor(() => {
      expect(dockerAPI.stopContainer).toHaveBeenCalledWith('abc123', 10)
    })
  })

  it('handles container restart action', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)
    vi.mocked(dockerAPI.restartContainer).mockResolvedValue({
      container_id: 'abc123',
      status: 'restarted',
      message: 'Container abc123 restarted successfully',
    })

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    // Find the restart button for the running container
    const restartButtons = screen.getAllByText('Restart')
    fireEvent.click(restartButtons[0])

    await waitFor(() => {
      expect(dockerAPI.restartContainer).toHaveBeenCalledWith('abc123', 10)
    })
  })

  it('handles container remove action', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)
    vi.mocked(dockerAPI.removeContainer).mockResolvedValue({
      container_id: 'abc123',
      status: 'removed',
      message: 'Container abc123 removed successfully',
    })

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    // Find the remove button
    const removeButtons = screen.getAllByText('Remove')
    fireEvent.click(removeButtons[0])

    await waitFor(() => {
      expect(dockerAPI.removeContainer).toHaveBeenCalledWith('abc123', true)
    })
  })

  it('opens logs modal when logs button is clicked', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)
    vi.mocked(dockerAPI.getContainerLogs).mockResolvedValue({
      logs: ['Log line 1', 'Log line 2', 'Log line 3'],
    })

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    // Find and click the logs button
    const logsButtons = screen.getAllByText('Logs')
    fireEvent.click(logsButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Container Logs - test-container-1')).toBeInTheDocument()
    })

    expect(dockerAPI.getContainerLogs).toHaveBeenCalledWith('abc123', 200)
  })

  it('handles refresh action', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('test-container-1')).toBeInTheDocument()
    })

    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    fireEvent.click(refreshButton)

    await waitFor(() => {
      expect(dockerAPI.listContainers).toHaveBeenCalledTimes(2)
    })
  })

  it('toggles show all containers checkbox', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    const checkbox = screen.getByLabelText('Show all containers')
    expect(checkbox).toBeChecked()

    fireEvent.click(checkbox)

    await waitFor(() => {
      expect(dockerAPI.listContainers).toHaveBeenCalledWith(false)
    })
  })

  it('handles API errors gracefully', async () => {
    vi.mocked(dockerAPI.listContainers).mockRejectedValue(new Error('API Error'))

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      // Should not crash and show some error state
      expect(screen.queryByText('Loading containers...')).not.toBeInTheDocument()
    })
  })

  it('displays container status badges correctly', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText('running')).toBeInTheDocument()
      expect(screen.getByText('exited')).toBeInTheDocument()
    })
  })

  it('displays port information when available', async () => {
    vi.mocked(dockerAPI.listContainers).mockResolvedValue(mockContainers)

    renderWithProviders(<ContainerManagement />)

    await waitFor(() => {
      expect(screen.getByText(/8080:80\/tcp/)).toBeInTheDocument()
    })
  })
})