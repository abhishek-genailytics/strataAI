"""
Analytics logger service for writing api_requests table entries.
Provides centralized logging for API usage, costs, and session analytics.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from ..utils.supabase_client import supabase_service


class AnalyticsLogger:
    """Service for logging API requests to the api_requests table for analytics and cost tracking."""
    
    @staticmethod
    async def log_request(
        organization_id: UUID,
        user_id: UUID,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        duration_ms: Optional[int] = None,
        provider_id: Optional[UUID] = None,
        model_id: Optional[str] = None,
        provider_request_id: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: Optional[int] = None,
        cost: Optional[Decimal] = None,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Log an API request to the api_requests table for analytics and cost tracking.
        
        Args:
            organization_id: Organization making the request
            user_id: User making the request
            endpoint: API endpoint (e.g., "/v1/chat/completions")
            method: HTTP method (default: "POST")
            status_code: HTTP status code (default: 200)
            duration_ms: Request duration in milliseconds
            provider_id: AI provider UUID (for provider-specific analytics)
            model_id: Model identifier (e.g., "openai/gpt-4o-mini")
            provider_request_id: Provider's request ID for debugging
            prompt_tokens: Input token count
            completion_tokens: Output token count
            total_tokens: Total tokens (calculated if not provided)
            cost: Request cost in USD (as Decimal for precision)
            currency: Currency code (default: "USD")
            metadata: Additional metadata (e.g., {"session_id": "<UUID>"})
            
        Returns:
            Request ID if successful, None if failed
        """
        try:
            # Calculate total tokens if not provided
            if total_tokens is None:
                total_tokens = prompt_tokens + completion_tokens
            
            # Convert cost to float for database storage
            cost_float = float(cost) if cost is not None else None
            
            # Prepare insert data with required fields
            insert_data = {
                "organization_id": str(organization_id),
                "user_id": str(user_id),
                "api_key_id": str(organization_id),  # Use org_id as placeholder for required field
                "model_name": model_id or "unknown",  # Use model_id or default
                "status_code": status_code,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "currency": currency,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add optional fields if provided
            if duration_ms is not None:
                insert_data["latency_ms"] = duration_ms
            if provider_id is not None:
                insert_data["provider_id"] = str(provider_id)
            if model_id is not None:
                insert_data["model_id"] = model_id
            if provider_request_id is not None:
                insert_data["provider_request_id"] = provider_request_id
            if cost_float is not None:
                insert_data["cost"] = cost_float
            if metadata is not None:
                insert_data["metadata"] = metadata
            
            # Insert to api_requests table
            result = supabase_service.table("api_requests").insert(insert_data).execute()
            
            if result.data:
                return result.data[0].get("id")
            return None
            
        except Exception as e:
            # Don't fail the request if analytics logging fails
            # Could add logging here if needed
            return None
    
    @staticmethod
    async def log_playground_request(
        organization_id: UUID,
        user_id: UUID,
        session_id: UUID,
        model_id: str,
        provider_id: Optional[UUID] = None,
        provider_request_id: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: Optional[Decimal] = None,
        duration_ms: Optional[int] = None,
        status_code: int = 200
    ) -> Optional[str]:
        """
        Convenience method for logging playground chat completion requests.
        
        Args:
            organization_id: Organization making the request
            user_id: User making the request
            session_id: Playground session ID (stored in metadata)
            model_id: Model identifier (e.g., "openai/gpt-4o-mini")
            provider_id: AI provider UUID
            provider_request_id: Provider's request ID
            prompt_tokens: Input token count
            completion_tokens: Output token count
            cost: Request cost in USD
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code (default: 200)
            
        Returns:
            Request ID if successful, None if failed
        """
        metadata = {
            "session_id": str(session_id),
            "provider_request_id": provider_request_id
        }
        
        return await AnalyticsLogger.log_request(
            organization_id=organization_id,
            user_id=user_id,
            endpoint="/v1/chat/completions",
            method="POST",
            status_code=status_code,
            duration_ms=duration_ms,
            provider_id=provider_id,
            model_id=model_id,
            provider_request_id=provider_request_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            metadata=metadata
        )
    
    @staticmethod
    async def calculate_model_cost(
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Optional[Decimal]:
        """
        Calculate cost for a model based on current pricing.
        
        Args:
            model_name: Model name (e.g., "gpt-4o-mini")
            prompt_tokens: Input token count
            completion_tokens: Output token count
            
        Returns:
            Total cost as Decimal, or None if pricing not found
        """
        try:
            # Get current model pricing
            pricing_result = supabase_service.table("model_pricing").select(
                "pricing_type, price_per_unit"
            ).eq("model_name", model_name).is_("effective_until", None).execute()
            
            if not pricing_result.data:
                return None
            
            total_cost = Decimal("0")
            
            for pricing in pricing_result.data:
                price_per_unit = Decimal(str(pricing["price_per_unit"]))
                
                if pricing["pricing_type"] == "input":
                    # Price is typically per 1K tokens
                    total_cost += (Decimal(prompt_tokens) / 1000) * price_per_unit
                elif pricing["pricing_type"] == "output":
                    total_cost += (Decimal(completion_tokens) / 1000) * price_per_unit
            
            return total_cost
            
        except Exception:
            return None
