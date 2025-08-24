import asyncio
import time
import json
from typing import Dict, List, Optional, AsyncGenerator
from uuid import UUID, uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.chat_completion import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
    ProviderError,
    ProviderModelInfo
)
from ..models.ai_provider import AIProvider
from .api_key_service import api_key_service
from .base import BaseService


class ProviderService:
    """Service for managing AI provider integrations with direct HTTP calls."""
    
    def __init__(self):
        self.provider_configs = {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "models": {
                    "gpt-4": {"max_tokens": 8192, "cost_input": 0.03, "cost_output": 0.06},
                    "gpt-4-turbo": {"max_tokens": 128000, "cost_input": 0.01, "cost_output": 0.03},
                    "gpt-3.5-turbo": {"max_tokens": 4096, "cost_input": 0.001, "cost_output": 0.002},
                }
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com/v1",
                "models": {
                    "claude-3-opus-20240229": {"max_tokens": 4096, "cost_input": 0.015, "cost_output": 0.075},
                    "claude-3-sonnet-20240229": {"max_tokens": 4096, "cost_input": 0.003, "cost_output": 0.015},
                    "claude-3-haiku-20240307": {"max_tokens": 4096, "cost_input": 0.00025, "cost_output": 0.00125},
                }
            }
        }
    
    def _get_provider_from_model(self, model: str) -> Optional[str]:
        """Determine provider from model name."""
        for provider, config in self.provider_configs.items():
            if model in config["models"]:
                return provider
        return None
    
    def _convert_messages_to_openai_format(self, messages: List[ChatMessage]) -> List[Dict]:
        """Convert chat messages to OpenAI API format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def _convert_messages_to_anthropic_format(self, messages: List[ChatMessage]) -> Dict:
        """Convert chat messages to Anthropic API format."""
        system_messages = [msg.content for msg in messages if msg.role == "system"]
        conversation_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages if msg.role != "system"
        ]
        
        return {
            "system": " ".join(system_messages) if system_messages else None,
            "messages": conversation_messages
        }
    
    async def _get_api_key(
        self, 
        db: AsyncSession, 
        provider: str, 
        user_id: UUID, 
        project_id: UUID
    ) -> str:
        """Get API key for the specified provider."""
        # Get provider info from database
        from sqlalchemy import select
        result = await db.execute(
            select(AIProvider).where(AIProvider.name == provider)
        )
        provider_obj = result.scalars().first()
        
        if not provider_obj:
            raise ValueError(f"Provider {provider} not found")
        
        # Get API keys for this provider
        api_keys = await api_key_service.get_by_project_and_provider(
            db, user_id=user_id, project_id=project_id, provider_id=provider_obj.id
        )
        
        if not api_keys:
            raise ValueError(f"No API key found for provider {provider}")
        
        # Get decrypted API key
        api_key_value = await api_key_service.get_decrypted_key(
            db, api_key_id=api_keys[0].id, user_id=user_id
        )
        
        if not api_key_value:
            raise ValueError(f"Failed to decrypt API key for provider {provider}")
        
        return api_key_value
    
    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        raise Exception("Max retries exceeded")
    
    async def _make_openai_request(
        self, 
        api_key: str, 
        model: str, 
        messages: List[Dict], 
        **kwargs
    ) -> Dict:
        """Make request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "stream": kwargs.get("stream", False)
        }
        
        if kwargs.get("max_tokens"):
            payload["max_tokens"] = kwargs["max_tokens"]
        if kwargs.get("top_p"):
            payload["top_p"] = kwargs["top_p"]
        if kwargs.get("frequency_penalty"):
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if kwargs.get("presence_penalty"):
            payload["presence_penalty"] = kwargs["presence_penalty"]
        if kwargs.get("stop"):
            payload["stop"] = kwargs["stop"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.provider_configs['openai']['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def _make_anthropic_request(
        self, 
        api_key: str, 
        model: str, 
        system: Optional[str], 
        messages: List[Dict], 
        **kwargs
    ) -> Dict:
        """Make request to Anthropic API."""
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        if system:
            payload["system"] = system
        if kwargs.get("top_p"):
            payload["top_p"] = kwargs["top_p"]
        if kwargs.get("stop"):
            payload["stop_sequences"] = kwargs["stop"] if isinstance(kwargs["stop"], list) else [kwargs["stop"]]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.provider_configs['anthropic']['base_url']}/messages",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def chat_completion(
        self, 
        db: AsyncSession, 
        request: ChatCompletionRequest, 
        user_id: UUID
    ) -> ChatCompletionResponse:
        """Generate chat completion using specified model and provider."""
        start_time = time.time()
        request_id = uuid4()
        
        # Determine provider
        provider = request.provider or self._get_provider_from_model(request.model)
        if not provider:
            raise ValueError(f"Unknown model: {request.model}")
        
        async def _make_request():
            # Get API key
            api_key = await self._get_api_key(
                db=db,
                provider=provider,
                user_id=user_id,
                project_id=request.project_id
            )
            
            # Make provider-specific request
            if provider == "openai":
                messages = self._convert_messages_to_openai_format(request.messages)
                return await self._make_openai_request(
                    api_key=api_key,
                    model=request.model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty,
                    stop=request.stop,
                    stream=request.stream
                )
            elif provider == "anthropic":
                converted = self._convert_messages_to_anthropic_format(request.messages)
                return await self._make_anthropic_request(
                    api_key=api_key,
                    model=request.model,
                    system=converted["system"],
                    messages=converted["messages"],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    stop=request.stop
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        try:
            # Execute with retry logic
            api_response = await self._retry_with_backoff(_make_request)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Convert response to our format
            if provider == "openai":
                content = api_response["choices"][0]["message"]["content"]
                usage = api_response["usage"]
                response_usage = ChatCompletionUsage(
                    prompt_tokens=usage["prompt_tokens"],
                    completion_tokens=usage["completion_tokens"],
                    total_tokens=usage["total_tokens"]
                )
            else:  # anthropic
                content = api_response["content"][0]["text"]
                usage = api_response["usage"]
                response_usage = ChatCompletionUsage(
                    prompt_tokens=usage["input_tokens"],
                    completion_tokens=usage["output_tokens"],
                    total_tokens=usage["input_tokens"] + usage["output_tokens"]
                )
            
            response = ChatCompletionResponse(
                id=f"chatcmpl-{request_id.hex[:8]}",
                created=int(time.time()),
                model=request.model,
                provider=provider,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=response_usage,
                request_id=request_id,
                processing_time_ms=processing_time
            )
            
            return response
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            raise ProviderError(
                provider=provider,
                error_type="HTTPError",
                error_message=f"HTTP {e.response.status_code}: {error_detail}"
            )
        except Exception as e:
            raise ProviderError(
                provider=provider,
                error_type=type(e).__name__,
                error_message=str(e)
            )
    
    async def chat_completion_stream(
        self, 
        db: AsyncSession, 
        request: ChatCompletionRequest, 
        user_id: UUID
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion."""
        request.stream = True
        
        # For now, we'll implement a simple streaming simulation
        # In a full implementation, you'd use the actual streaming capabilities
        response = await self.chat_completion(db, request, user_id)
        
        # Simulate streaming by yielding chunks
        content = response.choices[0].message.content
        words = content.split()
        
        for i, word in enumerate(words):
            chunk_data = {
                "id": response.id,
                "object": "chat.completion.chunk",
                "created": response.created,
                "model": response.model,
                "provider": response.provider,
                "choices": [{
                    "index": 0,
                    "delta": {"content": word + " " if i < len(words) - 1 else word},
                    "finish_reason": None if i < len(words) - 1 else "stop"
                }]
            }
            
            yield f"data: {json.dumps(chunk_data)}\n\n"
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        yield "data: [DONE]\n\n"
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)."""
        return max(1, len(text) // 4)
    
    def get_supported_models(self) -> List[ProviderModelInfo]:
        """Get list of all supported models across providers."""
        models = []
        
        for provider, config in self.provider_configs.items():
            for model, model_config in config["models"].items():
                models.append(ProviderModelInfo(
                    provider=provider,
                    model=model,
                    display_name=f"{provider.title()} {model}",
                    max_tokens=model_config["max_tokens"],
                    supports_streaming=True,
                    cost_per_1k_input_tokens=model_config["cost_input"],
                    cost_per_1k_output_tokens=model_config["cost_output"]
                ))
        
        return models
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get list of models for a specific provider."""
        if provider not in self.provider_configs:
            return []
        
        return list(self.provider_configs[provider]["models"].keys())


provider_service = ProviderService()
