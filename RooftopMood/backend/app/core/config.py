from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    weather_mode: str = "open_meteo"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_api_key: str | None = None
    weather_timeout_sec: float = 5.0
    weather_cache_ttl_sec: int = 900

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
