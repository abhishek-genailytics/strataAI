from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # Required (MVP)
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "StrataAI"
    ALLOWED_ORIGINS: str = "*"  # CSV format, default for demo
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # user client
    SUPABASE_SERVICE_KEY: str = ""  # service client for server-side ops
    ENCRYPTION_KEY: str = ""  # Fernet key for provider API keys
    
    # Optional (kept for parity, but unused in MVP Task 1)
    LOG_LEVEL: str = "INFO"
    ENABLE_REDIS: bool = False
    ENABLE_RATE_LIMITING: bool = False
    
    # Legacy fields (kept for compatibility with existing code)
    SUPABASE_JWT_SECRET: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_BURST: int = 10
    CACHE_TTL_DEFAULT: int = 300
    CACHE_TTL_MODELS: int = 3600
    CACHE_TTL_ANALYTICS: int = 60
    CACHE_ENABLED: bool = False
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert CSV ALLOWED_ORIGINS to list for CORS middleware"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Cached getter for settings"""
    return Settings()
