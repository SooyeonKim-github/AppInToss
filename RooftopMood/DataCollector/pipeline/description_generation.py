from __future__ import annotations

import logging

from analyzers.description_generator import TemplateDescriptionGenerator
from analyzers.view_feature_extractor import ViewFeatureExtractor
from analyzers.view_direction_estimator import ViewDirectionEstimator
from settings import BASE_DIR
from utils import read_csv, write_csv

LOGGER = logging.getLogger(__name__)

DESCRIPTION_FIELDS = [
    "cafe_id", "cafe_name", "region_code",
    "main_view", "main_view_score", "main_view_confidence", "view_position", "openness",
    "evidence_sunset_position", "evidence_sunset_position_confidence",
    "view_direction_deg", "view_direction_confidence", "view_direction_source", "view_direction_target",
    "landmarks", "feature_source_count",
    "view_description", "description_length", "description_confidence",
    "description_generated_by", "description_review_required", "description_reason",
]

DB_READY_FIELDS = [
    "cafe_id", "name", "category", "phone", "address", "road_address", "latitude", "longitude",
    "region_code", "kakao_place_id", "kakao_url", "naver_url", "providers",
    "rooftop_status", "rooftop_confidence",
    "han_river_score", "city_score", "palace_score", "forest_score",
    "main_view", "main_view_score", "main_view_confidence",
    "view_direction_deg", "view_direction_confidence", "view_direction_source", "view_direction_target",
    "landmarks", "view_description", "description_confidence",
    "description_generated_by", "description_review_required",
]


class DescriptionGenerationPipeline:
    def run(self) -> tuple[list[dict], list[dict]]:
        output_dir = BASE_DIR / "output"
        candidates_path = output_dir / "candidates_deduped.csv"
        classification_path = output_dir / "cafe_classification.csv"
        for path, command in (
            (candidates_path, "discover"),
            (classification_path, "classify"),
        ):
            if not path.exists():
                raise FileNotFoundError(f"{path.name}가 없습니다. 먼저 `{command}`를 실행하세요.")

        candidates = read_csv(candidates_path)
        classifications = read_csv(classification_path)
        candidate_by_id = {row.get("cafe_id", ""): row for row in candidates}

        extractor = ViewFeatureExtractor()
        generator = TemplateDescriptionGenerator()
        direction_estimator = ViewDirectionEstimator()
        description_rows: list[dict] = []
        db_rows: list[dict] = []

        for classification in classifications:
            cafe_id = classification.get("cafe_id", "")
            # Kakao-only V1: 오래된 Naver evidence 파일이 로컬에 남아 있어도 사용하지 않는다.
            cafe_evidence: list[dict] = []
            features = extractor.extract(classification, cafe_evidence)
            candidate = candidate_by_id.get(cafe_id, {})

            features["evidence_sunset_position"] = "UNKNOWN"
            features["evidence_sunset_position_confidence"] = 0.0
            view_direction = direction_estimator.estimate(candidate, features, cafe_evidence)
            features.update(view_direction)

            generated = generator.generate(features, classification.get("rooftop_status", ""))
            description = {
                "cafe_id": cafe_id,
                "cafe_name": classification.get("cafe_name", ""),
                "region_code": classification.get("region_code", ""),
                **features,
                **generated,
            }
            description_rows.append(description)

            db_rows.append({
                **candidate,
                "rooftop_status": classification.get("rooftop_status", ""),
                "rooftop_confidence": classification.get("rooftop_confidence", ""),
                "han_river_score": classification.get("han_river_score", ""),
                "city_score": classification.get("city_score", ""),
                "palace_score": classification.get("palace_score", ""),
                "forest_score": classification.get("forest_score", ""),
                **{k: description.get(k, "") for k in (
                    "main_view", "main_view_score", "main_view_confidence",
                    "view_direction_deg", "view_direction_confidence", "view_direction_source", "view_direction_target",
                    "landmarks", "view_description", "description_confidence",
                    "description_generated_by", "description_review_required",
                )},
            })

        write_csv(output_dir / "cafe_descriptions.csv", description_rows, DESCRIPTION_FIELDS)
        write_csv(output_dir / "cafe_db_ready.csv", db_rows, DB_READY_FIELDS)

        generated_count = sum(bool(row.get("view_description")) for row in description_rows)
        review_count = sum(int(row.get("description_review_required", 0) or 0) == 1 for row in description_rows)
        LOGGER.info("Descriptions generated=%d/%d | review_required=%d", generated_count, len(description_rows), review_count)
        return description_rows, db_rows
