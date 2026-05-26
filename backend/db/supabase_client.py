from functools import lru_cache
from typing import Any

try:
    from supabase import Client, create_client
except ModuleNotFoundError:
    Client = Any
    create_client = None

from config import settings


@lru_cache
def get_supabase_admin_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required.")
    if create_client is None:
        raise RuntimeError("The supabase package is required to create a Supabase client.")
    return create_client(settings.supabase_url, settings.supabase_service_key)
