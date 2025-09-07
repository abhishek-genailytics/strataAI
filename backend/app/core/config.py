from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "StrataAI"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"]  # Allow frontend domains
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_USAGE_ROLLUPS: bool = True
    ENABLE_PLAYGROUND_LOGGING: bool = True

    # Feature flags
    FORCE_ECHO_ADAPTER: bool = False
    PLAYGROUND_RESP_HEADERS: bool = True  # Mirror /v1 response headers in playground

    # Supabase (service + anon)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""                 # anon (client) if you need it
    SUPABASE_SERVICE_KEY: str = ""         # server-side

    # Crypto (Fernet for provider keys)
    ENCRYPTION_KEY: str = ""               # base64 Fernet key

    # Providers — OpenAI
    OPENAI_BASE_URL: str = "https://api.openai.com"
    OPENAI_CONNECT_TIMEOUT_S: float = 10.0
    OPENAI_READ_TIMEOUT_S: float = 60.0
    OPENAI_WRITE_TIMEOUT_S: float = 60.0

    # Providers — Anthropic
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_VERSION: str = "2023-06-01"
    ANTHROPIC_CONNECT_TIMEOUT_S: float = 10.0
    ANTHROPIC_READ_TIMEOUT_S: float = 60.0
    ANTHROPIC_WRITE_TIMEOUT_S: float = 60.0

    # Legacy fields (kept for compatibility with existing code)
    SUPABASE_JWT_SECRET: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    ENABLE_REDIS: bool = False
    ENABLE_RATE_LIMITING: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_BURST: int = 10
    CACHE_TTL_DEFAULT: int = 300
    CACHE_TTL_MODELS: int = 3600
    CACHE_TTL_ANALYTICS: int = 60
    CACHE_ENABLED: bool = False
    OPENAI_TOTAL_TIMEOUT_S: float = 65.0  # optional upper bound
    ANTHROPIC_TOTAL_TIMEOUT_S: float = 65.0  # optional upper bound

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["*"]  # Default to allow all if empty
            if v == "*":
                return ["*"]
            return [s.strip() for s in v.split(",") if s.strip()]
        return v if v is not None else ["*"]

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS to list for CORS middleware (backward compatibility)"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            if self.ALLOWED_ORIGINS == "*":
                return ["*"]
            return [s.strip() for s in self.ALLOWED_ORIGINS.split(",") if s.strip()]
        return self.ALLOWED_ORIGINS

    def safe_export(self) -> dict:
        """Return non-sensitive snapshot for startup logs."""
        redacted = {"<redacted>"}
        return {
            "PROJECT_NAME": self.PROJECT_NAME,
            "API_V1_STR": self.API_V1_STR,
            "LOG_LEVEL": self.LOG_LEVEL,
            "ALLOWED_ORIGINS": self.ALLOWED_ORIGINS,
            "FEATURE_FLAGS": {
                "FORCE_ECHO_ADAPTER": self.FORCE_ECHO_ADAPTER,
                "ENABLE_REQUEST_LOGGING": self.ENABLE_REQUEST_LOGGING,
                "ENABLE_USAGE_ROLLUPS": self.ENABLE_USAGE_ROLLUPS,
                "ENABLE_PLAYGROUND_LOGGING": self.ENABLE_PLAYGROUND_LOGGING,
                "PLAYGROUND_RESP_HEADERS": self.PLAYGROUND_RESP_HEADERS,
            },
            "PROVIDERS": {
                "openai": {
                    "base_url": self.OPENAI_BASE_URL,
                    "timeouts": [self.OPENAI_CONNECT_TIMEOUT_S, self.OPENAI_READ_TIMEOUT_S, self.OPENAI_WRITE_TIMEOUT_S]
                },
                "anthropic": {
                    "base_url": self.ANTHROPIC_BASE_URL,
                    "version": self.ANTHROPIC_VERSION,
                    "timeouts": [self.ANTHROPIC_CONNECT_TIMEOUT_S, self.ANTHROPIC_READ_TIMEOUT_S, self.ANTHROPIC_WRITE_TIMEOUT_S]
                },
            },
            "SUPABASE": {"url": self.SUPABASE_URL, "keys": list(redacted)},
            "CRYPTO": list(redacted),
        }

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Cached getter for settings"""
    return Settings()
