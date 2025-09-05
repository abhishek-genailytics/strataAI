"""
Unified API Gateway - OpenAI-compatible endpoint for multiple providers.
Provides a single /v1/chat/completions endpoint that works with any provider.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..middleware.pat_auth import require_pat_auth
from ..models.chat_completion import ChatCompletionRequest, UnifiedChatCompletionRequest, ChatCompletionResponse, ProviderError
from ..services.llm_adapters import AdapterFactory
from ..services.api_key_service import api_key_service
from ..utils.supabase_client import supabase

router = APIRouter(prefix="", tags=["unified-api"])

@router.get("/test-unified")
async def test_unified_api():
    """Simple test endpoint to verify unified API is working."""
    return {"message": "Unified API is working!", "timestamp": "2025-09-04T20:29:22"}

@router.get("/test-pat-auth")
async def test_pat_auth(user_context: Dict[str, Any] = Depends(require_pat_auth)):
    """Test PAT authentication endpoint."""
    return {
        "message": "PAT authentication working!",
        "user_context": user_context,
        "timestamp": "2025-09-04T20:29:22"
    }

@router.get("/test-db-connection")
async def test_pat_auth_simple():
    """Test PAT authentication endpoint without dependency injection."""
    try:
        import hashlib
        from ..utils.supabase_client import supabase
        
        # Test basic database connection
        token_hash = hashlib.sha256("pat_cPvHpcv2UAjdQktFmN6tIStnAYkU1QRkJAj20I4wH-k".encode()).hexdigest()
        
        # Test simple query - first get all tokens to see what's there
        all_tokens = supabase.table("personal_access_tokens").select("id, name, token_hash").limit(5).execute()
        
        # Then test our specific query
        response = supabase.table("personal_access_tokens").select("id, name").eq("token_hash", token_hash).limit(1).execute()
        
        return {
            "message": "Database query working!",
            "token_hash": token_hash[:20] + "...",
            "all_tokens": all_tokens.data,
            "query_result": response.data,
            "timestamp": "2025-09-04T20:29:22"
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": "2025-09-04T20:29:22"
        }

@router.post("/chat/completions-debug")
async def debug_chat_completion(request: UnifiedChatCompletionRequest):
    """Debug endpoint without authentication to test request parsing."""
    return {
        "debug": True,
        "received_model": request.model,
        "received_messages": request.messages,
        "provider_extracted": request.model.split("/")[0] if "/" in request.model else "no_provider",
        "message": "Request received successfully"
    }


async def get_provider_api_key(provider: str, organization_id: str) -> str:
    """
    Get the API key for a specific provider from the organization's stored keys.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        organization_id: Organization UUID
        
    Returns:
        Decrypted API key
        
    Raises:
        HTTPException: If API key not found or provider not supported
    """
    try:
        # Get provider info from database
        provider_response = supabase.table("ai_providers").select("id, name").eq("name", provider).execute()
        
        if not provider_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{provider}' not found"
            )
        
        provider_id = provider_response.data[0]["id"]
        
        # Get the API key for this organization + provider combination
        api_key_data = await api_key_service.get_by_provider(
            organization_id=organization_id,
            provider_id=provider_id
        )
        
        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for provider '{provider}'. Please add your {provider.title()} API key in the StrataAI dashboard."
            )
        
        # Get the decrypted API key
        decrypted_key = await api_key_service.get_decrypted_key(
            api_key_id=api_key_data["id"],
            organization_id=organization_id
        )
        
        if not decrypted_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve API key for provider '{provider}'"
            )
        
        return decrypted_key
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API key: {str(e)}"
        )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_unified_chat_completion(
    request: UnifiedChatCompletionRequest,
    user_context: Dict[str, Any] = Depends(require_pat_auth)
):
    """
    Create a chat completion using any supported provider with OpenAI-compatible interface.
    
    This is the main unified endpoint that abstracts away provider differences.
    Users only need their Strata PAT token and can switch providers by changing the model field.
    
    Example request:
    ```json
    {
        "model": "openai/gpt-3.5-turbo",  // or "anthropic/claude-3-haiku"
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7
    }
    ```
    
    Authentication: Bearer {STRATA_PAT}
    """
    try:
        print(f"DEBUG: User context: {user_context}")
        print(f"DEBUG: Request model: {request.model}")
        print(f"DEBUG: Request messages: {request.messages}")
        
        # Validate model format and extract provider
        if "/" not in request.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model must include provider prefix (e.g., 'openai/gpt-3.5-turbo', 'anthropic/claude-3-haiku')"
            )
        
        provider = request.model.split("/")[0]
        
        # Check for streaming request
        if request.stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /chat/completions/stream for streaming requests"
            )
        
        # Get the appropriate adapter
        try:
            adapter = AdapterFactory.get_adapter(request.model)
        except ValueError as e:
            supported_providers = AdapterFactory.get_supported_providers()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{str(e)}. Supported providers: {', '.join(supported_providers)}"
            )
        
        # Get API key for the provider
        api_key = await get_provider_api_key(provider, user_context["organization_id"])
        
        # Convert UnifiedChatCompletionRequest to ChatCompletionRequest for adapter
        from uuid import UUID
        full_request = ChatCompletionRequest(
            messages=request.messages,
            model=request.model,
            provider=provider,
            organization_id=UUID(user_context["organization_id"]),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop=request.stop,
            stream=request.stream
        )
        
        # Execute the request through the adapter
        async with adapter:
            response = await adapter.chat_completion(full_request, api_key)
        
        return response
        
    except HTTPException:
        raise
    except ProviderError as e:
        print(f"DEBUG: Provider error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "provider_error",
                "message": str(e),
                "provider": provider
            }
        )
    except Exception as e:
        print(f"DEBUG: Unexpected error in unified API: {e}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/chat/completions/stream")
async def create_unified_chat_completion_stream(
    request: ChatCompletionRequest,
    user_context: Dict[str, Any] = Depends(require_pat_auth)
):
    """
    Create a streaming chat completion using any supported provider.
    
    Returns Server-Sent Events (SSE) stream in OpenAI format regardless of the underlying provider.
    
    Example request:
    ```json
    {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": "Tell me a story"}
        ],
        "stream": true
    }
    ```
    
    Authentication: Bearer {STRATA_PAT}
    """
    try:
        # Validate model format and extract provider
        if "/" not in request.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model must include provider prefix (e.g., 'openai/gpt-3.5-turbo', 'anthropic/claude-3-haiku')"
            )
        
        provider = request.model.split("/")[0]
        
        # Force streaming mode
        request.stream = True
        
        # Get the appropriate adapter
        try:
            adapter = AdapterFactory.get_adapter(request.model)
        except ValueError as e:
            supported_providers = AdapterFactory.get_supported_providers()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{str(e)}. Supported providers: {', '.join(supported_providers)}"
            )
        
        # Get API key for the provider
        api_key = await get_provider_api_key(provider, user_context["organization_id"])
        
        # Create streaming response
        async def generate_stream():
            try:
                async with adapter:
                    async for chunk in adapter.chat_completion_stream(request, api_key):
                        yield chunk
            except ProviderError as e:
                error_chunk = f"data: {{'error': '{e.error_message}', 'provider': '{e.provider}'}}\n\n"
                yield error_chunk
            except Exception as e:
                error_chunk = f"data: {{'error': 'An unexpected error occurred'}}\n\n"
                yield error_chunk
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "Failed to initialize streaming"}
        )


@router.get("/models")
async def list_unified_models(
    user_context: Dict[str, Any] = Depends(require_pat_auth)
):
    """
    List all available models across all providers based on configured API keys.
    
    Returns models in the format: provider/model-name
    Only returns models for providers where the organization has configured API keys.
    
    Authentication: Bearer {STRATA_PAT}
    """
    try:
        available_models = []
        organization_id = user_context["organization_id"]
        
        # Get all configured providers for this organization
        api_keys_response = supabase.table("api_keys").select(
            "ai_providers!inner(name)"
        ).eq("organization_id", organization_id).eq("is_active", True).execute()
        
        configured_providers = set()
        for key_data in api_keys_response.data:
            provider_name = key_data["ai_providers"]["name"]
            configured_providers.add(provider_name)
        
        # Get models for each configured provider
        for provider in configured_providers:
            try:
                # Create a temporary adapter to get supported models
                temp_adapter = AdapterFactory.get_adapter(f"{provider}/dummy")
                models = temp_adapter.get_supported_models()
                
                # Add provider prefix to each model
                for model in models:
                    available_models.append(f"{provider}/{model}")
                    
            except Exception:
                # Skip providers that fail to initialize
                continue
        
        return {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": model.split("/")[0]
                }
                for model in sorted(available_models)
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.get("/providers")
async def list_supported_providers():
    """
    List all supported providers in the unified API.
    
    This endpoint doesn't require authentication and shows all providers
    that the unified API supports, regardless of user configuration.
    """
    return {
        "supported_providers": ["openai", "anthropic"],
        "model_format": "provider/model-name",
        "example_models": {
            "openai": ["openai/gpt-3.5-turbo", "openai/gpt-4"],
            "anthropic": ["anthropic/claude-3-haiku-20240307", "anthropic/claude-3-sonnet-20240229"]
        },
        "status": "unified_api_working"
    }
