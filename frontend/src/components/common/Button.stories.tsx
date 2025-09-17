import type { Meta, StoryObj } from '@storybook/react'
import { action } from '@storybook/addon-actions'
import { Play, Download, Trash2, Plus, Settings } from 'lucide-react'

import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Components/Common/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Button component is a versatile and accessible button implementation that supports multiple variants, sizes, and states.

## Features
- Multiple variants (primary, secondary, outline, ghost, destructive)
- Different sizes (sm, default, lg)
- Loading state with spinner
- Disabled state
- Icon support
- Full accessibility support
- Consistent styling with design system

## Usage
Use buttons to trigger actions, submit forms, or navigate to different parts of the application.
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'Visual style variant of the button',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'Size of the button',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the button is disabled',
    },
    loading: {
      control: 'boolean',
      description: 'Whether the button is in loading state',
    },
    children: {
      control: 'text',
      description: 'Button content',
    },
    onClick: {
      action: 'clicked',
      description: 'Click handler function',
    },
  },
  args: {
    onClick: action('clicked'),
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

// Basic variants
export const Default: Story = {
  args: {
    children: 'Default Button',
  },
}

export const Primary: Story = {
  args: {
    variant: 'default',
    children: 'Primary Button',
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
}

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline Button',
  },
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ghost Button',
  },
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
}

export const Link: Story = {
  args: {
    variant: 'link',
    children: 'Link Button',
  },
}

// Sizes
export const Small: Story = {
  args: {
    size: 'sm',
    children: 'Small Button',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    children: 'Large Button',
  },
}

// States
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button',
  },
}

export const Loading: Story = {
  args: {
    loading: true,
    children: 'Loading...',
  },
}

export const LoadingWithText: Story = {
  args: {
    loading: true,
    children: 'Saving...',
    variant: 'default',
  },
}

// With Icons
export const WithIcon: Story = {
  args: {
    children: (
      <>
        <Play className="w-4 h-4 mr-2" />
        Start Container
      </>
    ),
  },
}

export const IconOnly: Story = {
  args: {
    size: 'icon',
    children: <Settings className="w-4 h-4" />,
    'aria-label': 'Settings',
  },
}

export const DownloadButton: Story = {
  args: {
    variant: 'outline',
    children: (
      <>
        <Download className="w-4 h-4 mr-2" />
        Download
      </>
    ),
  },
}

export const DestructiveWithIcon: Story = {
  args: {
    variant: 'destructive',
    children: (
      <>
        <Trash2 className="w-4 h-4 mr-2" />
        Delete
      </>
    ),
  },
}

export const AddButton: Story = {
  args: {
    children: (
      <>
        <Plus className="w-4 h-4 mr-2" />
        Add Project
      </>
    ),
  },
}

// Button Groups
export const ButtonGroup: Story = {
  render: () => (
    <div className="flex space-x-2">
      <Button variant="outline">Cancel</Button>
      <Button>Save</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of button grouping for related actions.',
      },
    },
  },
}

export const ToolbarButtons: Story = {
  render: () => (
    <div className="flex items-center space-x-1 border rounded-lg p-1">
      <Button size="sm" variant="ghost">
        <Play className="w-4 h-4" />
      </Button>
      <Button size="sm" variant="ghost">
        <Download className="w-4 h-4" />
      </Button>
      <Button size="sm" variant="ghost">
        <Settings className="w-4 h-4" />
      </Button>
      <div className="border-l h-6 mx-1" />
      <Button size="sm" variant="ghost">
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of toolbar-style button layout.',
      },
    },
  },
}

// Real-world examples
export const ContainerActions: Story = {
  render: () => (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">Container Actions</h3>
      <div className="flex space-x-2">
        <Button size="sm">
          <Play className="w-4 h-4 mr-1" />
          Start
        </Button>
        <Button size="sm" variant="outline">
          Restart
        </Button>
        <Button size="sm" variant="outline">
          Stop
        </Button>
        <Button size="sm" variant="destructive">
          <Trash2 className="w-4 h-4 mr-1" />
          Remove
        </Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world example of container management actions.',
      },
    },
  },
}

export const FormActions: Story = {
  render: () => (
    <div className="space-y-4 max-w-md">
      <div className="space-y-2">
        <label className="text-sm font-medium">Project Name</label>
        <input
          type="text"
          placeholder="Enter project name"
          className="w-full px-3 py-2 border rounded-md"
        />
      </div>
      <div className="flex justify-end space-x-2">
        <Button variant="outline">Cancel</Button>
        <Button>Create Project</Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of form action buttons.',
      },
    },
  },
}

// Accessibility examples
export const AccessibilityExample: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-sm font-medium">Accessibility Features</h3>
      <div className="space-y-2">
        <Button aria-label="Play video" size="icon">
          <Play className="w-4 h-4" />
        </Button>
        <Button disabled aria-describedby="disabled-help">
          Disabled Action
        </Button>
        <p id="disabled-help" className="text-xs text-gray-500">
          This action is currently unavailable
        </p>
        <Button loading>
          <span className="sr-only">Loading, please wait</span>
          Processing...
        </Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Examples showing proper accessibility attributes and screen reader support.',
      },
    },
  },
}