from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be configured")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_supabase_service_client() -> Client:
    """Create and return a Supabase service client instance that bypasses RLS."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("Supabase URL and Service Key must be configured")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Global client instances
supabase: Client = get_supabase_client()  # For user operations (with RLS)
supabase_service: Client = get_supabase_service_client()  # For admin operations (bypasses RLS)
