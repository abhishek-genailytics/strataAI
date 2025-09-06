from fastapi import APIRouter, Depends, Body
from uuid import UUID
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.core.deps import resolve_organization, validate_model
from app.models.auth import CurrentCaller
from app.models.catalog import ResolvedModel
from app.services.adapter_factory import get_adapter

router = APIRouter(tags=["Unified API"])

def _resolve_model_from_body(req: ChatCompletionRequest = Body(...)) -> ResolvedModel:
    """Dependency to extract and validate model from request body."""
    import asyncio
    return asyncio.run(validate_model(req.model))

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(
    req: ChatCompletionRequest,
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
    resolved_model: ResolvedModel = Depends(_resolve_model_from_body),
) -> ChatCompletionResponse:
    # Enforce "no streaming" for MVP — ignore silently
    # req.stream may be True from client; we do not stream in this version

    # Model is now validated through the resolved_model dependency
    # resolved_model contains provider info, model capabilities, etc.
    
    # We now have access to the resolved organization_id for downstream use
    # (provider-key lookup, accounting, etc.) - will be used in Task 11
    
    # Use adapter factory to get the appropriate adapter
    adapter = get_adapter(resolved_model.provider_name)
    
    # Provider API key will be added in Task 11 (provider key lookup)
    return await adapter.chat_completion(
        organization_id=organization_id,
        request=req,
        model_name=resolved_model.model_name,
        api_key=None,
    )
