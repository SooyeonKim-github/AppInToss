from __future__ import annotations

from .weather_service import WeatherSnapshot


class SunsetScoreService:
    """일몰 전후 실제 예보를 0~100의 노을 기대도로 변환한다.

    - 구름: 완전 맑음보다 적당한 구름(약 20~45%)을 가장 높게 평가
    - 강수확률: 높을수록 강하게 감점
    - 가시거리: 20km 이상이면 최고점, 짧을수록 감점
    """

    def calculate(self, weather: WeatherSnapshot) -> tuple[int, str]:
        cloud_score = self._cloud_score(weather.cloud_cover)
        rain_score = max(0.0, 100.0 - weather.precipitation_probability * 1.35)
        visibility_score = max(0.0, min(100.0, weather.visibility_km / 20.0 * 100.0))

        score = round(
            cloud_score * 0.40
            + rain_score * 0.35
            + visibility_score * 0.25
        )
        score = max(0, min(100, score))

        if score >= 90:
            message = "오늘 노을 놓치면 아쉬워요 🔥"
        elif score >= 80:
            message = "오늘은 노을 보기 좋은 날이에요 🌇"
        elif score >= 60:
            message = "노을을 볼 가능성이 있어요 🙂"
        elif score >= 40:
            message = "구름이 많아 노을이 흐릴 수 있어요 ☁️"
        else:
            message = "오늘은 노을 보기 어려울 수 있어요 🌧️"
        return score, message

    @staticmethod
    def _cloud_score(cloud_cover: int) -> float:
        cloud = max(0, min(100, cloud_cover))
        if cloud < 10:
            return 78.0 + cloud * 0.7
        if cloud <= 45:
            return max(88.0, 100.0 - abs(cloud - 30) * 0.6)
        if cloud <= 70:
            return 88.0 - (cloud - 45) * 1.8
        return max(0.0, 43.0 - (cloud - 70) * 1.45)
