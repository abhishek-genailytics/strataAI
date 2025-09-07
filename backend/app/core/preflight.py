"""Preflight validation for application startup."""

import sys
from typing import List
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Environment variables that must be present in production
REQUIRED_IN_PROD = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY", 
    "ENCRYPTION_KEY"
]

# Environment variables that should be present but aren't critical
RECOMMENDED_VARS = [
    "SUPABASE_KEY",  # anon key for any client-side operations
]


def validate_required_env() -> List[str]:
    """Check for required environment variables."""
    settings = get_settings()
    missing = []
    
    for var_name in REQUIRED_IN_PROD:
        value = getattr(settings, var_name, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(var_name)
    
    return missing


def validate_recommended_env() -> List[str]:
    """Check for recommended environment variables."""
    settings = get_settings()
    missing = []
    
    for var_name in RECOMMENDED_VARS:
        value = getattr(settings, var_name, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(var_name)
    
    return missing


def validate_security_settings() -> List[str]:
    """Check security-related configuration."""
    settings = get_settings()
    warnings = []
    
    # Check CORS configuration
    if settings.ALLOWED_ORIGINS == ["*"]:
        warnings.append("ALLOWED_ORIGINS is set to '*' - consider tightening for production")
    
    # Check if we're in a development-like environment
    if settings.FORCE_ECHO_ADAPTER:
        warnings.append("FORCE_ECHO_ADAPTER is enabled - ensure this is intentional")
    
    return warnings


def validate_provider_config() -> List[str]:
    """Validate provider configuration."""
    settings = get_settings()
    issues = []
    
    # Check timeout values are reasonable
    if settings.OPENAI_CONNECT_TIMEOUT_S <= 0:
        issues.append("OPENAI_CONNECT_TIMEOUT_S must be positive")
    
    if settings.OPENAI_READ_TIMEOUT_S <= 0:
        issues.append("OPENAI_READ_TIMEOUT_S must be positive")
        
    if settings.ANTHROPIC_CONNECT_TIMEOUT_S <= 0:
        issues.append("ANTHROPIC_CONNECT_TIMEOUT_S must be positive")
        
    if settings.ANTHROPIC_READ_TIMEOUT_S <= 0:
        issues.append("ANTHROPIC_READ_TIMEOUT_S must be positive")
    
    # Check base URLs are valid
    if not settings.OPENAI_BASE_URL.startswith(("http://", "https://")):
        issues.append("OPENAI_BASE_URL must be a valid HTTP/HTTPS URL")
        
    if not settings.ANTHROPIC_BASE_URL.startswith(("http://", "https://")):
        issues.append("ANTHROPIC_BASE_URL must be a valid HTTP/HTTPS URL")
    
    return issues


def run_preflight() -> None:
    """Run all preflight checks and fail fast if critical issues found."""
    
    logger.info("Starting preflight validation")
    
    # Check required environment variables
    missing_required = validate_required_env()
    if missing_required:
        error_msg = f"Missing required environment variables: {', '.join(missing_required)}"
        logger.error("preflight_failed", error=error_msg, missing_vars=missing_required)
        raise RuntimeError(error_msg)
    
    # Check recommended environment variables (warnings only)
    missing_recommended = validate_recommended_env()
    if missing_recommended:
        logger.warning(
            "Missing recommended environment variables", 
            missing_vars=missing_recommended
        )
    
    # Check security settings (warnings only)
    security_warnings = validate_security_settings()
    for warning in security_warnings:
        logger.warning("security_warning", message=warning)
    
    # Check provider configuration
    provider_issues = validate_provider_config()
    if provider_issues:
        error_msg = f"Provider configuration issues: {'; '.join(provider_issues)}"
        logger.error("preflight_failed", error=error_msg, issues=provider_issues)
        raise RuntimeError(error_msg)
    
    logger.info("Preflight validation completed successfully")


def run_preflight_safe() -> bool:
    """Run preflight checks and return success status instead of raising."""
    try:
        run_preflight()
        return True
    except Exception as e:
        logger.error("preflight_validation_failed", error=str(e))
        return False
