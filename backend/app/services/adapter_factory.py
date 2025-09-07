from app.core.config import get_settings
from app.services.llm_adapters.echo import EchoAdapter
from app.core.exceptions import NotFoundError
from app.services.llm_adapters.openai import OpenAIAdapter
from app.services.llm_adapters.anthropic import AnthropicAdapter

_settings = get_settings()

def get_adapter(provider_name: str):
    if _settings.FORCE_ECHO_ADAPTER:
        return EchoAdapter()

    # Register real adapters here as you implement them
    registry = {
        "echo": EchoAdapter,
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        # "perplexity": PerplexityAdapter,
        # "grok": GrokAdapter,
        # "qwen": QwenAdapter,
        # "mistral": MistralAdapter,
        # "cohere": CohereAdapter,
    }

    cls = registry.get(provider_name)
    if not cls:
        raise NotFoundError("Adapter not implemented for this provider", code="adapter_not_implemented", param="model")
    return cls()
