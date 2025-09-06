# tiny helper now; expand later (e.g., allow aliases)
from typing import Tuple

def parse_model_id(model: str) -> Tuple[str, str]:
    """
    Returns (provider, native_model).
    Enforces 'provider/model' per MVP rules.
    """
    provider, native = model.split("/", 1)
    if not provider or not native:
        raise ValueError("model must be 'provider/model'")
    return provider, native
