// API Response Types
export interface APIResponse<T = any> {
  message: string;
  data?: T;
  success: boolean;
}

export interface ErrorResponse {
  message: string;
  detail?: string;
  success: boolean;
}

// Enums
export enum ProjectStatus {
  CREATED = 'created',
  BUILDING = 'building',
  BUILD_FAILED = 'build_failed',
  BUILT = 'built',
  DEPLOYED = 'deployed',
  DEPLOY_FAILED = 'deploy_failed',
}

export enum ServerStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
}

export enum TransportType {
  STDIO = 'stdio',
  SSE = 'sse',
  WEBSOCKET = 'websocket',
}

export enum PermissionStatus {
  ALLOWED = 'allowed',
  DENIED = 'denied',
  PENDING = 'pending',
}

// MCP Project Types
export interface MCPProject {
  id: number;
  name: string;
  description: string;
  python_version: string;
  tools: Tool[];
  requirements: string[];
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface MCPProjectCreate {
  name: string;
  description: string;
  python_version?: string;
  tools: Tool[];
  requirements?: string[];
}

export interface MCPProjectResponse {
  id: number;
  name: string;
  description: string;
  status: ProjectStatus;
  tools_count: number;
  created_at?: string;
}

// Tool Types
export interface Tool {
  name: string;
  description: string;
  schema?: Record<string, any>;
}

// MCP Server Types
export interface MCPServer {
  id: number;
  name: string;
  description: string;
  server_type: string;
  url?: string;
  transport: TransportType;
  tools: Tool[];
  status: ServerStatus;
  created_at: string;
  updated_at: string;
}

export interface MCPServerCreate {
  name: string;
  description: string;
  server_type?: string;
  url?: string;
  api_key?: string;
  transport?: TransportType;
}

export interface MCPServerResponse {
  id: number;
  name: string;
  description: string;
  server_type: string;
  status: ServerStatus;
  tools_count: number;
  transport: TransportType;
}

// LLM Client Types
export interface LLMClient {
  name: string;
  client_type: string;
  endpoint?: string;
  api_key?: string;
  connected_servers: string[];
  status: string;
}

export interface LLMClientResponse {
  name: string;
  client_type: string;
  status: string;
  connected_servers_count: number;
}

// Permission Types
export interface ToolPermission {
  tool_name: string;
  server_name: string;
  client_name: string;
  permission: PermissionStatus;
  timestamp: string;
}

export interface ToolPermissionCreate {
  tool_name: string;
  server_name: string;
  client_name: string;
}

// Secret Types
export interface SecretCreate {
  key: string;
  value: string;
  description?: string;
}

export interface SecretResponse {
  key: string;
  description: string;
  created_at: string;
  used_by: string[];
}

// Docker Types
export interface ContainerInfo {
  id: string;
  name: string;
  image: string;
  status: string;
  created: string;
  ports: Record<string, any>;
  labels?: Record<string, string>;
  state?: Record<string, any>;
  mounts?: string[];
}

export interface ImageInfo {
  id: string;
  tags: string[];
  created: string;
  size: number;
  labels: Record<string, string>;
  architecture: string;
  os: string;
}

// Build Types
export enum BuildStatus {
  PENDING = 'pending',
  BUILDING = 'building',
  SUCCESS = 'success',
  FAILED = 'failed',
}

export interface BuildInfo {
  build_id: string;
  project_name: string;
  status: BuildStatus;
  logs: string[];
  started_at: string;
  completed_at?: string;
}

export interface BuildLogEntry {
  status: string;
  message: string;
  timestamp: string;
}

// Gateway Types
export interface GatewayStatus {
  status: string;
  uptime: string;
  connected_servers: number;
  active_clients: number;
  container_id?: string;
}

// WebSocket Types
export interface WebSocketEvent {
  type: string;
  data: any;
  timestamp: string;
}

// Navigation Types
export interface NavItem {
  key: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  path?: string;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'password' | 'url' | 'email';
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
  validation?: Record<string, any>;
}

// Modal Types
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  fontSize: 'sm' | 'md' | 'lg';
}

// Search/Filter Types
export interface SearchFilters {
  query?: string;
  status?: string[];
  type?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
}

// Pagination Types
export interface PaginationInfo {
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationInfo;
}