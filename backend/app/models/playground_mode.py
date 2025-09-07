"""
Playground mode models for Gateway vs Direct toggle functionality.
"""
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any


class PlaygroundRequestSource(str, Enum):
    """Enum for playground request routing modes."""
    gateway = "gateway"    # unified pipeline parity
    direct = "direct"      # adapter fast-path


class PlaygroundSessionMeta(BaseModel):
    """Metadata for playground sessions including request source mode."""
    request_source: PlaygroundRequestSource = PlaygroundRequestSource.gateway
    client_session_id: Optional[str] = None          # for frontend reconciliation
    default_params: Dict[str, Any] = {}              # temperature, max_tokens, etc.
    
    class Config:
        use_enum_values = True
