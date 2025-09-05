"""
LLM Provider Adapters for unified API gateway.
Implements adapter pattern to normalize different provider APIs to OpenAI-compatible format.
"""
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from uuid import uuid4
import httpx
import asyncio

from ..models.chat_completion import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
    ProviderError
)


class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""
    
    def __init__(self, provider_name: str, base_url: str):
        self.provider_name = provider_name
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    @abstractmethod
    async def chat_completion(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> ChatCompletionResponse:
        """Execute chat completion request and return normalized response."""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> AsyncGenerator[str, None]:
        """Execute streaming chat completion and yield SSE-formatted chunks."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Return list of supported model names for this provider."""
        pass
    
    @abstractmethod
    def extract_model_name(self, full_model: str) -> str:
        """Extract actual model name from prefixed format (e.g., 'openai/gpt-4' -> 'gpt-4')."""
        pass
    
    def _create_error_response(self, error_msg: str, error_type: str = "provider_error") -> ProviderError:
        """Create standardized error response."""
        return ProviderError(
            provider=self.provider_name,
            error_message=error_msg,
            error_type=error_type
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI API."""
    
    def __init__(self):
        super().__init__("openai", "https://api.openai.com/v1")
        self.supported_models = [
            "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4-0125-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106"
        ]
    
    def get_supported_models(self) -> List[str]:
        return self.supported_models
    
    def extract_model_name(self, full_model: str) -> str:
        """Extract model name from 'openai/model-name' format."""
        if full_model.startswith("openai/"):
            return full_model[7:]  # Remove 'openai/' prefix
        return full_model
    
    def _prepare_request_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Convert unified request to OpenAI format."""
        model = self.extract_model_name(request.model)
        
        body = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]
        }
        
        # Add optional parameters
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            body["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            body["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            body["stop"] = request.stop
        if request.stream is not None:
            body["stream"] = request.stream
        
        return body
    
    async def chat_completion(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> ChatCompletionResponse:
        """Execute OpenAI chat completion."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            body = self._prepare_request_body(request)
            body["stream"] = False  # Ensure non-streaming
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise self._create_error_response(f"OpenAI API error: {error_msg}")
            
            data = response.json()
            
            # Convert to unified format (OpenAI format is already our standard)
            return ChatCompletionResponse(
                id=data["id"],
                object=data["object"],
                created=data["created"],
                model=request.model,  # Keep the prefixed model name
                choices=[
                    ChatCompletionChoice(
                        index=choice["index"],
                        message=ChatMessage(
                            role=choice["message"]["role"],
                            content=choice["message"]["content"]
                        ),
                        finish_reason=choice["finish_reason"]
                    )
                    for choice in data["choices"]
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=data["usage"]["prompt_tokens"],
                    completion_tokens=data["usage"]["completion_tokens"],
                    total_tokens=data["usage"]["total_tokens"]
                ) if data.get("usage") else None
            )
            
        except ProviderError:
            raise
        except Exception as e:
            raise self._create_error_response(f"OpenAI request failed: {str(e)}")
    
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> AsyncGenerator[str, None]:
        """Execute streaming OpenAI chat completion."""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            body = self._prepare_request_body(request)
            body["stream"] = True
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body
            ) as response:
                if response.status_code != 200:
                    error_msg = f"OpenAI API error: HTTP {response.status_code}"
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_part = line[6:]  # Remove "data: " prefix
                        if data_part.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        
                        try:
                            # Parse and modify the model name to include prefix
                            chunk_data = json.loads(data_part)
                            if "model" in chunk_data:
                                chunk_data["model"] = request.model  # Keep prefixed model name
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                        except json.JSONDecodeError:
                            # Forward raw data if JSON parsing fails
                            yield f"{line}\n"
                            
        except Exception as e:
            error_msg = f"OpenAI streaming failed: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic Claude API."""
    
    def __init__(self):
        super().__init__("anthropic", "https://api.anthropic.com/v1")
        self.supported_models = [
            "claude-3-opus-20240229", "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"
        ]
    
    def get_supported_models(self) -> List[str]:
        return self.supported_models
    
    def extract_model_name(self, full_model: str) -> str:
        """Extract model name from 'anthropic/model-name' format."""
        if full_model.startswith("anthropic/"):
            return full_model[10:]  # Remove 'anthropic/' prefix
        return full_model
    
    def _prepare_request_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Convert unified request to Anthropic format."""
        model = self.extract_model_name(request.model)
        
        # Separate system messages from conversation
        system_messages = []
        conversation_messages = []
        
        for msg in request.messages:
            if msg.role == "system":
                system_messages.append(msg.content)
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        body = {
            "model": model,
            "messages": conversation_messages,
            "max_tokens": request.max_tokens or 4096  # Anthropic requires max_tokens
        }
        
        # Add system message if present
        if system_messages:
            body["system"] = " ".join(system_messages)
        
        # Add optional parameters
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.stop is not None:
            body["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        if request.stream is not None:
            body["stream"] = request.stream
        
        return body
    
    async def chat_completion(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> ChatCompletionResponse:
        """Execute Anthropic chat completion and normalize to OpenAI format."""
        try:
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            body = self._prepare_request_body(request)
            body["stream"] = False
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=body
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise self._create_error_response(f"Anthropic API error: {error_msg}")
            
            data = response.json()
            
            # Convert Anthropic response to OpenAI format
            content = ""
            if data.get("content") and len(data["content"]) > 0:
                content = data["content"][0].get("text", "")
            
            return ChatCompletionResponse(
                id=data.get("id", f"chatcmpl-{uuid4().hex[:29]}"),
                object="chat.completion",
                created=int(time.time()),
                model=request.model,  # Keep the prefixed model name
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason=data.get("stop_reason", "stop")
                    )
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=data.get("usage", {}).get("input_tokens", 0),
                    completion_tokens=data.get("usage", {}).get("output_tokens", 0),
                    total_tokens=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                ) if data.get("usage") else None
            )
            
        except ProviderError:
            raise
        except Exception as e:
            raise self._create_error_response(f"Anthropic request failed: {str(e)}")
    
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> AsyncGenerator[str, None]:
        """Execute streaming Anthropic chat completion and convert to OpenAI SSE format."""
        try:
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            body = self._prepare_request_body(request)
            body["stream"] = True
            
            completion_id = f"chatcmpl-{uuid4().hex[:29]}"
            created_time = int(time.time())
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=headers,
                json=body
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Anthropic API error: HTTP {response.status_code}"
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_part = line[6:]
                        
                        try:
                            event_data = json.loads(data_part)
                            
                            # Convert Anthropic streaming format to OpenAI format
                            if event_data.get("type") == "content_block_delta":
                                delta_content = event_data.get("delta", {}).get("text", "")
                                if delta_content:
                                    openai_chunk = {
                                        "id": completion_id,
                                        "object": "chat.completion.chunk",
                                        "created": created_time,
                                        "model": request.model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"content": delta_content},
                                            "finish_reason": None
                                        }]
                                    }
                                    yield f"data: {json.dumps(openai_chunk)}\n\n"
                            
                            elif event_data.get("type") == "message_stop":
                                # Send final chunk with finish_reason
                                final_chunk = {
                                    "id": completion_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": request.model,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": "stop"
                                    }]
                                }
                                yield f"data: {json.dumps(final_chunk)}\n\n"
                                yield "data: [DONE]\n\n"
                                break
                                
                        except json.JSONDecodeError:
                            continue  # Skip malformed JSON
                            
        except Exception as e:
            error_msg = f"Anthropic streaming failed: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"


class AdapterFactory:
    """Factory for creating LLM adapters based on model prefixes."""
    
    _adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter
    }
    
    @classmethod
    def get_adapter(cls, model: str) -> LLMAdapter:
        """
        Get appropriate adapter based on model prefix.
        
        Args:
            model: Model name with provider prefix (e.g., 'openai/gpt-4')
            
        Returns:
            LLMAdapter instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if "/" not in model:
            raise ValueError(f"Model must include provider prefix (e.g., 'openai/gpt-4'). Got: {model}")
        
        provider = model.split("/")[0]
        
        if provider not in cls._adapters:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(f"Unsupported provider: {provider}. Supported providers: {supported}")
        
        return cls._adapters[provider]()
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported provider prefixes."""
        return list(cls._adapters.keys())
    
    @classmethod
    def register_adapter(cls, provider: str, adapter_class: type):
        """Register a new adapter for a provider."""
        cls._adapters[provider] = adapter_class
