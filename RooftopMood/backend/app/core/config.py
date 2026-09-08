from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    # json: 기존 샘플 데이터 / supabase: 운영 DB
    data_backend: str = "json"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "cafe-photos"
    photo_upload_enabled: bool = True
    photo_max_bytes: int = 10 * 1024 * 1024
    photo_max_side_px: int = 1600
    photo_webp_quality: int = 85

    weather_mode: str = "open_meteo"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_api_key: str | None = None
    weather_timeout_sec: float = 5.0
    weather_cache_ttl_sec: int = 900

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
