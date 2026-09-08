from datetime import datetime, timedelta
from math import cos, radians
from urllib.parse import quote

from app.repositories.cafe_repository import CafeRepository
from app.schemas.recommendation import RecommendationItem, TodaySunsetInfo
from app.services.sunset_service import SunsetResult, SunsetService

VIEW_LABELS = {
    "HAN_RIVER": "🌊 한강뷰",
    "CITY": "🏙️ 시티뷰",
    "PALACE": "🏯 궁궐뷰",
    "FOREST": "🌳 숲뷰",
}


class RecommendationService:
    FRONT_THRESHOLD_DEG = 22.0
    SIDE_VISIBLE_THRESHOLD_DEG = 110.0

    def __init__(self, repository: CafeRepository) -> None:
        self.repository = repository

    @staticmethod
    def _best_time(sunset: SunsetResult, start_before: int = 24, end_after: int = 8) -> str:
        base = datetime.combine(sunset.date, datetime.min.time()).replace(
            hour=sunset.sunset_hour,
            minute=sunset.sunset_minute,
        )
        start = base - timedelta(minutes=start_before)
        end = base + timedelta(minutes=end_after)
        return f"{start:%H:%M} ~ {end:%H:%M}"

    @staticmethod
    def _signed_delta(view_deg: float, sunset_deg: float) -> float:
        return (sunset_deg - view_deg + 180) % 360 - 180

    @staticmethod
    def _orientation_score(view_direction_deg: float | None, sunset_azimuth_deg: float) -> float:
        if view_direction_deg is None:
            return 35.0
        diff = abs((sunset_azimuth_deg - view_direction_deg + 180) % 360 - 180)
        if diff >= 90:
            return 0.0
        return max(0.0, cos(radians(diff)) * 100)

    @staticmethod
    def _view_direction(cafe: dict) -> tuple[float | None, float]:
        raw = cafe.get("viewDirectionDeg")
        confidence = cafe.get("viewDirectionConfidence")
        if raw in (None, ""):
            raw = cafe.get("orientationDeg")
            confidence = 0.65 if raw not in (None, "") else 0.0
        try:
            return float(raw), float(confidence or 0.0)
        except (TypeError, ValueError):
            return None, 0.0

    @staticmethod
    def _kakao_map_url(cafe: dict) -> str:
        for key in ("kakaoMapUrl", "placeUrl", "place_url", "sourceUrl", "source_url"):
            value = cafe.get(key)
            if value and "kakao" in str(value).lower():
                return str(value)
        return f"https://map.kakao.com/link/search/{quote(str(cafe.get('name', '카페')))}"

    def _cafe_sunset(self, cafe: dict, reference_sunset: SunsetResult) -> SunsetResult:
        try:
            return SunsetService().get_for_location(
                reference_sunset.date,
                float(cafe.get("latitude")),
                float(cafe.get("longitude")),
            )
        except (TypeError, ValueError):
            return reference_sunset

    def _today_sunset_info(self, cafe: dict, reference_sunset: SunsetResult) -> TodaySunsetInfo:
        cafe_sunset = self._cafe_sunset(cafe, reference_sunset)
        view_deg, direction_confidence = self._view_direction(cafe)

        if view_deg is None:
            position = "UNKNOWN"
            position_label = "방향 확인 필요"
            alignment = 0
            visible = False
            message = "오늘 노을 방향을 정확히 판단하기 어려워요."
            confidence = 0.0
        else:
            delta = self._signed_delta(view_deg, cafe_sunset.sunset_azimuth_deg)
            abs_delta = abs(delta)
            if abs_delta <= self.FRONT_THRESHOLD_DEG:
                position = "FRONT"
                position_label = "정면"
                message = "오늘 노을은 정면에서 보여요 🌇"
            elif delta > 0 and abs_delta <= self.SIDE_VISIBLE_THRESHOLD_DEG:
                position = "RIGHT"
                position_label = "오른쪽"
                message = "오늘 노을은 오른쪽 방향에서 보여요 🌇"
            elif delta < 0 and abs_delta <= self.SIDE_VISIBLE_THRESHOLD_DEG:
                position = "LEFT"
                position_label = "왼쪽"
                message = "오늘 노을은 왼쪽 방향에서 보여요 🌇"
            else:
                position = "OUT_OF_VIEW"
                position_label = "시야 밖"
                message = "오늘은 메인 뷰 방향에서 노을이 잘 보이지 않아요."

            alignment = round(self._orientation_score(view_deg, cafe_sunset.sunset_azimuth_deg))
            visible = position in {"FRONT", "RIGHT", "LEFT"}
            confidence = round(max(0.0, min(0.98, direction_confidence * 0.97)), 3)

        return TodaySunsetInfo(
            date=cafe_sunset.date.isoformat(),
            sunsetTime=cafe_sunset.sunset_time,
            sunsetAzimuthDeg=cafe_sunset.sunset_azimuth_deg,
            viewDirectionDeg=round(view_deg, 2) if view_deg is not None else None,
            position=position,
            positionLabel=position_label,
            alignmentScore=alignment,
            visible=visible,
            bestTime=self._best_time(cafe_sunset),
            message=message,
            confidence=confidence,
        )

    def _score(self, cafe: dict, selected_view: str | None, sunset: SunsetResult, sunset_condition_score: int) -> int:
        view_score = (
            cafe["views"].get(selected_view, 0) / 5 * 100
            if selected_view
            else cafe.get("sunsetViewScore", 0) / 5 * 100
        )
        cafe_sunset = self._cafe_sunset(cafe, sunset)
        view_deg, _ = self._view_direction(cafe)
        score = (
            self._orientation_score(view_deg, cafe_sunset.sunset_azimuth_deg) * 0.30
            + sunset_condition_score * 0.25
            + view_score * 0.20
            + cafe.get("openViewScore", 3) / 5 * 100 * 0.10
            + cafe.get("cafeQualityScore", 3) / 5 * 100 * 0.10
            + 100 * 0.05
        )
        return max(0, min(100, round(score)))

    def _to_item(self, cafe: dict, score: int, sunset: SunsetResult, selected_view: str | None) -> RecommendationItem:
        tags = [
            VIEW_LABELS[code]
            for code, rating in cafe["views"].items()
            if rating >= 4 and code in VIEW_LABELS
        ]
        if selected_view and VIEW_LABELS[selected_view] not in tags:
            tags.insert(0, VIEW_LABELS[selected_view])
        return RecommendationItem(
            id=cafe["id"],
            name=cafe["name"],
            regionName=cafe["region"]["name"],
            address=cafe["address"],
            viewDescription=cafe["viewDescription"],
            bestSeatTip=cafe["bestSeatTip"],
            todaySunsetInfo=self._today_sunset_info(cafe, sunset),
            score=score,
            tags=tags[:3],
            imageUrl=cafe.get("imageUrl"),
            photoStatus=cafe.get("photoStatus"),
            canUploadPhoto=bool(cafe.get("canUploadPhoto", cafe.get("imageUrl") is None)),
            kakaoMapUrl=self._kakao_map_url(cafe),
        )

    def recommend(self, view: str, region: str, sunset: SunsetResult, sunset_condition_score: int, limit: int = 5) -> list[RecommendationItem]:
        cafes = self.repository.find_by_view_region(view, region)
        ranked = sorted(
            ((cafe, self._score(cafe, view, sunset, sunset_condition_score)) for cafe in cafes),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [self._to_item(cafe, score, sunset, view) for cafe, score in ranked[:limit]]

    def sunset_best(self, sunset: SunsetResult, sunset_condition_score: int, limit: int = 5) -> list[RecommendationItem]:
        cafes = self.repository.all()
        ranked = sorted(
            (
                (cafe, self._score(cafe, None, sunset, sunset_condition_score))
                for cafe in cafes
                if cafe.get("active", True)
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        if not ranked:
            raise ValueError("추천 가능한 카페가 없습니다.")
        return [self._to_item(cafe, score, sunset, None) for cafe, score in ranked[:limit]]

    def cafe_today_sunset_info(self, cafe: dict, sunset: SunsetResult) -> TodaySunsetInfo:
        return self._today_sunset_info(cafe, sunset)
