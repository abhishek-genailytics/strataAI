from fastapi import APIRouter, Depends, Body, Request
from uuid import UUID
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.core.deps import resolve_organization, validate_model
from app.models.auth import CurrentCaller
from app.models.catalog import ResolvedModel
from app.services.adapter_factory import get_adapter
from app.services.provider_keys import get_active_api_key
from app.services.costing import compute_cost

router = APIRouter(tags=["Unified API"])

def _resolve_model_from_body(req: ChatCompletionRequest = Body(...)) -> ResolvedModel:
    """Dependency to extract and validate model from request body."""
    import asyncio
    return asyncio.run(validate_model(req.model))

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(
    request: Request,
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
    # Special case: echo adapter doesn't need API keys
    if resolved_model.provider_name == "echo":
        api_key_id, plaintext_key = None, None
    else:
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

    # 4) Compute cost from usage and model pricing (Task 13)
    cost = compute_cost(
        usage=resp.usage,
        model_id=resolved_model.id,
        region=None  # MVP: default; plug header/org setting later
    )

    # 5) Stash for logging middleware / Task 14 persistence
    request.state.cost_breakdown = cost
    request.state.model_id = resolved_model.id
    request.state.provider_id = resolved_model.provider_id
    if api_key_id:
        request.state.api_key_id = api_key_id

    return resp
