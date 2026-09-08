from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
import time

import httpx

from app.core.config import settings
from app.services.sunset_service import SunsetResult

logger = logging.getLogger(__name__)

SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780


@dataclass(frozen=True)
class WeatherSnapshot:
    cloud_cover: int
    precipitation_probability: int
    visibility_km: float
    source: str = "UNKNOWN"
    forecast_time: str | None = None


class WeatherService:
    """일몰 전후의 실제 예보로 노을 조건을 계산하기 위한 서비스.

    기본 개발 모드는 Open-Meteo Forecast API를 사용한다. API 키 없이 프로토타입
    테스트가 가능하며, 상용 배포 시에는 OPEN_METEO_BASE_URL을 customer endpoint로
    바꾸고 OPEN_METEO_API_KEY를 설정할 수 있다.
    """

    _cache: dict[str, tuple[float, WeatherSnapshot]] = {}

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client

    def get_seoul_snapshot(self, sunset: SunsetResult | None = None) -> WeatherSnapshot:
        if settings.weather_mode.lower() == "mock":
            return self._mock_snapshot()

        sunset = sunset or self._fallback_sunset_today()
        cache_key = f"seoul:{sunset.date.isoformat()}:{sunset.sunset_time}"
        cached = self._cache.get(cache_key)
        now = time.monotonic()
        if cached and now - cached[0] < settings.weather_cache_ttl_sec:
            return cached[1]

        try:
            snapshot = self._fetch_open_meteo(
                latitude=SEOUL_LAT,
                longitude=SEOUL_LON,
                sunset=sunset,
            )
            self._cache[cache_key] = (now, snapshot)
            return snapshot
        except Exception as exc:
            logger.warning("weather API failed; using conservative fallback: %s", exc)
            return WeatherSnapshot(
                cloud_cover=65,
                precipitation_probability=45,
                visibility_km=8.0,
                source="FALLBACK",
                forecast_time=sunset.sunset_time,
            )

    def _fetch_open_meteo(
        self,
        latitude: float,
        longitude: float,
        sunset: SunsetResult,
    ) -> WeatherSnapshot:
        base_url = settings.open_meteo_base_url.rstrip("/")
        params: dict[str, str | float | int] = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "cloud_cover,precipitation_probability,visibility",
            "timezone": "Asia/Seoul",
            "start_date": sunset.date.isoformat(),
            "end_date": sunset.date.isoformat(),
        }
        if settings.open_meteo_api_key:
            params["apikey"] = settings.open_meteo_api_key

        close_client = self.client is None
        client = self.client or httpx.Client(timeout=settings.weather_timeout_sec)
        try:
            response = client.get(base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        finally:
            if close_client:
                client.close()

        return self._snapshot_from_payload(payload, sunset)

    @staticmethod
    def _snapshot_from_payload(payload: dict, sunset: SunsetResult) -> WeatherSnapshot:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        clouds = hourly.get("cloud_cover") or []
        rain_probs = hourly.get("precipitation_probability") or []
        visibility = hourly.get("visibility") or []

        if not times or not (len(times) == len(clouds) == len(rain_probs) == len(visibility)):
            raise ValueError("weather API response is missing hourly variables")

        sunset_dt = datetime.combine(sunset.date, datetime.min.time()).replace(
            hour=sunset.sunset_hour,
            minute=sunset.sunset_minute,
        )

        rows: list[tuple[datetime, float, float, float]] = []
        for raw_time, cloud, rain, vis_m in zip(times, clouds, rain_probs, visibility):
            if cloud is None or rain is None or vis_m is None:
                continue
            dt = datetime.fromisoformat(raw_time)
            if abs((dt - sunset_dt).total_seconds()) <= 3600:
                rows.append((dt, float(cloud), float(rain), float(vis_m)))

        if not rows:
            valid_rows = [
                (datetime.fromisoformat(t), float(c), float(r), float(v))
                for t, c, r, v in zip(times, clouds, rain_probs, visibility)
                if c is not None and r is not None and v is not None
            ]
            if not valid_rows:
                raise ValueError("weather API response contains no usable hourly row")
            rows = [min(valid_rows, key=lambda row: abs((row[0] - sunset_dt).total_seconds()))]

        cloud_cover = round(sum(row[1] for row in rows) / len(rows))
        precipitation_probability = round(max(row[2] for row in rows))
        visibility_km = round(min(row[3] for row in rows) / 1000.0, 1)
        representative = min(rows, key=lambda row: abs((row[0] - sunset_dt).total_seconds()))[0]

        return WeatherSnapshot(
            cloud_cover=max(0, min(100, cloud_cover)),
            precipitation_probability=max(0, min(100, precipitation_probability)),
            visibility_km=max(0.0, visibility_km),
            source="OPEN_METEO",
            forecast_time=representative.strftime("%H:%M"),
        )

    @staticmethod
    def _mock_snapshot() -> WeatherSnapshot:
        return WeatherSnapshot(
            cloud_cover=32,
            precipitation_probability=10,
            visibility_km=18.0,
            source="MOCK",
            forecast_time=None,
        )

    @staticmethod
    def _fallback_sunset_today() -> SunsetResult:
        from app.services.sunset_service import SunsetService
        return SunsetService().get_today(date.today())
