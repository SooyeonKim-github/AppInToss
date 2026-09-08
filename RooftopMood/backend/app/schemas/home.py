from pydantic import BaseModel

from .common import ViewOption


class AppInfo(BaseModel):
    name: str
    description: str


class WeatherInfo(BaseModel):
    cloudCover: int
    precipitationProbability: int
    visibilityKm: float
    source: str
    forecastTime: str | None = None


class SunsetInfo(BaseModel):
    date: str
    time: str
    score: int
    message: str
    weather: WeatherInfo


class HomeResponse(BaseModel):
    app: AppInfo
    sunset: SunsetInfo
    views: list[ViewOption]
