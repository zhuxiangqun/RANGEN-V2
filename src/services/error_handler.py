"""
Global Error Handler - Now integrated with unified error handling system
"""
from typing import Dict, Any, Optional
from src.services.logging_service import get_logger
from src.utils.error_handler import ErrorManager, ErrorCategory, ErrorLevel, handle_error

logger = get_logger(__name__)

class ErrorHandler:
    """Legacy error handler - now delegates to unified ErrorManager"""
    
    @staticmethod
    def handle_error(error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Standardized error handling logic - now using unified ErrorManager.
        """
        # Delegate to unified error manager
        error_event = handle_error(
            error=error,
            category=ErrorCategory.UNKNOWN,
            level=ErrorLevel.MEDIUM,
            context=context or {}
        )
        
        return {
            "error": True,
            "message": error_event.message,
            "type": type(error).__name__ if error_event.exception else "string_error",
            "error_id": error_event.error_id,
            "category": error_event.category.value,
            "level": error_event.level.name
        }
    
    @staticmethod
    def get_error_manager() -> ErrorManager:
        """Get the unified error manager instance"""
        return ErrorManager()
