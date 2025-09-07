from typing import Iterable, Optional, Tuple
from app.models.openai_chat import ChatMessage, ChatCompletionUsage

# --- Strategy order ---
# 1) Provider usage (if provided to this function)  -> return as-is
# 2) Optional precise tokenizer (if installed/enabled)
# 3) Deterministic fallback: 1 token ~= 4 chars (ASCII-ish heuristic)

def concat_contents(messages: Iterable[ChatMessage]) -> str:
    """Concatenate all message contents into a single string."""
    return "".join(m.content or "" for m in messages)

def approx_tokens_from_text(text: str) -> int:
    """
    Deterministic, cheap: 1 token ≈ 4 chars. Min 1 if non-empty.
    This is a rough approximation suitable for fallback scenarios.
    """
    n = max(0, len(text))
    return 0 if n == 0 else max(1, (n + 3) // 4)

def estimate_usage_from_messages_and_reply(
    messages: Iterable[ChatMessage],
    assistant_text: str,
) -> ChatCompletionUsage:
    """
    Estimate token usage from messages and assistant reply using deterministic fallback.
    """
    prompt_text = concat_contents(messages)
    prompt_tokens = approx_tokens_from_text(prompt_text)
    completion_tokens = approx_tokens_from_text(assistant_text or "")
    return ChatCompletionUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )

# (Optional) Hooks — left as stubs for later tasks if you add tokenizers:
USE_PRECISE_TOKENIZERS = False  # keep False for Vercel MVP

def precise_count_if_available(
    messages: Iterable[ChatMessage], 
    assistant_text: str, 
    model_name: str, 
    provider: str
) -> Optional[ChatCompletionUsage]:
    """
    Hook for precise tokenizer counting when available.
    Currently returns None to use fallback counting.
    """
    if not USE_PRECISE_TOKENIZERS:
        return None
    # TODO: wire tiktoken (OpenAI) or anthropic tokenizer when enabled.
    return None

def unify_usage(
    provider_usage: Optional[Tuple[int, int, int]],
    messages: Iterable[ChatMessage],
    assistant_text: str,
    model_name: str,
    provider: str,
) -> ChatCompletionUsage:
    """
    Unified token usage calculation with fallback strategy:
    1. Use provider-reported usage if available
    2. Use precise tokenizer if enabled and available
    3. Fall back to deterministic estimation
    
    Args:
        provider_usage: Tuple of (prompt_tokens, completion_tokens, total_tokens) from provider
        messages: Input messages for token counting
        assistant_text: Assistant response text
        model_name: Model identifier
        provider: Provider name (openai, anthropic, echo, etc.)
    
    Returns:
        ChatCompletionUsage object with token counts
    """
    # 1) Provider usage
    if provider_usage:
        pt, ct, tt = provider_usage
        return ChatCompletionUsage(
            prompt_tokens=int(pt or 0), 
            completion_tokens=int(ct or 0), 
            total_tokens=int(tt or 0)
        )

    # 2) Precise (optional)
    precise = precise_count_if_available(messages, assistant_text, model_name, provider)
    if precise:
        return precise

    # 3) Fallback
    return estimate_usage_from_messages_and_reply(messages, assistant_text)
