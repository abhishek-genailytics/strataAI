import httpx
from typing import Any, Dict, List
from uuid import UUID

from app.services.llm_adapters.base import LLMAdapter
from app.models.openai_chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
)
from app.core.config import get_settings
from app.core.exceptions import (
    InvalidRequestError,
    AuthenticationError,
    RateLimitExceeded,
    ServiceUnavailable,
    UpstreamTimeout,
    ProviderError,
)
from app.services.token_counting import unify_usage


_settings = get_settings()


class OpenAIAdapter(LLMAdapter):
    provider_name = "openai"

    def _endpoint(self) -> str:
        # Legacy Chat Completions endpoint (non-stream)
        # POST {OPENAI_BASE_URL}/v1/chat/completions
        return f"{_settings.OPENAI_BASE_URL}/v1/chat/completions"

    def _headers(self, api_key: str) -> Dict[str, str]:
        # OpenAI requires Bearer auth
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def chat_completion(
        self,
        *,
        organization_id: UUID,
        request: ChatCompletionRequest,
        model_name: str,  # native name: "gpt-4o-mini", etc.
        api_key: str | None,  # provided by provider-key lookup (Task 11)
    ) -> ChatCompletionResponse:
        if not api_key:
            raise AuthenticationError(
                "Missing OpenAI API key for organization",
                code="provider_key_missing",
            )

        payload: Dict[str, Any] = {
            # Always send the native model name to OpenAI (not "openai/<name>")
            "model": model_name,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "n": request.n,
            "stop": request.stop,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
            "user": request.user,
            # Explicitly ensure non-stream for MVP
            "stream": False,
        }

        timeouts = httpx.Timeout(
            connect=_settings.OPENAI_CONNECT_TIMEOUT_S,
            read=_settings.OPENAI_READ_TIMEOUT_S,
            write=_settings.OPENAI_WRITE_TIMEOUT_S,
            pool=None,
        )

        try:
            async with httpx.AsyncClient(timeout=timeouts) as client:
                resp = await client.post(
                    self._endpoint(), headers=self._headers(api_key), json=payload
                )
        except httpx.ReadTimeout:
            raise UpstreamTimeout("OpenAI timed out", code="upstream_timeout")
        except httpx.ConnectTimeout:
            raise ServiceUnavailable("OpenAI connection timeout", code="connect_timeout")
        except httpx.HTTPError as e:
            raise ProviderError(f"OpenAI transport error: {e!s}", code="transport_error")

        # Error handling by status code and OpenAI error body
        if resp.status_code >= 400:
            try:
                ej = resp.json()
                emsg = ej.get("error", {}).get("message") or "Provider error"
                etype = ej.get("error", {}).get("type")
                ecode = ej.get("error", {}).get("code")
                eparam = ej.get("error", {}).get("param")
            except Exception:
                emsg, etype, ecode, eparam = "Provider error", None, None, None

            if resp.status_code in (400, 422):
                raise InvalidRequestError(emsg, code=ecode, param=eparam)
            if resp.status_code == 401:
                raise AuthenticationError(
                    emsg or "Invalid provider credentials", code=ecode
                )
            if resp.status_code == 429:
                raise RateLimitExceeded(emsg or "Rate limit exceeded", code=ecode)
            if resp.status_code in (500, 502):
                raise ProviderError(emsg or "Provider error", code=ecode)
            if resp.status_code in (503,):
                raise ServiceUnavailable(emsg or "Service unavailable", code=ecode)
            if resp.status_code in (504,):
                raise UpstreamTimeout(emsg or "Upstream timeout", code=ecode)
            raise ProviderError(emsg or "Provider error", code=ecode)

        data = resp.json()

        # Normalize to our OpenAI-shaped response model (non-stream)
        # We set "model" to the unified id: "openai/<native>"
        unified_model_id = f"openai/{data.get('model', model_name)}"

        # choices
        choices_in = data.get("choices", []) or []
        choices_out: List[ChatCompletionChoice] = []
        for idx, ch in enumerate(choices_in):
            msg = ch.get("message", {}) or {}
            choices_out.append(
                ChatCompletionChoice(
                    index=idx,
                    message=ChatMessage(
                        role=msg.get("role", "assistant"),
                        content=msg.get("content", ""),
                    ),
                    finish_reason=ch.get("finish_reason"),
                )
            )

        # Use centralized token counting with provider fallback
        usage_in = data.get("usage") or {}
        provider_usage = None
        if usage_in:
            provider_usage = (
                usage_in.get("prompt_tokens"),
                usage_in.get("completion_tokens"),
                usage_in.get("total_tokens"),
            )

        assistant_text = choices_out[0].message.content if choices_out else ""
        usage = unify_usage(
            provider_usage=provider_usage,
            messages=request.messages,
            assistant_text=assistant_text,
            model_name=model_name,
            provider="openai",
        )

        return ChatCompletionResponse(
            id=data.get("id") or self._response_id(),
            created=int(data.get("created") or self._created_ts()),
            model=unified_model_id,
            choices=choices_out,
            usage=usage,
        )

