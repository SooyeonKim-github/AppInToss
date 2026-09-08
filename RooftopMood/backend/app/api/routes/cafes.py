import httpx
from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from app.repositories.cafe_repository import CafeRepository
from app.services.photo_service import PhotoService, PhotoUploadError
from app.services.recommendation_service import RecommendationService
from app.services.sunset_service import SunsetService

router = APIRouter(tags=["cafes"])
repository = CafeRepository()
recommendation_service = RecommendationService(repository)
photo_service = PhotoService()


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


@router.post("/cafes/{cafe_id}/photo", status_code=201)
async def upload_cafe_photo(
    cafe_id: int,
    file: UploadFile = File(...),
    user_key: str | None = Header(default=None, alias="X-User-Key"),
) -> dict:
    cafe = repository.get(cafe_id)
    if cafe is None:
        raise HTTPException(status_code=404, detail="카페를 찾을 수 없습니다.")

    try:
        return await photo_service.upload(cafe_id, file, uploaded_by=user_key)
    except PhotoUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="사진 저장소와 통신하는 중 문제가 발생했어요.",
        ) from exc
