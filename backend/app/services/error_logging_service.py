"""
Error logging and monitoring service.
"""
import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import uuid4

from fastapi import Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.exceptions import StrataAIException
from ..models.error_response import ErrorType, ErrorSeverity


logger = logging.getLogger(__name__)


class ErrorLoggingService:
    """Service for logging and monitoring application errors."""
    
    def __init__(self):
        self.logger = logging.getLogger("strata_ai.errors")
    
    async def log_error(
        self,
        error: StrataAIException,
        request: Request,
        request_id: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Log a StrataAI application error."""
        
        error_log_id = str(uuid4())
        
        # Extract user ID from request if not provided
        if not user_id and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        # Create error log entry
        error_data = {
            "error_log_id": error_log_id,
            "request_id": request_id,
            "user_id": user_id,
            "error_type": error.error_type,
            "error_code": error.error_code,
            "message": error.message,
            "severity": error.severity,
            "timestamp": datetime.utcnow().isoformat(),
            "request_method": request.method,
            "request_url": str(request.url),
            "request_path": request.url.path,
            "user_agent": getattr(request.state, "user_agent", None),
            "client_ip": getattr(request.state, "client_ip", None),
            "details": [detail.dict() for detail in error.details] if error.details else None,
        }
        
        # Log to structured logger
        self.logger.error(
            f"Application error: {error.message}",
            extra={k: v for k, v in error_data.items() if k != 'message'}
        )
        
        # Store in database for monitoring
        await self._store_error_log(error_data)
        
        # Send alerts for high severity errors
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            await self._send_error_alert(error_data)
        
        return error_log_id
    
    async def log_validation_error(
        self,
        validation_error: ValidationError,
        request: Request,
        request_id: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Log a validation error."""
        
        error_log_id = str(uuid4())
        
        # Extract user ID from request if not provided
        if not user_id and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        # Convert validation errors to structured format
        validation_details = []
        for error in validation_error.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            validation_details.append({
                "field": field_path,
                "message": error["msg"],
                "code": error["type"],
                "value": error.get("input"),
            })
        
        error_data = {
            "error_log_id": error_log_id,
            "request_id": request_id,
            "user_id": user_id,
            "error_type": ErrorType.VALIDATION_ERROR,
            "error_code": "VALIDATION_FAILED",
            "message": "Request validation failed",
            "severity": ErrorSeverity.LOW,
            "timestamp": datetime.utcnow().isoformat(),
            "request_method": request.method,
            "request_url": str(request.url),
            "request_path": request.url.path,
            "user_agent": getattr(request.state, "user_agent", None),
            "client_ip": getattr(request.state, "client_ip", None),
            "details": validation_details,
        }
        
        # Log to structured logger
        self.logger.warning(
            f"Validation error: {len(validation_details)} field(s) failed validation",
            extra={k: v for k, v in error_data.items() if k != 'message'}
        )
        
        # Store in database
        await self._store_error_log(error_data)
        
        return error_log_id
    
    async def log_unexpected_error(
        self,
        error: Exception,
        request: Request,
        request_id: str,
        traceback_str: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Log an unexpected error with full traceback."""
        
        error_log_id = str(uuid4())
        
        # Extract user ID from request if not provided
        if not user_id and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        error_data = {
            "error_log_id": error_log_id,
            "request_id": request_id,
            "user_id": user_id,
            "error_type": ErrorType.INTERNAL_ERROR,
            "error_code": "UNEXPECTED_ERROR",
            "message": str(error),
            "severity": ErrorSeverity.CRITICAL,
            "timestamp": datetime.utcnow().isoformat(),
            "request_method": request.method,
            "request_url": str(request.url),
            "request_path": request.url.path,
            "user_agent": getattr(request.state, "user_agent", None),
            "client_ip": getattr(request.state, "client_ip", None),
            "exception_type": type(error).__name__,
            "traceback": traceback_str,
        }
        
        # Log to structured logger
        self.logger.critical(
            f"Unexpected error: {str(error)}",
            extra={k: v for k, v in error_data.items() if k != 'message'}
        )
        
        # Store in database
        await self._store_error_log(error_data)
        
        # Always send alerts for unexpected errors
        await self._send_error_alert(error_data)
        
        return error_log_id
    
    async def get_error_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        error_type: Optional[ErrorType] = None,
    ) -> Dict[str, Any]:
        """Get error statistics for monitoring dashboard."""
        
        # This would typically query the database
        # For now, return mock statistics
        return {
            "total_errors": 0,
            "error_rate": 0.0,
            "errors_by_type": {},
            "errors_by_severity": {},
            "top_error_paths": [],
            "error_trend": [],
        }
    
    async def _store_error_log(self, error_data: Dict[str, Any]) -> None:
        """Store error log in database."""
        try:
            # In a real implementation, this would store to Supabase
            # For now, we'll just log the structured data
            logger.info(f"Storing error log: {error_data['error_log_id']}")
            
        except Exception as e:
            # Don't let error logging failures break the application
            logger.error(f"Failed to store error log: {str(e)}")
    
    async def _send_error_alert(self, error_data: Dict[str, Any]) -> None:
        """Send error alert for high severity errors."""
        try:
            # In a real implementation, this would send alerts via email, Slack, etc.
            logger.warning(
                f"High severity error alert: {error_data['error_type']} - {error_data['message']}"
            )
            
        except Exception as e:
            # Don't let alerting failures break the application
            logger.error(f"Failed to send error alert: {str(e)}")


# Global error logging service instance
error_logging_service = ErrorLoggingService()
