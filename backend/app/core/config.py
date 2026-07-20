from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AttackChainGen"
    app_env: str = "development"
    secret_key: str = "change-me-to-a-long-random-secret-key-32chars"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://attackchain:strongpassword@localhost:5432/attackchaindb"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Elasticsearch (defaults, overridden per-stand)
    elastic_url: str = "https://localhost:9200"
    elastic_api_key: str = ""
    elastic_index_prefix: str = "logs-attackchain"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # First Admin
    admin_email: str = "admin@attackchain.local"
    admin_password: str = "Admin1234!"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
