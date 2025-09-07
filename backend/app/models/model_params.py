"""
Model parameter DTOs for playground parameter overrides and user defaults.
Follows OpenAI-style parameter naming and validation.
"""

from typing import Optional, Union, List
from pydantic import BaseModel, Field, field_validator


class ModelParams(BaseModel):
    """
    OpenAI-style model parameters for chat completions.
    All fields are optional to support partial overrides.
    """
    
    temperature: Optional[float] = Field(
        None,
        description="Controls randomness in the output. Higher values make output more random.",
        ge=0.0,
        le=2.0
    )
    
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum number of tokens to generate in the completion.",
        ge=1,
        le=200000  # High limit to accommodate various models
    )
    
    top_p: Optional[float] = Field(
        None,
        description="Nucleus sampling parameter. Alternative to temperature.",
        ge=0.0,
        le=1.0
    )
    
    presence_penalty: Optional[float] = Field(
        None,
        description="Penalizes new tokens based on whether they appear in the text so far.",
        ge=-2.0,
        le=2.0
    )
    
    frequency_penalty: Optional[float] = Field(
        None,
        description="Penalizes new tokens based on their existing frequency in the text so far.",
        ge=-2.0,
        le=2.0
    )
    
    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description="Up to 4 sequences where the API will stop generating further tokens."
    )

    @field_validator('stop')
    @classmethod
    def validate_stop(cls, v):
        """Validate stop sequences."""
        if v is None:
            return v
        
        if isinstance(v, str):
            return v
        
        if isinstance(v, list):
            if len(v) > 4:
                raise ValueError("stop sequences cannot exceed 4 items")
            if not all(isinstance(item, str) for item in v):
                raise ValueError("all stop sequences must be strings")
            return v
        
        raise ValueError("stop must be a string or list of strings")

    def merge_with(self, other: Optional['ModelParams']) -> 'ModelParams':
        """
        Merge this params with another, with other taking precedence.
        Returns a new ModelParams instance.
        """
        if other is None:
            return self.model_copy()
        
        merged_data = {}
        
        # Use other's values if present, otherwise fall back to self
        for field_name in self.model_fields:
            other_value = getattr(other, field_name, None)
            self_value = getattr(self, field_name, None)
            merged_data[field_name] = other_value if other_value is not None else self_value
        
        return ModelParams(**merged_data)

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert to dictionary, optionally excluding None values."""
        return self.model_dump(exclude_none=exclude_none)

    @classmethod
    def from_dict(cls, data: dict) -> 'ModelParams':
        """Create ModelParams from dictionary, ignoring unknown fields."""
        filtered_data = {k: v for k, v in data.items() if k in cls.model_fields}
        return cls(**filtered_data)

    @classmethod
    def get_system_defaults(cls) -> 'ModelParams':
        """Get system default parameters."""
        return cls(
            temperature=0.7,
            max_tokens=512,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            stop=None
        )

    def ensure_anthropic_requirements(self) -> 'ModelParams':
        """
        Ensure parameters meet Anthropic requirements.
        Anthropic requires max_tokens to be present.
        """
        result = self.model_copy()
        if result.max_tokens is None:
            result.max_tokens = 512  # Default for Anthropic
        return result


class RegenerateRequest(BaseModel):
    """Request body for regenerating assistant messages."""
    
    params: Optional[ModelParams] = Field(
        None,
        description="Parameter overrides for regeneration"
    )
    
    target: str = Field(
        "last",
        description="Target for regeneration: 'last' or specific assistant_message_id"
    )
    
    save_params: bool = Field(
        False,
        description="Whether to persist params as user defaults for this model"
    )

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate target field."""
        if v != "last" and not isinstance(v, str):
            raise ValueError("target must be 'last' or a valid message ID")
        return v


class ChatCompletionWithParams(BaseModel):
    """Extended chat completion request with parameter overrides."""
    
    # Core OpenAI fields (simplified for playground)
    messages: List[dict]
    model: str
    stream: bool = False
    
    # Parameter overrides
    params: Optional[ModelParams] = None
    save_params: bool = False
    
    # Direct parameter fields (for OpenAI compatibility)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None

    def get_merged_params(self) -> ModelParams:
        """
        Extract and merge parameters from both params object and direct fields.
        Direct fields take precedence over params object.
        """
        # Start with params object if present
        base_params = self.params or ModelParams()
        
        # Override with direct fields if present
        direct_params = ModelParams(
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            stop=self.stop
        )
        
        return base_params.merge_with(direct_params)
