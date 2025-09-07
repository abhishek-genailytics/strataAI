"""
Pydantic models for playground export functionality (PG-14).
Supports cURL generation (unified/provider) and JSON transcript exports.
"""
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ExportOptions(BaseModel):
    """Options for export customization."""
    limit_turns: Optional[int] = Field(None, description="Limit to last N user+assistant pairs")
    include_system: bool = Field(True, description="Include system message in export")
    override_system: Optional[str] = Field(None, description="Override system prompt for this export only")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameter overrides")
    provider: Optional[str] = Field(None, description="Provider override for curl_provider type")


class ExportRequest(BaseModel):
    """Request body for export endpoint."""
    type: Literal["curl_unified", "curl_provider", "json_transcript"] = Field(
        ..., description="Type of export to generate"
    )
    options: ExportOptions = Field(default_factory=ExportOptions, description="Export options")


class ExportResponse(BaseModel):
    """Response wrapper for all export types."""
    mime: str = Field(..., description="MIME type of the content")
    filename: Optional[str] = Field(None, description="Suggested filename for downloads")
    content: str = Field(..., description="Export content (cURL command or JSON)")


# JSON Transcript Models
class TranscriptSession(BaseModel):
    """Session metadata for transcript export."""
    id: UUID
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    system: Optional[str] = None
    default_params: Dict[str, Any] = Field(default_factory=dict)


class TranscriptMessage(BaseModel):
    """Message data for transcript export."""
    id: UUID
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: datetime


class TranscriptUsagePerMessage(BaseModel):
    """Per-message usage data for transcript."""
    message_id: UUID
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal


class TranscriptUsageTotals(BaseModel):
    """Total usage aggregation for transcript."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    currency: str = "USD"


class TranscriptUsage(BaseModel):
    """Complete usage data for transcript."""
    totals: TranscriptUsageTotals
    per_message: List[TranscriptUsagePerMessage]


class TranscriptExport(BaseModel):
    """Complete JSON transcript structure."""
    object: str = "strata_playground_transcript_v1"
    session: TranscriptSession
    messages: List[TranscriptMessage]
    usage: TranscriptUsage


# Parameter Models for cURL generation
class ExportParams(BaseModel):
    """Normalized parameters for export generation."""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    
    def to_openai_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI API format, removing None values."""
        result = {}
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.stop is not None:
            result["stop"] = self.stop
        if self.presence_penalty is not None:
            result["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            result["frequency_penalty"] = self.frequency_penalty
        return result
    
    def to_anthropic_dict(self) -> Dict[str, Any]:
        """Convert to Anthropic API format, removing unsupported params."""
        result = {}
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.stop is not None:
            # Anthropic uses stop_sequences and expects a list
            if isinstance(self.stop, list):
                result["stop_sequences"] = self.stop
            elif self.stop:
                result["stop_sequences"] = [self.stop]
        # Note: presence_penalty and frequency_penalty are ignored for Anthropic
        return result
