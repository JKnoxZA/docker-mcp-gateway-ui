import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Container,
  Search,
  Server,
  Users,
  Shield,
  Key,
  Monitor,
  FolderOpen,
  Menu,
  X,
  Bell,
  User,
} from 'lucide-react'

import { NavItem } from '@/types'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const navigation: NavItem[] = [
    { key: 'catalog', label: 'Server Catalog', icon: Search, path: '/catalog' },
    { key: 'servers', label: 'MCP Servers', icon: Server, path: '/servers' },
    { key: 'clients', label: 'LLM Clients', icon: Users, path: '/clients' },
    { key: 'permissions', label: 'Permissions', icon: Shield, path: '/permissions' },
    { key: 'secrets', label: 'Secrets', icon: Key, path: '/secrets' },
    { key: 'gateway', label: 'Gateway', icon: Monitor, path: '/gateway' },
    { key: 'containers', label: 'Containers', icon: Container, path: '/containers' },
    { key: 'projects', label: 'Projects', icon: FolderOpen, path: '/projects' },
  ]

  const isActiveRoute = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-4">
            <div className="flex items-center space-x-3">
              <Container className="h-8 w-8 text-primary-600" />
              <span className="text-lg font-semibold text-gray-900">MCP Manager</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          <nav className="mt-5 flex-1 space-y-1 px-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActiveRoute(item.path || '')
              return (
                <Link
                  key={item.key}
                  to={item.path || '/'}
                  onClick={() => setSidebarOpen(false)}
                  className={`group flex items-center space-x-3 rounded-md px-2 py-2 text-sm font-medium transition-colors ${
                    active
                      ? 'bg-primary-100 text-primary-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon
                    className={`h-5 w-5 ${
                      active ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          <div className="flex h-16 items-center px-4 shadow-sm">
            <div className="flex items-center space-x-3">
              <Container className="h-8 w-8 text-primary-600" />
              <span className="text-lg font-semibold text-gray-900">MCP Manager</span>
            </div>
          </div>
          <nav className="mt-5 flex-1 space-y-1 px-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = isActiveRoute(item.path || '')
              return (
                <Link
                  key={item.key}
                  to={item.path || '/'}
                  className={`group flex items-center space-x-3 rounded-md px-2 py-2 text-sm font-medium transition-colors ${
                    active
                      ? 'bg-primary-100 text-primary-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon
                    className={`h-5 w-5 ${
                      active ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          {/* Separator */}
          <div className="h-6 w-px bg-gray-200 lg:hidden" />

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              {/* Gateway status indicator */}
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                  <span className="text-sm text-gray-600">Gateway Running</span>
                </div>
              </div>
            </div>

            <div className="ml-auto flex items-center gap-x-4 lg:gap-x-6">
              {/* Notifications */}
              <button className="rounded-full p-2 text-gray-400 hover:text-gray-500">
                <Bell className="h-5 w-5" />
              </button>

              {/* Profile */}
              <div className="flex items-center space-x-3">
                <button className="flex items-center space-x-2 rounded-md p-2 text-gray-600 hover:bg-gray-50">
                  <User className="h-5 w-5" />
                  <span className="hidden sm:block text-sm font-medium">Admin</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout