from __future__ import annotations


class KakaoSignalClassifier:
    """Kakao Local의 '같은 실제 지역 안에서의 검색 적중'만 후보 신호로 사용한다."""

    ROOFTOP_STRONG = ("루프탑", "옥상", "rooftop")
    ROOFTOP_MEDIUM = ("테라스", "야외")
    VIEW_TERMS = {
        "HAN_RIVER": {"direct": ("한강뷰", "한강 뷰", "리버뷰", "리버 뷰"), "weak": ("한강",)},
        "CITY": {"direct": ("시티뷰", "시티 뷰", "도심뷰", "도심 뷰", "서울야경", "서울 야경", "스카이라인"), "weak": ("야경", "도심")},
        "PALACE": {"direct": ("궁궐뷰", "궁궐 뷰", "경복궁뷰", "경복궁 뷰", "창덕궁뷰", "창덕궁 뷰", "덕수궁뷰", "덕수궁 뷰"), "weak": ("궁궐", "경복궁", "창덕궁", "덕수궁")},
        "FOREST": {"direct": ("숲뷰", "숲 뷰", "서울숲뷰", "서울숲 뷰", "녹지뷰", "녹지 뷰"), "weak": ("서울숲", "숲", "녹지")},
    }

    def classify_all(self, candidates: list[dict]) -> list[dict]:
        return [self.classify(cafe) for cafe in candidates]

    def classify(self, cafe: dict) -> dict:
        queries = self._queries(cafe)
        hit_ratio = self._hit_ratio(cafe, queries)
        rooftop = self._classify_rooftop(cafe, queries, hit_ratio)
        result = {"cafe_id": cafe.get("cafe_id", ""), "cafe_name": cafe.get("name", ""), "region_code": cafe.get("region_code", ""), **rooftop}
        for code, terms in self.VIEW_TERMS.items():
            view = self._classify_view(queries, terms, hit_ratio)
            result.update({f"{code.lower()}_{key}": value for key, value in view.items()})
        return result

    def signal_summary(self, cafe: dict) -> dict:
        queries = self._queries(cafe)
        return {
            "cafe_id": cafe.get("cafe_id", ""), "cafe_name": cafe.get("name", ""), "region_code": cafe.get("region_code", ""),
            "raw_match_count": self._int(cafe.get("raw_match_count"), len(queries)),
            "matched_query_count": self._int(cafe.get("matched_query_count"), len(queries)),
            "region_query_total": self._int(cafe.get("region_query_total"), len(queries) or 1),
            "query_hit_ratio": round(self._hit_ratio(cafe, queries), 3),
            "matched_queries": "|".join(queries),
            "rooftop_query_hits": self._count_query_hits(queries, self.ROOFTOP_STRONG),
            "han_river_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["HAN_RIVER"]),
            "city_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["CITY"]),
            "palace_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["PALACE"]),
            "forest_query_hits": self._view_hit_count(queries, self.VIEW_TERMS["FOREST"]),
        }

    def _classify_rooftop(self, cafe: dict, queries: list[str], hit_ratio: float) -> dict:
        strong_hits = self._count_query_hits(queries, self.ROOFTOP_STRONG)
        medium_hits = self._count_query_hits(queries, self.ROOFTOP_MEDIUM)
        place_text = f"{cafe.get('name', '')} {cafe.get('category', '')}".lower()
        place_strong = int(any(term in place_text for term in self.ROOFTOP_STRONG))
        place_medium = int(any(term in place_text for term in self.ROOFTOP_MEDIUM))
        score = strong_hits * 4.0 + medium_hits * 1.5 + place_strong * 2.0 + place_medium * 0.75

        if strong_hits >= 2 or (strong_hits >= 1 and place_strong): status = "CONFIRMED"
        elif strong_hits >= 1 or medium_hits >= 2: status = "PROBABLE"
        elif medium_hits >= 1 or (self._has_any_view_signal(queries) and hit_ratio >= 0.5): status = "REVIEW"
        else: status = "REJECT"

        if strong_hits:
            confidence = 0.54 + 0.12 * hit_ratio + min(max(strong_hits - 1, 0), 2) * 0.12 + (0.06 if place_strong else 0.0)
        elif medium_hits:
            confidence = 0.36 + 0.12 * hit_ratio + min(medium_hits, 2) * 0.05
        elif status == "REVIEW": confidence = 0.28 + 0.08 * hit_ratio
        else: confidence = 0.10
        if status == "CONFIRMED": confidence = max(confidence, 0.72)
        positive_count = strong_hits + medium_hits + place_strong + place_medium
        return {"rooftop_status": status, "rooftop_score": round(score, 2), "rooftop_confidence": round(min(confidence, 0.92), 3), "rooftop_positive_evidence": positive_count, "rooftop_negative_evidence": 0, "rooftop_source_count": 1 if positive_count else 0, "rooftop_recent_negative": 0}

    def _classify_view(self, queries: list[str], terms: dict[str, tuple[str, ...]], hit_ratio: float) -> dict:
        direct_hits = weak_hits = 0
        for query in queries:
            text = query.lower()
            if any(term in text for term in terms["direct"]): direct_hits += 1
            elif any(term in text for term in terms["weak"]): weak_hits += 1
        if direct_hits:
            raw_score = direct_hits * 3.0 + weak_hits * 0.75
            score = 5 if direct_hits >= 3 else 4 if direct_hits == 2 else 3
            confidence = 0.58 + 0.10 * hit_ratio + min(direct_hits - 1, 2) * 0.12 + min(weak_hits, 1) * 0.04
        elif weak_hits:
            raw_score = weak_hits * 1.0; score = 2 if weak_hits >= 2 else 1
            confidence = 0.34 + 0.10 * hit_ratio + min(weak_hits - 1, 2) * 0.08
        else:
            raw_score = 0.0; score = 0; confidence = 0.0
        return {"score": score, "raw_score": round(raw_score, 2), "confidence": round(min(confidence, 0.92), 3), "positive_evidence": direct_hits + weak_hits, "negative_evidence": 0, "source_count": 1 if direct_hits + weak_hits else 0}

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
        try: return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError): return default
