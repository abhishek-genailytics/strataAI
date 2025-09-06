from fastapi import APIRouter, Depends
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.models.auth import CurrentCaller
from app.utils.model_id import parse_model_id
from app.core.exceptions import InvalidRequestError, NotFoundError

router = APIRouter(tags=["Unified API"])

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(
    req: ChatCompletionRequest,
    caller: CurrentCaller = Depends(require_pat),
) -> ChatCompletionResponse:
    # Enforce "no streaming" for MVP — ignore silently
    # req.stream may be True from client; we do not stream in this version

    # Validate model id (provider/model)
    try:
        provider, native_model = parse_model_id(req.model)
    except ValueError:
        # OpenAI: type=invalid_request_error, param="model"
        raise InvalidRequestError("model must be 'provider/model'", param="model")

    # Not implemented yet: adapters (Task 7/8)
    # Keep a typed 404 for now (clearer than 501)
    raise NotFoundError("Adapter not implemented for this model")
