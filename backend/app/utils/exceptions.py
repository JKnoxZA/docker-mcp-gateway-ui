"""Custom exception classes for the MCP Gateway application"""

from typing import Any, Dict, Optional


class MCPGatewayException(Exception):
    """Base exception class for MCP Gateway"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DockerException(MCPGatewayException):
    """Docker-related exceptions"""

    pass


class MCPServerException(MCPGatewayException):
    """MCP server-related exceptions"""

    pass


class ProjectException(MCPGatewayException):
    """Project-related exceptions"""

    pass


class BuildException(MCPGatewayException):
    """Build-related exceptions"""

    pass


class DatabaseException(MCPGatewayException):
    """Database-related exceptions"""

    pass


class AuthenticationException(MCPGatewayException):
    """Authentication-related exceptions"""

    pass


class AuthorizationException(MCPGatewayException):
    """Authorization-related exceptions"""

    pass


class ValidationException(MCPGatewayException):
    """Input validation exceptions"""

    pass


class ConfigurationException(MCPGatewayException):
    """Configuration-related exceptions"""

    pass


class ExternalServiceException(MCPGatewayException):
    """External service integration exceptions"""

    pass
