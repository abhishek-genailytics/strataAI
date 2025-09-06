from fastapi import APIRouter, HTTPException, status
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.utils.model_id import parse_model_id

router = APIRouter(tags=["Unified API"])

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(req: ChatCompletionRequest) -> ChatCompletionResponse:
    # Enforce "no streaming" for MVP — ignore silently
    # req.stream may be True from client; we do not stream in this version

    # Validate model id (provider/model)
    try:
        provider, native_model = parse_model_id(req.model)
    except ValueError as e:
        # Task 3 will normalize error envelopes; for now regular HTTP error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Stub behavior (we will replace with adapter call in Task 7/8)
    # For now, return a deterministic placeholder that matches the schema
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="chat.completions is defined but provider adapters are not wired yet."
    )
