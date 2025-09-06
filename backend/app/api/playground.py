"""
Playground-specific API endpoints that use direct Supabase authentication
and user's configured provider API keys without PAT complexity.
"""
from typing import List, Optional, AsyncGenerator
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..services.playground_service import PlaygroundProviderService
from ..utils.supabase_client import supabase_service

router = APIRouter(prefix="/playground", tags=["playground"])


class PlaygroundMessage(BaseModel):
    role: str
    content: str


class PlaygroundChatRequest(BaseModel):
    model: str  # Format: "provider/model" (e.g., "openai/gpt-4")
    messages: List[PlaygroundMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2500
    stream: Optional[bool] = False
    session_id: Optional[str] = None  # Current session ID for continuation


class PlaygroundModelInfo(BaseModel):
    id: str  # Format: "provider/model"
    provider: str
    model: str
    display_name: str
    max_tokens: int
    supports_streaming: bool
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None


@router.get("/models", response_model=List[PlaygroundModelInfo])
async def get_playground_models(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get models available in playground based on user's configured API keys."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Get models for providers where user has active API keys
        # First get the API keys for this organization
        api_keys_result = supabase_service.table("api_keys").select(
            "provider_id"
        ).eq("organization_id", str(organization.id)).eq("is_active", True).execute()
        
        if not api_keys_result.data:
            return []
        
        provider_ids = [key['provider_id'] for key in api_keys_result.data]
        
        # Now get models for those providers
        result = supabase_service.table("ai_models").select(
            """
            model_name,
            display_name,
            max_tokens,
            supports_streaming,
            ai_providers(name, id),
            model_pricing(pricing_type, price_per_unit)
            """
        ).eq("is_active", True).in_("provider_id", provider_ids).execute()
        
        models = []
        if result.data:
            for model_data in result.data:
                provider_info = model_data.get('ai_providers')
                if not provider_info:
                    continue
                    
                provider_name = provider_info['name']
                
                # Calculate pricing
                input_cost = None
                output_cost = None
                if model_data.get('model_pricing'):
                    for pricing in model_data['model_pricing']:
                        if pricing['pricing_type'] == 'input':
                            input_cost = float(pricing['price_per_unit'])
                        elif pricing['pricing_type'] == 'output':
                            output_cost = float(pricing['price_per_unit'])
                
                models.append(PlaygroundModelInfo(
                    id=f"{provider_name}/{model_data['model_name']}",
                    provider=provider_name,
                    model=model_data['model_name'],
                    display_name=model_data['display_name'],
                    max_tokens=model_data['max_tokens'] or 4096,
                    supports_streaming=model_data['supports_streaming'] or False,
                    cost_per_1k_input_tokens=input_cost,
                    cost_per_1k_output_tokens=output_cost
                ))
        
        return models
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve playground models: {str(e)}"
        )


@router.post("/chat/completions")
async def playground_chat_completion(
    request: PlaygroundChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Direct chat completion for playground using user's provider API keys with session management."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Parse provider and model from request
        if "/" not in request.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model must be in format 'provider/model'"
            )
        
        provider_name, model_name = request.model.split("/", 1)
        
        # Get or create session based on provider compatibility
        session_id = await PlaygroundProviderService.create_or_get_session(
            str(current_user.id),
            provider_name,
            model_name,
            request.session_id
        )
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Save user message to database (we'll update token count after API response)
        user_message = messages[-1]  # Last message should be the user's input
        user_message_id = None
        if user_message["role"] == "user":
            user_message_id = await PlaygroundProviderService.save_message_with_tokens(
                session_id,
                "user",
                user_message["content"],
                provider_name,
                model_name,
                0,  # Will be updated with actual token count from API response
                "input"
            )
        
        # Get API key for the provider
        api_key = await PlaygroundProviderService.get_decrypted_api_key(
            organization.id, provider_name
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for provider: {provider_name}"
            )
        
        if request.stream:
            # Return streaming response
            async def generate():
                full_response = ""
                async for chunk in PlaygroundProviderService.chat_completion_stream(
                    organization.id,
                    provider_name,
                    model_name,
                    messages,
                    request.temperature or 0.7,
                    request.max_tokens or 2500
                ):
                    # Extract content from streaming chunks for saving
                    if "data: " in chunk and chunk.strip() != "data: [DONE]":
                        try:
                            chunk_data = json.loads(chunk.replace("data: ", ""))
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    full_response += delta["content"]
                        except:
                            pass
                    yield chunk
                
                # Save assistant response after streaming completes
                if full_response:
                    await PlaygroundProviderService.save_message_with_tokens(
                        session_id,
                        "assistant",
                        full_response,
                        provider_name,
                        model_name,
                        len(full_response.split()),  # Approximate token count for streaming
                        "output"
                    )
                    
                    # Generate session name if this is the first user message
                    await PlaygroundProviderService.update_session_name_if_needed(
                        session_id, provider_name, model_name, user_message["content"], api_key
                    )
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": session_id  # Return session ID in header
                }
            )
        else:
            # Return non-streaming response
            response = await PlaygroundProviderService.chat_completion(
                organization.id,
                provider_name,
                model_name,
                messages,
                request.temperature or 0.7,
                request.max_tokens or 2500,
                stream=False
            )
            
            # Save assistant response and extract token usage
            if "choices" in response and response["choices"]:
                assistant_content = response["choices"][0]["message"]["content"]
                
                # Extract token usage
                usage = response.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # Update user message token count
                if user_message_id and input_tokens > 0:
                    await PlaygroundProviderService.update_message_token_count(
                        user_message_id, input_tokens
                    )
                
                # Save assistant message
                await PlaygroundProviderService.save_message_with_tokens(
                    session_id,
                    "assistant",
                    assistant_content,
                    provider_name,
                    model_name,
                    output_tokens,
                    "output"
                )
                
                # Generate session name if this is the first user message
                await PlaygroundProviderService.update_session_name_if_needed(
                    session_id, provider_name, model_name, user_message["content"], api_key
                )
            
            # Add session ID to response
            response["session_id"] = session_id
            
            # Ensure all database operations are committed before returning
            # Small delay to ensure session name generation completes
            import asyncio
            await asyncio.sleep(0.1)
            
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Playground chat completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )


@router.get("/api-keys/status")
async def get_api_keys_status(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get status of configured API keys for playground."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        result = supabase_service.table("api_keys").select(
            """
            name,
            is_active,
            last_used_at,
            ai_providers(name, display_name)
            """
        ).eq("organization_id", str(organization.id)).execute()
        
        return {
            "api_keys": [
                {
                    "provider": key['ai_providers']['name'],
                    "provider_display_name": key['ai_providers']['display_name'],
                    "name": key['name'],
                    "is_active": key['is_active'],
                    "last_used_at": key['last_used_at']
                }
                for key in result.data
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API keys status: {str(e)}"
        )
