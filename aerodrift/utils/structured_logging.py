"""
Structured Logging Configuration for AeroDrift.

This module provides enhanced structured logging with JSON formatting,
context tracking, and performance monitoring capabilities.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import traceback


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context information for log entries."""
    component: str
    operation: Optional[str] = None
    resource_id: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    
    Formats log records as JSON with consistent field names
    and includes context information when available.
    """
    
    def __init__(self, include_extra_fields: bool = True):
        """
        Initialize the structured formatter.
        
        Args:
            include_extra_fields: Whether to include extra fields from log records
        """
        super().__init__()
        self.include_extra_fields = include_extra_fields
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add context if available
        if hasattr(record, 'context') and record.context:
            context_dict = asdict(record.context) if isinstance(record.context, LogContext) else record.context
            log_entry['context'] = context_dict
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        
        # Add extra fields if enabled
        if self.include_extra_fields:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                              'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                              'relativeCreated', 'thread', 'threadName', 'processName',
                              'process', 'message', 'exc_info', 'exc_text', 'stack_info',
                              'context', 'duration_ms']:
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextualLogger:
    """
    Logger with contextual information support.
    
    Provides enhanced logging capabilities with automatic context
    tracking and structured output formatting.
    """
    
    def __init__(self, name: str, context: Optional[LogContext] = None):
        """
        Initialize contextual logger.
        
        Args:
            name: Logger name
            context: Initial log context
        """
        self.logger = logging.getLogger(name)
        self.context = context or LogContext(component=name)
    
    def with_context(self, **kwargs) -> 'ContextualLogger':
        """
        Create a new logger with additional context.
        
        Args:
            **kwargs: Additional context fields
            
        Returns:
            New ContextualLogger with merged context
        """
        new_context = LogContext(
            component=self.context.component,
            operation=kwargs.get('operation', self.context.operation),
            resource_id=kwargs.get('resource_id', self.context.resource_id),
            correlation_id=kwargs.get('correlation_id', self.context.correlation_id),
            user_id=kwargs.get('user_id', self.context.user_id),
            session_id=kwargs.get('session_id', self.context.session_id),
            metadata={**self.context.metadata, **kwargs.get('metadata', {})}
        )
        return ContextualLogger(self.logger.name, new_context)
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """
        Internal logging method with context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional log fields
        """
        log_record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.value),
            fn=None,
            lno=0,
            msg=message,
            args=(),
            exc_info=kwargs.get('exc_info')
        )
        
        # Add context to record
        log_record.context = self.context
        
        # Add duration if provided
        if 'duration_ms' in kwargs:
            log_record.duration_ms = kwargs['duration_ms']
        
        # Add any extra fields
        for key, value in kwargs.items():
            if key not in ['exc_info', 'duration_ms']:
                setattr(log_record, key, value)
        
        self.logger.handle(log_record)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with context and traceback."""
        kwargs['exc_info'] = True
        self._log(LogLevel.ERROR, message, **kwargs)


class PerformanceLogger:
    """
    Logger for performance monitoring and timing.
    
    Tracks operation durations and provides performance metrics logging.
    """
    
    def __init__(self, logger: ContextualLogger):
        """
        Initialize performance logger.
        
        Args:
            logger: Contextual logger to use for performance logging
        """
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str):
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation to time
        """
        import time
        self._start_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str, **kwargs):
        """
        End timing an operation and log performance.
        
        Args:
            operation_name: Name of the operation
            **kwargs: Additional context for the log
        """
        import time
        
        if operation_name not in self._start_times:
            self.logger.warning(f"Operation '{operation_name}' was not started")
            return
        
        duration_ms = (time.time() - self._start_times[operation_name]) * 1000
        del self._start_times[operation_name]
        
        self.logger.info(
            f"Operation '{operation_name}' completed",
            operation=operation_name,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def time_operation(self, operation_name: str):
        """
        Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Context manager for timing
        """
        from contextlib import contextmanager
        
        @contextmanager
        def timer():
            self.start_operation(operation_name)
            try:
                yield
            finally:
                self.end_operation(operation_name)
        
        return timer()


def setup_structured_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_output: bool = True,
    console_output: bool = True
) -> None:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_output: Whether to use JSON formatting
        console_output: Whether to output to console
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if json_output:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str, context: Optional[LogContext] = None) -> ContextualLogger:
    """
    Get a contextual logger for a component.
    
    Args:
        name: Logger name
        context: Optional initial context
        
    Returns:
        ContextualLogger instance
    """
    return ContextualLogger(name, context)