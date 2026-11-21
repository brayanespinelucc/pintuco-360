from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pintuco 360"
    environment: str = "development"
    cors_origins: str = "http://localhost:8501"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    public_app_url: str = "https://colorlink-web-4jb5.onrender.com"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
