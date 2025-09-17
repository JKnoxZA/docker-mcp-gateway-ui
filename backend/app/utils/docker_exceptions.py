"""Custom Docker-related exceptions for better error handling"""

import docker.errors


class DockerManagerException(Exception):
    """Base exception for Docker manager operations"""
    pass


class DockerConnectionError(DockerManagerException):
    """Docker daemon connection error"""
    pass


class DockerContainerError(DockerManagerException):
    """Container operation error"""
    pass


class DockerImageError(DockerManagerException):
    """Image operation error"""
    pass


class DockerNetworkError(DockerManagerException):
    """Network operation error"""
    pass


class DockerVolumeError(DockerManagerException):
    """Volume operation error"""
    pass


class DockerBuildError(DockerManagerException):
    """Build operation error"""
    pass


class DockerPermissionError(DockerManagerException):
    """Docker permission/access error"""
    pass


class DockerResourceExhaustedError(DockerManagerException):
    """Docker resource exhaustion error"""
    pass


def map_docker_error(error: Exception) -> DockerManagerException:
    """Map Docker SDK errors to custom exceptions"""

    # Check for connection-related errors
    if "connection" in str(error).lower() or "refused" in str(error).lower():
        return DockerConnectionError(f"Failed to connect to Docker daemon: {error}")

    elif isinstance(error, docker.errors.APIError):
        status_code = getattr(error, 'status_code', None)

        if status_code == 404:
            return DockerContainerError(f"Resource not found: {error}")
        elif status_code == 403:
            return DockerPermissionError(f"Permission denied: {error}")
        elif status_code == 409:
            return DockerContainerError(f"Resource conflict: {error}")
        elif status_code == 500:
            return DockerManagerException(f"Docker daemon error: {error}")
        else:
            return DockerManagerException(f"Docker API error: {error}")

    elif isinstance(error, docker.errors.ImageNotFound):
        return DockerImageError(f"Image not found: {error}")

    elif isinstance(error, docker.errors.ContainerError):
        return DockerContainerError(f"Container error: {error}")

    elif isinstance(error, docker.errors.BuildError):
        return DockerBuildError(f"Build failed: {error}")

    elif isinstance(error, docker.errors.NotFound):
        return DockerContainerError(f"Resource not found: {error}")

    elif isinstance(error, docker.errors.DockerException):
        return DockerManagerException(f"Docker operation failed: {error}")

    else:
        return DockerManagerException(f"Unexpected error: {error}")


def is_recoverable_error(error: Exception) -> bool:
    """Check if an error is recoverable and should be retried"""

    if isinstance(error, DockerConnectionError):
        return True

    if isinstance(error, DockerManagerException) and "timeout" in str(error).lower():
        return True

    if isinstance(error, docker.errors.APIError):
        status_code = getattr(error, 'status_code', None)
        # Retry on server errors, but not client errors
        return status_code and 500 <= status_code < 600

    return False