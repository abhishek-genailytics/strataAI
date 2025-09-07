from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from supabase import Client

from app.models.playground_usage import (
    SessionTotals,
    SessionBreakdownItem,
    SessionUsageResponse,
    SessionSeriesPoint
)
from app.models.playground_hud import HudRecentItem
from app.utils.microcache import usage_cache


class PlaygroundUsageService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def get_session_usage(
        self,
        session_id: str,
        window: str = "all",
        include_breakdown: bool = True
    ) -> SessionUsageResponse:
        """Get usage totals and breakdown for a session."""
        
        # Check cache first
        cache_key = f"usage:{session_id}:{window}:{include_breakdown}"
        cached_result = usage_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Calculate time window
        from_time, to_time = self._get_time_window(window, session_id)
        
        # Get totals
        totals = await self._get_session_totals(session_id, from_time, to_time)
        
        # Get breakdown if requested
        breakdown = []
        if include_breakdown:
            breakdown = await self._get_session_breakdown(session_id, from_time, to_time)
        
        result = SessionUsageResponse(
            session_id=session_id,
            window=window,
            totals=totals,
            breakdown=breakdown,
            generated_at=datetime.utcnow()
        )
        
        # Cache the result
        usage_cache.set(cache_key, result, ttl=30)
        return result
    
    async def get_session_usage_series(
        self,
        session_id: str,
        bucket: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[SessionSeriesPoint]:
        """Get usage series data for charting."""
        
        # Default to session lifetime if no time bounds provided
        if not since or not until:
            session_bounds = await self._get_session_time_bounds(session_id)
            since = since or session_bounds["created_at"]
            until = until or session_bounds["updated_at"]
        
        # Check cache
        cache_key = f"series:{session_id}:{bucket}:{since.isoformat()}:{until.isoformat()}"
        cached_result = usage_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get series data
        series_data = await self._get_usage_series(session_id, bucket, since, until)
        
        # Cache the result
        usage_cache.set(cache_key, series_data, ttl=30)
        return series_data
    
    async def _get_session_totals(
        self,
        session_id: str,
        from_time: Optional[datetime],
        to_time: Optional[datetime]
    ) -> SessionTotals:
        """Get aggregated totals for a session."""
        
        query = self.supabase.table("api_requests").select(
            "prompt_tokens, completion_tokens, total_tokens, cost, currency"
        ).eq("metadata->>session_id", session_id).gte("status_code", 200).lte("status_code", 299)
        
        if from_time:
            query = query.gte("created_at", from_time.isoformat())
        if to_time:
            query = query.lte("created_at", to_time.isoformat())
        
        response = query.execute()
        
        if not response.data:
            return SessionTotals(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                cost=Decimal("0"),
                currency="USD",
                request_count=0
            )
        
        # Aggregate the results
        prompt_tokens = sum(row.get("prompt_tokens", 0) or 0 for row in response.data)
        completion_tokens = sum(row.get("completion_tokens", 0) or 0 for row in response.data)
        total_tokens = sum(row.get("total_tokens", 0) or 0 for row in response.data)
        cost = sum(Decimal(str(row.get("cost", 0) or 0)) for row in response.data)
        currency = response.data[0].get("currency", "USD") if response.data else "USD"
        request_count = len(response.data)
        
        return SessionTotals(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            currency=currency,
            request_count=request_count
        )
    
    async def _get_session_breakdown(
        self,
        session_id: str,
        from_time: Optional[datetime],
        to_time: Optional[datetime]
    ) -> List[SessionBreakdownItem]:
        """Get per-provider/model breakdown for a session."""
        
        # First get the raw aggregated data
        query = self.supabase.table("api_requests").select(
            "model_id, provider_id, prompt_tokens, completion_tokens, total_tokens, cost"
        ).eq("metadata->>session_id", session_id).gte("status_code", 200).lte("status_code", 299)
        
        if from_time:
            query = query.gte("created_at", from_time.isoformat())
        if to_time:
            query = query.lte("created_at", to_time.isoformat())
        
        response = query.execute()
        
        if not response.data:
            return []
        
        # Group by model_id and provider_id
        grouped = {}
        for row in response.data:
            key = (row.get("provider_id"), row.get("model_id"))
            if key not in grouped:
                grouped[key] = {
                    "requests": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": Decimal("0")
                }
            
            grouped[key]["requests"] += 1
            grouped[key]["prompt_tokens"] += row.get("prompt_tokens", 0) or 0
            grouped[key]["completion_tokens"] += row.get("completion_tokens", 0) or 0
            grouped[key]["total_tokens"] += row.get("total_tokens", 0) or 0
            grouped[key]["cost"] += Decimal(str(row.get("cost", 0) or 0))
        
        # Get provider and model names
        breakdown = []
        for (provider_id, model_id), stats in grouped.items():
            # Get provider name
            provider_response = self.supabase.table("ai_providers").select("name").eq("id", provider_id).single().execute()
            provider_name = provider_response.data.get("name", "unknown") if provider_response.data else "unknown"
            
            # Get model name
            model_response = self.supabase.table("ai_models").select("model_name").eq("id", model_id).single().execute()
            model_name = model_response.data.get("model_name", "unknown") if model_response.data else "unknown"
            
            breakdown.append(SessionBreakdownItem(
                provider=provider_name,
                model=model_name,
                requests=stats["requests"],
                prompt_tokens=stats["prompt_tokens"],
                completion_tokens=stats["completion_tokens"],
                total_tokens=stats["total_tokens"],
                cost=stats["cost"]
            ))
        
        # Sort by cost descending
        breakdown.sort(key=lambda x: x.cost, reverse=True)
        return breakdown
    
    async def _get_usage_series(
        self,
        session_id: str,
        bucket: str,
        since: datetime,
        until: datetime
    ) -> List[SessionSeriesPoint]:
        """Get time series data for usage charts."""
        
        # Get raw data first
        query = self.supabase.table("api_requests").select(
            "created_at, total_tokens, cost"
        ).eq("metadata->>session_id", session_id).gte("status_code", 200).lte("status_code", 299).gte(
            "created_at", since.isoformat()
        ).lte("created_at", until.isoformat()).order("created_at")
        
        response = query.execute()
        
        if not response.data:
            return []
        
        # Group by time bucket
        series_data = {}
        for row in response.data:
            created_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            
            # Calculate bucket start time
            if bucket == "hour":
                bucket_start = created_at.replace(minute=0, second=0, microsecond=0)
            else:  # day
                bucket_start = created_at.replace(hour=0, minute=0, second=0, microsecond=0)
            
            bucket_key = bucket_start.isoformat()
            
            if bucket_key not in series_data:
                series_data[bucket_key] = {
                    "period_start": bucket_start,
                    "request_count": 0,
                    "total_tokens": 0,
                    "cost": Decimal("0")
                }
            
            series_data[bucket_key]["request_count"] += 1
            series_data[bucket_key]["total_tokens"] += row.get("total_tokens", 0) or 0
            series_data[bucket_key]["cost"] += Decimal(str(row.get("cost", 0) or 0))
        
        # Convert to list and sort by time
        series = []
        for data in series_data.values():
            series.append(SessionSeriesPoint(
                period_start=data["period_start"],
                request_count=data["request_count"],
                total_tokens=data["total_tokens"],
                cost=data["cost"]
            ))
        
        series.sort(key=lambda x: x.period_start)
        return series
    
    async def get_recent_requests(
        self,
        session_id: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        limit: int = 10
    ) -> List[HudRecentItem]:
        """Get recent API requests for a session."""
        
        # Validate limit
        if limit > 50:
            limit = 50
        
        query = self.supabase.table("api_requests").select(
            "id, created_at, status_code, latency_ms, provider_id, model_id, "
            "prompt_tokens, completion_tokens, total_tokens, cost, currency, metadata"
        ).eq("metadata->>session_id", session_id)
        
        if from_time:
            query = query.gte("created_at", from_time.isoformat())
        if to_time:
            query = query.lte("created_at", to_time.isoformat())
        
        response = query.order("created_at", desc=True).limit(limit).execute()
        
        if not response.data:
            return []
        
        # Build provider and model name maps for efficiency
        provider_ids = set(row.get("provider_id") for row in response.data if row.get("provider_id"))
        model_ids = set(row.get("model_id") for row in response.data if row.get("model_id"))
        
        provider_map = {}
        if provider_ids:
            provider_response = self.supabase.table("ai_providers").select("id, name").in_("id", list(provider_ids)).execute()
            provider_map = {p["id"]: p["name"] for p in provider_response.data}
        
        model_map = {}
        if model_ids:
            model_response = self.supabase.table("ai_models").select("id, model_name").in_("id", list(model_ids)).execute()
            model_map = {m["id"]: m["model_name"] for m in model_response.data}
        
        # Convert to HudRecentItem objects
        recent_items = []
        for row in response.data:
            provider_name = provider_map.get(row.get("provider_id"), "unknown")
            model_name = model_map.get(row.get("model_id"), "unknown")
            
            # Extract provider_request_id from metadata
            metadata = row.get("metadata", {}) or {}
            provider_request_id = metadata.get("provider_request_id")
            
            recent_items.append(HudRecentItem(
                id=row["id"],
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                status_code=row.get("status_code", 0),
                duration_ms=row.get("latency_ms", 0),
                provider=provider_name,
                model=model_name,
                prompt_tokens=row.get("prompt_tokens", 0) or 0,
                completion_tokens=row.get("completion_tokens", 0) or 0,
                total_tokens=row.get("total_tokens", 0) or 0,
                cost=Decimal(str(row.get("cost", 0) or 0)),
                provider_request_id=provider_request_id
            ))
        
        return recent_items
    
    async def _get_session_time_bounds(self, session_id: str) -> dict:
        """Get session creation and last update times."""
        
        response = self.supabase.table("chat_sessions").select(
            "created_at, updated_at"
        ).eq("id", session_id).single().execute()
        
        if not response.data:
            raise ValueError(f"Session {session_id} not found")
        
        return {
            "created_at": datetime.fromisoformat(response.data["created_at"].replace("Z", "+00:00")),
            "updated_at": datetime.fromisoformat(response.data["updated_at"].replace("Z", "+00:00"))
        }
    
    def _get_time_window(self, window: str, session_id: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Calculate time window bounds based on window parameter."""
        
        if window == "all":
            return None, None
        
        now = datetime.utcnow()
        
        if window == "24h":
            return now - timedelta(hours=24), now
        elif window == "7d":
            return now - timedelta(days=7), now
        elif window == "30d":
            return now - timedelta(days=30), now
        else:
            # Default to all if unknown window
            return None, None
