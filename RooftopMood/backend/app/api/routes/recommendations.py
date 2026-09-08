from fastapi import APIRouter, HTTPException, Query

from app.repositories.cafe_repository import CafeRepository
from app.schemas.common import ViewCode
from app.schemas.recommendation import RecommendationListResponse, SunsetBestResponse
from app.services.recommendation_service import RecommendationService
from app.services.sunset_score_service import SunsetScoreService
from app.services.sunset_service import SunsetService
from app.services.weather_service import WeatherService

router = APIRouter(tags=["recommendations"])
repository = CafeRepository()
service = RecommendationService(repository)


def _context():
    sunset = SunsetService().get_today()
    weather = WeatherService().get_seoul_snapshot(sunset)
    score, _ = SunsetScoreService().calculate(weather)
    return sunset, score


@router.get("/recommendations", response_model=RecommendationListResponse)
def get_recommendations(
    view: ViewCode = Query(...),
    region: str = Query(..., min_length=2),
) -> RecommendationListResponse:
    sunset, condition_score = _context()
    items = service.recommend(view, region, sunset, condition_score)
    return RecommendationListResponse(recommendations=items)


@router.get("/recommendations/sunset-best", response_model=SunsetBestResponse)
def get_sunset_best() -> SunsetBestResponse:
    sunset, condition_score = _context()
    try:
        item = service.sunset_best(sunset, condition_score)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SunsetBestResponse(recommendation=item)
