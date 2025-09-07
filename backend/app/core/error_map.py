"""
Provider error mapping to normalized StrataError exceptions.
Maps provider-specific error responses to OpenAI-compatible error types.
"""

from typing import Dict, Any, Optional, Type
import httpx
from .errors import (
    StrataError,
    AuthError,
    BadRequestError,
    RateLimitError,
    ModelNotFoundError,
    UpstreamServerError,
    TimeoutError,
    ServerError,
    PermissionError
)


def extract_provider_request_id(response: httpx.Response) -> Optional[str]:
    """
    Extract provider request ID from response headers or body.
    
    Args:
        response: HTTP response from provider
        
    Returns:
        Provider request ID if found, None otherwise
    """
    # Check common header names
    header_names = [
        'x-request-id',
        'request-id', 
        'x-trace-id',
        'cf-ray',
        'x-amzn-requestid'
    ]
    
    for header in header_names:
        if header in response.headers:
            return response.headers[header]
    
    # Check response body for ID fields
    try:
        if response.headers.get('content-type', '').startswith('application/json'):
            body = response.json()
            if isinstance(body, dict):
                # Common ID field names
                id_fields = ['id', 'request_id', 'requestId', 'trace_id']
                for field in id_fields:
                    if field in body and isinstance(body[field], str):
                        return body[field]
    except Exception:
        pass  # Ignore JSON parsing errors
    
    return None


def map_openai_error(response: httpx.Response) -> StrataError:
    """
    Map OpenAI API error response to StrataError.
    
    Args:
        response: HTTP response from OpenAI API
        
    Returns:
        Appropriate StrataError instance
    """
    provider_request_id = extract_provider_request_id(response)
    status = response.status_code
    
    try:
        error_data = response.json()
        error_info = error_data.get('error', {})
        message = error_info.get('message', 'Unknown error')
        error_type = error_info.get('type', '')
        code = error_info.get('code', '')
        param = error_info.get('param')
    except Exception:
        message = f"HTTP {status} error from OpenAI"
        error_type = ''
        code = ''
        param = None
    
    # Map by status code and error details
    if status == 400:
        if 'context_length_exceeded' in code or 'maximum context length' in message.lower():
            return BadRequestError(
                message=message,
                code="context_length_exceeded",
                param=param,
                provider_request_id=provider_request_id
            )
        elif 'invalid' in code or 'invalid' in message.lower():
            return BadRequestError(
                message=message,
                code=code or "invalid_param",
                param=param,
                provider_request_id=provider_request_id
            )
        else:
            return BadRequestError(
                message=message,
                code=code or "invalid_request",
                param=param,
                provider_request_id=provider_request_id
            )
    
    elif status == 401:
        return AuthError(
            message=message,
            provider_request_id=provider_request_id
        )
    
    elif status == 403:
        return PermissionError(
            message=message,
            code=code or "model_disabled_for_org",
            param=param,
            provider_request_id=provider_request_id
        )
    
    elif status == 404:
        return ModelNotFoundError(
            model=param or "unknown",
            provider_request_id=provider_request_id
        )
    
    elif status == 429:
        return RateLimitError(
            message=message,
            provider_request_id=provider_request_id
        )
    
    elif status >= 500:
        return UpstreamServerError(
            status_code=status,
            message=message,
            provider_request_id=provider_request_id
        )
    
    else:
        return ServerError(
            message=f"Unexpected OpenAI API response: {status} {message}",
            provider_request_id=provider_request_id
        )


