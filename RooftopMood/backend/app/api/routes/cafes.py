from fastapi import APIRouter, HTTPException

from app.repositories.cafe_repository import CafeRepository
from app.services.recommendation_service import RecommendationService
from app.services.sunset_service import SunsetService

router = APIRouter(tags=["cafes"])
repository = CafeRepository()
recommendation_service = RecommendationService(repository)


@router.get("/cafes/{cafe_id}")
def get_cafe(cafe_id: int) -> dict:
    cafe = repository.get(cafe_id)
    if cafe is None:
        raise HTTPException(status_code=404, detail="카페를 찾을 수 없습니다.")
    sunset = SunsetService().get_today()
    return {
        "cafe": cafe,
        "todaySunsetInfo": recommendation_service.cafe_today_sunset_info(cafe, sunset).model_dump(),
    }
