from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    return int(raw_value)


@dataclass(frozen=True)
class Settings:
    service_name: str = "homecare-ccv-backend"
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = _int_env("API_PORT", 8000)

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_key: str | None = os.getenv("SUPABASE_SERVICE_KEY")
    supabase_anon_key: str | None = os.getenv("SUPABASE_ANON_KEY")

    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: str | None = os.getenv("TELEGRAM_WEBHOOK_URL")

    resend_api_key: str | None = os.getenv("RESEND_API_KEY")
    from_email: str = os.getenv("FROM_EMAIL", "alertas@homecareccv.co")

    ml_api_url: str = os.getenv("ML_API_URL", "http://localhost:8000")
    ml_model_path: str = os.getenv("ML_MODEL_PATH", "backend/ml/models/best_model.pkl")
    rag_chunk_size: int = _int_env("RAG_CHUNK_SIZE", 500)
    rag_overlap: int = _int_env("RAG_OVERLAP", 50)
    monitoring_interval_hours: int = _int_env("MONITORING_INTERVAL_HOURS", 6)


settings = Settings()
