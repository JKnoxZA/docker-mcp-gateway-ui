import React, { useState, useEffect } from 'react';
import { 
  Play, FileText, Settings, Container, Plus, Hammer, Rocket, Eye, Terminal, Folder,
  Search, Key, Users, Shield, Monitor, Zap, Globe, Server, AlertCircle, CheckCircle,
  Clock, X, Edit, Trash2, Link, RefreshCw
} from 'lucide-react';

const MCPDockerInterface = () => {
  // State management
  const [projects, setProjects] = useState([]);
  const [containers, setContainers] = useState([]);
  const [mcpServers, setMcpServers] = useState([]);
  const [serverCatalog, setServerCatalog] = useState([]);
  const [llmClients, setLlmClients] = useState([]);
  const [toolPermissions, setToolPermissions] = useState([]);
  const [secrets, setSecrets] = useState([]);
  const [gatewayStatus, setGatewayStatus] = useState({});
  const [allTools, setAllTools] = useState([]);
  
  const [activeTab, setActiveTab] = useState('servers');
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showAddServer, setShowAddServer] = useState(false);
  const [showAddSecret, setShowAddSecret] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedServer, setSelectedServer] = useState(null);

  // Mock data initialization
  useEffect(() => {
    // Initialize with sample data
    setServerCatalog([
      {
        name: 'brave-search',
        description: 'Search the web using Brave Search API',
        type: 'official',
        tools: ['brave_web_search'],
        requires_api_key: true
      },
      {
        name: 'obsidian',
        description: 'Interact with Obsidian vaults',
        type: 'official',
        tools: ['append_to_note', 'search_notes', 'create_note'],
        requires_api_key: true
      },
      {
        name: 'github',
        description: 'GitHub repository management',
        type: 'official',
        tools: ['create_issue', 'list_repos', 'create_pr'],
        requires_api_key: true
      }
    ]);

    setMcpServers([
      {
        name: 'obsidian-vault',
        description: 'My Obsidian vault integration',
        type: 'official',
        status: 'connected',
        tools: [
          { name: 'append_to_note', description: 'Add content to existing notes' },
          { name: 'search_notes', description: 'Search through all notes' }
        ],
        transport: 'stdio'
      },
      {
        name: 'weather-api',
        description: 'Weather data service',
        type: 'custom',
        status: 'connected',
        tools: [
          { name: 'get_weather', description: 'Get current weather' },
          { name: 'get_forecast', description: 'Get weather forecast' }
        ],
        transport: 'stdio'
      }
    ]);

    setLlmClients([
      { name: 'Claude', type: 'claude', status: 'available', connected_servers: ['obsidian-vault'] },
      { name: 'Cursor', type: 'cursor', status: 'available', connected_servers: [] },
      { name: 'LM Studio', type: 'lm_studio', status: 'available', connected_servers: ['weather-api'] }
    ]);

    setToolPermissions([
      {
        tool_name: 'append_to_note',
        server_name: 'obsidian-vault',
        client_name: 'Claude',
        permission: 'pending',
        timestamp: '2024-01-15 10:30'
      },
      {
        tool_name: 'get_weather',
        server_name: 'weather-api',
        client_name: 'LM Studio',
        permission: 'allowed',
        timestamp: '2024-01-15 09:15'
      }
    ]);

    setGatewayStatus({
      status: 'running',
      uptime: '2 hours',
      connected_servers: 2,
      active_clients: 2
    });

    setSecrets([
      { key: 'obsidian_api_key', description: 'Obsidian API key', created_at: '2024-01-15' },
      { key: 'github_token', description: 'GitHub access token', created_at: '2024-01-14' }
    ]);
  }, []);

  // Server Catalog Component
  const ServerCatalog = () => {
    const [searchTerm, setSearchTerm] = useState('');
    
    const filteredCatalog = serverCatalog.filter(server =>
      server.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      server.description.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const addServerFromCatalog = (catalogServer) => {
      setSelectedServer(catalogServer);
      setShowAddServer(true);
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">Server Catalog</h2>
          <button
            onClick={() => setShowAddServer(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Plus size={16} />
            <span>Add Custom Server</span>
          </button>
        </div>

        <div className="relative">
          <Search size={20} className="absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search servers..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCatalog.map(server => (
            <div key={server.name} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold">{server.name}</h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {server.type}
                  </span>
                </div>
                {server.requires_api_key && (
                  <Key size={16} className="text-yellow-600" title="Requires API Key" />
                )}
              </div>
              
              <p className="text-gray-600 text-sm mb-3">{server.description}</p>
              
              <div className="text-xs text-gray-500 mb-3">
                Tools: {server.tools.join(', ')}
              </div>
              
              <button
                onClick={() => addServerFromCatalog(server)}
                className="w-full py-2 bg-green-100 text-green-700 rounded hover:bg-green-200 text-sm font-medium"
              >
                Add Server
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // MCP Servers Management
  const MCPServers = () => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'connected': return 'text-green-600';
        case 'error': return 'text-red-600';
        case 'disconnected': return 'text-gray-600';
        default: return 'text-gray-600';
      }
    };

    const testConnection = async (serverName) => {
      console.log('Testing connection to:', serverName);
      // Simulate connection test
      setMcpServers(prev => prev.map(s => 
        s.name === serverName ? { ...s, status: 'connected' } : s
      ));
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">MCP Servers</h2>
          <button
            onClick={() => setActiveTab('catalog')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Search size={16} />
            <span>Browse Catalog</span>
          </button>
        </div>

        <div className="grid gap-4">
          {mcpServers.map(server => (
            <div key={server.name} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold">{server.name}</h3>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {server.type}
                    </span>
                    <span className={`text-sm font-medium flex items-center ${getStatusColor(server.status)}`}>
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        server.status === 'connected' ? 'bg-green-500' : 
                        server.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                      }`}></div>
                      {server.status}
                    </span>
                  </div>
                  <p className="text-gray-600 text-sm mt-1">{server.description}</p>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => testConnection(server.name)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    title="Test Connection"
                  >
                    <RefreshCw size={16} />
                  </button>
                  <button className="p-2 text-gray-600 hover:bg-gray-50 rounded">
                    <Settings size={16} />
                  </button>
                  <button className="p-2 text-red-600 hover:bg-red-50 rounded">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              <div className="text-sm">
                <p className="text-gray-600 mb-2">
                  Transport: <span className="font-mono">{server.transport}</span>
                </p>
                <div>
                  <p className="text-gray-600 mb-1">Tools ({server.tools?.length || 0}):</p>
                  <div className="flex flex-wrap gap-2">
                    {server.tools?.map(tool => (
                      <span
                        key={tool.name}
                        className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs"
                        title={tool.description}
                      >
                        {tool.name}
                      </span>
                    )) || <span className="text-gray-400">No tools</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // LLM Clients Management
  const LLMClients = () => {
    const [selectedClient, setSelectedClientLocal] = useState(null);
    const [availableServers, setAvailableServers] = useState([]);

    const connectClientToServers = (clientName, serverNames) => {
      setLlmClients(prev => prev.map(client =>
        client.name === clientName
          ? { ...client, connected_servers: serverNames, status: 'connected' }
          : client
      ));
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">LLM Clients</h2>
        </div>

        <div className="grid gap-4">
          {llmClients.map(client => (
            <div key={client.name} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold">{client.name}</h3>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {client.type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Connected to {client.connected_servers?.length || 0} servers
                  </p>
                </div>
                
                <button 
                  onClick={() => setSelectedClientLocal(client)}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                >
                  Configure
                </button>
              </div>

              <div className="text-sm">
                <p className="text-gray-600 mb-2">Connected Servers:</p>
                <div className="flex flex-wrap gap-2">
                  {client.connected_servers?.length > 0 ? (
                    client.connected_servers.map(serverName => (
                      <span key={serverName} className="bg-green-50 text-green-700 px-2 py-1 rounded text-xs">
                        {serverName}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400">No servers connected</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {selectedClient && (
          <ClientConfigModal 
            client={selectedClient}
            servers={mcpServers}
            onConnect={connectClientToServers}
            onClose={() => setSelectedClientLocal(null)}
          />
        )}
      </div>
    );
  };

  // Tool Permissions Management
  const ToolPermissions = () => {
    const handlePermission = (index, action) => {
      setToolPermissions(prev => prev.map((perm, i) =>
        i === index ? { ...perm, permission: action } : perm
      ));
    };

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Tool Permissions</h2>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tool</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Server</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {toolPermissions.map((permission, index) => (
                <tr key={index}>
                  <td className="px-4 py-3 font-mono text-sm">{permission.tool_name}</td>
                  <td className="px-4 py-3 text-sm">{permission.server_name}</td>
                  <td className="px-4 py-3 text-sm">{permission.client_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      permission.permission === 'allowed' ? 'bg-green-100 text-green-800' :
                      permission.permission === 'denied' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {permission.permission}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {permission.permission === 'pending' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handlePermission(index, 'allowed')}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                        >
                          <CheckCircle size={16} />
                        </button>
                        <button
                          onClick={() => handlePermission(index, 'denied')}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Secrets Management
  const SecretsManagement = () => {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">Secrets Management</h2>
          <button
            onClick={() => setShowAddSecret(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            <Plus size={16} />
            <span>Add Secret</span>
          </button>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Key</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {secrets.map(secret => (
                <tr key={secret.key}>
                  <td className="px-4 py-3 font-mono text-sm">{secret.key}</td>
                  <td className="px-4 py-3 text-sm">{secret.description}</td>
                  <td className="px-4 py-3 text-sm">{secret.created_at}</td>
                  <td className="px-4 py-3">
                    <div className="flex space-x-2">
                      <button className="p-1 text-blue-600 hover:bg-blue-50 rounded">
                        <Edit size={16} />
                      </button>
                      <button className="p-1 text-red-600 hover:bg-red-50 rounded">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Gateway Monitoring
  const GatewayMonitoring = () => {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">MCP Gateway Status</h2>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Gateway Status</p>
                <p className={`text-lg font-semibold ${
                  gatewayStatus.status === 'running' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {gatewayStatus.status}
                </p>
              </div>
              <Server className={gatewayStatus.status === 'running' ? 'text-green-600' : 'text-red-600'} size={24} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Connected Servers</p>
                <p className="text-lg font-semibold">{gatewayStatus.connected_servers}</p>
              </div>
              <Link className="text-blue-600" size={24} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Clients</p>
                <p className="text-lg font-semibold">{gatewayStatus.active_clients}</p>
              </div>
              <Users className="text-purple-600" size={24} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Uptime</p>
                <p className="text-lg font-semibold">{gatewayStatus.uptime}</p>
              </div>
              <Clock className="text-orange-600" size={24} />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Gateway Logs</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm h-64 overflow-y-auto">
            <div>[2024-01-15 10:30:15] MCP Gateway started</div>
            <div>[2024-01-15 10:30:16] Connected to obsidian-vault server</div>
            <div>[2024-01-15 10:30:17] Connected to weather-api server</div>
            <div>[2024-01-15 10:30:18] Client 'Claude' connected</div>
            <div>[2024-01-15 10:31:22] Tool execution: append_to_note (allowed)</div>
            <div>[2024-01-15 10:32:05] Tool execution: get_weather (success)</div>
          </div>
        </div>
      </div>
    );
  };

  // Add Server Modal
  const AddServerModal = () => {
    const [serverData, setServerData] = useState({
      name: selectedServer?.name || '',
      description: selectedServer?.description || '',
      type: selectedServer?.type || 'custom',
      url: '',
      api_key: '',
      transport: 'stdio'
    });

    const addServer = async () => {
      console.log('Adding server:', serverData);
      setMcpServers([...mcpServers, { 
        ...serverData, 
        status: 'disconnected',
        tools: selectedServer?.tools?.map(name => ({ name, description: `Tool: ${name}` })) || []
      }]);
      setShowAddServer(false);
      setSelectedServer(null);
      setServerData({ name: '', description: '', type: 'custom', url: '', api_key: '', transport: 'stdio' });
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg w-96">
          <h3 className="text-lg font-semibold mb-4">Add MCP Server</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Server Name</label>
              <input
                type="text"
                className="w-full border rounded px-3 py-2"
                value={serverData.name}
                onChange={(e) => setServerData({ ...serverData, name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full border rounded px-3 py-2 h-20"
                value={serverData.description}
                onChange={(e) => setServerData({ ...serverData, description: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                className="w-full border rounded px-3 py-2"
                value={serverData.type}
                onChange={(e) => setServerData({ ...serverData, type: e.target.value })}
              >
                <option value="official">Official</option>
                <option value="custom">Custom</option>
                <option value="remote">Remote</option>
              </select>
            </div>

            {serverData.type === 'remote' && (
              <div>
                <label className="block text-sm font-medium mb-1">URL</label>
                <input
                  type="url"
                  className="w-full border rounded px-3 py-2"
                  value={serverData.url}
                  onChange={(e) => setServerData({ ...serverData, url: e.target.value })}
                  placeholder="https://api.example.com/mcp"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-1">API Key (Optional)</label>
              <input
                type="password"
                className="w-full border rounded px-3 py-2"
                value={serverData.api_key}
                onChange={(e) => setServerData({ ...serverData, api_key: e.target.value })}
                placeholder="Enter API key if required"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 mt-6">
            <button
              onClick={() => {
                setShowAddServer(false);
                setSelectedServer(null);
              }}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              onClick={addServer}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Add Server
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Client Configuration Modal
  const ClientConfigModal = ({ client, servers, onConnect, onClose }) => {
    const [selectedServers, setSelectedServers] = useState(client.connected_servers || []);

    const handleServerToggle = (serverName) => {
      setSelectedServers(prev =>
        prev.includes(serverName)
          ? prev.filter(s => s !== serverName)
          : [...prev, serverName]
      );
    };

    const saveConfiguration = () => {
      onConnect(client.name, selectedServers);
      onClose();
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg w-96">
          <h3 className="text-lg font-semibold mb-4">Configure {client.name}</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Connect to Servers:</label>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {servers.map(server => (
                  <label key={server.name} className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedServers.includes(server.name)}
                      onChange={() => handleServerToggle(server.name)}
                      className="rounded"
                    />
                    <div>
                      <span className="text-sm font-medium">{server.name}</span>
                      <p className="text-xs text-gray-500">{server.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              onClick={saveConfiguration}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Container className="text-blue-600" size={24} />
              <h1 className="text-xl font-semibold text-gray-900">MCP Docker Manager</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Gateway Status: </span>
              <span className={`font-medium ${
                gatewayStatus.status === 'running' ? 'text-green-600' : 'text-red-600'
              }`}>
                ● {gatewayStatus.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'catalog', label: 'Server Catalog', icon: Search },
              { key: 'servers', label: 'MCP Servers', icon: Server },
              { key: 'clients', label: 'LLM Clients', icon: Users },
              { key: 'permissions', label: 'Permissions', icon: Shield },
              { key: 'secrets', label: 'Secrets', icon: Key },
              { key: 'gateway', label: 'Gateway', icon: Monitor },
              { key: 'containers', label: 'Containers', icon: Container }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'catalog' && <ServerCatalog />}
        {activeTab === 'servers' && <MCPServers />}
        {activeTab === 'clients' && <LLMClients />}
        {activeTab === 'permissions' && <ToolPermissions />}
        {activeTab === 'secrets' && <SecretsManagement />}
        {activeTab === 'gateway' && <GatewayMonitoring />}
        {activeTab === 'containers' && (
          <div>
            <h2 className="text-2xl font-semibold mb-6">Docker Containers</h2>
            <div className="text-center py-12">
              <Container size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">Container management interface would go here</p>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddServer && <AddServerModal />}
    </div>
  );
};

export default MCPDockerInterface;