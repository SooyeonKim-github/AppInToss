from fastapi import APIRouter

from app.schemas.common import ViewOption
from app.schemas.home import AppInfo, HomeResponse, SunsetInfo, WeatherInfo
from app.services.sunset_score_service import SunsetScoreService
from app.services.sunset_service import SunsetService
from app.services.weather_service import WeatherService

router = APIRouter(tags=["home"])

VIEWS = [
    ViewOption(code="HAN_RIVER", name="한강뷰", emoji="🌊"),
    ViewOption(code="CITY", name="시티뷰", emoji="🏙️"),
    ViewOption(code="PALACE", name="궁궐뷰", emoji="🏯"),
    ViewOption(code="FOREST", name="숲뷰", emoji="🌳"),
]


@router.get("/home", response_model=HomeResponse)
def get_home() -> HomeResponse:
    sunset = SunsetService().get_today()
    weather = WeatherService().get_seoul_snapshot(sunset)
    score, message = SunsetScoreService().calculate(weather)
    return HomeResponse(
        app=AppInfo(
            name="루프탑무드",
            description="노을이 예쁜 서울 루프탑 카페를 찾아드려요.",
        ),
        sunset=SunsetInfo(
            date=sunset.date.isoformat(),
            time=sunset.sunset_time,
            score=score,
            message=message,
            weather=WeatherInfo(
                cloudCover=weather.cloud_cover,
                precipitationProbability=weather.precipitation_probability,
                visibilityKm=weather.visibility_km,
                source=weather.source,
                forecastTime=weather.forecast_time,
            ),
        ),
        views=VIEWS,
    )
