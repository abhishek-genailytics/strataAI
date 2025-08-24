import json
import time
from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.database import get_db
from ..models import APIRequestCreate
from ..services.api_request_service import api_request_service
from ..services.cost_calculation_service import cost_calculation_service
from ..services.usage_tracking_service import usage_tracking_service


class UsageLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and track usage metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logged_paths = {
            "/chat/completions",
            "/chat/completions/stream"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only log specific API endpoints
        if not any(request.url.path.startswith(path) for path in self.logged_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request data
        request_body = None
        try:
            body = await request.body()
            if body:
                request_body = json.loads(body.decode())
        except Exception:
            request_body = None
        
        # Get user context from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        project_id = getattr(request.state, 'project_id', None)
        api_key_id = getattr(request.state, 'api_key_id', None)
        
        # Process the request
        response = await call_next(request)
        
        # Calculate latency
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        # Extract response data
        response_body = None
        if hasattr(response, 'body'):
            try:
                response_body = json.loads(response.body.decode())
            except Exception:
                response_body = None
        
        # Log the request if we have user context
        if user_id and project_id and api_key_id:
            await self._log_request(
                user_id=user_id,
                project_id=project_id,
                api_key_id=api_key_id,
                request_body=request_body,
                response_body=response_body,
                status_code=response.status_code,
                latency_ms=latency_ms
            )
        
        return response
    
    async def _log_request(
        self,
        user_id: UUID,
        project_id: UUID,
        api_key_id: UUID,
        request_body: Optional[dict],
        response_body: Optional[dict],
        status_code: int,
        latency_ms: int
    ):
        """Log the API request and update usage metrics."""
        try:
            async for db in get_db():
                # Extract model and token information
                model_name = "unknown"
                input_tokens = 0
                output_tokens = 0
                provider_id = None
                error_message = None
                
                if request_body:
                    model_name = request_body.get("model", "unknown")
                
                if response_body:
                    usage = response_body.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    
                    if "error" in response_body:
                        error_message = response_body["error"].get("message", "Unknown error")
                
                # Determine provider from model name
                provider_id = await self._get_provider_id_from_model(db, model_name)
                
                if not provider_id:
                    # Skip logging if we can't determine provider
                    return
                
                # Calculate cost
                cost_usd = await cost_calculation_service.calculate_cost(
                    db=db,
                    provider_id=provider_id,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
                
                # Create API request log
                api_request_data = APIRequestCreate(
                    user_id=user_id,
                    project_id=project_id,
                    api_key_id=api_key_id,
                    provider_id=provider_id,
                    model_name=model_name,
                    request_payload=self._sanitize_payload(request_body),
                    response_payload=self._sanitize_payload(response_body),
                    status_code=status_code,
                    error_message=error_message,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms
                )
                
                # Save API request
                await api_request_service.create(db, obj_in=api_request_data)
                
                # Update usage metrics
                is_successful = 200 <= status_code < 300
                await usage_tracking_service.update_usage_metrics(
                    db=db,
                    user_id=user_id,
                    project_id=project_id,
                    provider_id=provider_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    is_successful=is_successful
                )
                
                await db.commit()
                break
                
        except Exception as e:
            # Log error but don't break the request flow
            print(f"Error logging request: {e}")
    
    async def _get_provider_id_from_model(self, db, model_name: str) -> Optional[UUID]:
        """Determine provider ID from model name."""
        from sqlalchemy import select
        from ..models import AIProvider
        
        # Simple model name to provider mapping
        if model_name.startswith("gpt"):
            provider_name = "openai"
        elif model_name.startswith("claude"):
            provider_name = "anthropic"
        else:
            return None
        
        result = await db.execute(
            select(AIProvider.id).where(AIProvider.name == provider_name)
        )
        row = result.first()
        return row[0] if row else None
    
    def _sanitize_payload(self, payload: Optional[dict]) -> Optional[dict]:
        """Remove sensitive information from payload before logging."""
        if not payload:
            return None
        
        # Create a copy to avoid modifying original
        sanitized = payload.copy()
        
        # Remove sensitive keys
        sensitive_keys = ["api_key", "authorization", "password", "token"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
        
        # Limit payload size to prevent database bloat
        payload_str = json.dumps(sanitized)
        if len(payload_str) > 10000:  # 10KB limit
            return {"truncated": True, "size": len(payload_str)}
        
        return sanitized
