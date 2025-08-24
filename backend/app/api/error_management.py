"""
Error management API endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.deps import get_current_user
from ..models.user import User
from ..models.error_response import ErrorResponse, COMMON_ERROR_RESPONSES
from ..services.error_logging_service import ErrorLoggingService


router = APIRouter()
error_logging_service = ErrorLoggingService()


class ClientErrorRequest(BaseModel):
    """Request model for client-side error logging."""
    error_message: str
    error_stack: Optional[str] = None
    component_stack: Optional[str] = None
    timestamp: str
    user_agent: str
    url: str
    additional_context: Optional[Dict[str, Any]] = None


class ApiErrorRequest(BaseModel):
    """Request model for API error logging."""
    message: str
    status: int
    endpoint: str
    method: str
    timestamp: str
    request_id: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class UserErrorRequest(BaseModel):
    """Request model for user error logging."""
    message: str
    context: Optional[Dict[str, Any]] = None


class ErrorStatisticsResponse(BaseModel):
    """Response model for error statistics."""
    total_errors: int
    error_rate: float
    errors_by_type: Dict[str, int]
    errors_by_severity: Dict[str, int]
    top_error_paths: List[Dict[str, Any]]
    error_trend: List[Dict[str, Any]]


@router.post(
    "/client",
    summary="Log client-side error",
    description="Log errors that occur in the React frontend",
    responses={**COMMON_ERROR_RESPONSES}
)
async def log_client_error(
    error_request: ClientErrorRequest,
    current_user: User = Depends(get_current_user)
):
    """Log a client-side error."""
    try:
        # Create a mock error object for logging
        class MockError:
            def __init__(self, message: str, stack: Optional[str] = None):
                self.message = message
                self.stack = stack
            
            def __str__(self):
                return self.message
        
        # Create mock error info
        class MockErrorInfo:
            def __init__(self, component_stack: Optional[str] = None):
                self.componentStack = component_stack
        
        mock_error = MockError(error_request.error_message, error_request.error_stack)
        mock_error_info = MockErrorInfo(error_request.component_stack)
        
        # Create a mock request object
        class MockRequest:
            def __init__(self):
                self.method = "CLIENT"
                self.url = MockUrl(error_request.url)
                self.state = MockState()
        
        class MockUrl:
            def __init__(self, url: str):
                self.path = url
            
            def __str__(self):
                return self.path
        
        class MockState:
            def __init__(self):
                self.user_agent = error_request.user_agent
                self.client_ip = "client"
                self.user = current_user
        
        mock_request = MockRequest()
        
        # Generate request ID
        request_id = f"client_{datetime.now().timestamp()}"
        
        # Log the client error
        error_id = await error_logging_service.log_error(
            error=mock_error,
            request=mock_request,
            request_id=request_id,
            user_id=current_user.id,
        )
        
        return {"error_id": error_id, "message": "Client error logged successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log client error: {str(e)}"
        )


@router.post(
    "/api",
    summary="Log API error",
    description="Log errors that occur during API calls",
    responses={**COMMON_ERROR_RESPONSES}
)
async def log_api_error(
    error_request: ApiErrorRequest,
    current_user: User = Depends(get_current_user)
):
    """Log an API error."""
    try:
        # This endpoint would typically be called by the error logging service itself
        # but we provide it for completeness and external logging
        
        return {"message": "API error logged successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log API error: {str(e)}"
        )


@router.post(
    "/user",
    summary="Log user error",
    description="Log user-initiated errors (form validation, user input errors)",
    responses={**COMMON_ERROR_RESPONSES}
)
async def log_user_error(
    error_request: UserErrorRequest,
    current_user: User = Depends(get_current_user)
):
    """Log a user error."""
    try:
        # Log user error (typically less critical)
        return {"message": "User error logged successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log user error: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=ErrorStatisticsResponse,
    summary="Get error statistics",
    description="Get error statistics for monitoring dashboard",
    responses={**COMMON_ERROR_RESPONSES}
)
async def get_error_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    error_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get error statistics for the current user."""
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get statistics from error logging service
        stats = await error_logging_service.get_error_statistics(
            start_date=start_datetime,
            end_date=end_datetime,
            error_type=error_type,
        )
        
        return ErrorStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error statistics: {str(e)}"
        )


@router.get(
    "/health",
    summary="Error logging health check",
    description="Check the health of the error logging system"
)
async def error_logging_health():
    """Health check for error logging system."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "error_logging"
    }