def map_anthropic_error(response: httpx.Response) -> StrataError:
    """
    Map Anthropic API error response to StrataError.
    
    Args:
        response: HTTP response from Anthropic API
        
    Returns:
        Appropriate StrataError instance
    """
    provider_request_id = extract_provider_request_id(response)
    status = response.status_code
    
    try:
        error_data = response.json()
        error_info = error_data.get('error', {})
        message = error_info.get('message', 'Unknown error')
        error_type = error_info.get('type', '')
    except Exception:
        message = f"HTTP {status} error from Anthropic"
        error_type = ''
    
    # Map by status code and error type
    if status == 400:
        if error_type == 'invalid_request_error':
            if 'maximum context length' in message.lower() or 'too many tokens' in message.lower():
                return BadRequestError(
                    message=message,
                    code="context_length_exceeded",
                    provider_request_id=provider_request_id
                )
            elif 'max_tokens' in message.lower():
                return BadRequestError(
                    message=message,
                    code="invalid_param",
                    param="max_tokens",
                    provider_request_id=provider_request_id
                )
            else:
                return BadRequestError(
                    message=message,
                    code="invalid_request",
                    provider_request_id=provider_request_id
                )
        else:
            return BadRequestError(
                message=message,
                code="invalid_param",
                provider_request_id=provider_request_id
            )
    
    elif status == 401:
        return AuthError(
            message=message,
            provider_request_id=provider_request_id
        )
    
    elif status == 403:
        return PermissionError(
            message=message,
            code="model_disabled_for_org",
            provider_request_id=provider_request_id
        )
    
    elif status == 404:
        return ModelNotFoundError(
            model="unknown",
            provider_request_id=provider_request_id
        )
    
    elif status == 429:
        return RateLimitError(
            message=message,
            provider_request_id=provider_request_id
        )
    
    elif status >= 500:
        return UpstreamServerError(
            status_code=status,
            message=message,
            provider_request_id=provider_request_id
        )
    
    else:
        return ServerError(
            message=f"Unexpected Anthropic API response: {status} {message}",
            provider_request_id=provider_request_id
        )


def map_transport_error(error: Exception, provider: str = "unknown") -> StrataError:
    """
    Map HTTP transport errors to StrataError.
    
    Args:
        error: HTTP transport exception (httpx errors)
        provider: Provider name for context
        
    Returns:
        Appropriate StrataError instance
    """
    if isinstance(error, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TimeoutException)):
        timeout_seconds = 30  # Default timeout
        if hasattr(error, 'request') and hasattr(error.request, 'extensions'):
            timeout_seconds = error.request.extensions.get('timeout', {}).get('read', 30)
        
        return TimeoutError(
            timeout_seconds=int(timeout_seconds),
            provider_request_id=None
        )
    
    elif isinstance(error, httpx.HTTPStatusError):
        # Map by provider
        if 'openai' in provider.lower():
            return map_openai_error(error.response)
        elif 'anthropic' in provider.lower():
            return map_anthropic_error(error.response)
        else:
            # Generic mapping for unknown providers
            status = error.response.status_code
            provider_request_id = extract_provider_request_id(error.response)
            
            if status == 401:
                return AuthError(provider_request_id=provider_request_id)
            elif status == 429:
                return RateLimitError(provider_request_id=provider_request_id)
            elif status >= 500:
                return UpstreamServerError(
                    status_code=status,
                    provider_request_id=provider_request_id
                )
            else:
                return BadRequestError(
                    message=f"HTTP {status} error from {provider}",
                    provider_request_id=provider_request_id
                )
    
    else:
        # Generic network/connection errors
        return ServerError(
            message=f"Network error communicating with {provider}: {str(error)}"
        )


# Provider-specific error mappers
PROVIDER_ERROR_MAPPERS = {
    'openai': map_openai_error,
    'anthropic': map_anthropic_error
}


def map_provider_error(provider: str, response: httpx.Response) -> StrataError:
    """
    Map provider-specific error response to StrataError.
    
    Args:
        provider: Provider name (openai, anthropic, etc.)
        response: HTTP response from provider
        
    Returns:
        Appropriate StrataError instance
    """
    mapper = PROVIDER_ERROR_MAPPERS.get(provider.lower())
    if mapper:
        return mapper(response)
    else:
        # Generic fallback mapping
        status = response.status_code
        provider_request_id = extract_provider_request_id(response)
        
        if status == 401:
            return AuthError(provider_request_id=provider_request_id)
        elif status == 429:
            return RateLimitError(provider_request_id=provider_request_id)
        elif status >= 500:
            return UpstreamServerError(
                status_code=status,
                provider_request_id=provider_request_id
            )
        else:
            return BadRequestError(
                message=f"HTTP {status} error from {provider}",
                provider_request_id=provider_request_id
            )
