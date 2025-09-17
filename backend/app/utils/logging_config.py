"""Enhanced logging configuration with structured logging support"""

import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.config.settings import settings


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add service information
        log_record['service'] = 'mcp-docker-gateway'
        log_record['version'] = getattr(settings, 'VERSION', '1.0.0')

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

        # Add structured data
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        # This would be populated by middleware in a real request
        # For now, we'll add placeholders
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(self, '_request_id', None)
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(self, '_user_id', None)
        return True


def setup_logging() -> None:
    """Setup comprehensive logging configuration"""

    # Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '[{asctime}] {levelname:<8} [{name}] {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '{levelname} - {message}',
                'style': '{',
            },
            'json': {
                '()': StructuredFormatter,
                'format': '%(timestamp)s %(level)s %(name)s %(message)s'
            }
        },
        'filters': {
            'request_context': {
                '()': RequestContextFilter,
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'detailed' if settings.DEBUG else 'simple',
                'stream': sys.stdout,
                'filters': ['request_context']
            },
            'file_info': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',
                'filename': log_dir / 'app.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'filters': ['request_context']
            },
            'file_error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',
                'filename': log_dir / 'error.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 10,
                'filters': ['request_context']
            },
            'docker_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',
                'filename': log_dir / 'docker.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 3,
                'filters': ['request_context']
            },
            'security_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',
                'filename': log_dir / 'security.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 10,
                'filters': ['request_context']
            }
        },
        'loggers': {
            # Root logger
            '': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': settings.LOG_LEVEL,
                'propagate': False
            },
            # App loggers
            'app': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': settings.LOG_LEVEL,
                'propagate': False
            },
            # Docker operations
            'app.core.docker_manager': {
                'handlers': ['console', 'docker_file', 'file_error'],
                'level': 'DEBUG' if settings.DEBUG else 'INFO',
                'propagate': False
            },
            # Security events
            'app.security': {
                'handlers': ['console', 'security_file', 'file_error'],
                'level': 'INFO',
                'propagate': False
            },
            # External libraries
            'uvicorn': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': False
            },
            'fastapi': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': False
            },
            'sqlalchemy': {
                'handlers': ['file_info'],
                'level': 'WARNING',
                'propagate': False
            },
            'docker': {
                'handlers': ['docker_file'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }

    # Apply configuration
    logging.config.dictConfig(logging_config)


def get_logger(name: str, **context) -> structlog.BoundLogger:
    """Get a structured logger with context"""
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger


def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None,
                     result: Any = None, error: Exception = None,
                     duration_ms: float = None, logger: logging.Logger = None):
    """Log function call details"""
    if logger is None:
        logger = logging.getLogger(__name__)

    log_data = {
        'event': 'function_call',
        'function': func_name,
        'duration_ms': duration_ms
    }

    if args:
        log_data['args_count'] = len(args)
    if kwargs:
        log_data['kwargs_keys'] = list(kwargs.keys())
    if error:
        log_data['error'] = str(error)
        log_data['error_type'] = type(error).__name__

    if error:
        logger.error("Function call failed", extra={'extra_data': log_data})
    else:
        logger.info("Function call completed", extra={'extra_data': log_data})


class PerformanceLogger:
    """Context manager for performance logging"""

    def __init__(self, operation: str, logger: logging.Logger = None, **context):
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.context = context
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        self.logger.info(
            f"Starting {self.operation}",
            extra={'extra_data': {'event': 'operation_start', 'operation': self.operation, **self.context}}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = (time.perf_counter() - self.start_time) * 1000  # Convert to milliseconds

        log_data = {
            'event': 'operation_complete',
            'operation': self.operation,
            'duration_ms': round(duration, 2),
            **self.context
        }

        if exc_type:
            log_data['error'] = str(exc_val)
            log_data['error_type'] = exc_type.__name__
            self.logger.error(
                f"Operation {self.operation} failed",
                extra={'extra_data': log_data}
            )
        else:
            level = logging.WARNING if duration > 5000 else logging.INFO  # Warn on slow operations
            self.logger.log(
                level,
                f"Operation {self.operation} completed in {duration:.2f}ms",
                extra={'extra_data': log_data}
            )


def audit_log(action: str, resource_type: str, resource_id: str = None,
              user_id: str = None, details: dict = None, logger: logging.Logger = None):
    """Log audit events"""
    if logger is None:
        logger = logging.getLogger('app.security')

    audit_data = {
        'event': 'audit',
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if details:
        audit_data['details'] = details

    logger.info(f"Audit: {action} on {resource_type}", extra={'extra_data': audit_data})