from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Growing AI Tutor"
    app_password: str = "change-me-before-deployment"
    session_secret: str = "dev-only-secret-change-me"
    session_https_only: bool = False
    database_url: str = "sqlite:///./data/tutor.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
