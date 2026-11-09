"""Central environment-driven configuration for Doc-Drift Guardian."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    google_api_key: str = ""
    adk_model: str = "gemini-3.5-flash-lite"
    github_token: str = ""
    database_url: str = "sqlite:///./docdrift.db"
    chroma_dir: str = "./chroma_store"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # google-genai/ADK reads credentials from the process environment. The
    # Settings object reads .env, but that alone does not populate os.environ.
    api_key = settings.google_api_key or settings.gemini_api_key
    if api_key:
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
        os.environ.setdefault("GEMINI_API_KEY", api_key)
    return settings
