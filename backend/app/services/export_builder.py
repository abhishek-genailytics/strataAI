"""
Export builder service for PG-14 playground export functionality.
Generates cURL commands (unified/provider) and JSON transcripts with proper parameter merging.
"""
import json
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from ..models.openai_chat import ChatMessage
from ..models.playground_export import (
    ExportParams, TranscriptExport, TranscriptSession, TranscriptMessage,
    TranscriptUsage, TranscriptUsageTotals, TranscriptUsagePerMessage
)
from ..utils.supabase_client import get_supabase_user_client


class ExportBuilder:
    """Service for building export content (cURL commands and JSON transcripts)."""
    
    def __init__(self, jwt_token: Optional[str] = None):
        self.sb = get_supabase_user_client(jwt_token) if jwt_token else None
    
    def build_curl_unified(
        self,
        api_base: str,
        pat_placeholder: str,
        model_slash_id: str,
        messages: List[ChatMessage],
        params: ExportParams,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Build cURL command for unified API (/v1/chat/completions).
        
        Args:
            api_base: Base API URL (e.g., https://api.strataai.com)
            pat_placeholder: PAT token placeholder (e.g., $STRATA_PAT)
            model_slash_id: Model ID in provider/model format
            messages: Assembled messages array
            params: Merged parameters
            organization_id: Optional organization ID for X-Organization-ID header
            
        Returns:
            Ready-to-copy cURL command string
        """
        # Build request body
        body = {
            "model": model_slash_id,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": False
        }
        
        # Add non-None parameters
        body.update(params.to_openai_dict())
        
        # Build headers
        headers = [
            f'-H "Authorization: Bearer {pat_placeholder}"',
            '-H "Content-Type: application/json"'
        ]
        
        # Add organization header if provided
        if organization_id:
            headers.append(f'-H "X-Organization-ID: {organization_id}"')
        
        # Build cURL command
        headers_str = " \\\n  ".join(headers)
        body_json = json.dumps(body, separators=(",", ":"))
        
        return f"""curl -s {api_base}/v1/chat/completions \\
  {headers_str} \\
  -d '{body_json}'"""
    
    def build_curl_provider(
        self,
        provider: str,
        messages: List[ChatMessage],
        params: ExportParams,
        model_suffix: str,
        placeholders: Dict[str, str]
    ) -> str:
        """
        Build cURL command for native provider API.
        
        Args:
            provider: Provider name (openai/anthropic)
            messages: Assembled messages array
            params: Merged parameters
            model_suffix: Model name without provider prefix
            placeholders: API key placeholders by provider
            
        Returns:
            Ready-to-copy cURL command string
        """
        if provider.lower() == "openai":
            return self._build_openai_curl(messages, params, model_suffix, placeholders)
        elif provider.lower() == "anthropic":
            return self._build_anthropic_curl(messages, params, model_suffix, placeholders)
        else:
            raise ValueError(f"Unsupported provider for provider-cURL export: {provider}")
    
    def _build_openai_curl(
        self,
        messages: List[ChatMessage],
        params: ExportParams,
        model_suffix: str,
        placeholders: Dict[str, str]
    ) -> str:
        """Build OpenAI native cURL command."""
        body = {
            "model": model_suffix,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": False
        }
        
        # Add OpenAI-compatible parameters
        body.update(params.to_openai_dict())
        
        body_json = json.dumps(body, separators=(",", ":"))
        api_key_placeholder = placeholders.get("OPENAI", "$OPENAI_API_KEY")
        
        return f"""curl -s https://api.openai.com/v1/chat/completions \\
  -H "Authorization: Bearer {api_key_placeholder}" \\
  -H "Content-Type: application/json" \\
  -d '{body_json}'"""
    
    def _build_anthropic_curl(
        self,
        messages: List[ChatMessage],
        params: ExportParams,
        model_suffix: str,
        placeholders: Dict[str, str]
    ) -> str:
        """Build Anthropic native cURL command."""
        # Anthropic requires max_tokens and has different parameter names
        body = {
            "model": model_suffix,
            "max_tokens": params.max_tokens or 512,  # Required for Anthropic
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages]
        }
        
        # Add Anthropic-compatible parameters (excludes presence/frequency penalties)
        anthropic_params = params.to_anthropic_dict()
        body.update(anthropic_params)
        
        # Remove None values for cleanliness
        body = {k: v for k, v in body.items() if v is not None}
        
        body_json = json.dumps(body, separators=(",", ":"))
        api_key_placeholder = placeholders.get("ANTHROPIC", "$ANTHROPIC_API_KEY")
        
        return f"""curl -s https://api.anthropic.com/v1/messages \\
  -H "x-api-key: {api_key_placeholder}" \\
  -H "anthropic-version: 2023-06-01" \\
  -H "Content-Type: application/json" \\
  -d '{body_json}'"""
    
    async def build_json_transcript(
        self,
        session_id: UUID,
        user_id: UUID,
        messages: List[ChatMessage],
        limit_turns: Optional[int] = None,
        include_system: bool = True
    ) -> TranscriptExport:
        """
        Build JSON transcript export with session metadata and usage data.
        
        Args:
            session_id: Session UUID
            user_id: User UUID for ownership verification
            messages: Assembled messages for export
            limit_turns: Optional limit for message filtering
            include_system: Whether system messages are included
            
        Returns:
            Complete transcript export object
        """
        if not self.sb:
            raise ValueError("JWT token required for transcript generation")
        
        # Fetch session metadata
        session_data = await self._fetch_session_metadata(session_id, user_id)
        
        # Fetch messages from database (with usage data)
        db_messages = await self._fetch_messages_with_usage(
            session_id, limit_turns, include_system
        )
        
        # Fetch usage totals
        usage_data = await self._fetch_usage_totals(session_id)
        
        # Build transcript structure
        transcript = TranscriptExport(
            session=session_data,
            messages=db_messages,
            usage=usage_data
        )
        
        return transcript
    
    async def _fetch_session_metadata(self, session_id: UUID, user_id: UUID) -> TranscriptSession:
        """Fetch session metadata for transcript."""
        result = self.sb.table("chat_sessions").select(
            "id, title, provider_id, model_id, created_at, updated_at, metadata"
        ).eq("id", str(session_id)).eq("user_id", str(user_id)).execute()
        
        if not result.data:
            from ..errors.openai_envelope import session_not_found_error
            session_not_found_error(str(session_id))
        
        session_row = result.data[0]
        
        # Get provider and model names
        provider_result = self.sb.table("ai_providers").select(
            "name"
        ).eq("id", session_row["provider_id"]).execute()
        
        model_result = self.sb.table("ai_models").select(
            "name"
        ).eq("id", session_row["model_id"]).execute()
        
        provider_name = provider_result.data[0]["name"] if provider_result.data else "unknown"
        model_name = model_result.data[0]["name"] if model_result.data else "unknown"
        
        # Get system prompt
        from ..services.system_prompt_svc import SystemPromptService
        system_service = SystemPromptService(self.sb.auth.get_session().access_token)
        system_prompt = system_service.get(session_id)
        
        # Parse metadata for default params
        metadata = session_row.get("metadata", {}) or {}
        default_params = metadata.get("default_params", {})
        
        return TranscriptSession(
            id=UUID(session_row["id"]),
            title=session_row["title"] or f"{provider_name}/{model_name} Session",
            provider=provider_name,
            model=f"{provider_name}/{model_name}",
            created_at=datetime.fromisoformat(session_row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(session_row["updated_at"].replace("Z", "+00:00")),
            system=system_prompt,
            default_params=default_params
        )
    
    async def _fetch_messages_with_usage(
        self,
        session_id: UUID,
        limit_turns: Optional[int],
        include_system: bool
    ) -> List[TranscriptMessage]:
        """Fetch messages for transcript (respecting limit_turns)."""
        # Build query
        query = self.sb.table("chat_messages").select(
            "id, role, content, created_at"
        ).eq("session_id", str(session_id))
        
        if not include_system:
            query = query.neq("role", "system")
        
        query = query.order("created_at", desc=False).order("id", desc=False)
        
        # Apply limit if specified
        if limit_turns is not None:
            # For transcript, we want the last N turns, so we need to fetch all and slice
            query = query.limit(1000)  # Large limit, then slice in memory
        
        result = query.execute()
        rows = result.data or []
        
        # Apply limit_turns filtering
        if limit_turns is not None and limit_turns > 0:
            # Filter to user/assistant pairs, take last N pairs
            user_assistant_rows = [
                row for row in rows if row["role"] in ["user", "assistant"]
            ]
            if len(user_assistant_rows) > limit_turns * 2:
                user_assistant_rows = user_assistant_rows[-(limit_turns * 2):]
            
            # Add back system messages if include_system
            if include_system:
                system_rows = [row for row in rows if row["role"] == "system"]
                rows = system_rows + user_assistant_rows
            else:
                rows = user_assistant_rows
        
        # Convert to transcript messages
        messages = []
        for row in rows:
            created_at = row["created_at"]
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            
            messages.append(TranscriptMessage(
                id=UUID(row["id"]),
                role=row["role"],
                content=row["content"],
                created_at=created_at
            ))
        
        return messages
    
    async def _fetch_usage_totals(self, session_id: UUID) -> TranscriptUsage:
        """Fetch usage totals and per-message breakdown for transcript."""
        # Fetch per-message usage data
        per_message_usage = []
        
        # Get token usage for assistant messages in this session
        usage_result = self.sb.table("token_usage").select(
            "message_id, input_tokens, output_tokens, total_tokens"
        ).in_(
            "message_id",
            self.sb.table("chat_messages").select("id").eq("session_id", str(session_id)).eq("role", "assistant")
        ).execute()
        
        # Get cost data from api_requests for this session
        cost_result = self.sb.table("api_requests").select(
            "prompt_tokens, completion_tokens, total_cost"
        ).eq("metadata->>session_id", str(session_id)).eq("status_code", 200).execute()
        
        # Build per-message usage (simplified - we'll aggregate costs)
        total_cost = Decimal("0.00")
        for usage_row in usage_result.data or []:
            # For now, we'll distribute cost evenly across messages
            # In a real implementation, you'd want more precise cost tracking per message
            per_message_usage.append(TranscriptUsagePerMessage(
                message_id=UUID(usage_row["message_id"]),
                prompt_tokens=usage_row.get("input_tokens", 0) or 0,
                completion_tokens=usage_row.get("output_tokens", 0) or 0,
                total_tokens=usage_row.get("total_tokens", 0) or 0,
                cost=Decimal("0.00")  # Simplified for MVP
            ))
        
        # Calculate totals from api_requests
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        
        for cost_row in cost_result.data or []:
            total_prompt_tokens += cost_row.get("prompt_tokens", 0) or 0
            total_completion_tokens += cost_row.get("completion_tokens", 0) or 0
            total_cost += Decimal(str(cost_row.get("total_cost", 0) or 0))
        
        total_tokens = total_prompt_tokens + total_completion_tokens
        
        totals = TranscriptUsageTotals(
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            cost=total_cost,
            currency="USD"
        )
        
        return TranscriptUsage(
            totals=totals,
            per_message=per_message_usage
        )
    
    def get_api_key_placeholders(self) -> Dict[str, str]:
        """Get standard API key placeholders for cURL generation."""
        return {
            "OPENAI": "$OPENAI_API_KEY",
            "ANTHROPIC": "$ANTHROPIC_API_KEY"
        }
