from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _normalize_database_url(value: str) -> str:
    """Make Railway-style PostgreSQL URLs use the installed psycopg v3 driver."""
    value = value.strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    cors_origins: tuple[str, ...]
    db_pool_size: int
    db_max_overflow: int
    db_pool_recycle_seconds: int

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def allow_all_origins(self) -> bool:
        return "*" in self.cors_origins


def load_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    database_url = _normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./jeomechu.db")
    )

    raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    cors_origins = tuple(
        item.strip() for item in raw_origins.split(",") if item.strip()
    ) or ("http://localhost:5173",)

    return Settings(
        environment=environment,
        database_url=database_url,
        cors_origins=cors_origins,
        db_pool_size=_as_int("DB_POOL_SIZE", 5),
        db_max_overflow=_as_int("DB_MAX_OVERFLOW", 10),
        db_pool_recycle_seconds=_as_int("DB_POOL_RECYCLE_SECONDS", 300),
    )


settings = load_settings()
