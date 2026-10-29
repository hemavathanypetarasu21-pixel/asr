from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelOption(BaseModel):
    id: str
    label: str


# backend/.env, independent of the working directory the server is started from
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, case_sensitive=True, extra="ignore")

    # Application
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    FRONTEND_URL: str

    # Server (server.py)
    SERVER_HOST: str
    SERVER_PORT: int
    SERVER_RELOAD: bool

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    # Supabase auth (access tokens verified against the project's JWKS)
    SUPABASE_URL: str
    SUPABASE_JWT_AUDIENCE: str

    # Uploads and listing
    MAX_UPLOAD_MB: int
    RECORDINGS_MAX_PAGE_SIZE: int
    FFPROBE_BINARY: str
    FFMPEG_BINARY: str

    # Dialect detection (Whisper language probabilities for Malay vs Tamil)
    DIALECT_DETECTION_MIN_CONFIDENCE: float
    DIALECT_DETECTION_MIN_MARGIN: float
    DIALECT_DETECTION_MAX_WINDOWS: int

    # Translation (Gemini). Users save their own key in Settings; this server key is the
    # fallback and may be left empty to require a per-user key.
    GEMINI_API_KEY: str
    GEMINI_TEMPERATURE: float
    # How long the list of models a Gemini key can use is cached
    GEMINI_MODEL_CACHE_SECONDS: int

    # Fernet key used to encrypt user API keys at rest
    ENCRYPTION_KEY: str

    # Dropdown options (JSON lists of {"id", "label"})
    RECOGNITION_MODELS: list[ModelOption]
    TRANSLATION_MODELS: list[ModelOption]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def supabase_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"


settings = Settings()
