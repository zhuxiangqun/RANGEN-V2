"""
Unified Error Handling System
=============================
Centralized error handling for RANGEN V2.
Provides consistent error handling across all modules.

This module consolidates error handling from:
- src/utils/error_handler.py
- src/services/error_handler.py
- src/core/langgraph_error_handler.py

Usage:
    from src.utils.unified_errors import handle_error, RangenError, ErrorCode
    
    try:
        risky_operation()
    except RangenError as e:
        handle_error(e, context={"operation": "risky_operation"})
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import logging
import uuid

# Import existing error manager if available
try:
    from src.utils.error_handler import ErrorManager, ErrorCategory, ErrorLevel
    _HAS_ERROR_MANAGER = True
except ImportError:
    _HAS_ERROR_MANAGER = False


logger = logging.getLogger(__name__)


# Error Codes
class ErrorCode(Enum):
    """RANGEN Error Codes"""
    # General
    UNKNOWN = "UNKNOWN"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    TIMEOUT = "TIMEOUT"
    
    # Agent
    AGENT_INIT_FAILED = "AGENT_INIT_FAILED"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    
    # RAG/Retrieval
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    KNOWLEDGE_BASE_ERROR = "KNOWLEDGE_BASE_ERROR"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    
    # LLM
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RESPONSE_INVALID = "LLM_RESPONSE_INVALID"
    
    # Config
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # Workspace
    WORKSPACE_INIT_FAILED = "WORKSPACE_INIT_FAILED"
    WORKSPACE_CLEANUP_FAILED = "WORKSPACE_CLEANUP_FAILED"
    
    # Security
    AUTH_FAILED = "AUTH_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


# Error Severity
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RangenError(Exception):
    """Base exception for RANGEN"""
    message: str
    code: ErrorCode = ErrorCode.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __str__(self):
        return f"[{self.code.value}] {self.message} (ID: {self.error_id})"


# Specific Exceptions
class AgentError(RangenError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.AGENT_EXECUTION_FAILED, **kwargs)


class RetrievalError(RangenError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.RETRIEVAL_FAILED, **kwargs)


class LLMError(RangenError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.LLM_API_ERROR, **kwargs)


class ConfigError(RangenError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.CONFIG_INVALID, **kwargs)


class WorkspaceError(RangenError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.WORKSPACE_INIT_FAILED, **kwargs)


# Error Handler
class UnifiedErrorHandler:
    """
    Centralized error handler for RANGEN.
    Provides consistent error handling, logging, and recovery.
    """
    
    def __init__(self):
        self._errors: List[Dict[str, Any]] = []
        self._error_manager = None
        
        if _HAS_ERROR_MANAGER:
            try:
                self._error_manager = ErrorManager()
            except Exception:
                pass
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> Dict[str, Any]:
        """Handle an error and return error info."""
        
        error_info = {
            "error_id": str(uuid.uuid4())[:8],
            "type": type(error).__name__,
            "message": str(error),
            "severity": severity.value,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc()
        }
        
        # Store error
        self._errors.append(error_info)
        
        # Log error
        log_level = {
            ErrorSeverity.LOW: logging.WARNING,
            ErrorSeverity.MEDIUM: logging.ERROR,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"[{error_info['error_id']}] {error_info['type']}: {error_info['message']}",
            extra={"context": context}
        )
        
        # Delegate to existing error manager if available
        if self._error_manager:
            try:
                self._error_manager.handle_error(error, context or {})
            except Exception:
                pass
        
        return error_info
    
    def get_errors(
        self,
        limit: int = 100,
        severity: Optional[ErrorSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Get recent errors."""
        errors = self._errors[-limit:]
        
        if severity:
            errors = [e for e in errors if e["severity"] == severity.value]
        
        return errors
    
    def clear_errors(self):
        """Clear error history."""
        self._errors.clear()


# Global handler instance
_error_handler: Optional[UnifiedErrorHandler] = None


def get_error_handler() -> UnifiedErrorHandler:
    """Get global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = UnifiedErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
) -> Dict[str, Any]:
    """Convenience function to handle errors."""
    return get_error_handler().handle_error(error, context, severity)


def rangen_error(code: ErrorCode, message: str, **kwargs) -> RangenError:
    """Convenience function to create RANGEN errors."""
    return RangenError(message=message, code=code, **kwargs)


# Export all error types
__all__ = [
    'ErrorCode',
    'ErrorSeverity', 
    'RangenError',
    'AgentError',
    'RetrievalError',
    'LLMError',
    'ConfigError',
    'WorkspaceError',
    'UnifiedErrorHandler',
    'get_error_handler',
    'handle_error',
    'rangen_error',
]
