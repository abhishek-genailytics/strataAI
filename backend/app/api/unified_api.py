from fastapi import APIRouter, Depends
from uuid import UUID
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.core.deps import resolve_organization
from app.models.auth import CurrentCaller
from app.utils.model_id import parse_model_id
from app.core.exceptions import InvalidRequestError, NotFoundError

router = APIRouter(tags=["Unified API"])

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(
    req: ChatCompletionRequest,
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
) -> ChatCompletionResponse:
    # Enforce "no streaming" for MVP — ignore silently
    # req.stream may be True from client; we do not stream in this version

    # Validate model id (provider/model)
    try:
        provider, native_model = parse_model_id(req.model)
    except ValueError:
        # OpenAI: type=invalid_request_error, param="model"
        raise InvalidRequestError("model must be 'provider/model'", param="model")

    # We now have access to the resolved organization_id for downstream use
    # (provider-key lookup, accounting, etc.) - will be used in Task 11
    
    # Not implemented yet: adapters (Task 7/8)
    # Keep a typed 404 for now (clearer than 501)
    raise NotFoundError("Adapter not implemented for this model")
