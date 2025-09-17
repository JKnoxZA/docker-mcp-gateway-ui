import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'

import { LogViewer } from './LogViewer'

const meta: Meta<typeof LogViewer> = {
  title: 'Components/Common/LogViewer',
  component: LogViewer,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The LogViewer component provides a feature-rich interface for viewing and managing log data.

## Features
- Real-time log streaming with WebSocket support
- Search and filtering capabilities
- Auto-scrolling with manual override
- Loading states and refresh functionality
- Copy to clipboard support
- Responsive design with proper scrolling
- Accessibility support

## Usage
Use the LogViewer to display container logs, build logs, or any other streaming text data.
        `,
      },
    },
  },
  argTypes: {
    title: {
      control: 'text',
      description: 'Title displayed in the log viewer header',
    },
    logs: {
      control: 'object',
      description: 'Array of log lines to display',
    },
    isStreaming: {
      control: 'boolean',
      description: 'Whether logs are currently streaming',
    },
    isLoading: {
      control: 'boolean',
      description: 'Whether logs are being loaded',
    },
    showControls: {
      control: 'boolean',
      description: 'Whether to show control buttons',
    },
    showSearch: {
      control: 'boolean',
      description: 'Whether to show search functionality',
    },
    autoScroll: {
      control: 'boolean',
      description: 'Whether to auto-scroll to new logs',
    },
    maxHeight: {
      control: 'text',
      description: 'Maximum height CSS class',
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

// Sample log data
const sampleLogs = [
  '[2024-01-15 10:30:00] INFO: Starting application server',
  '[2024-01-15 10:30:01] INFO: Database connection established',
  '[2024-01-15 10:30:02] INFO: Redis connection established',
  '[2024-01-15 10:30:03] INFO: Loading configuration files',
  '[2024-01-15 10:30:04] WARN: Configuration file not found, using defaults',
  '[2024-01-15 10:30:05] INFO: MCP Gateway initialized',
  '[2024-01-15 10:30:06] INFO: Docker client connected',
  '[2024-01-15 10:30:07] INFO: Starting HTTP server on port 8000',
  '[2024-01-15 10:30:08] INFO: Server ready to accept connections',
  '[2024-01-15 10:30:10] INFO: Processing container list request',
  '[2024-01-15 10:30:11] DEBUG: Found 5 containers',
  '[2024-01-15 10:30:12] INFO: Request completed successfully',
]

const containerLogs = [
  '2024-01-15T10:30:00.123Z [INFO] Container starting...',
  '2024-01-15T10:30:01.456Z [INFO] Initializing application',
  '2024-01-15T10:30:02.789Z [INFO] Loading environment variables',
  '2024-01-15T10:30:03.012Z [WARN] Environment variable API_KEY not set',
  '2024-01-15T10:30:04.345Z [INFO] Starting web server',
  '2024-01-15T10:30:05.678Z [INFO] Server listening on port 3000',
  '2024-01-15T10:30:10.901Z [INFO] Received HTTP GET /health',
  '2024-01-15T10:30:11.234Z [INFO] Health check passed',
  '2024-01-15T10:30:15.567Z [INFO] Received HTTP GET /api/data',
  '2024-01-15T10:30:16.890Z [ERROR] Database connection failed',
  '2024-01-15T10:30:17.123Z [ERROR] Request failed with status 500',
]

const buildLogs = [
  'Step 1/8 : FROM node:18-alpine',
  ' ---> 7b69d1b06f16',
  'Step 2/8 : WORKDIR /app',
  ' ---> Running in 8d7a1b2c3d4e',
  'Removing intermediate container 8d7a1b2c3d4e',
  ' ---> 9e8f7g6h5i4j',
  'Step 3/8 : COPY package*.json ./',
  ' ---> 0k9l8m7n6o5p',
  'Step 4/8 : RUN npm ci --only=production',
  ' ---> Running in 1q2w3e4r5t6y',
  'npm WARN deprecated module@1.0.0',
  'added 250 packages in 30.5s',
  'Removing intermediate container 1q2w3e4r5t6y',
  ' ---> 2u7i8o9p0a1s',
  'Step 5/8 : COPY . .',
  ' ---> 3d4f5g6h7j8k',
  'Successfully built 4l5z6x7c8v9b',
  'Successfully tagged my-app:latest',
]

// Basic examples
export const Default: Story = {
  args: {
    title: 'Application Logs',
    logs: sampleLogs,
    showControls: true,
    showSearch: true,
    autoScroll: true,
  },
}

export const ContainerLogs: Story = {
  args: {
    title: 'Container nginx-proxy',
    logs: containerLogs,
    showControls: true,
    showSearch: true,
    autoScroll: true,
    maxHeight: 'max-h-96',
  },
}

export const BuildLogs: Story = {
  args: {
    title: 'Build: my-app:latest',
    logs: buildLogs,
    showControls: true,
    showSearch: false,
    autoScroll: true,
    maxHeight: 'max-h-80',
  },
}

// States
export const Loading: Story = {
  args: {
    title: 'Loading Logs',
    logs: [],
    isLoading: true,
    showControls: true,
    showSearch: true,
  },
}

export const Streaming: Story = {
  args: {
    title: 'Live Container Logs',
    logs: containerLogs,
    isStreaming: true,
    showControls: true,
    showSearch: true,
    autoScroll: true,
  },
}

export const EmptyLogs: Story = {
  args: {
    title: 'No Logs Available',
    logs: [],
    showControls: true,
    showSearch: true,
  },
}

// Without controls
export const MinimalViewer: Story = {
  args: {
    title: 'Simple Log View',
    logs: sampleLogs.slice(0, 5),
    showControls: false,
    showSearch: false,
    autoScroll: false,
  },
}

// Interactive example with live updates
export const LiveExample: Story = {
  render: () => {
    const [logs, setLogs] = useState(sampleLogs.slice(0, 3))
    const [isStreaming, setIsStreaming] = useState(false)

    const addLog = () => {
      const newLog = `[${new Date().toISOString().slice(0, 19).replace('T', ' ')}] INFO: New log entry ${logs.length + 1}`
      setLogs(prev => [...prev, newLog])
    }

    const startStreaming = () => {
      setIsStreaming(true)
      const interval = setInterval(() => {
        addLog()
      }, 2000)

      setTimeout(() => {
        clearInterval(interval)
        setIsStreaming(false)
      }, 10000)
    }

    const clearLogs = () => {
      setLogs([])
    }

    return (
      <div className="space-y-4">
        <div className="flex space-x-2">
          <button
            onClick={addLog}
            className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
          >
            Add Log
          </button>
          <button
            onClick={startStreaming}
            disabled={isStreaming}
            className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 disabled:opacity-50"
          >
            {isStreaming ? 'Streaming...' : 'Start Stream'}
          </button>
          <button
            onClick={clearLogs}
            className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
          >
            Clear
          </button>
        </div>
        <LogViewer
          title="Interactive Log Viewer"
          logs={logs}
          isStreaming={isStreaming}
          showControls={true}
          showSearch={true}
          autoScroll={true}
          maxHeight="max-h-64"
        />
      </div>
    )
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive example showing live log updates and streaming.',
      },
    },
  },
}

// Different log types
export const ErrorLogs: Story = {
  args: {
    title: 'Error Logs',
    logs: [
      '[2024-01-15 10:30:00] ERROR: Database connection failed',
      '[2024-01-15 10:30:01] ERROR: Timeout connecting to redis://localhost:6379',
      '[2024-01-15 10:30:02] ERROR: Failed to start server: Port 8000 already in use',
      '[2024-01-15 10:30:03] FATAL: Application startup failed',
      '[2024-01-15 10:30:04] ERROR: Process exited with code 1',
    ],
    showControls: true,
    showSearch: true,
  },
}

export const MultilineLogEntry: Story = {
  args: {
    title: 'Docker Build with Multiline Output',
    logs: [
      'Step 1/5 : FROM python:3.11-slim',
      ' ---> 7b69d1b06f16',
      'Step 2/5 : WORKDIR /app',
      ' ---> Running in container_id',
      'Removing intermediate container container_id',
      ' ---> a1b2c3d4e5f6',
      'Step 3/5 : COPY requirements.txt .',
      ' ---> g7h8i9j0k1l2',
      'Step 4/5 : RUN pip install -r requirements.txt',
      ' ---> Running in container_id_2',
      'Collecting fastapi==0.104.1',
      '  Downloading fastapi-0.104.1-py3-none-any.whl (92 kB)',
      'Collecting uvicorn[standard]==0.24.0',
      '  Downloading uvicorn-0.24.0-py3-none-any.whl (59 kB)',
      'Installing collected packages: fastapi, uvicorn',
      'Successfully installed fastapi-0.104.1 uvicorn-0.24.0',
      'Removing intermediate container container_id_2',
      ' ---> m3n4o5p6q7r8',
      'Successfully built image_id',
      'Successfully tagged my-app:latest',
    ],
    showControls: true,
    showSearch: true,
    maxHeight: 'max-h-80',
  },
}

// Real-world usage patterns
export const DockerContainerExample: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Container: web-server</h3>
      <LogViewer
        title="Live Container Logs"
        logs={[
          '2024-01-15T10:30:00.000Z [nginx] Starting nginx server',
          '2024-01-15T10:30:01.000Z [nginx] Configuration loaded from /etc/nginx/nginx.conf',
          '2024-01-15T10:30:02.000Z [nginx] Server started on port 80',
          '2024-01-15T10:35:15.000Z [nginx] 172.17.0.1 - GET /health HTTP/1.1 200',
          '2024-01-15T10:35:16.000Z [nginx] 172.17.0.1 - GET /api/status HTTP/1.1 200',
          '2024-01-15T10:35:20.000Z [nginx] 172.17.0.1 - GET /dashboard HTTP/1.1 200',
        ]}
        isStreaming={true}
        showControls={true}
        showSearch={true}
        autoScroll={true}
        maxHeight="max-h-64"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world example of viewing Docker container logs.',
      },
    },
  },
}

export const BuildProgressExample: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Building: mcp-server:latest</h3>
      <LogViewer
        title="Build Progress"
        logs={buildLogs}
        isStreaming={false}
        showControls={true}
        showSearch={false}
        autoScroll={false}
        maxHeight="max-h-80"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world example of viewing Docker build progress.',
      },
    },
  },
}