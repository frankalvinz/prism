from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import OAUTH_CALLBACK_PATH


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PRISM"
    app_version: str = "0.1.0"
    analyzer_version: str = "0.1.0"

    github_api_base: str = "https://api.github.com"
    github_token: str | None = None
    github_user_agent: str = "PRISM-PR-Analyzer/0.1"

    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    session_secret: str | None = None
    public_web_url: str = "http://localhost:3000"
    session_ttl_seconds: int = 8 * 60 * 60

    max_files: int = 100
    max_patch_size: int = 200_000
    max_total_diff_size: int = 1_000_000

    cache_ttl_seconds: int = 300
    cache_enabled: bool = True

    ai_enabled: bool = False
    ai_provider: str = "null"
    ai_model: str | None = None
    ai_base_url: str | None = None

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def oauth_enabled(self) -> bool:
        return bool(self.github_oauth_client_id and self.github_oauth_client_secret)

    @property
    def oauth_callback_url(self) -> str:
        return f"{self.public_web_url.rstrip('/')}{OAUTH_CALLBACK_PATH}"

    @property
    def cookie_secure(self) -> bool:
        return self.public_web_url.lower().startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
