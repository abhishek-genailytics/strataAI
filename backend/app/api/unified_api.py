from fastapi import APIRouter, Depends, Body, Request, Header, Response
from uuid import UUID
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.core.auth import require_pat
from app.core.deps import resolve_organization
from app.models.auth import CurrentCaller
from app.services.unified_service import UnifiedChatService
from app.core.telemetry import TelemetryHook

router = APIRouter(dependencies=[Depends(TelemetryHook())], tags=["Unified API"])

@router.post("/chat/completions", response_model=ChatCompletionResponse, name="OpenAI-compatible chat")
async def chat_completions(
    request: Request,
    req: ChatCompletionRequest,
    response: Response,
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
    x_session_id: str | None = Header(None, alias="X-Session-ID"),
) -> ChatCompletionResponse:
    # --- Non-stream enforcement ---
    requested_stream = bool(req.stream)
    if requested_stream:
        # Soft signal for clients; still a normal JSON body
        response.headers["X-Stream-Disabled"] = "1"
        # (Optionally) include reason
        response.headers["X-Stream-Reason"] = "MVP_non_stream"

    # Use unified service for all chat completion logic
    unified_service = UnifiedChatService()
    resp = await unified_service.chat_completions_internal(
        organization_id=organization_id,
        initiated_by_user_id=caller.user_id,
        request=req,
        x_session_id=x_session_id,
    )

    # Store state for telemetry logging (if needed by middleware)
    request.state.caller = caller
    request.state.usage = resp.usage

    return resp
