from typing import Optional
from functools import lru_cache

# Import supabase only when needed to avoid hanging on import
_supabase_module = None

def _get_supabase_module():
    """Lazy import of supabase module"""
    global _supabase_module
    if _supabase_module is None:
        from supabase import create_client, Client
        _supabase_module = {'create_client': create_client, 'Client': Client}
    return _supabase_module

@lru_cache()
def get_supabase_user_client():
    """Lazy singleton for Supabase user client"""
    from .config import get_settings
    settings = get_settings()
    
    # Return None if Supabase is not configured (for MVP)
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None
    
    supabase_mod = _get_supabase_module()
    return supabase_mod['create_client'](settings.SUPABASE_URL, settings.SUPABASE_KEY)

@lru_cache()
def get_supabase_service_client():
    """Lazy singleton for Supabase service client (server-side operations)"""
    from .config import get_settings
    settings = get_settings()
    
    # Return None if Supabase is not configured (for MVP)
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return None
    
    supabase_mod = _get_supabase_module()
    return supabase_mod['create_client'](settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
