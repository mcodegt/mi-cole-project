from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILES = (BACKEND_DIR / ".env", Path(".env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Opción A: URL completa (Docker / CI)
    database_url: Optional[str] = None

    # Opción B: componentes (desarrollo local — backend/.env)
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "postgres"
    database_password: str = ""
    database_name: str = "mi_cole_db"

    jwt_secret: str = "change-me-in-production"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    cors_origins: str = "http://localhost:4200"
    superadmin_email: str = "superadmin@micole.dev"
    superadmin_password: str = "ChangeMe123!"
    superadmin_name: str = "Super Admin"
    static_root: Optional[str] = None
    storage_root: Optional[str] = None
    platform_login_logo_url: Optional[str] = None
    platform_login_subtitle: str = "Mi Cole — Plataforma educativa"
    platform_login_primary_color: str = "#2563eb"

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            password = quote_plus(self.database_password)
            self.database_url = (
                f"postgresql+psycopg://{self.database_user}:{password}"
                f"@{self.database_host}:{self.database_port}/{self.database_name}"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
