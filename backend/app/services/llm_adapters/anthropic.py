import httpx
from typing import Any, Dict, List
from uuid import UUID

from app.services.llm_adapters.base import LLMAdapter
from app.models.openai_chat import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatCompletionUsage, ChatMessage
)
from app.core.config import get_settings
from app.core.exceptions import (
    InvalidRequestError, AuthenticationError, RateLimitExceeded,
    ServiceUnavailable, UpstreamTimeout, ProviderError
)
from app.services.token_counting import unify_usage

_settings = get_settings()

def _collect_system(req: ChatCompletionRequest) -> str | None:
    """Collect all system messages and join them with double newlines."""
    systems = [m.content for m in req.messages if m.role == "system" and (m.content or "").strip()]
    return "\n\n".join(systems) if systems else None

def _anthropic_messages(req: ChatCompletionRequest) -> List[Dict[str, Any]]:
    """Convert OpenAI messages to Anthropic format, filtering out system messages."""
    result: List[Dict[str, Any]] = []
    for m in req.messages:
        if m.role == "system":
            continue  # handled via top-level 'system'
        if m.role not in ("user", "assistant"):
            continue
        # MVP: assume string content only
        result.append({"role": m.role, "content": m.content})
    return result

class AnthropicAdapter(LLMAdapter):
    provider_name = "anthropic"

    def _endpoint(self) -> str:
        return f"{_settings.ANTHROPIC_BASE_URL}/v1/messages"

    def _headers(self, api_key: str) -> Dict[str, str]:
        return {
            "x-api-key": api_key,                 # required
            "anthropic-version": _settings.ANTHROPIC_VERSION,  # required
            "content-type": "application/json",
        }

    async def chat_completion(
        self,
        *,
        organization_id: UUID,
        request: ChatCompletionRequest,
        model_name: str,      # native e.g., "claude-sonnet-4-20250514"
        api_key: str | None,
    ) -> ChatCompletionResponse:
        if not api_key:
            raise AuthenticationError("Missing Anthropic API key for organization", code="provider_key_missing")

        system_text = _collect_system(request)
        max_toks = request.max_tokens or 1024  # default from settings if you prefer

        payload: Dict[str, Any] = {
            "model": model_name,
            "max_tokens": max_toks,                 # required
            "messages": _anthropic_messages(request),
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": False,                        # MVP: non-streaming
        }
        if system_text:
            payload["system"] = system_text
        if request.stop:
            payload["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        if request.user:
            payload["metadata"] = {"user_id": request.user}

        timeouts = httpx.Timeout(
            connect=_settings.ANTHROPIC_CONNECT_TIMEOUT_S,
            read=_settings.ANTHROPIC_READ_TIMEOUT_S,
            write=_settings.ANTHROPIC_WRITE_TIMEOUT_S,
            pool=None,
        )

        try:
            async with httpx.AsyncClient(timeout=timeouts) as client:
                resp = await client.post(self._endpoint(), headers=self._headers(api_key), json=payload)
        except httpx.ReadTimeout:
            raise UpstreamTimeout("Anthropic timed out", code="upstream_timeout")
        except httpx.ConnectTimeout:
            raise ServiceUnavailable("Anthropic connection timeout", code="connect_timeout")
        except httpx.HTTPError as e:
            raise ProviderError(f"Anthropic transport error: {e!s}", code="transport_error")

        if resp.status_code >= 400:
            try:
                ej = resp.json()
                emsg = ej.get("error", {}).get("message") or "Provider error"
                etype = ej.get("error", {}).get("type")
                ecode = ej.get("error", {}).get("code")
            except Exception:
                emsg, etype, ecode = "Provider error", None, None

            if resp.status_code in (400, 422):
                raise InvalidRequestError(emsg, code=ecode)
            if resp.status_code == 401:
                raise AuthenticationError(emsg or "Invalid provider credentials", code=ecode)
            if resp.status_code == 429:
                raise RateLimitExceeded(emsg or "Rate limit exceeded", code=ecode)
            if resp.status_code in (500, 502):
                raise ProviderError(emsg or "Provider error", code=ecode)
            if resp.status_code == 503:
                raise ServiceUnavailable(emsg or "Service unavailable", code=ecode)
            if resp.status_code == 504:
                raise UpstreamTimeout(emsg or "Upstream timeout", code=ecode)
            raise ProviderError(emsg or "Provider error", code=ecode)

        data = resp.json()

        # Build assistant message
        blocks = data.get("content") or []
        assistant_texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        assistant_text = "\n\n".join([t for t in assistant_texts if t is not None])

        # Translate stop reason
        stop_reason = data.get("stop_reason")
        if stop_reason == "max_tokens":
            finish_reason = "length"
        else:  # "end_turn" or "stop_sequence" (and others default to 'stop')
            finish_reason = "stop"

        # Use centralized token counting with provider fallback
        usage_in = data.get("usage") or {}
        provider_usage = None
        if usage_in:
            provider_usage = (
                usage_in.get("input_tokens"),
                usage_in.get("output_tokens"),
                (usage_in.get("input_tokens", 0) + usage_in.get("output_tokens", 0)),
            )

        usage = unify_usage(
            provider_usage=provider_usage,
            messages=request.messages,
            assistant_text=assistant_text,
            model_name=model_name,
            provider="anthropic",
        )

        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content=assistant_text),
            finish_reason=finish_reason,
        )

        return ChatCompletionResponse(
            id=data.get("id") or self._response_id(),
            created=int(self._created_ts()),          # Anthropic doesn't return Unix ts; use local
            model=f"anthropic/{data.get('model', model_name)}",
            choices=[choice],
            usage=usage,
        )
