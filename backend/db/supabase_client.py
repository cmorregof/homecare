from functools import lru_cache
from typing import Any

try:
    from supabase import Client, create_client
except ModuleNotFoundError:
    Client = Any
    create_client = None

from config import settings

PLACEHOLDER_MARKERS = ("xxxxx", "...", "eyJhbGciOiJIUzI1NiIs")


@lru_cache
def get_supabase_admin_client() -> Client:
    if (
        not settings.supabase_url
        or not settings.supabase_service_key
        or _looks_placeholder(settings.supabase_url)
        or _looks_placeholder(settings.supabase_service_key)
    ):
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required.")
    if create_client is None:
        raise RuntimeError("The supabase package is required to create a Supabase client.")
    return create_client(settings.supabase_url, settings.supabase_service_key)


def _looks_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)
