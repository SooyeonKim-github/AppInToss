from __future__ import annotations

from collections import Counter
from math import atan2, cos, degrees, radians, sin
import re

from analyzers.evidence_utils import compact_text, relevance_multiplier


class ViewDirectionEstimator:
    """카페의 '주 뷰 방향'을 가능한 근거만으로 추정한다.

    우선순위:
      1) 블로그 Evidence의 명시적 방위(서향/남서향/서쪽 시야 등)
      2) 확인된 랜드마크 좌표
      3) 한강/궁궐/숲 주 뷰의 지리적 target 좌표
      4) 그 외 UNKNOWN
    """

    CARDINALS = {
        "북향": 0.0, "북쪽": 0.0,
        "북동향": 45.0, "북동쪽": 45.0,
        "동향": 90.0, "동쪽": 90.0,
        "남동향": 135.0, "남동쪽": 135.0,
        "남향": 180.0, "남쪽": 180.0,
        "남서향": 225.0, "남서쪽": 225.0,
        "서향": 270.0, "서쪽": 270.0,
        "북서향": 315.0, "북서쪽": 315.0,
    }

    TARGETS = {
        "남산타워": (37.55117, 126.98823),
        "롯데월드타워": (37.51250, 127.10250),
        "경복궁": (37.57962, 126.97704),
        "창덕궁": (37.57943, 126.99104),
        "덕수궁": (37.56581, 126.97513),
        "북한산": (37.65874, 126.97700),
        "서울숲": (37.54439, 127.03744),
        "남산": (37.55117, 126.98823),
    }

    PALACE_TARGETS = {
        "경복궁": TARGETS["경복궁"],
        "창덕궁": TARGETS["창덕궁"],
        "덕수궁": TARGETS["덕수궁"],
    }
    FOREST_TARGETS = {
        "서울숲": TARGETS["서울숲"],
        "남산": TARGETS["남산"],
        "북한산": TARGETS["북한산"],
    }

    HAN_RIVER_LINE = [
        (37.5920, 126.8180),
        (37.5750, 126.8500),
        (37.5580, 126.8800),
        (37.5480, 126.9100),
        (37.5330, 126.9350),
        (37.5190, 126.9600),
        (37.5100, 126.9850),
        (37.5140, 127.0120),
        (37.5260, 127.0400),
        (37.5270, 127.0680),
        (37.5170, 127.0950),
        (37.5220, 127.1250),
    ]

    _EXPLICIT_PATTERN = re.compile(
        r"(?:뷰|루프탑|테라스|좌석|시야|창|난간)?.{0,10}"
        r"(북동향|남동향|남서향|북서향|북향|동향|남향|서향|북동쪽|남동쪽|남서쪽|북서쪽|북쪽|동쪽|남쪽|서쪽)"
        r".{0,12}(?:뷰|보이|바라|트여|열려|향|시야|난간|좌석)?"
    )

    def estimate(self, candidate: dict, features: dict, evidence_rows: list[dict]) -> dict:
        lat, lon = self._coords(candidate)
        if lat is None or lon is None:
            return self._empty("NO_CAFE_COORDINATES")

        explicit = self._explicit_direction(evidence_rows)
        if explicit:
            deg, count, total = explicit
            consistency = count / max(total, 1)
            confidence = min(0.96, 0.72 + min(count, 3) * 0.07 + consistency * 0.03)
            return self._result(deg, confidence, "EVIDENCE_CARDINAL", "", count)

        landmarks = [x for x in str(features.get("landmarks", "")).split("|") if x]
        for landmark in landmarks:
            target = self.TARGETS.get(landmark)
            if target:
                bearing = self.initial_bearing(lat, lon, *target)
                return self._result(bearing, 0.90, "LANDMARK_GEOMETRY", landmark, 1)

        main_view = features.get("main_view")
        if main_view == "HAN_RIVER":
            target = self._nearest_point_on_polyline(lat, lon, self.HAN_RIVER_LINE)
            bearing = self.initial_bearing(lat, lon, *target)
            return self._result(bearing, 0.76, "HAN_RIVER_GEOMETRY", "한강", 1)

        if main_view == "PALACE":
            name, target = self._nearest_target(lat, lon, self.PALACE_TARGETS)
            bearing = self.initial_bearing(lat, lon, *target)
            return self._result(bearing, 0.82, "PALACE_GEOMETRY", name, 1)

        if main_view == "FOREST":
            name, target = self._nearest_target(lat, lon, self.FOREST_TARGETS)
            bearing = self.initial_bearing(lat, lon, *target)
            return self._result(bearing, 0.68, "FOREST_GEOMETRY", name, 1)

        return self._empty("NO_RELIABLE_VIEW_DIRECTION")

    def _explicit_direction(self, rows: list[dict]) -> tuple[float, int, int] | None:
        counts: Counter[float] = Counter()
        seen_sources: set[str] = set()
        for row in rows:
            if relevance_multiplier(row.get("relevance_score")) <= 0:
                continue
            source = row.get("source_url") or f"{row.get('title','')}|{row.get('post_date','')}"
            if source in seen_sources:
                continue
            seen_sources.add(source)
            text = compact_text(row.get("title"), row.get("description"))
            for match in self._EXPLICIT_PATTERN.finditer(text):
                term = match.group(1)
                if term in self.CARDINALS:
                    counts[self.CARDINALS[term]] += 1
        if not counts:
            return None
        deg, count = counts.most_common(1)[0]
        return deg, count, sum(counts.values())

    @staticmethod
    def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        phi1, phi2 = radians(lat1), radians(lat2)
        dlon = radians(lon2 - lon1)
        y = sin(dlon) * cos(phi2)
        x = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dlon)
        return (degrees(atan2(y, x)) + 360) % 360

    @staticmethod
    def _coords(candidate: dict) -> tuple[float | None, float | None]:
        try:
            return float(candidate.get("latitude")), float(candidate.get("longitude"))
        except (TypeError, ValueError):
            return None, None

    @staticmethod
    def _nearest_target(lat: float, lon: float, targets: dict[str, tuple[float, float]]) -> tuple[str, tuple[float, float]]:
        name = min(targets, key=lambda n: (targets[n][0] - lat) ** 2 + ((targets[n][1] - lon) * cos(radians(lat))) ** 2)
        return name, targets[name]

    @classmethod
    def _nearest_point_on_polyline(
        cls, lat: float, lon: float, points: list[tuple[float, float]]
    ) -> tuple[float, float]:
        kx = cos(radians(lat))
        px, py = lon * kx, lat
        best = points[0]
        best_d2 = float("inf")
        for (lat1, lon1), (lat2, lon2) in zip(points, points[1:]):
            x1, y1 = lon1 * kx, lat1
            x2, y2 = lon2 * kx, lat2
            dx, dy = x2 - x1, y2 - y1
            denom = dx * dx + dy * dy
            t = 0.0 if denom == 0 else ((px - x1) * dx + (py - y1) * dy) / denom
            t = max(0.0, min(1.0, t))
            x, y = x1 + t * dx, y1 + t * dy
            d2 = (px - x) ** 2 + (py - y) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best = (y, x / kx)
        return best

    @staticmethod
    def _result(deg: float, confidence: float, source: str, target: str, evidence_count: int) -> dict:
        return {
            "view_direction_deg": round(deg % 360, 2),
            "view_direction_confidence": round(confidence, 3),
            "view_direction_source": source,
            "view_direction_target": target,
            "view_direction_evidence_count": evidence_count,
        }

    @staticmethod
    def _empty(reason: str) -> dict:
        return {
            "view_direction_deg": "",
            "view_direction_confidence": 0.0,
            "view_direction_source": "UNKNOWN",
            "view_direction_target": "",
            "view_direction_evidence_count": 0,
            "view_direction_reason": reason,
        }
