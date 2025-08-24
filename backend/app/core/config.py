from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "StrataAI"
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # Cache Configuration
    CACHE_TTL_DEFAULT: int = int(os.getenv("CACHE_TTL_DEFAULT", "300"))  # 5 minutes
    CACHE_TTL_MODELS: int = int(os.getenv("CACHE_TTL_MODELS", "3600"))  # 1 hour
    CACHE_TTL_ANALYTICS: int = int(os.getenv("CACHE_TTL_ANALYTICS", "60"))  # 1 minute
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # ScaleKit Configuration
    SCALEKIT_ENVIRONMENT_URL: str = os.getenv("SCALEKIT_ENVIRONMENT_URL", "")
    SCALEKIT_CLIENT_ID: str = os.getenv("SCALEKIT_CLIENT_ID", "")
    SCALEKIT_CLIENT_SECRET: str = os.getenv("SCALEKIT_CLIENT_SECRET", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
