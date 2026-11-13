from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VoxLedger AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./voxledger.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # WebSocket / Realtime Voice Streaming Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    VOICE_STREAM_SAMPLE_RATE: int = 16000
    VOICE_STREAM_CHANNELS: int = 1

    # Gnani AI (Prisma v3.0 & Timbre v3.0) Configuration
    GNANI_API_KEY: SecretStr = SecretStr("")
    GNANI_STT_MODEL: str = "prisma-v3.0"
    GNANI_TTS_MODEL: str = "timbre-v3.0"
    GNANI_STT_ENABLED: bool = True
    GNANI_TTS_ENABLED: bool = True
    GNANI_STT_WS_URL: str = "wss://api.vachana.ai/stt/v3/stream"
    GNANI_TTS_API_URL: str = "https://api.vachana.ai/api/v1/tts/inference"
    GNANI_TTS_DEFAULT_VOICE: str = "Shivani"
    GNANI_DEFAULT_LANGUAGE: str = "hi-IN"
    GNANI_TIMEOUT_SECONDS: float = 15.0

    @property
    def has_gnani_credentials(self) -> bool:
        val = self.GNANI_API_KEY.get_secret_value()
        return bool(val and len(val) > 10 and not val.lower().startswith("your_"))

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
