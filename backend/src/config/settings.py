from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    WHATSAPP_VERIFY_TOKEN: Optional[str] = "dev_token"
    DO_SPACES_KEY: Optional[str] = None
    DO_SPACES_SECRET: Optional[str] = None
    DO_SPACES_ENDPOINT: Optional[str] = None
    DO_SPACES_BUCKET: Optional[str] = None
    DO_SPACES_REGION: str = "sgp1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()