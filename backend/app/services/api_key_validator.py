"""
API key validation service for different AI providers.
"""
import re
import httpx
from typing import Dict, Optional
from app.models.api_key import APIKeyValidationResult


class APIKeyValidator:
    """Service for validating API keys against different providers."""
    
    # API key format patterns for different providers
    KEY_PATTERNS = {
        "openai": r"^sk-[a-zA-Z0-9_-]{10,}$",  # Very flexible: at least 10 chars after sk-
        "anthropic": r"^sk-ant-[a-zA-Z0-9_-]{10,}$",  # Flexible: sk-ant- followed by at least 10 chars
        "google": r"^AIza[0-9A-Za-z_-]{35}$",
    }
    
    # Validation endpoints for different providers
    VALIDATION_ENDPOINTS = {
        "openai": "https://api.openai.com/v1/models",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "google": "https://generativelanguage.googleapis.com/v1/models",
    }
    
    async def validate_api_key(self, api_key: str, provider_name: str) -> APIKeyValidationResult:
        """Validate an API key for a specific provider."""
        provider_name = provider_name.lower()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Starting validation for {provider_name} API key: {api_key[:10]}...")
        
        # First check format
        if not self._validate_key_format(api_key, provider_name):
            logger.error(f"Format validation failed for {provider_name} API key")
            return APIKeyValidationResult(
                is_valid=False,
                provider_name=provider_name,
                error_message=f"Invalid API key format for {provider_name}"
            )
        
        # Then validate with provider API
        try:
            is_valid, key_info, error_msg = await self._validate_with_provider(api_key, provider_name)
            return APIKeyValidationResult(
                is_valid=is_valid,
                provider_name=provider_name,
                error_message=error_msg,
                key_info=key_info
            )
        except Exception as e:
            return APIKeyValidationResult(
                is_valid=False,
                provider_name=provider_name,
                error_message=f"Validation error: {str(e)}"
            )
    
    def _validate_key_format(self, api_key: str, provider_name: str) -> bool:
        """Validate API key format using regex patterns."""
        pattern = self.KEY_PATTERNS.get(provider_name)
        if not pattern:
            # If no pattern defined, assume format is valid
            return True
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating {provider_name} API key format: {api_key[:10]}...")
        logger.info(f"Using pattern: {pattern}")
        
        is_valid = bool(re.match(pattern, api_key))
        logger.info(f"Format validation result: {is_valid}")
        
        return is_valid
    
    async def _validate_with_provider(self, api_key: str, provider_name: str) -> tuple[bool, Optional[Dict], Optional[str]]:
        """Validate API key by making a test request to the provider."""
        if provider_name == "openai":
            return await self._validate_openai_key(api_key)
        elif provider_name == "anthropic":
            return await self._validate_anthropic_key(api_key)
        elif provider_name == "google":
            return await self._validate_google_key(api_key)
        else:
            return False, None, f"Validation not implemented for provider: {provider_name}"
    
    async def _validate_openai_key(self, api_key: str) -> tuple[bool, Optional[Dict], Optional[str]]:
        """Validate OpenAI API key."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, {"models_count": len(data.get("data", []))}, None
                elif response.status_code == 401:
                    return False, None, "Invalid API key"
                else:
                    return False, None, f"API error: {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Request timeout"
        except Exception as e:
            return False, None, f"Network error: {str(e)}"
    
    async def _validate_anthropic_key(self, api_key: str) -> tuple[bool, Optional[Dict], Optional[str]]:
        """Validate Anthropic API key."""
        try:
            async with httpx.AsyncClient() as client:
                # Use a minimal test request
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}]
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, {"model": "claude-3-haiku-20240307"}, None
                elif response.status_code == 401:
                    return False, None, "Invalid API key"
                elif response.status_code == 400:
                    # Bad request might still indicate valid auth
                    error_data = response.json()
                    if "authentication" in str(error_data).lower():
                        return False, None, "Invalid API key"
                    return True, {"validated": True}, None
                else:
                    return False, None, f"API error: {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Request timeout"
        except Exception as e:
            return False, None, f"Network error: {str(e)}"
    
    async def _validate_google_key(self, api_key: str) -> tuple[bool, Optional[Dict], Optional[str]]:
        """Validate Google AI API key."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, {"models_count": len(data.get("models", []))}, None
                elif response.status_code == 403:
                    return False, None, "Invalid API key or insufficient permissions"
                else:
                    return False, None, f"API error: {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Request timeout"
        except Exception as e:
            return False, None, f"Network error: {str(e)}"


# Global validator instance
api_key_validator = APIKeyValidator()
