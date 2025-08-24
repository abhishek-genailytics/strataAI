from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.chat_completion import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ProviderModelInfo,
    ProviderError
)
from ..models.organization import Organization
from ..services.provider_service import provider_service

router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    Create a chat completion using the specified model and provider in organization context.
    
    This endpoint provides a unified interface to multiple AI providers
    (OpenAI, Anthropic) with organization-aware API key management.
    """
    try:
        if request.stream:
            # For streaming requests, redirect to streaming endpoint
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /chat/completions/stream for streaming requests"
            )
        
        response = await provider_service.chat_completion(
            request=request,
            user_id=current_user.id,
            organization_id=organization.id if organization else None
        )
        
        return response
        
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "provider_error",
                "message": e.error_message,
                "provider": e.provider,
                "error_type": e.error_type
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "internal_error", "message": "An unexpected error occurred"}
        )


@router.post("/chat/completions/stream")
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    Create a streaming chat completion using the specified model and provider in organization context.
    
    Returns a Server-Sent Events (SSE) stream of completion chunks.
    """
    try:
        # Force streaming mode
        request.stream = True
        
        async def generate():
            try:
                async for chunk in provider_service.chat_completion_stream(
                    request=request,
                    user_id=current_user.id,
                    organization_id=organization.id if organization else None
                ):
                    yield chunk
            except ProviderError as e:
                error_chunk = f"data: {{'error': '{e.error_message}', 'provider': '{e.provider}'}}\n\n"
                yield error_chunk
            except Exception as e:
                error_chunk = f"data: {{'error': 'An unexpected error occurred'}}\n\n"
                yield error_chunk
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request", "message": str(e)}
        )


@router.get("/models", response_model=List[ProviderModelInfo])
async def list_models(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    List all available models across all providers based on configured API keys in organization context.
    
    Returns model information including pricing, token limits, and capabilities.
    """
    return await provider_service.get_available_models(
        user_id=current_user.id,
        organization_id=organization.id if organization else None
    )


@router.get("/models/{provider}", response_model=List[str])
async def list_provider_models(
    provider: str,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    List available models for a specific provider based on configured API keys in organization context.
    """
    models = await provider_service.get_provider_models(
        provider=provider,
        user_id=current_user.id,
        organization_id=organization.id if organization else None
    )
    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found or has no available models"
        )
    
    return models
