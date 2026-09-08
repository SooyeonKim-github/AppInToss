from __future__ import annotations

from analyzers.view_direction_estimator import ViewDirectionEstimator
from utils import haversine_m


class KakaoSignalClassifier:
    """Kakao Local 검색 신호 + Daum 블로그 Evidence를 보수적으로 결합한다.

    자동 분류는 최대 STRONG_PROBABLE까지만 만든다. CONFIRMED는 관리자/사진 등
    별도 검증 이후에만 부여하는 상태로 남긴다.
    """

    ROOFTOP_STRONG = ("루프탑", "옥상", "rooftop")
    ROOFTOP_MEDIUM = ("테라스", "야외")
    VIEW_TERMS = {
        "HAN_RIVER": {"direct": ("한강뷰", "한강 뷰", "리버뷰", "리버 뷰"), "weak": ("한강",)},
        "CITY": {"direct": ("시티뷰", "시티 뷰", "도심뷰", "도심 뷰", "서울야경", "서울 야경", "스카이라인"), "weak": ("야경", "도심")},
        "PALACE": {"direct": ("궁궐뷰", "궁궐 뷰", "경복궁뷰", "경복궁 뷰", "창덕궁뷰", "창덕궁 뷰", "덕수궁뷰", "덕수궁 뷰"), "weak": ("궁궐", "경복궁", "창덕궁", "덕수궁")},
        "FOREST": {"direct": ("숲뷰", "숲 뷰", "서울숲뷰", "서울숲 뷰", "녹지뷰", "녹지 뷰"), "weak": ("서울숲", "숲", "녹지", "남산")},
    }

    def classify_all(self, candidates: list[dict], evidence_by_id: dict[str, dict] | None = None) -> list[dict]:
        evidence_by_id = evidence_by_id or {}
        return [self.classify(cafe, evidence_by_id.get(str(cafe.get("cafe_id", "")), {})) for cafe in candidates]

    def classify(self, cafe: dict, evidence: dict | None = None) -> dict:
        evidence = evidence or {}
        queries = self._queries(cafe)
        hit_ratio = self._hit_ratio(cafe, queries)
        rooftop = self._classify_rooftop(cafe, queries, hit_ratio, evidence)
        result = {
            "cafe_id": cafe.get("cafe_id", ""),
            "cafe_name": cafe.get("name", ""),
            "region_code": cafe.get("region_code", ""),
            **rooftop,
        }
        for code, terms in self.VIEW_TERMS.items():
            view = self._classify_view(cafe, queries, terms, hit_ratio, evidence, code)
            result.update({f"{code.lower()}_{key}": value for key, value in view.items()})
        return result

    def signal_summary(self, cafe: dict, evidence: dict | None = None) -> dict:
        evidence = evidence or {}
        queries = self._queries(cafe)
        families = self._query_families(queries)
        return {
            "cafe_id": cafe.get("cafe_id", ""),
            "cafe_name": cafe.get("name", ""),
            "region_code": cafe.get("region_code", ""),
            "raw_match_count": self._int(cafe.get("raw_match_count"), len(queries)),
            "matched_query_count": self._int(cafe.get("matched_query_count"), len(queries)),
            "region_query_total": self._int(cafe.get("region_query_total"), len(queries) or 1),
            "query_hit_ratio": round(self._hit_ratio(cafe, queries), 3),
            "query_family_count": len(families),
            "query_families": "|".join(sorted(families)),
            "matched_queries": "|".join(queries),
            "rooftop_query_hits": self._count_query_hits(queries, self.ROOFTOP_STRONG),
            "han_river_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["HAN_RIVER"]),
            "city_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["CITY"]),
            "palace_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["PALACE"]),
            "forest_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["FOREST"]),
            "blog_rooftop_evidence": self._int(evidence.get("ROOFTOP")),
            "blog_sunset_evidence": self._int(evidence.get("SUNSET")),
            "blog_han_river_evidence": self._int(evidence.get("HAN_RIVER")),
            "blog_city_evidence": self._int(evidence.get("CITY")),
            "blog_palace_evidence": self._int(evidence.get("PALACE")),
            "blog_forest_evidence": self._int(evidence.get("FOREST")),
            "tistory_rooftop_evidence": self._int(evidence.get("TISTORY_ROOFTOP")),
            "tistory_total_evidence": self._int(evidence.get("TISTORY_TOTAL")),
        }

    def _classify_rooftop(self, cafe: dict, queries: list[str], hit_ratio: float, evidence: dict) -> dict:
        strong_hits = self._count_query_hits(queries, self.ROOFTOP_STRONG)
        medium_hits = self._count_query_hits(queries, self.ROOFTOP_MEDIUM)
        blog_hits = self._int(evidence.get("ROOFTOP"))
        tistory_hits = self._int(evidence.get("TISTORY_ROOFTOP"))

        place_text = f"{cafe.get('name', '')} {cafe.get('category', '')}".lower()
        place_strong = int(any(term in place_text for term in self.ROOFTOP_STRONG))
        place_medium = int(any(term in place_text for term in self.ROOFTOP_MEDIUM))

        score = 0.0
        if strong_hits >= 1:
            score += 1.0
        if strong_hits >= 2:
            score += 0.75
        if medium_hits >= 1:
            score += 0.4
        if hit_ratio >= 0.5:
            score += 0.5
        if place_strong:
            score += 1.5
        elif place_medium:
            score += 0.5
        if blog_hits >= 1:
            score += 1.25
        if blog_hits >= 2:
            score += 0.75
        if tistory_hits >= 1:
            score += 0.25

        if score >= 4.0 and blog_hits >= 2:
            status = "STRONG_PROBABLE"
        elif score >= 2.5 and (blog_hits >= 1 or place_strong):
            status = "PROBABLE"
        elif strong_hits >= 1 or medium_hits >= 1 or blog_hits >= 1 or self._has_any_view_signal(queries):
            status = "REVIEW"
        else:
            status = "REJECT"

        if status == "STRONG_PROBABLE":
            confidence = min(0.85, 0.72 + min(blog_hits, 3) * 0.03 + min(tistory_hits, 1) * 0.03)
        elif status == "PROBABLE":
            confidence = min(0.69, 0.52 + min(score - 2.5, 1.5) * 0.08 + min(blog_hits, 2) * 0.03)
        elif status == "REVIEW":
            confidence = min(0.49, 0.30 + 0.12 * hit_ratio + min(blog_hits, 1) * 0.05)
        else:
            confidence = 0.10

        positive_count = strong_hits + medium_hits + place_strong + place_medium + blog_hits
        source_count = int(strong_hits + medium_hits + place_strong + place_medium > 0) + int(blog_hits > 0)
        return {
            "rooftop_status": status,
            "rooftop_score": round(score, 2),
            "rooftop_confidence": round(confidence, 3),
            "rooftop_positive_evidence": positive_count,
            "rooftop_negative_evidence": 0,
            "rooftop_source_count": source_count,
            "rooftop_recent_negative": 0,
        }

    def _classify_view(
        self,
        cafe: dict,
        queries: list[str],
        terms: dict[str, tuple[str, ...]],
        hit_ratio: float,
        evidence: dict,
        code: str,
    ) -> dict:
        direct_hits = 0
        weak_hits = 0
        for query in queries:
            text = query.lower()
            if any(term in text for term in terms["direct"]):
                direct_hits += 1
            elif any(term in text for term in terms["weak"]):
                weak_hits += 1

        blog_hits = self._int(evidence.get(code))
        geo_strength = self._geo_support(cafe, code)

        raw_score = direct_hits * 1.0 + weak_hits * 0.35 + min(blog_hits, 3) * 1.25 + geo_strength
        if blog_hits >= 2 and direct_hits >= 1:
            score = 4
        elif blog_hits >= 1 and (direct_hits >= 1 or geo_strength >= 0.8):
            score = 3
        elif blog_hits >= 1 or direct_hits >= 1:
            score = 2
        elif weak_hits >= 1 and geo_strength >= 0.5:
            score = 1
        else:
            score = 0

        confidence = 0.0
        if direct_hits:
            confidence += 0.30
        if weak_hits:
            confidence += 0.10
        if blog_hits:
            confidence += 0.22 + min(blog_hits - 1, 2) * 0.09
        confidence += min(geo_strength, 1.0) * 0.18
        confidence += 0.05 * hit_ratio
        confidence = min(confidence, 0.85)
        if score == 0:
            confidence = 0.0
        elif blog_hits == 0:
            confidence = min(confidence, 0.52)

        return {
            "score": score,
            "raw_score": round(raw_score, 2),
            "confidence": round(confidence, 3),
            "positive_evidence": direct_hits + weak_hits + blog_hits,
            "negative_evidence": 0,
            "source_count": int(direct_hits + weak_hits > 0) + int(blog_hits > 0) + int(geo_strength > 0),
        }

    def _geo_support(self, cafe: dict, code: str) -> float:
        try:
            lat = float(cafe.get("latitude"))
            lon = float(cafe.get("longitude"))
        except (TypeError, ValueError):
            return 0.0

        if code == "HAN_RIVER":
            distance = min(haversine_m(lat, lon, tlat, tlon) for tlat, tlon in ViewDirectionEstimator.HAN_RIVER_LINE)
            return 1.0 if distance <= 1200 else 0.6 if distance <= 2500 else 0.0
        if code == "PALACE":
            distance = min(haversine_m(lat, lon, *target) for target in ViewDirectionEstimator.PALACE_TARGETS.values())
            return 1.0 if distance <= 900 else 0.5 if distance <= 1800 else 0.0
        if code == "FOREST":
            distance = min(haversine_m(lat, lon, *target) for target in ViewDirectionEstimator.FOREST_TARGETS.values())
            return 0.8 if distance <= 800 else 0.4 if distance <= 1800 else 0.0
        return 0.0

    def _query_families(self, queries: list[str]) -> set[str]:
        families: set[str] = set()
        if self._count_query_hits(queries, self.ROOFTOP_STRONG + self.ROOFTOP_MEDIUM):
            families.add("ROOFTOP")
        if any("노을" in q or "일몰" in q for q in queries):
            families.add("SUNSET")
        for code, terms in self.VIEW_TERMS.items():
            if self._view_hit_count(queries, terms):
                families.add(code)
        if any("뷰 좋은" in q or "전망" in q for q in queries):
            families.add("GENERIC_VIEW")
        return families

    def _has_any_view_signal(self, queries: list[str]) -> bool:
        return any(self._view_hit_count(queries, terms) for terms in self.VIEW_TERMS.values())

    @staticmethod
    def _queries(cafe: dict) -> list[str]:
        return [part.strip() for part in str(cafe.get("matched_queries", "") or "").split("|") if part.strip()]

    @classmethod
    def _hit_ratio(cls, cafe: dict, queries: list[str]) -> float:
        try:
            value = float(cafe.get("query_hit_ratio", ""))
            return max(0.0, min(1.0, value))
        except (TypeError, ValueError):
            total = cls._int(cafe.get("region_query_total"), len(queries) or 1)
            matched = cls._int(cafe.get("matched_query_count"), len(queries))
            return max(0.0, min(1.0, matched / max(total, 1)))

    @staticmethod
    def _count_query_hits(queries: list[str], terms: tuple[str, ...]) -> int:
        return sum(1 for query in queries if any(term in query.lower() for term in terms))

    @staticmethod
    def _view_hit_count(queries: list[str], terms: dict[str, tuple[str, ...]]) -> int:
        return sum(1 for query in queries if any(term in query.lower() for term in terms["direct"] + terms["weak"]))

    @staticmethod
    def _int(value: object, default: int = 0) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
