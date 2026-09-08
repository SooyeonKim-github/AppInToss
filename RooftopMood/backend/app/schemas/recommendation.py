from pydantic import BaseModel


class TodaySunsetInfo(BaseModel):
    date: str
    sunsetTime: str
    sunsetAzimuthDeg: float
    viewDirectionDeg: float | None = None
    position: str
    positionLabel: str
    alignmentScore: int
    visible: bool
    bestTime: str
    message: str
    confidence: float


class RecommendationItem(BaseModel):
    id: int
    name: str
    regionName: str
    address: str
    viewDescription: str
    bestSeatTip: str
    todaySunsetInfo: TodaySunsetInfo
    score: int
    tags: list[str]
    imageUrl: str | None = None


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationItem]


class SunsetBestResponse(BaseModel):
    recommendation: RecommendationItem
