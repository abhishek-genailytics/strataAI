"""
OpenAI error envelope helpers for unified API.
"""
from typing import Any, Dict, Optional

OPENAI_TYPES_BY_STATUS = {
    400: "invalid_request_error",
    401: "authentication_error",
    403: "permission_error",
    404: "not_found_error",
    409: "conflict_error",
    422: "invalid_request_error",  # request validation
    429: "rate_limit_exceeded",
    500: "server_error",
    502: "bad_gateway",
    503: "service_unavailable",
    504: "timeout_error",
}

def is_public_openai_path(path: str) -> bool:
    """Check if the request path should use OpenAI error format."""
    return path.startswith("/v1/")

def openai_error_body(message: str, *, type_: Optional[str] = None, param: Optional[str] = None, code: Optional[str] = None) -> Dict[str, Any]:
    """Create OpenAI-compatible error response body."""
    return {
        "error": {
            "message": message,
            "type": type_ or "server_error",
            "param": param,
            "code": code,
        }
    }

def infer_type_from_status(status_code: int) -> str:
    """Infer OpenAI error type from HTTP status code."""
    return OPENAI_TYPES_BY_STATUS.get(status_code, "server_error")
