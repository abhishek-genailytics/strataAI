# tiny helper now; expand later (e.g., allow aliases)
from typing import Tuple
from .aliases import normalize_provider

def parse_model_id(model: str) -> Tuple[str, str]:
    """
    Returns (provider, native_model).
    Enforces 'provider/model' per MVP rules.
    Applies provider aliases for normalization.
    """
    if "/" not in model:
        raise ValueError("model must be 'provider/model'")
    
    provider, native = model.split("/", 1)
    if not provider or not native:
        raise ValueError("model must be 'provider/model'")
    
    return normalize_provider(provider), native
