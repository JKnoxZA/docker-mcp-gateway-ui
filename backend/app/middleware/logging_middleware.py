"""Logging middleware for request tracking and performance monitoring"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging_config import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses"""

    def __init__(self, app, logger_name: str = "app.middleware"):
        super().__init__(app)
        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Bind request context to logger
        request_logger = self.logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )

        # Log request start
        request_logger.info(
            "HTTP request started",
            query_params=dict(request.query_params),
            user_agent=request.headers.get("user-agent", "unknown"),
            content_length=request.headers.get("content-length", 0)
        )

        # Add request ID to request state for use in handlers
        request.state.request_id = request_id
        request.state.logger = request_logger

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log response
            log_level = "info"
            if response.status_code >= 400:
                log_level = "warning" if response.status_code < 500 else "error"

            getattr(request_logger, log_level)(
                "HTTP request completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                response_size=response.headers.get("content-length", "unknown")
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            request_logger.error(
                "HTTP request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )

            # Re-raise the exception
            raise


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-related events"""

    def __init__(self, app, logger_name: str = "app.security"):
        super().__init__(app)
        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for security-relevant patterns
        self._log_security_events(request)

        response = await call_next(request)

        # Log authentication failures
        if response.status_code == 401:
            self.logger.warning(
                "Authentication failed",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown")
            )

        # Log authorization failures
        elif response.status_code == 403:
            self.logger.warning(
                "Authorization failed",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown"
            )

        return response

    def _log_security_events(self, request: Request):
        """Log potential security events"""

        # Log suspicious patterns
        suspicious_patterns = [
            "../",  # Path traversal
            "<script",  # XSS attempts
            "union select",  # SQL injection
            "admin",  # Admin access attempts
            "passwd",  # System file access
        ]

        path_lower = request.url.path.lower()
        query_lower = str(request.query_params).lower()

        for pattern in suspicious_patterns:
            if pattern in path_lower or pattern in query_lower:
                self.logger.warning(
                    "Suspicious request pattern detected",
                    pattern=pattern,
                    path=request.url.path,
                    query_params=dict(request.query_params),
                    client_ip=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent", "unknown")
                )
                break

        # Log requests to sensitive endpoints
        sensitive_endpoints = [
            "/api/auth/",
            "/api/secrets/",
            "/api/docker/",
        ]

        for endpoint in sensitive_endpoints:
            if request.url.path.startswith(endpoint):
                self.logger.info(
                    "Access to sensitive endpoint",
                    endpoint=endpoint,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                break