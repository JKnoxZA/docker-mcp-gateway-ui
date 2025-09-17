import type { Meta, StoryObj } from '@storybook/react'
import { CheckCircle, AlertCircle, Clock, XCircle } from 'lucide-react'

import { StatusBadge } from './StatusBadge'

const meta: Meta<typeof StatusBadge> = {
  title: 'Components/Common/StatusBadge',
  component: StatusBadge,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The StatusBadge component displays status information with appropriate colors and optional icons.

## Features
- Multiple status variants with semantic colors
- Optional icon support
- Consistent sizing and spacing
- Accessible color combinations
- Customizable styling

## Usage
Use status badges to indicate the current state of containers, projects, builds, or any other entity in the system.
        `,
      },
    },
  },
  argTypes: {
    status: {
      control: 'select',
      options: ['success', 'error', 'warning', 'info', 'pending'],
      description: 'Status type that determines color and styling',
    },
    children: {
      control: 'text',
      description: 'Badge content',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

// Basic statuses
export const Success: Story = {
  args: {
    status: 'success',
    children: 'Running',
  },
}

export const Error: Story = {
  args: {
    status: 'error',
    children: 'Failed',
  },
}

export const Warning: Story = {
  args: {
    status: 'warning',
    children: 'Warning',
  },
}

export const Info: Story = {
  args: {
    status: 'info',
    children: 'Info',
  },
}

export const Pending: Story = {
  args: {
    status: 'pending',
    children: 'Pending',
  },
}

// With icons
export const SuccessWithIcon: Story = {
  args: {
    status: 'success',
    children: (
      <>
        <CheckCircle className="w-3 h-3 mr-1" />
        Active
      </>
    ),
  },
}

export const ErrorWithIcon: Story = {
  args: {
    status: 'error',
    children: (
      <>
        <XCircle className="w-3 h-3 mr-1" />
        Stopped
      </>
    ),
  },
}

export const WarningWithIcon: Story = {
  args: {
    status: 'warning',
    children: (
      <>
        <AlertCircle className="w-3 h-3 mr-1" />
        Warning
      </>
    ),
  },
}

export const PendingWithIcon: Story = {
  args: {
    status: 'pending',
    children: (
      <>
        <Clock className="w-3 h-3 mr-1" />
        Building
      </>
    ),
  },
}

// Container status examples
export const ContainerStatuses: Story = {
  render: () => (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Container Statuses</h3>
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Running:</span>
          <StatusBadge status="success">
            <CheckCircle className="w-3 h-3 mr-1" />
            Running
          </StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Exited:</span>
          <StatusBadge status="error">
            <XCircle className="w-3 h-3 mr-1" />
            Exited
          </StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Created:</span>
          <StatusBadge status="info">
            <Clock className="w-3 h-3 mr-1" />
            Created
          </StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Restarting:</span>
          <StatusBadge status="warning">
            <AlertCircle className="w-3 h-3 mr-1" />
            Restarting
          </StatusBadge>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world example showing different container statuses.',
      },
    },
  },
}

// Build status examples
export const BuildStatuses: Story = {
  render: () => (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Build Statuses</h3>
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Success:</span>
          <StatusBadge status="success">Built</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Failed:</span>
          <StatusBadge status="error">Build Failed</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Building:</span>
          <StatusBadge status="pending">Building...</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Queued:</span>
          <StatusBadge status="info">Queued</StatusBadge>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example showing build pipeline statuses.',
      },
    },
  },
}

// Server status examples
export const ServerStatuses: Story = {
  render: () => (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">MCP Server Statuses</h3>
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Connected:</span>
          <StatusBadge status="success">Connected</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Disconnected:</span>
          <StatusBadge status="error">Disconnected</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Connecting:</span>
          <StatusBadge status="pending">Connecting...</StatusBadge>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm w-20">Error:</span>
          <StatusBadge status="error">Error</StatusBadge>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example showing MCP server connection statuses.',
      },
    },
  },
}

// Grouped badges
export const BadgeGroups: Story = {
  render: () => (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium mb-2">Inline Group</h4>
        <div className="flex space-x-2">
          <StatusBadge status="success">Active</StatusBadge>
          <StatusBadge status="warning">2 Warnings</StatusBadge>
          <StatusBadge status="info">5 Tools</StatusBadge>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium mb-2">Stacked Group</h4>
        <div className="space-y-1">
          <StatusBadge status="success">Health Check: Passed</StatusBadge>
          <StatusBadge status="info">Last Updated: 2 min ago</StatusBadge>
          <StatusBadge status="warning">Memory: 85%</StatusBadge>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Examples of grouping multiple status badges.',
      },
    },
  },
}

// Custom styling
export const CustomStyling: Story = {
  render: () => (
    <div className="space-y-2">
      <StatusBadge status="success" className="font-bold">
        Custom Bold
      </StatusBadge>
      <StatusBadge status="info" className="text-xs">
        Small Text
      </StatusBadge>
      <StatusBadge status="warning" className="px-4 py-2">
        Large Padding
      </StatusBadge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Examples of custom styling with additional CSS classes.',
      },
    },
  },
}