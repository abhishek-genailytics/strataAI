from fastapi import APIRouter, Depends, Body
from uuid import UUID
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.core.deps import resolve_organization, validate_model
from app.models.auth import CurrentCaller
from app.models.catalog import ResolvedModel
from app.services.adapter_factory import get_adapter
from app.services.provider_keys import get_active_api_key

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

    # 1) Pick adapter
    adapter = get_adapter(resolved_model.provider_name)

    # 2) Load org-scoped provider key (throws OpenAI-style errors via middleware)
    api_key_id, plaintext_key = get_active_api_key(
        organization_id=organization_id,
        provider_id=resolved_model.provider_id
    )

    # 3) Call provider adapter
    resp = await adapter.chat_completion(
        organization_id=organization_id,
        request=req,
        model_name=resolved_model.model_name,
        api_key=plaintext_key,
    )

    # (Task 14 will persist api_requests and include api_key_id)
    return resp
