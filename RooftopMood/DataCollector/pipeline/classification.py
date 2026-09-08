from __future__ import annotations

import logging

from analyzers.kakao_signal_classifier import KakaoSignalClassifier
from settings import BASE_DIR
from utils import read_csv, write_csv

LOGGER = logging.getLogger(__name__)

CLASSIFICATION_FIELDS = [
    "cafe_id", "cafe_name", "region_code",
    "rooftop_status", "rooftop_score", "rooftop_confidence", "rooftop_positive_evidence",
    "rooftop_negative_evidence", "rooftop_source_count", "rooftop_recent_negative",
]
for code in ("han_river", "city", "palace", "forest"):
    CLASSIFICATION_FIELDS.extend([
        f"{code}_score", f"{code}_raw_score", f"{code}_confidence", f"{code}_positive_evidence",
        f"{code}_negative_evidence", f"{code}_source_count",
    ])

REVIEW_FIELDS = CLASSIFICATION_FIELDS + ["review_reasons"]
SIGNAL_FIELDS = [
    "cafe_id", "cafe_name", "region_code", "raw_match_count",
    "matched_query_count", "region_query_total", "query_hit_ratio",
    "query_family_count", "query_families", "matched_queries",
    "rooftop_query_hits", "han_river_query_hits", "city_query_hits", "palace_query_hits", "forest_query_hits",
    "blog_rooftop_evidence", "blog_sunset_evidence", "blog_han_river_evidence", "blog_city_evidence",
    "blog_palace_evidence", "blog_forest_evidence", "tistory_rooftop_evidence", "tistory_total_evidence",
]
DISCOVERY_FIELDS = ["view_candidate", "cafe_count", "evidence_count", "sample_evidence", "suggested_action"]


class ClassificationPipeline:
    """Kakao Local + Daum Blog Evidence로 Rooftop/View를 보수적으로 분류한다."""

    def run(self) -> tuple[list[dict], list[dict], list[dict]]:
        output_dir = BASE_DIR / "output"
        candidates_path = output_dir / "candidates_deduped.csv"
        if not candidates_path.exists():
            raise FileNotFoundError("candidates_deduped.csv가 없습니다. 먼저 discover를 실행하세요.")

        candidates = read_csv(candidates_path)
        evidence_path = output_dir / "evidence_summary.csv"
        evidence_rows = read_csv(evidence_path) if evidence_path.exists() else []
        evidence_by_id = {str(row.get("cafe_id", "")): row for row in evidence_rows}
        if not evidence_rows:
            LOGGER.warning("evidence_summary.csv가 없습니다. Local 신호만으로 보수적으로 분류합니다. evidence 실행을 권장합니다.")

        classifier = KakaoSignalClassifier()
        combined = classifier.classify_all(candidates, evidence_by_id)
        signal_rows = [
            classifier.signal_summary(cafe, evidence_by_id.get(str(cafe.get("cafe_id", "")), {}))
            for cafe in candidates
        ]

        review_rows: list[dict] = []
        for row in combined:
            reasons = self._review_reasons(row)
            if reasons:
                review = dict(row)
                review["review_reasons"] = "|".join(reasons)
                review_rows.append(review)

        discovered: list[dict] = []

        write_csv(output_dir / "cafe_classification.csv", combined, CLASSIFICATION_FIELDS)
        write_csv(output_dir / "kakao_signal_summary.csv", signal_rows, SIGNAL_FIELDS)
        write_csv(output_dir / "review_required.csv", review_rows, REVIEW_FIELDS)
        write_csv(output_dir / "discovered_views.csv", discovered, DISCOVERY_FIELDS)

        LOGGER.info(
            "Kakao V2 classification cafes=%d | strong_probable=%d | probable=%d | review=%d | reject=%d",
            len(combined),
            sum(row.get("rooftop_status") == "STRONG_PROBABLE" for row in combined),
            sum(row.get("rooftop_status") == "PROBABLE" for row in combined),
            sum(row.get("rooftop_status") == "REVIEW" for row in combined),
            sum(row.get("rooftop_status") == "REJECT" for row in combined),
        )
        return combined, review_rows, discovered

    @staticmethod
    def _review_reasons(row: dict) -> list[str]:
        reasons: list[str] = []
        status = row.get("rooftop_status")
        if status in {"STRONG_PROBABLE", "PROBABLE", "REVIEW"}:
            reasons.append("AUTO_CLASSIFICATION_NOT_CONFIRMED")
        if status == "REVIEW":
            reasons.append("ROOFTOP_EVIDENCE_WEAK")
        if float(row.get("rooftop_confidence", 0) or 0) < 0.65 and status not in {"REJECT"}:
            reasons.append("LOW_ROOFTOP_CONFIDENCE")
        for code in ("han_river", "city", "palace", "forest"):
            score = int(row.get(f"{code}_score", 0) or 0)
            confidence = float(row.get(f"{code}_confidence", 0) or 0)
            if score >= 2 and confidence < 0.6:
                reasons.append(f"LOW_{code.upper()}_CONFIDENCE")
        return reasons
