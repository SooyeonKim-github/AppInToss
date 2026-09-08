from __future__ import annotations

import logging

from analyzers.other_view_discovery import OtherViewDiscovery
from analyzers.rooftop_classifier import RooftopClassifier
from analyzers.view_classifier import ViewClassifier
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
DISCOVERY_FIELDS = ["view_candidate", "cafe_count", "evidence_count", "sample_evidence", "suggested_action"]


class ClassificationPipeline:
    def run(self) -> tuple[list[dict], list[dict], list[dict]]:
        output_dir = BASE_DIR / "output"
        candidates_path = output_dir / "candidates_deduped.csv"
        evidence_path = output_dir / "cafe_evidences.csv"
        if not candidates_path.exists():
            raise FileNotFoundError("candidates_deduped.csv가 없습니다. 먼저 discover를 실행하세요.")
        if not evidence_path.exists():
            raise FileNotFoundError("cafe_evidences.csv가 없습니다. 먼저 evidence를 실행하세요.")

        candidates = read_csv(candidates_path)
        evidence_rows = read_csv(evidence_path)

        rooftop_rows = RooftopClassifier(BASE_DIR / "config" / "rooftop_keywords.yaml").classify_all(candidates, evidence_rows)
        view_rows = ViewClassifier(BASE_DIR / "config" / "view_keywords.yaml").classify_all(candidates, evidence_rows)
        view_by_id = {row["cafe_id"]: row for row in view_rows}

        combined: list[dict] = []
        review_rows: list[dict] = []
        for rooftop in rooftop_rows:
            merged = dict(rooftop)
            merged.update({k: v for k, v in view_by_id.get(rooftop["cafe_id"], {}).items() if k not in {"cafe_id", "cafe_name", "region_code"}})
            combined.append(merged)

            reasons = self._review_reasons(merged)
            if reasons:
                review = dict(merged)
                review["review_reasons"] = "|".join(reasons)
                review_rows.append(review)

        discovered = OtherViewDiscovery().discover(evidence_rows)

        write_csv(output_dir / "cafe_classification.csv", combined, CLASSIFICATION_FIELDS)
        write_csv(output_dir / "review_required.csv", review_rows, REVIEW_FIELDS)
        write_csv(output_dir / "discovered_views.csv", discovered, DISCOVERY_FIELDS)

        LOGGER.info(
            "Classification cafes=%d | confirmed=%d | review_required=%d | other_view_candidates=%d",
            len(combined),
            sum(row.get("rooftop_status") == "CONFIRMED" for row in combined),
            len(review_rows),
            len(discovered),
        )
        return combined, review_rows, discovered

    @staticmethod
    def _review_reasons(row: dict) -> list[str]:
        reasons: list[str] = []
        if row.get("rooftop_status") in {"PROBABLE", "REVIEW"}:
            reasons.append("ROOFTOP_UNCERTAIN")
        if float(row.get("rooftop_confidence", 0) or 0) < 0.65 and row.get("rooftop_status") != "REJECT":
            reasons.append("LOW_ROOFTOP_CONFIDENCE")
        if int(row.get("rooftop_recent_negative", 0) or 0) == 1:
            reasons.append("RECENT_NEGATIVE_EVIDENCE")
        for code in ("han_river", "city", "palace", "forest"):
            score = int(row.get(f"{code}_score", 0) or 0)
            confidence = float(row.get(f"{code}_confidence", 0) or 0)
            positives = int(row.get(f"{code}_positive_evidence", 0) or 0)
            negatives = int(row.get(f"{code}_negative_evidence", 0) or 0)
            if score >= 2 and confidence < 0.6:
                reasons.append(f"LOW_{code.upper()}_CONFIDENCE")
            if positives and negatives:
                reasons.append(f"CONFLICT_{code.upper()}")
        return reasons
