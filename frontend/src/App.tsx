import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'
import ServerCatalog from './pages/ServerCatalog'
import MCPServers from './pages/MCPServers'
import LLMClients from './pages/LLMClients'
import ToolPermissions from './pages/ToolPermissions'
import SecretsManagement from './pages/SecretsManagement'
import GatewayMonitoring from './pages/GatewayMonitoring'
import ContainerManagement from './pages/ContainerManagement'
import ProjectManagement from './pages/ProjectManagement'

function App() {
  return (
    <Layout>
      <Routes>
        {/* Default redirect to servers */}
        <Route path="/" element={<Navigate to="/servers" replace />} />

        {/* Main application routes */}
        <Route path="/catalog" element={<ServerCatalog />} />
        <Route path="/servers" element={<MCPServers />} />
        <Route path="/clients" element={<LLMClients />} />
        <Route path="/permissions" element={<ToolPermissions />} />
        <Route path="/secrets" element={<SecretsManagement />} />
        <Route path="/gateway" element={<GatewayMonitoring />} />
        <Route path="/containers" element={<ContainerManagement />} />
        <Route path="/projects" element={<ProjectManagement />} />

        {/* 404 fallback */}
        <Route path="*" element={<Navigate to="/servers" replace />} />
      </Routes>
    </Layout>
  )
}

export default App