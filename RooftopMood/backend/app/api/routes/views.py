from fastapi import APIRouter

from app.repositories.cafe_repository import CafeRepository
from app.schemas.common import RegionResponseItem, ViewCode

router = APIRouter(tags=["views"])
repository = CafeRepository()


@router.get("/views/{view}/regions")
def get_regions(view: ViewCode) -> dict:
    regions = repository.find_regions_for_view(view)
    return {
        "view": view,
        "regions": [RegionResponseItem(**region) for region in regions],
    }
